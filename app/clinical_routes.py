"""Structured clinical history and treatment log (synthetic-data MVP).

No diagnosis, no model inference, no automatic inheritance of clinical findings.
Records are append-only at the API level; finalized assessments reject writes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from .db import get_db
from .models import Assessment, ClinicalHistoryRecord, TreatmentIntervention, AuditEvent
from .clinical_schemas import ClinicalHistoryIn, ClinicalHistoryOut, InterventionIn, InterventionOut
from .clinical_rules import generate_history_warnings

router = APIRouter(tags=["Structured clinical history"])

def get_assessment(db: Session, assessment_id: str) -> Assessment:
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada")
    return assessment

def ensure_editable(assessment: Assessment):
    if assessment.status == "validated":
        raise HTTPException(status_code=409, detail="Avaliação finalizada. Correções exigem adendo formal em versão futura.")

def serialize_history(item: ClinicalHistoryRecord) -> ClinicalHistoryOut:
    return ClinicalHistoryOut(id=item.id, assessment_id=item.assessment_id,
                              revision=item.revision, recorded_at=item.recorded_at,
                              recorder_id=item.recorder_id, reporter=item.reporter,
                              data=item.data, alerts=item.alerts)

@router.post("/assessments/{assessment_id}/history", response_model=ClinicalHistoryOut, status_code=201)
def record_history(assessment_id: str, payload: ClinicalHistoryIn, db: Session = Depends(get_db)):
    assessment = get_assessment(db, assessment_id)
    ensure_editable(assessment)
    latest = db.scalar(select(func.max(ClinicalHistoryRecord.revision)).where(ClinicalHistoryRecord.assessment_id == assessment_id))
    data = payload.model_dump(exclude={"human_confirmed", "recorder_id", "reporter"}, mode="json")
    alerts = generate_history_warnings(payload)
    record = ClinicalHistoryRecord(assessment_id=assessment_id, revision=(latest or 0) + 1,
                                   recorder_id=payload.recorder_id, reporter=payload.reporter,
                                   data=data, alerts=alerts)
    db.add(record)
    db.flush()
    db.add(AuditEvent(entity_type="assessment", entity_id=assessment_id,
                      action="history_recorded", actor="owner",
                      detail=f"history_id={record.id};revision={record.revision};alert_count={len(alerts)}"))
    db.commit()
    db.refresh(record)
    return serialize_history(record)

@router.get("/assessments/{assessment_id}/history", response_model=list[ClinicalHistoryOut])
def history_revisions(assessment_id: str, db: Session = Depends(get_db)):
    get_assessment(db, assessment_id)
    records = db.scalars(select(ClinicalHistoryRecord)
                         .where(ClinicalHistoryRecord.assessment_id == assessment_id)
                         .order_by(ClinicalHistoryRecord.revision)).all()
    return [serialize_history(x) for x in records]

@router.get("/assessments/{assessment_id}/previous-history")
def previous_history(assessment_id: str, db: Session = Depends(get_db)):
    assessment = get_assessment(db, assessment_id)
    older = db.scalars(select(Assessment)
                       .where(Assessment.lesion_id == assessment.lesion_id,
                              Assessment.status == "validated",
                              Assessment.captured_at < assessment.captured_at)
                       .order_by(Assessment.captured_at.desc(), Assessment.id.desc())).all()
    for prior in older:
        last = db.scalar(select(ClinicalHistoryRecord)
                         .where(ClinicalHistoryRecord.assessment_id == prior.id)
                         .order_by(ClinicalHistoryRecord.revision.desc()))
        if last is not None:
            return {
                "source_assessment_id": prior.id,
                "source_captured_at": prior.captured_at,
                "revision": last.revision,
                "data": last.data,
                "warning": "Dados históricos, não verificados na avaliação atual. Não importar como achados confirmados.",
            }
    return {"source_assessment_id": None, "data": None,
            "warning": "Não há anamnese anterior validada para esta lesão."}

@router.post("/assessments/{assessment_id}/interventions", response_model=InterventionOut, status_code=201)
def create_intervention(assessment_id: str, payload: InterventionIn, db: Session = Depends(get_db)):
    assessment = get_assessment(db, assessment_id)
    ensure_editable(assessment)
    intervention = TreatmentIntervention(
        assessment_id=assessment_id, type=payload.type, status=payload.status,
        description=payload.description, performed_at=payload.performed_at,
        recorder_id=payload.recorder_id, notes=payload.notes,
    )
    db.add(intervention)
    db.flush()
    db.add(AuditEvent(entity_type="assessment", entity_id=assessment_id,
                      action="intervention_recorded", actor="owner",
                      detail=f"intervention_id={intervention.id};type={intervention.type};status={intervention.status}"))
    db.commit()
    db.refresh(intervention)
    return InterventionOut.model_validate(intervention, from_attributes=True)

@router.get("/assessments/{assessment_id}/interventions", response_model=list[InterventionOut])
def list_interventions(assessment_id: str, db: Session = Depends(get_db)):
    get_assessment(db, assessment_id)
    return db.scalars(select(TreatmentIntervention)
                      .where(TreatmentIntervention.assessment_id == assessment_id)
                      .order_by(TreatmentIntervention.recorded_at, TreatmentIntervention.id)).all()

@router.get("/lesions/{lesion_id}/interventions", response_model=list[InterventionOut])
def list_lesion_interventions(lesion_id: str, db: Session = Depends(get_db)):
    from .models import Lesion
    if db.get(Lesion, lesion_id) is None:
        raise HTTPException(status_code=404, detail="Lesão não encontrada")
    return db.scalars(select(TreatmentIntervention)
                      .join(Assessment, TreatmentIntervention.assessment_id == Assessment.id)
                      .where(Assessment.lesion_id == lesion_id)
                      .order_by(TreatmentIntervention.recorded_at, TreatmentIntervention.id)).all()

@router.get("/lesions/{lesion_id}/clinical-timeline")
def clinical_timeline(lesion_id: str, db: Session = Depends(get_db)):
    """Latest signed-in-session entries per assessment, no diagnostic inference."""
    from .models import Lesion
    if db.get(Lesion, lesion_id) is None:
        raise HTTPException(status_code=404, detail="Lesão não encontrada")
    assessments = db.scalars(select(Assessment)
        .where(Assessment.lesion_id == lesion_id)
        .order_by(Assessment.captured_at, Assessment.id)).all()
    result = []
    for assessment in assessments:
        history = db.scalar(select(ClinicalHistoryRecord)
            .where(ClinicalHistoryRecord.assessment_id == assessment.id)
            .order_by(ClinicalHistoryRecord.revision.desc()))
        interventions = db.scalars(select(TreatmentIntervention)
            .where(TreatmentIntervention.assessment_id == assessment.id)
            .order_by(TreatmentIntervention.recorded_at, TreatmentIntervention.id)).all()
        result.append({
            "assessment_id": assessment.id,
            "captured_at": assessment.captured_at,
            "assessment_status": assessment.status,
            "history": serialize_history(history).model_dump(mode="json") if history is not None else None,
            "interventions": [InterventionOut.model_validate(x, from_attributes=True).model_dump(mode="json")
                              for x in interventions],
            "clinical_validation": False,
        })
    return result
