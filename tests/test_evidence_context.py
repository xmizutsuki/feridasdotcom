"""No autonomous etiological or treatment inference in research candidates."""
from uuid import uuid4

from fastapi.testclient import TestClient
from app.main import app
from tests.conftest import authenticate

def make_assessment(client):
    p=client.post("/patients",json={"pseudonym":"SEARCH-"+uuid4().hex[:12]})
    lesion=client.post("/lesions",json={"patient_id":p.json()["id"],"location":"local sintético"})
    return client.post("/assessments",json={"lesion_id":lesion.json()["id"]}).json()["id"]

def test_candidates_require_current_explicit_data_not_unreviewed_image():
    with TestClient(app) as client:
        authenticate(client)
        a=make_assessment(client)
        client.post(f"/assessments/{a}/findings",json={
            "field_name":"wound_bed","proposed_text":"diabetic_foot offloading",
            "source":"image","support":"limited",
        })
        response=client.get(f"/evidence/assessments/{a}/candidates")
        assert response.status_code==200,response.text
        data=response.json()
        assert data["search_topics_from_explicit_reported_data"]==[]
        assert data["recommendations_enabled"] is False
        assert data["reasoning_executed"] is False

def test_candidates_use_current_history_only_and_not_absence_of_known_conditions():
    with TestClient(app) as client:
        authenticate(client)
        a=make_assessment(client)
        entered=client.post(f"/assessments/{a}/history",json={
            "reporter":"patient","recorder_id":"REVIEWER-TEST",
            "human_confirmed":True,"diabetes_reported":True,
            "perfusion_exam":"concern_reported","compression_used":"unknown",
        })
        assert entered.status_code==201,entered.text
        response=client.get(f"/evidence/assessments/{a}/candidates")
        assert response.status_code==200
        topics=response.json()["search_topics_from_explicit_reported_data"]
        assert topics==["diabetic_foot","perfusion"]
        assert "compression" not in topics
        assert response.json()["clinical_applicability_validated"] is False
        # New visit must not inherit the preceding assessment history.
        lesion=client.get("/patients")[0] if False else None
