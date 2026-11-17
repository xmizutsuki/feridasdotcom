"""Controlled scientific document ingestion and page-text citation verification.

Machine verification establishes only that text appears on a specific page of
a specific uploaded PDF. It does NOT verify clinical applicability, accuracy,
publisher authenticity, licensing or whether the document is current.
"""
import hashlib
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session
from sqlalchemy import select
from .db import get_db
from .models import EvidenceDocument, VerifiedCitation, AuditEvent
from .evidence_retrieval import SOURCE_BY_ID
from .pdf_evidence import read_pages, check_citation, MAX_PDF_BYTES
from .media import store_encrypted, read_encrypted
from .security import settings

router = APIRouter(prefix="/evidence/documents", tags=["PDF evidence verification"])

class VerifyQuote(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    page_number: int = Field(ge=1, le=100)
    excerpt: str = Field(min_length=20, max_length=500)
    checked_by: str = Field(min_length=2, max_length=100)

@router.post("", status_code=201)
async def upload_document(
    source_id: str,
    edition_label: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if source_id not in SOURCE_BY_ID:
        raise HTTPException(status_code=422, detail="Fonte deve constar no catálogo fechado")
    edition_label = edition_label.strip()
    if not 1 <= len(edition_label) <= 100:
        raise HTTPException(status_code=422, detail="Edição inválida")
    if file.filename is None or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=422, detail="Envie apenas PDF")
    data = await file.read(MAX_PDF_BYTES + 1)
    try:
        pages = read_pages(data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    digest = hashlib.sha256(data).hexdigest()
    existing = db.scalar(select(EvidenceDocument).where(EvidenceDocument.sha256 == digest))
    if existing:
        raise HTTPException(status_code=409, detail="PDF já cadastrado")
    filename, _ = store_encrypted(data, settings())
    item = EvidenceDocument(
        catalog_source_id=source_id, edition_label=edition_label,
        filename=filename, sha256=digest, page_count=len(pages),
    )
    db.add(item)
    db.flush()
    db.add(AuditEvent(
        entity_type="evidence_document", entity_id=item.id,
        action="uploaded", actor="owner",
        detail=f"source={source_id};sha256={digest};pages={len(pages)};publisher_unverified",
    ))
    db.commit()
    db.refresh(item)
    return {"id": item.id, "source_id": item.catalog_source_id,
            "edition_label": item.edition_label, "page_count": item.page_count,
            "sha256": item.sha256, "publisher_authenticity_verified": False,
            "clinical_use_authorized": False}

@router.get("")
def list_documents(db: Session = Depends(get_db)):
    records = db.scalars(select(EvidenceDocument).order_by(EvidenceDocument.uploaded_at.desc())).all()
    return [{"id": r.id, "source_id": r.catalog_source_id, "edition_label": r.edition_label,
             "page_count": r.page_count, "sha256": r.sha256, "uploaded_at": r.uploaded_at,
             "clinical_use_authorized": False} for r in records]

@router.post("/{document_id}/verify-quote", status_code=201)
def verify_quote(document_id: str, payload: VerifyQuote, db: Session = Depends(get_db)):
    document = db.get(EvidenceDocument, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    try:
        original = read_encrypted(document.filename, settings())
        quote_hash, page_hash = check_citation(original, payload.page_number, payload.excerpt)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    existing = db.scalar(select(VerifiedCitation).where(
        VerifiedCitation.document_id == document.id,
        VerifiedCitation.page_number == payload.page_number,
        VerifiedCitation.excerpt_sha256 == quote_hash,
    ))
    if existing:
        raise HTTPException(status_code=409, detail="Essa citação já foi verificada")
    record = VerifiedCitation(
        document_id=document.id, page_number=payload.page_number,
        excerpt=payload.excerpt, excerpt_sha256=quote_hash,
        page_text_sha256=page_hash, checked_by=payload.checked_by,
    )
    db.add(record)
    db.flush()
    db.add(AuditEvent(
        entity_type="verified_citation", entity_id=record.id,
        action="machine_page_match", actor="owner",
        detail=f"document={document.id};page={record.page_number};page_hash={page_hash};clinical_review=false",
    ))
    db.commit()
    db.refresh(record)
    return {"id": record.id, "document_id": document.id,
            "page_number": record.page_number, "excerpt": record.excerpt,
            "excerpt_sha256": record.excerpt_sha256, "page_text_sha256": record.page_text_sha256,
            "verification_method": "extracted_text_exact_substring_v1",
            "matched_in_uploaded_document": True, "independent_clinical_review": False,
            "clinical_applicability_validated": False}

@router.get("/{document_id}/citations")
def list_citations(document_id: str, db: Session = Depends(get_db)):
    if db.get(EvidenceDocument, document_id) is None:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    citations = db.scalars(select(VerifiedCitation).where(
        VerifiedCitation.document_id == document_id
    ).order_by(VerifiedCitation.page_number, VerifiedCitation.id)).all()
    return [{"id": c.id, "document_id": c.document_id, "page_number": c.page_number,
             "excerpt": c.excerpt, "verification_method": "extracted_text_exact_substring_v1",
             "clinical_applicability_validated": False} for c in citations]
