"""Structured history and treatment contracts for the synthetic-data clinical MVP.

No defaults imply negative clinical findings. Null/unknown means *not assessed*.
"""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class ClinicalHistoryIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    onset_days: int | None = Field(default=None, ge=0, le=36500)
    pain_score: int | None = Field(default=None, ge=0, le=10)
    pain_worsening: bool | None = None
    fever_reported: bool | None = None
    rapidly_worsening: bool | None = None
    spreading_redness: bool | None = None
    purulent_drainage_reported: bool | None = None
    malodor_reported: bool | None = None
    exudate_amount: Literal["none", "low", "moderate", "high", "unknown"] | None = None
    perfusion_exam: Literal["not_assessed", "no_concern_reported", "concern_reported"] | None = None
    diabetes_reported: bool | None = None
    pressure_offloading: Literal["yes", "no", "unknown", "not_applicable"] | None = None
    compression_used: Literal["yes", "no", "unknown", "not_applicable"] | None = None
    allergies: str | None = Field(default=None, max_length=500)
    comorbidities: str | None = Field(default=None, max_length=1000)
    current_medications: str | None = Field(default=None, max_length=1000)
    context_notes: str | None = Field(default=None, max_length=2000)
    reporter: Literal["professional", "patient", "caregiver", "record_review"]
    recorder_id: str = Field(min_length=2, max_length=100)
    human_confirmed: bool

    @model_validator(mode="after")
    def require_assessment_data_and_explicit_review(self):
        if not self.human_confirmed:
            raise ValueError("Confirmação explícita do registro pelo profissional é necessária")
        observations = self.model_dump(exclude={"human_confirmed", "reporter", "recorder_id"})
        if all(value is None for value in observations.values()):
            raise ValueError("Informe pelo menos um dado; não registrar anamnese vazia")
        return self

class ClinicalHistoryOut(BaseModel):
    id: str
    assessment_id: str
    revision: int
    recorded_at: datetime
    recorder_id: str
    reporter: str
    data: dict
    alerts: list[dict]
    clinical_validation: bool = False

class InterventionIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    type: Literal["cleansing", "dressing", "offloading", "compression", "debridement", "referral", "other"]
    status: Literal["planned", "performed", "not_performed"]
    description: str = Field(min_length=3, max_length=2000)
    performed_at: datetime | None = None
    recorder_id: str = Field(min_length=2, max_length=100)
    human_confirmed: bool
    notes: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_workflow(self):
        if not self.human_confirmed:
            raise ValueError("Confirmar explicitamente o registro")
        if self.status != "performed" and self.performed_at is not None:
            raise ValueError("Somente ações realizadas podem conter performed_at")
        if self.status == "performed" and self.performed_at is None:
            raise ValueError("Intervenção realizada exige data/hora")
        return self

class InterventionOut(BaseModel):
    id: str
    assessment_id: str
    type: str
    status: str
    description: str
    performed_at: datetime | None
    recorder_id: str
    recorded_at: datetime
    notes: str | None
