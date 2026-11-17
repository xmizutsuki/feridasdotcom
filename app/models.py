from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import String, Text, ForeignKey, DateTime, Float, Integer, CheckConstraint, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

def uid():
    return str(uuid4())

def now():
    return datetime.now(timezone.utc)

class Patient(Base):
    __tablename__ = "patients"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    pseudonym: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    lesions: Mapped[list["Lesion"]] = relationship(back_populates="patient")

class Lesion(Base):
    __tablename__ = "lesions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), index=True)
    location: Mapped[str] = mapped_column(String(180))
    etiology: Mapped[str | None] = mapped_column(String(120), nullable=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    patient: Mapped[Patient] = relationship(back_populates="lesions")
    assessments: Mapped[list["Assessment"]] = relationship(back_populates="lesion")

class Assessment(Base):
    __tablename__ = "assessments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    lesion_id: Mapped[str] = mapped_column(ForeignKey("lesions.id"), index=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    area_cm2: Mapped[float | None] = mapped_column(Float, nullable=True)
    area_method: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    lesion: Mapped[Lesion] = relationship(back_populates="assessments")
    findings: Mapped[list["Finding"]] = relationship(back_populates="assessment")

class Finding(Base):
    __tablename__ = "findings"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    assessment_id: Mapped[str] = mapped_column(ForeignKey("assessments.id"), index=True)
    field_name: Mapped[str] = mapped_column(String(100))
    proposed_text: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(30))
    support: Mapped[str] = mapped_column(String(30))
    validation_status: Mapped[str] = mapped_column(String(30), default="pending")
    validated_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assessment: Mapped[Assessment] = relationship(back_populates="findings")

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[str] = mapped_column(String(36), index=True)
    action: Mapped[str] = mapped_column(String(50))
    actor: Mapped[str] = mapped_column(String(100))
    detail: Mapped[str] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Photo(Base):
    __tablename__ = "photos"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    assessment_id: Mapped[str] = mapped_column(ForeignKey("assessments.id"), index=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(48), unique=True, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    media_type: Mapped[str] = mapped_column(String(40), default="image/jpeg")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class ClinicalHistoryRecord(Base):
    """Append-only clinical-history revisions. No direct update/delete endpoint."""
    __tablename__ = "clinical_history_records"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    assessment_id: Mapped[str] = mapped_column(ForeignKey("assessments.id"), index=True, nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    recorder_id: Mapped[str] = mapped_column(String(100), nullable=False)
    reporter: Mapped[str] = mapped_column(String(30), nullable=False)
    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    alerts: Mapped[list] = mapped_column(JSON, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class TreatmentIntervention(Base):
    """Each planned/performed event is immutable at API level."""
    __tablename__ = "treatment_interventions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    assessment_id: Mapped[str] = mapped_column(ForeignKey("assessments.id"), index=True, nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    performed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    recorder_id: Mapped[str] = mapped_column(String(100), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
