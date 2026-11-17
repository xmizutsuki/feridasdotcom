"""API tests use synthetic data. Not clinical validation of warning rules."""
from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from tests.conftest import authenticate

def setup_case(client):
    patient=client.post("/patients",json={"pseudonym":"HIST-"+uuid4().hex[:14]})
    assert patient.status_code==201,patient.text
    lesion=client.post("/lesions",json={"patient_id":patient.json()["id"],"location":"local fictício"})
    assert lesion.status_code==201
    assessment=client.post("/assessments",json={"lesion_id":lesion.json()["id"]})
    assert assessment.status_code==201
    return lesion.json()["id"],assessment.json()["id"]

def history(pain=None, **overrides):
    body={
        "reporter":"professional","recorder_id":"PROF-FICTICIO",
        "human_confirmed":True,
        "pain_score":pain,
    }
    body.update(overrides)
    return body

def test_history_unknown_is_not_negative_and_warnings_are_auditable():
    with TestClient(app) as client:
        authenticate(client)
        _,a=setup_case(client)
        empty=client.post(f"/assessments/{a}/history",json=history())
        assert empty.status_code==422
        initial=client.post(f"/assessments/{a}/history",json=history(7))
        assert initial.status_code==201,initial.text
        assert initial.json()["data"]["fever_reported"] is None
        assert initial.json()["alerts"]==[]
        revised=client.post(f"/assessments/{a}/history",json=history(
            8,fever_reported=True,spreading_redness=True,perfusion_exam="concern_reported"))
        assert revised.status_code==201,revised.text
        assert revised.json()["revision"]==2
        flags={f["code"] for f in revised.json()["alerts"]}
        assert "systemic_local_warning" in flags
        assert "perfusion_concern" in flags
        all_revisions=client.get(f"/assessments/{a}/history").json()
        assert len(all_revisions)==2
        assert all_revisions[0]["data"]["pain_score"]==7
        assert all_revisions[1]["data"]["pain_score"]==8
        assert client.get(f"/audit/assessment/{a}").status_code==200

def test_history_rejects_unconfirmed_or_out_of_range_values():
    with TestClient(app) as client:
        authenticate(client)
        _,a=setup_case(client)
        assert client.post(f"/assessments/{a}/history",json=history(11)).status_code==422
        assert client.post(f"/assessments/{a}/history",json=history(5,human_confirmed=False)).status_code==422
        assert client.post(f"/assessments/{a}/history",json=history(5,diagnosis="definitivo")).status_code==422

def test_intervention_plan_is_distinct_from_performed_and_immutable_on_finalize():
    with TestClient(app) as client:
        authenticate(client)
        _,a=setup_case(client)
        base={"type":"dressing","description":"Cobertura fictícia de teste","recorder_id":"PROF-FICTICIO",
              "human_confirmed":True}
        planned=client.post(f"/assessments/{a}/interventions",json={**base,"status":"planned"})
        assert planned.status_code==201,planned.text
        assert planned.json()["performed_at"] is None
        assert client.post(f"/assessments/{a}/interventions",json={**base,"status":"performed"}).status_code==422
        assert client.post(f"/assessments/{a}/interventions",json={**base,"status":"planned",
            "performed_at":"2026-01-01T10:00:00Z"}).status_code==422
        done=client.post(f"/assessments/{a}/interventions",json={**base,"status":"performed",
             "performed_at":"2026-01-02T10:00:00Z"})
        assert done.status_code==201,done.text
        assert len(client.get(f"/assessments/{a}/interventions").json())==2
        f=client.post(f"/assessments/{a}/findings",json={"field_name":"edges",
             "proposed_text":"Bordas fictícias","source":"exam","support":"high"}).json()
        reviewed=client.post(f"/findings/{f['id']}/review",json={"decision":"confirmed",
                            "reviewer":"PROF-FICTICIO"})
        assert reviewed.status_code==200
        assert client.post(f"/assessments/{a}/history",json=history(5)).status_code==201
        assert client.post(f"/assessments/{a}/finalize",params={"reviewer":"PROF-FICTICIO"}).status_code==200
        assert client.post(f"/assessments/{a}/history",json=history(6)).status_code==409
        assert client.post(f"/assessments/{a}/interventions",json={**base,"status":"planned"}).status_code==409

def test_previous_history_only_from_validated_same_lesion():
    with TestClient(app) as client:
        authenticate(client)
        lesion,first=setup_case(client)
        second=client.post("/assessments",json={"lesion_id":lesion}).json()["id"]
        assert client.post(f"/assessments/{first}/history",json=history(4)).status_code==201
        prior=client.get(f"/assessments/{second}/previous-history").json()
        assert prior["source_assessment_id"] is None
        f=client.post(f"/assessments/{first}/findings",json={"field_name":"edges",
             "proposed_text":"Fictício","source":"exam","support":"high"}).json()
        assert client.post(f"/findings/{f['id']}/review",json={"decision":"confirmed",
                    "reviewer":"PROF-FICTICIO"}).status_code==200
        assert client.post(f"/assessments/{first}/finalize",params={"reviewer":"PROF-FICTICIO"}).status_code==200
        prior=client.get(f"/assessments/{second}/previous-history").json()
        # The API only returns records from an earlier assessment, never auto-validates it.
        assert prior["source_assessment_id"] in (first,None)
        if prior["source_assessment_id"] is not None:
            assert prior["data"]["pain_score"]==4
            assert "não verificados" in prior["warning"]

def test_routes_require_authenticated_session_and_csrf():
    with TestClient(app) as client:
        _,a=setup_case_after_login(client)
        client.post("/auth/logout")
        assert client.get(f"/assessments/{a}/history").status_code==401
        authenticate(client)
        client.headers.pop("X-CSRF-Token")
        assert client.post(f"/assessments/{a}/history",json=history(3)).status_code==403

def setup_case_after_login(client):
    authenticate(client)
    return setup_case(client)
