"""Typed evidence-ready clinical context; NOT diagnostic reasoning or medical advice."""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class Provenance(BaseModel):
    model_config = ConfigDict(extra="forbid")
    assessment_id: str
    record_id: str
    recorded_at: datetime | None
    recorder_id: str | None

class ValidatedObservation(BaseModel):
    field_name: str
    text: str
    proposed_source: Literal["image", "reported", "exam", "unknown"]
    support_at_proposal: str
    human_decision: Literal["confirmed", "corrected"]
    provenance: Provenance

class ClinicalDatum(BaseModel):
    field_name: str
    value: str | bool | int | float
    reporter: str
    provenance: Provenance

class InterventionSnapshot(BaseModel):
    type: str
    status: Literal["planned", "performed", "not_performed"]
    description: str
    performed_at: datetime | None
    provenance: Provenance

class ContextSnapshot(BaseModel):
    schema_version: Literal["context-v1"] = "context-v1"
    assessment_id: str
    lesion_id: str
    assessment_status: Literal["draft", "validated"]
    observations: list[ValidatedObservation]
    reported_clinical_data: list[ClinicalDatum]
    interventions: list[InterventionSnapshot]
    warnings: list[dict]
    excluded_unreviewed_count: int = Field(ge=0)
    excluded_rejected_count: int = Field(ge=0)
    not_evaluable_count: int = Field(ge=0)
    history_revision: int | None = None
    missing_sections: list[str]
    research_ready: bool = False
    recommendations_enabled: bool = False
    clinical_validation: bool = False

class EvidenceSource(BaseModel):
    """Metadata only; no assertion that the source substantiates a particular claim."""
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    document_id: str = Field(min_length=4, max_length=100)
    title: str = Field(min_length=5, max_length=350)
    issuer: str = Field(min_length=2, max_length=150)
    edition: str = Field(min_length=1, max_length=60)
    url: str = Field(min_length=12, max_length=1000)
    verification_status: Literal["not_verified", "manually_verified"]
    verified_by: str | None = None
    verified_at: datetime | None = None

class EvidenceReadiness(BaseModel):
    context: ContextSnapshot
    sources: list[EvidenceSource] = Field(default_factory=list)
    evidence_verified: bool = False
    reasoning_executed: bool = False
    differential_diagnoses: list = Field(default_factory=list)
    suggested_interventions: list = Field(default_factory=list)
    message: str = "Contexto organizado; não há raciocínio diagnóstico nem recomendação clínica autorizada."
