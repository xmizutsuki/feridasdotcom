"""Read-only audit of operator-authored hypotheses; no generated diagnoses.

The engine checks record provenance and exact-page citation IDs only. It cannot
assess whether evidence logically supports the hypothesis or whether a clinical
action is safe. There is no endpoint for executing a treatment suggestion.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .db import get_db
from .models import Assessment, VerifiedCitation
from .second_opinion import make_context
from .differential_schemas import (
    DifferentialAuditInput, DifferentialAuditResult, DifferentialCandidateAudit,
)

router = APIRouter(prefix="/assessments", tags=["Differential structural audit"])

@router.post("/{assessment_id}/audit-differential", response_model=DifferentialAuditResult)
def audit_differential(
    assessment_id: str, payload: DifferentialAuditInput, db: Session = Depends(get_db),
):
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada")
    snapshot = make_context(db, assessment)
    reviewed_ids = {f.provenance.record_id for f in snapshot.observations}
    outputs = []
    for candidate in payload.candidates:
        issues = []
        linked_ids = set(candidate.supporting_finding_ids + candidate.opposing_finding_ids)
        unknown = linked_ids - reviewed_ids
        if unknown:
            issues.append("Há achados sem revisão válida ou pertencentes a outra avaliação")
        if not candidate.supporting_finding_ids:
            issues.append("Nenhum achado favorável confirmado foi vinculado")
        if not candidate.opposing_finding_ids:
            # A lack of opposing findings is not automatic proof or disproof.
            issues.append("Nenhum achado contrário foi vinculado; registrar ausência de dados, se aplicável")
        quote_count = 0
        for cid in candidate.citation_ids:
            citation = db.get(VerifiedCitation, cid)
            if citation is None:
                issues.append("Uma ou mais citações não foram verificadas no PDF enviado")
            else:
                quote_count += 1
        if not candidate.citation_ids:
            issues.append("Nenhuma citação de página verificável foi vinculada")
        # Records may be structurally linked yet clinically unrelated.
        outputs.append(DifferentialCandidateAudit(
            title=candidate.title,
            structurally_supported=(not issues),
            linked_confirmed_observations=len(linked_ids & reviewed_ids),
            linked_verified_pdf_quotes=quote_count,
            blocking_issues=issues,
        ))
    return DifferentialAuditResult(
        assessment_id=assessment_id,
        status="structurally_checked" if all(x.structurally_supported for x in outputs) else "blocked",
        candidates=outputs,
    )
