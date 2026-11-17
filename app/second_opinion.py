"""Evidence-gated assembly of human-reviewed clinical context.

Only current-assessment data are included. No unreviewed visual findings,
no historical inheritance, no diagnoses, no image inference and no advice.
The resulting snapshot is an INPUT for a later independently validated system.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Assessment, Finding, ClinicalHistoryRecord, TreatmentIntervention
from .second_opinion_schemas import (
    Provenance, ValidatedObservation, ClinicalDatum,
    InterventionSnapshot, ContextSnapshot, EvidenceReadiness,
)

def latest_history(db: Session, assessment_id: str):
    return db.scalar(
        select(ClinicalHistoryRecord)
        .where(ClinicalHistoryRecord.assessment_id == assessment_id)
        .order_by(ClinicalHistoryRecord.revision.desc(), ClinicalHistoryRecord.recorded_at.desc())
    )

def make_context(db: Session, assessment: Assessment) -> ContextSnapshot:
    findings = db.scalars(
        select(Finding).where(Finding.assessment_id == assessment.id)
        .order_by(Finding.field_name, Finding.id)
    ).all()
    observations = []
    for f in findings:
        if f.validation_status not in ("confirmed", "corrected"):
            continue
        if f.support == "not_evaluable" or f.source == "unknown":
            continue
        if not f.validated_text or not f.reviewed_by or not f.reviewed_at:
            continue
        observations.append(ValidatedObservation(
            field_name=f.field_name,
            text=f.validated_text,
            proposed_source=f.source,
            support_at_proposal=f.support,
            human_decision=f.validation_status,
            provenance=Provenance(assessment_id=assessment.id, record_id=f.id,
                                  recorded_at=f.reviewed_at, recorder_id=f.reviewed_by),
        ))
    history = latest_history(db, assessment.id)
    data = []
    if history is not None:
        for key, value in sorted(history.data.items()):
            # Explicit null/unknown are not positive or negative findings.
            if value is None or (isinstance(value, str) and value.strip().lower() in ("", "unknown", "not_assessed")):
                continue
            data.append(ClinicalDatum(
                field_name=key, value=value, reporter=history.reporter,
                provenance=Provenance(assessment_id=assessment.id, record_id=history.id,
                                      recorded_at=history.recorded_at, recorder_id=history.recorder_id),
            ))
    treatment_records = db.scalars(
        select(TreatmentIntervention).where(TreatmentIntervention.assessment_id == assessment.id)
        .order_by(TreatmentIntervention.recorded_at, TreatmentIntervention.id)
    ).all()
    interventions = [
        InterventionSnapshot(
            type=i.type, status=i.status, description=i.description,
            performed_at=i.performed_at,
            provenance=Provenance(assessment_id=assessment.id, record_id=i.id,
                                  recorded_at=i.recorded_at, recorder_id=i.recorder_id),
        ) for i in treatment_records
    ]
    missing_sections = []
    if not observations:
        missing_sections.append("semiologia_confirmada")
    if history is None:
        missing_sections.append("anamnese_atual_registrada")
    if not interventions:
        missing_sections.append("intervencoes_registradas")
    if assessment.area_cm2 is None:
        missing_sections.append("area_mensurada")
    else:
        # Current area is stored separately in legacy assessment and is not human validated field-by-field.
        missing_sections.append("validacao_especifica_da_area")
    return ContextSnapshot(
        assessment_id=assessment.id, lesion_id=assessment.lesion_id,
        assessment_status=assessment.status if assessment.status in ("draft","validated") else "draft",
        observations=observations,
        reported_clinical_data=data,
        interventions=interventions,
        warnings=list(history.alerts) if history is not None else [],
        excluded_unreviewed_count=sum(f.validation_status == "pending" for f in findings),
        excluded_rejected_count=sum(f.validation_status == "rejected" for f in findings),
        not_evaluable_count=sum(f.support == "not_evaluable" for f in findings),
        history_revision=history.revision if history is not None else None,
        missing_sections=missing_sections,
    )

def make_evidence_readiness(db: Session, assessment: Assessment) -> EvidenceReadiness:
    # Deliberately empty until an externally verified/versioned evidence corpus exists.
    # Never present model generated sources as verified.
    return EvidenceReadiness(context=make_context(db, assessment))
