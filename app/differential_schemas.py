"""Structural safety audit for manually authored differential hypotheses.

Never generate differential diagnoses or recommendations. Validate only that
the operator's proposed links point to reviewed facts and exact PDF quotes.
"""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class DifferentialCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=4, max_length=180)
    supporting_finding_ids: list[str] = Field(default_factory=list, max_length=20)
    opposing_finding_ids: list[str] = Field(default_factory=list, max_length=20)
    citation_ids: list[str] = Field(default_factory=list, max_length=12)
    missing_information: list[str] = Field(min_length=1, max_length=15)
    contraindications_to_check: list[str] = Field(min_length=1, max_length=15)
    clinician_note: str = Field(min_length=10, max_length=1200)

    @model_validator(mode="after")
    def disjoint(self):
        if set(self.supporting_finding_ids) & set(self.opposing_finding_ids):
            raise ValueError("Um achado não pode estar simultaneamente a favor e contra")
        if len(self.supporting_finding_ids) != len(set(self.supporting_finding_ids)):
            raise ValueError("Achado de apoio duplicado")
        if len(self.opposing_finding_ids) != len(set(self.opposing_finding_ids)):
            raise ValueError("Achado contrário duplicado")
        if len(self.citation_ids) != len(set(self.citation_ids)):
            raise ValueError("Citação duplicada")
        return self

class DifferentialAuditInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    candidates: list[DifferentialCandidate] = Field(min_length=1, max_length=5)
    clinician_id: str = Field(min_length=2, max_length=100)

class DifferentialCandidateAudit(BaseModel):
    title: str
    structurally_supported: bool
    linked_confirmed_observations: int
    linked_verified_pdf_quotes: int
    blocking_issues: list[str]
    clinical_applicability_validated: bool = False

class DifferentialAuditResult(BaseModel):
    assessment_id: str
    status: Literal["blocked", "structurally_checked"]
    candidates: list[DifferentialCandidateAudit]
    reasoning_generated_by_ai: bool = False
    clinical_applicability_validated: bool = False
    recommendations_enabled: bool = False
    requires_independent_clinician_review: bool = True
    message: str = "Auditoria estrutural experimental; não é um parecer diagnóstico ou autorização de conduta."
