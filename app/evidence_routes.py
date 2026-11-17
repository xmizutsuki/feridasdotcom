"""Publisher catalog and operator-reviewed evidence excerpt API.

A human declaration that a passage was checked does not constitute independent
scientific appraisal. No diagnosis, therapeutic recommendation or clinical approval.
"""
import hashlib
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from .db import get_db
from .evidence_catalog import CATALOG
from .evidence_retrieval import SOURCE_BY_ID, retrieve
from .evidence_schemas import EvidencePassageIn, EvidencePassageOut, EvidenceSearchResult
from .models import AuditEvent, EvidencePassage

router = APIRouter(prefix="/evidence", tags=["Experimental scientific library"])

@router.get("/catalog")
def catalog():
    return {"sources": CATALOG, "content_verified": False,
            "note": "Editora identificada; nenhum trecho ou recomendação clínica está validado pelo catálogo."}

@router.post("/passages", response_model=EvidencePassageOut, status_code=201)
def add_passage(payload: EvidencePassageIn, db: Session = Depends(get_db)):
    if payload.catalog_source_id not in SOURCE_BY_ID:
        raise HTTPException(status_code=422, detail="Fonte não pertence ao catálogo fechado.")
    # Fixed metadata prevent URL injection and untraceable invented publishers.
    excerpt_hash = hashlib.sha256(payload.excerpt.encode("utf-8")).hexdigest()
    duplicate = db.scalar(select(EvidencePassage).where(
        EvidencePassage.catalog_source_id == payload.catalog_source_id,
        EvidencePassage.excerpt_sha256 == excerpt_hash,
    ))
    if duplicate is not None:
        raise HTTPException(status_code=409, detail="Trecho já cadastrado para essa fonte.")
    item = EvidencePassage(
        catalog_source_id=payload.catalog_source_id,
        source_location=payload.source_location,
        excerpt=payload.excerpt,
        excerpt_sha256=excerpt_hash,
        language=payload.language,
        topic_tags=payload.topic_tags,
        applicability_notes=payload.applicability_notes,
        reviewed_by=payload.reviewed_by,
    )
    db.add(item)
    db.flush()
    db.add(AuditEvent(
        entity_type="evidence_passage", entity_id=item.id, action="operator_attested",
        actor="owner", detail=f"source={item.catalog_source_id};sha256={excerpt_hash};independent_review=false",
    ))
    db.commit()
    db.refresh(item)
    return EvidencePassageOut.model_validate(item)

@router.get("/passages", response_model=list[EvidencePassageOut])
def list_passages(db: Session = Depends(get_db)):
    return db.scalars(select(EvidencePassage).order_by(EvidencePassage.reviewed_at.desc())).all()

@router.get("/search", response_model=EvidenceSearchResult)
def search_passages(
    q: str = Query(min_length=2, max_length=180),
    limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    return retrieve(db, q, limit)
