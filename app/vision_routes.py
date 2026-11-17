"""Explicit opt-in AI draft generation, no automatic clinical validation."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from .db import get_db
from .models import Assessment, Photo, Finding, AuditEvent
from .media import read_encrypted
from .security import settings
from .vision import analyze_photo, enabled

router = APIRouter(prefix="/assessments", tags=["Experimental image analysis"])

@router.get("/ai/status")
def ai_status():
    return {
        "enabled": enabled(),
        "scope": "visual_description_draft_only",
        "clinical_validation": False,
    }

@router.post("/{assessment_id}/analyze-image", status_code=201)
async def generate_visual_draft(
    assessment_id: str,
    photo_id: str = Query(..., min_length=36, max_length=36),
    confirm_external_processing: bool = Query(False),
    db: Session = Depends(get_db),
):
    if not confirm_external_processing:
        raise HTTPException(status_code=412, detail="Confirmação explícita de envio externo é obrigatória")
    if not enabled():
        raise HTTPException(status_code=503, detail="Análise remota não configurada")
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada")
    if assessment.status == "validated":
        raise HTTPException(status_code=409, detail="Avaliação finalizada")
    photo = db.get(Photo, photo_id)
    if photo is None or photo.assessment_id != assessment_id:
        raise HTTPException(status_code=404, detail="Foto não pertence à avaliação")
    existing = db.scalars(select(Finding).where(Finding.assessment_id == assessment_id)).all()
    if existing:
        raise HTTPException(status_code=409, detail="Revisar achados existentes antes de uma nova análise. Não sobrescrever conteúdo humano.")
    config = settings()
    try:
        image = read_encrypted(photo.filename, config)
        result, model = await analyze_photo(image)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception:
        # Do not leak credential, patient data or response bodies from external provider.
        raise HTTPException(status_code=502, detail="Falha na análise remota ou resposta inválida") from None
    for candidate in result.findings:
        db.add(Finding(
            assessment_id=assessment_id,
            field_name=candidate.field_name,
            proposed_text=candidate.proposed_text,
            source=candidate.source,
            support=candidate.support,
            validation_status="pending",
        ))
    db.add(AuditEvent(
        entity_type="assessment", entity_id=assessment_id, action="ai_visual_draft",
        actor="system", detail=f"Model={model}; photo={photo.id}; fields={len(result.findings)}; UNVALIDATED",
    ))
    db.commit()
    return {
        "assessment_id": assessment_id,
        "photo_id": photo_id,
        "model": model,
        "status": "pending_human_review",
        "needs_better_image": result.needs_better_image,
        "capture_guidance": result.capture_guidance,
        "limitations": result.limitations,
        "findings_created": len(result.findings),
        "clinical_validation": False,
    }
