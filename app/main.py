from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from .db import Base, engine, get_db
from .models import Patient, Lesion, Assessment, Finding, AuditEvent
from .schemas import (
    PatientCreate, PatientOut, LesionCreate, LesionOut, AssessmentCreate,
    AssessmentOut, FindingCreate, FindingOut, FindingReview, AuditOut, TrendPoint,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)  # MVP only; migrations required before production.
    yield

app = FastAPI(
    title="feridasdotcom — protótipo",
    description="Protótipo técnico NÃO validado clinicamente. Não armazenar dados reais de pacientes.",
    version="0.1.0",
    lifespan=lifespan,
)

def audit(db: Session, kind: str, entity_id: str, action: str, actor: str, detail: str):
    db.add(AuditEvent(entity_type=kind, entity_id=entity_id, action=action, actor=actor, detail=detail))

def get_or_404(db: Session, model, object_id: str):
    item = db.get(model, object_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    return item

@app.get("/health")
def health():
    return {"status": "ok", "clinical_validation": False}

@app.post("/patients", response_model=PatientOut, status_code=201)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    if db.scalar(select(Patient).where(Patient.pseudonym == payload.pseudonym)):
        raise HTTPException(status_code=409, detail="Pseudônimo já existente")
    patient = Patient(pseudonym=payload.pseudonym)
    db.add(patient)
    db.flush()
    audit(db, "patient", patient.id, "created", "prototype", "Pseudonym created")
    db.commit()
    db.refresh(patient)
    return patient

@app.get("/patients", response_model=list[PatientOut])
def list_patients(db: Session = Depends(get_db)):
    return db.scalars(select(Patient).order_by(Patient.created_at.desc())).all()

@app.post("/lesions", response_model=LesionOut, status_code=201)
def create_lesion(payload: LesionCreate, db: Session = Depends(get_db)):
    get_or_404(db, Patient, payload.patient_id)
    lesion = Lesion(**payload.model_dump())
    db.add(lesion)
    db.flush()
    audit(db, "lesion", lesion.id, "created", "prototype", "Lesion created")
    db.commit()
    db.refresh(lesion)
    return lesion

@app.get("/patients/{patient_id}/lesions", response_model=list[LesionOut])
def patient_lesions(patient_id: str, db: Session = Depends(get_db)):
    get_or_404(db, Patient, patient_id)
    return db.scalars(select(Lesion).where(Lesion.patient_id == patient_id)).all()

@app.post("/assessments", response_model=AssessmentOut, status_code=201)
def create_assessment(payload: AssessmentCreate, db: Session = Depends(get_db)):
    get_or_404(db, Lesion, payload.lesion_id)
    if payload.area_cm2 is not None and not payload.area_method:
        raise HTTPException(status_code=422, detail="Método de mensuração obrigatório quando houver área")
    obj = Assessment(**payload.model_dump())
    db.add(obj)
    db.flush()
    audit(db, "assessment", obj.id, "created", "prototype", "Draft assessment created")
    db.commit()
    db.refresh(obj)
    return obj

@app.get("/lesions/{lesion_id}/assessments", response_model=list[AssessmentOut])
def list_assessments(lesion_id: str, db: Session = Depends(get_db)):
    get_or_404(db, Lesion, lesion_id)
    return db.scalars(select(Assessment).where(Assessment.lesion_id == lesion_id).order_by(Assessment.captured_at)).all()

@app.post("/assessments/{assessment_id}/findings", response_model=FindingOut, status_code=201)
def create_finding(assessment_id: str, payload: FindingCreate, db: Session = Depends(get_db)):
    assessment = get_or_404(db, Assessment, assessment_id)
    if assessment.status == "validated":
        raise HTTPException(status_code=409, detail="Avaliação finalizada; criar adendo em implementação futura")
    finding = Finding(assessment_id=assessment_id, **payload.model_dump())
    db.add(finding)
    db.flush()
    audit(db, "finding", finding.id, "proposed", "prototype", f"Finding proposed: {finding.field_name}")
    db.commit()
    db.refresh(finding)
    return finding

@app.get("/assessments/{assessment_id}/findings", response_model=list[FindingOut])
def list_findings(assessment_id: str, db: Session = Depends(get_db)):
    get_or_404(db, Assessment, assessment_id)
    return db.scalars(select(Finding).where(Finding.assessment_id == assessment_id)).all()

@app.post("/findings/{finding_id}/review", response_model=FindingOut)
def review_finding(finding_id: str, payload: FindingReview, db: Session = Depends(get_db)):
    finding = get_or_404(db, Finding, finding_id)
    assessment = get_or_404(db, Assessment, finding.assessment_id)
    if assessment.status == "validated" or finding.validation_status != "pending":
        raise HTTPException(status_code=409, detail="Revisão não permitida; registro deve preservar histórico")
    if payload.decision == "corrected" and not payload.corrected_text:
        raise HTTPException(status_code=422, detail="Correção exige texto")
    finding.validation_status = payload.decision
    finding.validated_text = payload.corrected_text if payload.decision == "corrected" else (
        finding.proposed_text if payload.decision == "confirmed" else None
    )
    finding.reviewed_by = payload.reviewer
    finding.reviewed_at = datetime.now(timezone.utc)
    audit(db, "finding", finding.id, "reviewed", payload.reviewer, f"Decision: {payload.decision}")
    db.commit()
    db.refresh(finding)
    return finding

@app.post("/assessments/{assessment_id}/finalize", response_model=AssessmentOut)
def finalize(assessment_id: str, reviewer: str, db: Session = Depends(get_db)):
    assessment = get_or_404(db, Assessment, assessment_id)
    if assessment.status == "validated":
        raise HTTPException(status_code=409, detail="Avaliação já finalizada")
    findings = db.scalars(select(Finding).where(Finding.assessment_id == assessment_id)).all()
    if not findings or any(f.validation_status == "pending" for f in findings):
        raise HTTPException(status_code=422, detail="Revise todos os achados antes de finalizar")
    assessment.status = "validated"
    audit(db, "assessment", assessment.id, "finalized", reviewer, "Assessment validated")
    db.commit()
    db.refresh(assessment)
    return assessment

@app.get("/lesions/{lesion_id}/trend", response_model=list[TrendPoint])
def lesion_trend(lesion_id: str, db: Session = Depends(get_db)):
    get_or_404(db, Lesion, lesion_id)
    assessments = db.scalars(
        select(Assessment).where(Assessment.lesion_id == lesion_id, Assessment.status == "validated")
        .order_by(Assessment.captured_at, Assessment.id)
    ).all()
    baseline = next((a.area_cm2 for a in assessments if a.area_cm2 is not None and a.area_cm2 > 0), None)
    return [
        TrendPoint(
            assessment_id=a.id, captured_at=a.captured_at, area_cm2=a.area_cm2,
            change_from_baseline_percent=(
                round((a.area_cm2 - baseline) / baseline * 100, 2)
                if baseline is not None and a.area_cm2 is not None else None
            )
        ) for a in assessments
    ]

@app.get("/audit/{entity_type}/{entity_id}", response_model=list[AuditOut])
def audit_log(entity_type: str, entity_id: str, db: Session = Depends(get_db)):
    return db.scalars(
        select(AuditEvent).where(AuditEvent.entity_type == entity_type, AuditEvent.entity_id == entity_id)
        .order_by(AuditEvent.occurred_at, AuditEvent.id)
    ).all()

# Interface local do protótipo (não disponibilizar publicamente sem autenticação).
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

@app.get('/', include_in_schema=False)
def home():
    return RedirectResponse(url='/app/')

app.mount('/app', StaticFiles(directory=Path(__file__).resolve().parent.parent / 'web', html=True), name='web')

# Mandatory single-owner access control and private media routes.
from .secure_routes import install_security
install_security(app)

# Optional multimodal visual draft. Authentication middleware applies to these routes too.
from .vision_routes import router as vision_router
app.include_router(vision_router)
