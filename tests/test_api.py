from tests.conftest import authenticate
import os
import tempfile
from pathlib import Path

# Isolated test database; no real patient data.
_tmp = tempfile.TemporaryDirectory()
os.environ["DATABASE_URL"] = "sqlite:///" + str(Path(_tmp.name) / "test.db")

from fastapi.testclient import TestClient
from app.main import app

def test_workflow_and_audit():
    with TestClient(app) as client:
        authenticate(client)
        assert client.get("/health").json()["clinical_validation"] is False
        patient = client.post("/patients", json={"pseudonym": "TEST-001"})
        assert patient.status_code == 201
        pid = patient.json()["id"]
        lesion = client.post("/lesions", json={"patient_id": pid, "location": "perna esquerda"})
        assert lesion.status_code == 201
        lid = lesion.json()["id"]
        first = client.post("/assessments", json={"lesion_id": lid, "area_cm2": 10, "area_method": "manual"})
        assert first.status_code == 201
        aid = first.json()["id"]
        finding = client.post(f"/assessments/{aid}/findings", json={
            "field_name":"wound_bed", "proposed_text":"Área amarelada aparente",
            "source":"image", "support":"limited"
        })
        fid = finding.json()["id"]
        assert client.post(f"/assessments/{aid}/finalize", params={"reviewer":"TEST"}).status_code == 422
        review = client.post(f"/findings/{fid}/review", json={
            "decision":"corrected", "corrected_text":"Esfacelo confirmado no exame",
            "reviewer":"TEST-CLINICIAN"
        })
        assert review.status_code == 200
        assert review.json()["proposed_text"] != review.json()["validated_text"]
        assert client.post(f"/assessments/{aid}/finalize", params={"reviewer":"TEST-CLINICIAN"}).status_code == 200
        assert client.post(f"/findings/{fid}/review", json={
            "decision":"confirmed", "reviewer":"TEST-CLINICIAN"
        }).status_code == 409
        trend = client.get(f"/lesions/{lid}/trend").json()
        assert len(trend) == 1 and trend[0]["change_from_baseline_percent"] == 0
        audit = client.get(f"/audit/finding/{fid}").json()
        assert [e["action"] for e in audit] == ["proposed", "reviewed"]

def test_area_requires_method_and_no_negative_area():
    with TestClient(app) as client:
        authenticate(client)
        pid = client.post("/patients", json={"pseudonym":"TEST-002"}).json()["id"]
        lid = client.post("/lesions", json={"patient_id":pid,"location":"pé"}).json()["id"]
        assert client.post("/assessments", json={"lesion_id":lid,"area_cm2":10}).status_code == 422
        assert client.post("/assessments", json={"lesion_id":lid,"area_cm2":-1,"area_method":"manual"}).status_code == 422
