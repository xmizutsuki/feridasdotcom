import io
from uuid import uuid4
from unittest.mock import AsyncMock
from PIL import Image
from fastapi.testclient import TestClient
import pytest
from pydantic import ValidationError
from app.main import app
from app.vision import VisualDraft
from tests.conftest import authenticate

def valid_draft():
    return VisualDraft.model_validate({
        "findings": [
            {"field_name":"edges", "proposed_text":"Bordas aparentemente irregulares",
             "source":"image", "support":"limited"},
            {"field_name":"depth", "proposed_text":"Profundidade não avaliável em fotografia bidimensional",
             "source":"unknown", "support":"not_evaluable"}
        ],
        "needs_better_image":False,
        "capture_guidance":"Fotografia adicional, se necessário",
        "limitations":["Não permite exame de profundidade, dor ou perfusão"]
    })

def test_schema_rejects_false_depth_certainty():
    with pytest.raises(ValidationError):
        VisualDraft.model_validate({
            "findings":[{"field_name":"depth", "proposed_text":"Profundidade 4 centímetros",
                         "source":"image", "support":"high"}],
            "needs_better_image":False, "capture_guidance":"",
            "limitations":["Sem medidas"]
        })

def test_schema_rejects_duplicate_fields():
    item={"field_name":"depth","proposed_text":"Não avaliável na foto",
          "source":"unknown","support":"not_evaluable"}
    with pytest.raises(ValidationError):
        VisualDraft.model_validate({
            "findings":[item,item],
            "needs_better_image":True, "capture_guidance":"Refazer",
            "limitations":["Sem profundidade"]
        })

def prepare_assessment(client):
    p=client.post("/patients",json={"pseudonym":"SYN-"+uuid4().hex[:12]}).json()
    l=client.post("/lesions",json={"patient_id":p["id"],"location":"local fictício"}).json()
    a=client.post("/assessments",json={"lesion_id":l["id"]}).json()
    buf=io.BytesIO()
    Image.new("RGB",(160,120),(140,65,90)).save(buf,format="JPEG")
    photo=client.post(f"/assessments/{a['id']}/photos",files={"image":("synthetic.jpg",buf.getvalue(),"image/jpeg")}).json()
    return a["id"],photo["id"]

def test_opt_in_and_safe_persistence(monkeypatch):
    with TestClient(app) as client:
        authenticate(client)
        assessment_id,photo_id=prepare_assessment(client)
        path=f"/assessments/{assessment_id}/analyze-image?photo_id={photo_id}"
        assert client.post(path).status_code == 412
        assert client.post(path+"&confirm_external_processing=true").status_code == 503
        monkeypatch.setattr("app.vision_routes.enabled",lambda: True)
        fake=AsyncMock(return_value=(valid_draft(),"mock-test-model"))
        monkeypatch.setattr("app.vision_routes.analyze_photo",fake)
        response=client.post(path+"&confirm_external_processing=true")
        assert response.status_code == 201,response.text
        assert response.json()["status"]=="pending_human_review"
        assert response.json()["findings_created"]==2
        assert fake.await_count==1
        findings=client.get(f"/assessments/{assessment_id}/findings").json()
        assert all(f["validation_status"]=="pending" for f in findings)
        assert any(f["field_name"]=="depth" and f["support"]=="not_evaluable" for f in findings)
        assert client.post(path+"&confirm_external_processing=true").status_code == 409

def test_wrong_assessment_photo_is_rejected_before_remote_call(monkeypatch):
    with TestClient(app) as client:
        authenticate(client)
        assessment_id,photo_id=prepare_assessment(client)
        other_assessment,_=prepare_assessment(client)
        monkeypatch.setattr("app.vision_routes.enabled",lambda:True)
        fake=AsyncMock(return_value=(valid_draft(),"mock"))
        monkeypatch.setattr("app.vision_routes.analyze_photo",fake)
        response=client.post(f"/assessments/{other_assessment}/analyze-image?photo_id={photo_id}&confirm_external_processing=true")
        assert response.status_code==404
        fake.assert_not_awaited()
