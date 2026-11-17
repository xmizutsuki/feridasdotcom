"""Photo-to-photo comparison metadata: not a clinical image registration algorithm."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .db import get_db
from .models import Photo, Assessment
from .media import read_encrypted
from .quality import inspect_quality
from .security import settings

router = APIRouter(prefix="/photos", tags=["Experimental longitudinal comparison"])

@router.get("/{current_id}/compare/{previous_id}")
def compare_photo_metadata(current_id: str, previous_id: str, db: Session = Depends(get_db)):
    if current_id == previous_id:
        raise HTTPException(status_code=422, detail="Selecione duas fotografias diferentes")
    current, previous = db.get(Photo, current_id), db.get(Photo, previous_id)
    if current is None or previous is None:
        raise HTTPException(status_code=404, detail="Fotografia não encontrada")
    current_assessment = db.get(Assessment, current.assessment_id)
    previous_assessment = db.get(Assessment, previous.assessment_id)
    if current_assessment is None or previous_assessment is None:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada")
    if current_assessment.lesion_id != previous_assessment.lesion_id:
        raise HTTPException(status_code=409, detail="Não comparar lesões diferentes")
    if current.assessment_id == previous.assessment_id:
        raise HTTPException(status_code=422, detail="Selecione fotografias de avaliações distintas")
    if current_assessment.captured_at <= previous_assessment.captured_at:
        raise HTTPException(status_code=422, detail="A avaliação atual precisa ser posterior à anterior")
    config = settings()
    try:
        cq = inspect_quality(read_encrypted(current.filename, config))
        pq = inspect_quality(read_encrypted(previous.filename, config))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Imagem indisponível") from exc
    return {
        "lesion_id": current_assessment.lesion_id,
        "current_photo_id": current_id,
        "previous_photo_id": previous_id,
        "current_quality": cq.model_dump(),
        "previous_quality": pq.model_dump(),
        "same_pixel_dimensions": current.width == previous.width and current.height == previous.height,
        "spatial_alignment_validated": False,
        "quantitative_area_comparison_allowed": False,
        "interpretation": "Comparação de metadados somente. Ângulo, escala, distância, iluminação e evolução tecidual ainda requerem avaliação profissional.",
    }
