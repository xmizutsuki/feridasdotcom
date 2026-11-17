"""Opt-in experimental reasoning from synthetic cases only.

Fails closed on missing human-review, citations, severe warning or bad model JSON.
Never persists diagnoses, issues orders, or approves treatment.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session
from .db import get_db
from .models import Assessment, VerifiedCitation, EvidenceDocument, AuditEvent
from .second_opinion import make_context
from .reasoning import enabled, generate_draft, audit_draft
from .reasoning_schemas import ReasoningAuditResult
from .semantic_audit import enabled as semantic_enabled, review_semantics, evaluate_verdicts
from .pdf_evidence import check_citation
from .media import read_encrypted
from .security import settings

router = APIRouter(prefix="/assessments", tags=["Experimental synthetic reasoning"])

class ReasoningRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    citation_ids: list[str] = Field(min_length=1, max_length=8)
    confirm_synthetic_scenario: bool
    confirm_external_processing: bool

@router.get("/reasoning/status")
def reasoning_status():
    return {"enabled": enabled(), "semantic_reviewer_enabled": semantic_enabled(), "synthetic_only": True,
            "clinical_validation": False, "therapeutic_recommendations_enabled": False}

@router.post("/{assessment_id}/reasoning-draft", response_model=ReasoningAuditResult)
async def reasoning_draft(
    assessment_id: str, payload: ReasoningRequest, db: Session = Depends(get_db),
):
    if not payload.confirm_synthetic_scenario or not payload.confirm_external_processing:
        raise HTTPException(status_code=412, detail="Confirme cenário sintético e envio externo")
    if not enabled():
        raise HTTPException(status_code=503, detail="Análise experimental não habilitada")
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada")
    context = make_context(db, assessment)
    if assessment.status != "validated" or not context.observations or not context.reported_clinical_data:
        raise HTTPException(status_code=409, detail="Finalize avaliação com achados revisados e anamnese atual")
    if context.excluded_unreviewed_count:
        raise HTTPException(status_code=409, detail="Existem achados não revisados")
    urgent = any(a.get("priority") == "urgent_review" for a in context.warnings)
    if urgent:
        raise HTTPException(status_code=409, detail="Sinais relatados exigem avaliação presencial prioritária; não executar raciocínio automatizado")
    if len(payload.citation_ids) != len(set(payload.citation_ids)):
        raise HTTPException(status_code=422, detail="Citações duplicadas")
    citations = []
    config = settings()
    try:
        for citation_id in payload.citation_ids:
            citation = db.get(VerifiedCitation, citation_id)
            if citation is None:
                raise HTTPException(status_code=422, detail="Citação selecionada inexistente")
            document = db.get(EvidenceDocument, citation.document_id)
            if document is None:
                raise HTTPException(status_code=422, detail="Documento ausente")
            pdf = read_encrypted(document.filename, config)
            quote_digest, page_digest = check_citation(pdf, citation.page_number, citation.excerpt)
            if quote_digest != citation.excerpt_sha256 or page_digest != citation.page_text_sha256:
                raise HTTPException(status_code=409, detail="Documento/citação alterado desde a verificação")
            citations.append({
                "citation_id": citation.id,
                "catalog_source_id": document.catalog_source_id,
                "edition": document.edition_label,
                "page": citation.page_number,
                "quote": citation.excerpt,
                "publisher_authenticity_verified": False,
                "clinical_applicability_verified": False,
            })
    except ValueError:
        raise HTTPException(status_code=409, detail="PDF não disponível para reconferência") from None
    # Only de-identified, explicitly reviewed fields: never send IDs of patient or lesion.
    observations = [
        {"record_id": o.provenance.record_id, "field": o.field_name, "text": o.text,
         "origin": o.proposed_source, "reviewed": True}
        for o in context.observations
    ]
    observations += [
        {"record_id": d.provenance.record_id, "field": d.field_name,
         "value": d.value, "reporter": d.reporter, "reviewed": True}
        for d in context.reported_clinical_data
    ]
    # Anamnesis values are still user-generated; send synthetic test data only.
    context_for_model = {
        "observations": observations[:50], "missing_sections": context.missing_sections,
        "assessments_from_prior_visits": "not_included",
        "clinical_validation": False,
    }
    try:
        draft, model_name = await generate_draft(context_for_model, citations)
    except Exception:
        # Never expose model responses, credentials, or clinical context in errors.
        raise HTTPException(status_code=502, detail="Falha no modelo ou contrato de saída inválido") from None
    allowed = {o["record_id"] for o in observations}
    audited = audit_draft(assessment_id, model_name, draft, allowed,
                          set(payload.citation_ids), urgent=False)
    # Independent reviewer must be configured separately from the generator.
    # Structural consistency does not substitute semantic review; fail closed.
    if audited.status != "blocked":
        if not semantic_enabled():
            audited.status = "blocked"
            for hypothesis in audited.hypotheses:
                hypothesis.semantic_audit_status = "blocked"
                hypothesis.semantic_audit_issues.append(
                    "Revisão semântica independente não configurada"
                )
        else:
            try:
                semantic, reviewer_model = await review_semantics(
                    context_for_model,
                    [item.model_dump() for item in draft.hypotheses],
                    citations,
                )
                issues_by_hypothesis = evaluate_verdicts(
                    [item.model_dump() for item in draft.hypotheses], semantic
                )
                audited.semantic_audit_performed = True
                audited.semantic_audit_model = reviewer_model
                for hypothesis, issues in zip(audited.hypotheses, issues_by_hypothesis):
                    hypothesis.semantic_audit_issues = issues
                    hypothesis.semantic_audit_status = (
                        "blocked" if issues else "reviewer_supported"
                    )
                if any(issues_by_hypothesis):
                    audited.status = "blocked"
            except Exception:
                audited.status = "blocked"
                for hypothesis in audited.hypotheses:
                    hypothesis.semantic_audit_status = "blocked"
                    hypothesis.semantic_audit_issues.append(
                        "Revisão independente falhou ou retornou resposta incompleta"
                    )
    # Even reviewer-supported results remain experimental and clinically unvalidated.
    db.add(AuditEvent(
        entity_type="assessment", entity_id=assessment_id,
        action="synthetic_reasoning_attempt", actor="owner",
        detail=f"model={model_name[:80]};outcome={audited.status};hypotheses={len(draft.hypotheses)};synthetic_only=true",
    ))
    db.commit()
    return audited
