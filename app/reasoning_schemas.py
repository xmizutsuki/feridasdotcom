"""Strict schema for experimental AI-generated differential drafts.

A structurally valid reference is never treated as proof of clinical correctness.
No treatment instructions, dosing or automated orders are permitted as fields.
"""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class HypothesisDraft(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=4, max_length=140)
    rationale: str = Field(min_length=15, max_length=900)
    supporting_record_ids: list[str] = Field(min_length=1, max_length=12)
    opposing_record_ids: list[str] = Field(max_length=12)
    citation_ids: list[str] = Field(min_length=1, max_length=6)
    missing_information: list[str] = Field(min_length=1, max_length=8)
    contraindications_to_check: list[str] = Field(min_length=1, max_length=8)
    uncertainty_note: str = Field(min_length=10, max_length=400)

    @model_validator(mode="after")
    def unique_links(self):
        for values in (self.supporting_record_ids, self.opposing_record_ids, self.citation_ids):
            if len(values) != len(set(values)):
                raise ValueError("Referências duplicadas")
        if set(self.supporting_record_ids) & set(self.opposing_record_ids):
            raise ValueError("Mesmo registro nas listas favorável e contrária")
        return self

class ReasoningDraft(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    hypotheses: list[HypothesisDraft] = Field(min_length=1, max_length=3)
    general_limitations: list[str] = Field(min_length=1, max_length=8)

class HypothesisAudit(BaseModel):
    title: str
    rationale: str
    supporting_record_ids: list[str]
    opposing_record_ids: list[str]
    citation_ids: list[str]
    missing_information: list[str]
    contraindications_to_check: list[str]
    uncertainty_note: str
    blocking_issues: list[str]
    structurally_accepted: bool
    clinically_validated: bool = False

class ReasoningAuditResult(BaseModel):
    assessment_id: str
    status: Literal["blocked", "review_required"]
    model: str
    hypotheses: list[HypothesisAudit]
    general_limitations: list[str]
    urgent_warning_present: bool
    clinician_review_required: bool = True
    semantic_evidence_verified: bool = False
    therapeutic_recommendations_enabled: bool = False
    clinical_validation: bool = False
    message: str = "Hipóteses experimentais; a integridade dos vínculos não comprova correção, segurança ou aplicabilidade clínica."
