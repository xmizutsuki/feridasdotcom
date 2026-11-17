"""Read-only experimental preparation for future evidence-grounded second opinion."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .db import get_db
from .models import Assessment
from .second_opinion import make_context, make_evidence_readiness
from .second_opinion_schemas import ContextSnapshot, EvidenceReadiness

router = APIRouter(prefix="/assessments", tags=["Second opinion preparation"])

def assessment_or_404(db: Session, assessment_id: str):
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada")
    return assessment

@router.get("/{assessment_id}/clinical-context", response_model=ContextSnapshot)
def clinical_context(assessment_id: str, db: Session = Depends(get_db)):
    return make_context(db, assessment_or_404(db, assessment_id))

@router.get("/{assessment_id}/evidence-readiness", response_model=EvidenceReadiness)
def evidence_readiness(assessment_id: str, db: Session = Depends(get_db)):
    return make_evidence_readiness(db, assessment_or_404(db, assessment_id))
