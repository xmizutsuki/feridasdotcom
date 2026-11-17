"""Synthetic evidence workflow tests. Matching a PDF quote is NOT clinical proof."""
from io import BytesIO
from uuid import uuid4
from reportlab.pdfgen.canvas import Canvas
from fastapi.testclient import TestClient
from app.main import app
from tests.conftest import authenticate
from app.pdf_evidence import read_pages, check_citation

SYNTHETIC_QUOTE = "Synthetic protocol sample states that this document is only used for testing clinical record integrity."

def synthetic_pdf(message=SYNTHETIC_QUOTE):
    output=BytesIO()
    canvas=Canvas(output, pagesize=(612,792))
    canvas.drawString(44,700,message)
    canvas.showPage()
    canvas.save()
    return output.getvalue()

def new_document(client):
    pdf=synthetic_pdf()
    res=client.post(
        "/evidence/documents",
        params={"source_id":"iwgdf-2023-guidelines","edition_label":"SYNTHETIC-TEST"},
        files={"file":("synthetic.pdf",pdf,"application/pdf")},
    )
    assert res.status_code==201,res.text
    return res.json()["id"]

def test_pdf_has_extractable_text_and_correct_quote_location():
    data=synthetic_pdf()
    assert len(read_pages(data))==1
    digest,page_digest=check_citation(data,1,SYNTHETIC_QUOTE)
    assert len(digest)==64 and len(page_digest)==64
    try:
        check_citation(data,1,"This invented text cannot possibly be on the test page.")
        assert False, "mismatch should fail"
    except ValueError:
        pass
    try:
        check_citation(data,2,SYNTHETIC_QUOTE)
        assert False, "wrong page should fail"
    except ValueError:
        pass

def test_private_document_upload_and_pdf_quote_match():
    with TestClient(app) as client:
        assert client.get("/evidence/documents").status_code==401
        authenticate(client)
        document_id=new_document(client)
        denied=client.post(f"/evidence/documents/{document_id}/verify-quote",
            json={"page_number":1,"excerpt":"Fabricated text that should not appear here","checked_by":"TEST-OPERATOR"})
        assert denied.status_code==422
        valid=client.post(f"/evidence/documents/{document_id}/verify-quote",
            json={"page_number":1,"excerpt":SYNTHETIC_QUOTE,"checked_by":"TEST-OPERATOR"})
        assert valid.status_code==201,valid.text
        assert valid.json()["matched_in_uploaded_document"] is True
        assert valid.json()["clinical_applicability_validated"] is False
        citation_id=valid.json()["id"]
        listed=client.get(f"/evidence/documents/{document_id}/citations").json()
        assert listed[0]["id"]==citation_id
        repeat=client.post(f"/evidence/documents/{document_id}/verify-quote",
            json={"page_number":1,"excerpt":SYNTHETIC_QUOTE,"checked_by":"TEST-OPERATOR"})
        assert repeat.status_code==409

def test_pdf_upload_rejects_bad_bytes():
    with TestClient(app) as client:
        authenticate(client)
        res=client.post("/evidence/documents",
            params={"source_id":"iwgdf-2023-guidelines","edition_label":"fake"},
            files={"file":("fake.pdf",b"not actually pdf","application/pdf")})
        assert res.status_code==422
        res=client.post("/evidence/documents",
            params={"source_id":"source-not-in-catalog","edition_label":"fake"},
            files={"file":("fake.pdf",synthetic_pdf(),"application/pdf")})
        assert res.status_code==422

def make_case(client):
    patient=client.post("/patients",json={"pseudonym":"DIFF-"+uuid4().hex[:12]})
    lesion=client.post("/lesions",json={"patient_id":patient.json()["id"],"location":"synthetic site"})
    assessment=client.post("/assessments",json={"lesion_id":lesion.json()["id"]})
    assert assessment.status_code==201
    return assessment.json()["id"]

def add_finding(client,aid,kind="confirmed"):
    r=client.post(f"/assessments/{aid}/findings",json={
        "field_name":"edges","proposed_text":"Synthetic borders observed","source":"exam","support":"limited"})
    assert r.status_code==201
    fid=r.json()["id"]
    if kind=="confirmed":
        reviewed=client.post(f"/findings/{fid}/review",json={
            "decision":"confirmed","reviewer":"TEST-REVIEWER"})
        assert reviewed.status_code==200
    return fid

def test_differential_audit_blocks_unreviewed_or_nonexistent_citations():
    with TestClient(app) as client:
        authenticate(client)
        aid=make_case(client)
        fid=add_finding(client,aid,kind="pending")
        proposal={"clinician_id":"TEST-REVIEWER","candidates":[{
            "title":"Hypothesis invented only for a synthetic test",
            "supporting_finding_ids":[fid],"opposing_finding_ids":[],
            "citation_ids":[str(uuid4())],"missing_information":["Unmeasured example"],
            "contraindications_to_check":["Not known in synthetic case"],
            "clinician_note":"This is a testing artifact only, not a diagnostic opinion"
        }]}
        result=client.post(f"/assessments/{aid}/audit-differential",json=proposal)
        assert result.status_code==200,result.text
        assert result.json()["status"]=="blocked"
        assert result.json()["candidates"][0]["structurally_supported"] is False
        assert result.json()["recommendations_enabled"] is False
        assert result.json()["reasoning_generated_by_ai"] is False

def test_structural_success_does_not_mean_clinical_validation():
    with TestClient(app) as client:
        authenticate(client)
        aid=make_case(client)
        support=add_finding(client,aid,kind="confirmed")
        contrary=add_finding(client,aid,kind="confirmed")
        doc_id=new_document(client)
        citation=client.post(f"/evidence/documents/{doc_id}/verify-quote",
            json={"page_number":1,"excerpt":SYNTHETIC_QUOTE,"checked_by":"TEST-OPERATOR"}).json()["id"]
        payload={"clinician_id":"TEST-REVIEWER","candidates":[{
            "title":"Synthetic alternative proposed by operator",
            "supporting_finding_ids":[support],"opposing_finding_ids":[contrary],
            "citation_ids":[citation],"missing_information":["Unknown details"],
            "contraindications_to_check":["Unknown medication status"],
            "clinician_note":"This hypothesis is entirely synthetic and has no clinical meaning"
        }]}
        result=client.post(f"/assessments/{aid}/audit-differential",json=payload)
        assert result.status_code==200,result.text
        assert result.json()["status"]=="structurally_checked"
        assert result.json()["clinical_applicability_validated"] is False
        assert result.json()["requires_independent_clinician_review"] is True
