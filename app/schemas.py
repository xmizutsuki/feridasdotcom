from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

class ORMResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class PatientCreate(BaseModel):
    pseudonym: str = Field(min_length=2, max_length=80)

class PatientOut(ORMResponse):
    id: str
    pseudonym: str
    created_at: datetime

class LesionCreate(BaseModel):
    patient_id: str
    location: str = Field(min_length=2, max_length=180)
    etiology: str | None = Field(default=None, max_length=120)

class LesionOut(ORMResponse):
    id: str
    patient_id: str
    location: str
    etiology: str | None
    opened_at: datetime

class AssessmentCreate(BaseModel):
    lesion_id: str
    area_cm2: float | None = Field(default=None, ge=0)
    area_method: str | None = Field(default=None, max_length=80)
    notes: str | None = Field(default=None, max_length=2000)

class AssessmentOut(ORMResponse):
    id: str
    lesion_id: str
    captured_at: datetime
    area_cm2: float | None
    area_method: str | None
    notes: str | None
    status: str

class FindingCreate(BaseModel):
    field_name: str = Field(min_length=2, max_length=100)
    proposed_text: str = Field(min_length=1)
    source: Literal["image", "reported", "exam", "unknown"]
    support: Literal["high", "limited", "not_evaluable"]

class FindingOut(ORMResponse):
    id: str
    assessment_id: str
    field_name: str
    proposed_text: str
    source: str
    support: str
    validation_status: str
    validated_text: str | None
    reviewed_by: str | None
    reviewed_at: datetime | None

class FindingReview(BaseModel):
    decision: Literal["confirmed", "corrected", "rejected"]
    reviewer: str = Field(min_length=2, max_length=100)
    corrected_text: str | None = Field(default=None, min_length=1)

class AuditOut(ORMResponse):
    id: str
    entity_type: str
    entity_id: str
    action: str
    actor: str
    detail: str
    occurred_at: datetime

class TrendPoint(BaseModel):
    assessment_id: str
    captured_at: datetime
    area_cm2: float | None
    change_from_baseline_percent: float | None
