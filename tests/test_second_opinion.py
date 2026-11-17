"""Synthetic-data tests for second-opinion context integrity (not clinical validation)."""
from uuid import uuid4

from fastapi.testclient import TestClient
from app.main import app
from tests.conftest import authenticate

def make_case(client):
    p = client.post("/patients", json={"pseudonym": "CONTEXT-" + uuid4().hex[:14]})
    assert p.status_code == 201, p.text
    lesion = client.post("/lesions", json={
        "patient_id": p.json()["id"], "location": "local anatômico sintético",
    })
    assert lesion.status_code == 201, lesion.text
    assessment = client.post("/assessments", json={"lesion_id": lesion.json()["id"]})
    assert assessment.status_code == 201, assessment.text
    return lesion.json()["id"], assessment.json()["id"]

def add_finding(client, assessment_id, name, text, source="image", support="limited"):
    r = client.post(f"/assessments/{assessment_id}/findings", json={
        "field_name": name, "proposed_text": text, "source": source, "support": support,
    })
    assert r.status_code == 201, r.text
    return r.json()["id"]

def review(client, fid, decision, corrected=None):
    payload = {"decision": decision, "reviewer": "SYNTHETIC-REVIEWER"}
    if corrected is not None:
        payload["corrected_text"] = corrected
    r = client.post(f"/findings/{fid}/review", json=payload)
    assert r.status_code == 200, r.text

def test_unreviewed_rejected_and_non_evaluable_are_not_facts():
    with TestClient(app) as client:
        authenticate(client)
        _, assessment = make_case(client)
        pending = add_finding(client, assessment, "wound_bed", "possível esfacelo")
        accepted = add_finding(client, assessment, "edges", "bordas irregulares")
        corrected = add_finding(client, assessment, "periwound", "aspecto duvidoso")
        rejected = add_finding(client, assessment, "color", "vermelho")
        limited = add_finding(client, assessment, "depth", "não visível", source="unknown", support="not_evaluable")
        review(client, accepted, "confirmed")
        review(client, corrected, "corrected", "pele adjacente com aspecto ressecado")
        review(client, rejected, "rejected")
        review(client, limited, "confirmed")
        result = client.get(f"/assessments/{assessment}/clinical-context")
        assert result.status_code == 200, result.text
        context = result.json()
        assert context["excluded_unreviewed_count"] == 1
        assert context["excluded_rejected_count"] == 1
        assert context["not_evaluable_count"] == 1
        assert len(context["observations"]) == 2
        assert not any(x["provenance"]["record_id"] in (pending, rejected, limited) for x in context["observations"])
        assert any(x["text"] == "pele adjacente com aspecto ressecado" and x["human_decision"] == "corrected" for x in context["observations"])
        assert all(x["provenance"]["recorder_id"] == "SYNTHETIC-REVIEWER" for x in context["observations"])
        assert context["research_ready"] is False
        assert context["recommendations_enabled"] is False
        assert context["clinical_validation"] is False

def test_history_provenance_null_and_treatment_distinction():
    with TestClient(app) as client:
        authenticate(client)
        _, assessment = make_case(client)
        history = client.post(f"/assessments/{assessment}/history", json={
            "reporter": "patient", "recorder_id": "SYNTHETIC-REVIEWER",
            "human_confirmed": True, "pain_score": 5,
            "fever_reported": False, "diabetes_reported": None,
            "exudate_amount": "unknown", "rapidly_worsening": True,
        })
        assert history.status_code == 201, history.text
        base = {"type": "dressing", "description": "Cobertura hipotética em caso sintético",
                "recorder_id": "SYNTHETIC-REVIEWER", "human_confirmed": True}
        assert client.post(f"/assessments/{assessment}/interventions", json={**base, "status": "planned"}).status_code == 201
        assert client.post(f"/assessments/{assessment}/interventions", json={
            **base, "status": "performed", "performed_at": "2026-11-17T10:00:00Z",
        }).status_code == 201
        snapshot = client.get(f"/assessments/{assessment}/clinical-context").json()
        observed = {datum["field_name"]: datum for datum in snapshot["reported_clinical_data"]}
        assert observed["pain_score"]["value"] == 5
        assert observed["fever_reported"]["value"] is False
        assert "diabetes_reported" not in observed
        assert "exudate_amount" not in observed
        assert observed["pain_score"]["provenance"]["record_id"] == history.json()["id"]
        assert any(x["code"] == "rapid_deterioration" for x in snapshot["warnings"])
        assert {x["status"] for x in snapshot["interventions"]} == {"planned", "performed"}
        assert any(x["status"] == "performed" and x["performed_at"] is not None for x in snapshot["interventions"])
        assert snapshot["history_revision"] == 1

def test_no_autogenerated_claims_or_fake_evidence():
    with TestClient(app) as client:
        authenticate(client)
        _, assessment = make_case(client)
        response = client.get(f"/assessments/{assessment}/evidence-readiness")
        assert response.status_code == 200
        result = response.json()
        assert result["sources"] == []
        assert result["evidence_verified"] is False
        assert result["reasoning_executed"] is False
        assert result["differential_diagnoses"] == []
        assert result["suggested_interventions"] == []
        assert "semiologia_confirmada" in result["context"]["missing_sections"]
        assert "anamnese_atual_registrada" in result["context"]["missing_sections"]

def test_context_routes_authentication_and_isolation():
    with TestClient(app) as client:
        assert client.get("/assessments/not-a-real-id/clinical-context").status_code == 401
        authenticate(client)
        assert client.get("/assessments/not-a-real-id/clinical-context").status_code == 404
        assert client.get("/assessments/not-a-real-id/evidence-readiness").status_code == 404

def test_prior_visit_does_not_silently_inherit_clinical_data():
    with TestClient(app) as client:
        authenticate(client)
        lesion, first = make_case(client)
        response = client.post(f"/assessments/{first}/history", json={
            "reporter": "professional", "recorder_id": "SYNTHETIC-REVIEWER",
            "human_confirmed": True, "pain_score": 9,
        })
        assert response.status_code == 201
        finding = add_finding(client, first, "edges", "irregular")
        review(client, finding, "confirmed")
        assert client.post(f"/assessments/{first}/finalize", params={"reviewer":"SYNTHETIC-REVIEWER"}).status_code == 200
        later = client.post("/assessments", json={"lesion_id": lesion})
        assert later.status_code == 201
        second = later.json()["id"]
        context = client.get(f"/assessments/{second}/clinical-context").json()
        assert context["observations"] == []
        assert context["reported_clinical_data"] == []
        assert context["history_revision"] is None
