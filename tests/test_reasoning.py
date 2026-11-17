"""AI differential tests use mocks and entirely synthetic records/PDFs.

Passing tests validates interface and fail-closed invariants, NOT clinical safety.
"""
from io import BytesIO
from uuid import uuid4
from unittest.mock import AsyncMock
from reportlab.pdfgen.canvas import Canvas
from fastapi.testclient import TestClient
from app.main import app
from app.reasoning_schemas import ReasoningDraft
from app.semantic_audit import SemanticAuditDraft
from tests.conftest import authenticate

QUOTE = "Synthetic document text used exclusively for testing the provenance of scientific statements."

def make_pdf():
    out=BytesIO()
    canvas=Canvas(out)
    canvas.drawString(40,650,QUOTE+" "+uuid4().hex)
    canvas.showPage()
    canvas.save()
    return out.getvalue()

def setup_case(client, urgent=False):
    p=client.post("/patients",json={"pseudonym":"REASON-"+uuid4().hex[:12]}).json()["id"]
    l=client.post("/lesions",json={"patient_id":p,"location":"synthetic leg"}).json()["id"]
    a=client.post("/assessments",json={"lesion_id":l}).json()["id"]
    f=client.post(f"/assessments/{a}/findings",json={
        "field_name":"edges","proposed_text":"synthetic borders",
        "source":"exam","support":"limited"}).json()["id"]
    assert client.post(f"/findings/{f}/review",json={
        "decision":"confirmed","reviewer":"TEST"}).status_code==200
    h=client.post(f"/assessments/{a}/history",json={
        "reporter":"professional","recorder_id":"TEST","human_confirmed":True,
        "pain_score":4,"rapidly_worsening":urgent,
    })
    assert h.status_code==201,h.text
    assert client.post(f"/assessments/{a}/finalize",params={"reviewer":"TEST"}).status_code==200
    doc=client.post("/evidence/documents",params={
        "source_id":"iwgdf-2023-guidelines","edition_label":"SYNTHETIC",
    },files={"file":("test.pdf",make_pdf(),"application/pdf")})
    assert doc.status_code==201,doc.text
    quote=client.post(f"/evidence/documents/{doc.json()['id']}/verify-quote",
        json={"page_number":1,"excerpt":QUOTE,"checked_by":"TEST"})
    assert quote.status_code==201,quote.text
    return a,f,h.json()["id"],quote.json()["id"]

def request(cid):
    return {"citation_ids":[cid],"confirm_synthetic_scenario":True,
            "confirm_external_processing":True}

def fake_draft(finding_id,history_id,citation_id,invalid=False):
    return ReasoningDraft.model_validate({
        "hypotheses":[{
            "title":"Entirely fictional example hypothesis",
            "rationale":"Only a synthetic illustration of a possible differential, not clinical advice.",
            "supporting_record_ids":[str(uuid4()) if invalid else finding_id],
            "opposing_record_ids":[history_id],
            "citation_ids":[citation_id],
            "missing_information":["Additional synthetic tests needed"],
            "contraindications_to_check":["Unknown synthetic medication state"],
            "uncertainty_note":"No clinical validity established for this generated example."
        }],
        "general_limitations":["Experimental synthetic demonstration only"],
    })

def test_reasoning_disabled_by_default():
    with TestClient(app) as client:
        authenticate(client)
        a,f,h,c=setup_case(client)
        result=client.post(f"/assessments/{a}/reasoning-draft",json=request(c))
        assert result.status_code==503

def test_rejects_missing_opt_in_even_if_model_enabled(monkeypatch):
    with TestClient(app) as client:
        authenticate(client)
        a,f,h,c=setup_case(client)
        monkeypatch.setattr("app.reasoning_routes.enabled",lambda:True)
        payload=request(c)
        payload["confirm_external_processing"]=False
        assert client.post(f"/assessments/{a}/reasoning-draft",json=payload).status_code==412

def test_guard_blocks_urgent_case_without_remote_call(monkeypatch):
    with TestClient(app) as client:
        authenticate(client)
        a,f,h,c=setup_case(client,urgent=True)
        monkeypatch.setattr("app.reasoning_routes.enabled",lambda:True)
        model=AsyncMock(return_value=(fake_draft(f,h,c),"mock"))
        monkeypatch.setattr("app.reasoning_routes.generate_draft",model)
        assert client.post(f"/assessments/{a}/reasoning-draft",json=request(c)).status_code==409
        model.assert_not_awaited()

def fake_review(citation_id, verdict="supported", population="yes"):
    return SemanticAuditDraft.model_validate({
        "hypotheses":[{
            "hypothesis_index":0,
            "verdicts":[{
                "citation_id":citation_id,
                "verdict":verdict,
                "rationale":"Synthetic review placeholder, not clinical evidence.",
                "population_applicable":population,
                "contraindication_conflict":False
            }],
            "unsupported_clinical_assertions":[],
            "unsafe_or_overconfident_language":False,
            "missing_critical_clinical_information":[]
        }],
        "limitations":["Synthetic independent structural exercise only"]
    })

