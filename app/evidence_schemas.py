"""Evidence corpus contracts. Verification is OPERATOR ATTESTATION, not independent adjudication."""
import re
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

TOPICS = {"diabetic_foot", "wound_healing", "infection", "perfusion", "offloading",
          "venous_ulcer", "pressure_injury", "assessment", "compression", "general"}

class EvidencePassageIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    catalog_source_id: str = Field(min_length=4, max_length=100)
    source_location: str = Field(min_length=3, max_length=160)
    excerpt: str = Field(min_length=20, max_length=350)
    language: Literal["pt", "en", "es"] = "en"
    topic_tags: list[str] = Field(min_length=1, max_length=6)
    applicability_notes: str | None = Field(default=None, max_length=600)
    reviewed_by: str = Field(min_length=2, max_length=100)
    confirmation: Literal["verified_in_original_document"]

    @field_validator("topic_tags")
    @classmethod
    def accepted_tags(cls, tags):
        if len(tags) != len(set(tags)) or any(t not in TOPICS for t in tags):
            raise ValueError("Use tópicos válidos, sem repetição")
        return tags

    @model_validator(mode="after")
    def no_markup(self):
        if any(x in self.excerpt for x in ("<script", "javascript:", "{%")):
            raise ValueError("Não inserir marcação ou código no corpus")
        return self

class EvidencePassageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    catalog_source_id: str
    source_location: str
    excerpt: str
    excerpt_sha256: str
    language: str
    topic_tags: list[str]
    applicability_notes: str | None
    reviewed_by: str
    reviewed_at: datetime

class EvidenceMatch(BaseModel):
    passage: EvidencePassageOut
    publisher_title: str
    publisher_url: str
    lexical_score: int = Field(ge=0)
    source_checked_by_operator: bool = True
    clinical_applicability_validated: bool = False

class EvidenceSearchResult(BaseModel):
    query: str
    matches: list[EvidenceMatch]
    retrieval_method: Literal["local_lexical_v1"] = "local_lexical_v1"
    reasoning_executed: bool = False
    recommendations_enabled: bool = False
    message: str = "Trechos para consulta e conferência. Relevância lexical não comprova aplicabilidade clínica."
