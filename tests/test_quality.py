"""Non-clinical validation of image-quality and longitudinal metadata."""
from io import BytesIO
from uuid import uuid4
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app
from app.quality import inspect_quality
from tests.conftest import authenticate

def jpeg(color=(90, 110, 120), size=(800, 600)):
    buf = BytesIO()
    Image.new("RGB",size,color).save(buf,format="JPEG")
    return buf.getvalue()

def test_quality_heuristics_are_not_clinical_certification():
    report = inspect_quality(jpeg(color=(0,0,0)))
    assert report.recapture_suggested is True
    assert any("escura" in w for w in report.warnings)
    assert report.quantitative_measurement_allowed is False
    assert report.clinical_validation is False
    assert report.version == "heuristic-v1"

def test_small_photo_is_flagged_and_does_not_measure_area():
    report=inspect_quality(jpeg(size=(160,120)))
    assert any("Resolução" in w for w in report.warnings)
    assert not report.quantitative_measurement_allowed

def test_photo_quality_requires_login():
    with TestClient(app) as client:
        assert client.get("/photos/"+str(uuid4())+"/quality").status_code==401

def make_photo(client, patient=None):
    if patient is None:
        patient=client.post("/patients",json={"pseudonym":"Q-"+uuid4().hex[:12]}).json()["id"]
    lesion=client.post("/lesions",json={"patient_id":patient,"location":"anatomia fictícia"}).json()["id"]
    assessment=client.post("/assessments",json={"lesion_id":lesion}).json()["id"]
    photo=client.post(f"/assessments/{assessment}/photos",
                      files={"image":("synthetic.jpg",jpeg(),"image/jpeg")}).json()
    assert photo["quality"]["quantitative_measurement_allowed"] is False
    return lesion,assessment,photo["id"]

def test_photo_quality_and_different_lesion_comparison_blocked():
    with TestClient(app) as client:
        authenticate(client)
        _,_,first=make_photo(client)
        _,_,second=make_photo(client)
        quality=client.get(f"/photos/{first}/quality")
        assert quality.status_code==200
        assert quality.json()["clinical_validation"] is False
        response=client.get(f"/photos/{second}/compare/{first}")
        assert response.status_code==409

def test_comparison_between_two_assessments_same_lesion():
    with TestClient(app) as client:
        authenticate(client)
        lesion,_,photo_old=make_photo(client)
        a2=client.post("/assessments",json={"lesion_id":lesion}).json()["id"]
        photo_new=client.post(f"/assessments/{a2}/photos",
            files={"image":("test.jpg",jpeg(color=(100,110,120)),"image/jpeg")}).json()["id"]
        response=client.get(f"/photos/{photo_new}/compare/{photo_old}")
        assert response.status_code==200,response.text
        data=response.json()
        assert data["spatial_alignment_validated"] is False
        assert data["quantitative_area_comparison_allowed"] is False
        assert data["same_pixel_dimensions"] is True
