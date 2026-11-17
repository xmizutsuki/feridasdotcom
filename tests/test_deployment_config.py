"""Deployment safety checks for hosted, synthetic-data-only staging.

These tests do not contact Neon or Render and do not establish clinical safety.
"""
import pytest
from fastapi.testclient import TestClient
from app.db import database_url
from app.main import app
from tests.conftest import authenticate

def test_render_requires_persistent_postgres(monkeypatch):
    monkeypatch.setenv("FERIDAS_REQUIRE_POSTGRES", "true")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./ephemeral.db")
    with pytest.raises(RuntimeError, match="PostgreSQL obrigatório"):
        database_url()

def test_neon_url_normalizes_for_psycopg3(monkeypatch):
    monkeypatch.setenv("FERIDAS_REQUIRE_POSTGRES", "true")
    monkeypatch.setenv("DATABASE_URL", "postgresql://example:password@example.invalid/db?sslmode=require")
    assert database_url().startswith("postgresql+psycopg://")
    assert "sslmode=require" in database_url()

def test_sqlite_allowed_locally_when_postgres_not_required(monkeypatch):
    monkeypatch.setenv("FERIDAS_REQUIRE_POSTGRES", "false")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./feridas_dev.db")
    assert database_url().startswith("sqlite")

def test_staging_prevents_persistent_photo_upload(monkeypatch):
    monkeypatch.setenv("FERIDAS_DISABLE_MEDIA_UPLOADS", "true")
    with TestClient(app) as client:
        authenticate(client)
        patient=client.post("/patients",json={"pseudonym":"STAGING-TEST"}).json()
        lesion=client.post("/lesions",json={"patient_id":patient["id"],"location":"synthetic test"}).json()
        assessment=client.post("/assessments",json={"lesion_id":lesion["id"]}).json()
        upload=client.post(f"/assessments/{assessment['id']}/photos",
            files={"image":("sample.jpg",b"not a real photo","image/jpeg")})
        assert upload.status_code==503
        assert "armazenamento" in upload.json()["detail"]

def test_staging_prevents_pdf_upload(monkeypatch):
    monkeypatch.setenv("FERIDAS_DISABLE_MEDIA_UPLOADS", "true")
    with TestClient(app) as client:
        authenticate(client)
        upload=client.post("/evidence/documents",
            params={"source_id":"iwgdf-2023-guidelines","edition_label":"synthetic test"},
            files={"file":("sample.pdf",b"%PDF-1.7","application/pdf")})
        assert upload.status_code==503
        assert "armazenamento" in upload.json()["detail"]