def test_model_output_does_not_become_validated_diagnosis(monkeypatch):
    with TestClient(app) as client:
        authenticate(client)
        a,f,h,c=setup_case(client)
        monkeypatch.setattr("app.reasoning_routes.enabled",lambda:True)
        model=AsyncMock(return_value=(fake_draft(f,h,c),"mock-test"))
        monkeypatch.setattr("app.reasoning_routes.generate_draft",model)
        monkeypatch.setattr("app.reasoning_routes.semantic_enabled",lambda:True)
        reviewer=AsyncMock(return_value=(fake_review(c),"independent-review-model"))
        monkeypatch.setattr("app.reasoning_routes.review_semantics",reviewer)
        result=client.post(f"/assessments/{a}/reasoning-draft",json=request(c))
        assert result.status_code==200,result.text
        data=result.json()
        assert data["status"]=="review_required"
        assert data["semantic_audit_performed"] is True
        assert data["hypotheses"][0]["semantic_audit_status"]=="reviewer_supported"
        assert reviewer.await_count==1
        assert data["clinical_validation"] is False
        assert data["therapeutic_recommendations_enabled"] is False
        assert data["hypotheses"][0]["clinically_validated"] is False
        assert data["semantic_evidence_verified"] is False
        assert model.await_count==1
        context_sent=model.await_args.args[0]
        assert "assessment_id" not in context_sent
        assert "patient_id" not in context_sent

def test_invented_record_reference_blocks_output(monkeypatch):
    with TestClient(app) as client:
        authenticate(client)
        a,f,h,c=setup_case(client)
        monkeypatch.setattr("app.reasoning_routes.enabled",lambda:True)
        monkeypatch.setattr("app.reasoning_routes.generate_draft",
                            AsyncMock(return_value=(fake_draft(f,h,c,invalid=True),"mock")))
        result=client.post(f"/assessments/{a}/reasoning-draft",json=request(c))
        assert result.status_code==200,result.text
        assert result.json()["status"]=="blocked"
        assert not result.json()["hypotheses"][0]["structurally_accepted"]

def test_unverified_citation_rejected_before_model(monkeypatch):
    with TestClient(app) as client:
        authenticate(client)
        a,f,h,c=setup_case(client)
        monkeypatch.setattr("app.reasoning_routes.enabled",lambda:True)
        model=AsyncMock(return_value=(fake_draft(f,h,c),"mock"))
        monkeypatch.setattr("app.reasoning_routes.generate_draft",model)
        assert client.post(f"/assessments/{a}/reasoning-draft",json=request(str(uuid4()))).status_code==422
        model.assert_not_awaited()

def test_reasoning_requires_authentication():
    with TestClient(app) as client:
        assert client.get("/assessments/reasoning/status").status_code==401

def test_missing_independent_reviewer_blocks_even_valid_structural_links(monkeypatch):
    with TestClient(app) as client:
        authenticate(client)
        a,f,h,c=setup_case(client)
        monkeypatch.setattr("app.reasoning_routes.enabled",lambda:True)
        monkeypatch.setattr("app.reasoning_routes.semantic_enabled",lambda:False)
        monkeypatch.setattr("app.reasoning_routes.generate_draft",
                            AsyncMock(return_value=(fake_draft(f,h,c),"generator-test")))
        response=client.post(f"/assessments/{a}/reasoning-draft",json=request(c))
        assert response.status_code==200,response.text
        data=response.json()
        assert data["status"]=="blocked"
        assert data["semantic_audit_performed"] is False
        assert data["hypotheses"][0]["semantic_audit_status"]=="blocked"
        assert data["clinical_validation"] is False

def test_semantic_contradiction_blocks_even_with_valid_citation_id(monkeypatch):
    with TestClient(app) as client:
        authenticate(client)
        a,f,h,c=setup_case(client)
        monkeypatch.setattr("app.reasoning_routes.enabled",lambda:True)
        monkeypatch.setattr("app.reasoning_routes.semantic_enabled",lambda:True)
        monkeypatch.setattr("app.reasoning_routes.generate_draft",
                            AsyncMock(return_value=(fake_draft(f,h,c),"generator-test")))
        monkeypatch.setattr("app.reasoning_routes.review_semantics",
                            AsyncMock(return_value=(fake_review(c,"contradicted"),"reviewer-test")))
        response=client.post(f"/assessments/{a}/reasoning-draft",json=request(c))
        assert response.status_code==200,response.text
        data=response.json()
        assert data["status"]=="blocked"
        assert data["semantic_audit_performed"] is True
        assert data["hypotheses"][0]["semantic_audit_status"]=="blocked"
        assert data["semantic_evidence_verified"] is False

def test_semantic_reviewer_error_fails_closed(monkeypatch):
    with TestClient(app) as client:
        authenticate(client)
        a,f,h,c=setup_case(client)
        monkeypatch.setattr("app.reasoning_routes.enabled",lambda:True)
        monkeypatch.setattr("app.reasoning_routes.semantic_enabled",lambda:True)
        monkeypatch.setattr("app.reasoning_routes.generate_draft",
                            AsyncMock(return_value=(fake_draft(f,h,c),"generator-test")))
        monkeypatch.setattr("app.reasoning_routes.review_semantics",
                            AsyncMock(side_effect=RuntimeError("Mock provider unavailable")))
        response=client.post(f"/assessments/{a}/reasoning-draft",json=request(c))
        assert response.status_code==200,response.text
        assert response.json()["status"]=="blocked"
        assert response.json()["semantic_audit_performed"] is False
        assert response.json()["hypotheses"][0]["semantic_audit_status"]=="blocked"
