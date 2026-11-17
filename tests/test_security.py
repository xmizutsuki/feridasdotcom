"""Synthetic integration tests for the access boundary and encrypted media."""
import io
from uuid import uuid4
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app
from tests.conftest import authenticate

def test_private_api_and_csrf():
    with TestClient(app) as client:
        assert client.get("/patients").status_code == 401
        assert client.get("/auth/session").status_code == 401
        assert client.post("/auth/login", json={"password":"wrong"}).status_code == 401
        authenticate(client)
        client.headers.pop("X-CSRF-Token")
        assert client.post("/patients", json={"pseudonym":"TEST-NO-CSRF"}).status_code == 403
        csrf = client.get("/auth/session").json()["csrf"]
        client.headers["X-CSRF-Token"] = csrf
        created = client.post("/patients", json={"pseudonym":"SYN-"+uuid4().hex[:12]})
        assert created.status_code == 201
        assert client.post("/auth/logout").status_code == 200
        assert client.get("/patients").status_code == 401

def test_photo_requires_owner_and_restricts_invalid_upload():
    with TestClient(app) as client:
        authenticate(client)
        patient = client.post("/patients", json={"pseudonym":"SYN-"+uuid4().hex[:12]}).json()
        lesion = client.post("/lesions", json={"patient_id":patient["id"],"location":"membro fictício"}).json()
        assessment = client.post("/assessments",json={"lesion_id":lesion["id"]}).json()
        path = f"/assessments/{assessment['id']}/photos"
        invalid = client.post(path,files={"image":("wrong.jpg",b"not-an-image","image/jpeg")})
        assert invalid.status_code == 422
        image = Image.new("RGB",(128,96),(115,30,70))
        buf = io.BytesIO()
        image.save(buf,format="JPEG")
        upload = client.post(path,files={"image":("test.jpg",buf.getvalue(),"image/jpeg")})
        assert upload.status_code == 201, upload.text
        photo_id = upload.json()["id"]
        assert client.get(path).json()[0]["id"] == photo_id
        data = client.get("/photos/"+photo_id)
        assert data.status_code == 200
        assert data.headers["content-type"].startswith("image/jpeg")
        assert data.headers["cache-control"] == "no-store"
        assert data.content[:2] == bytes([255, 216])
        client.post("/auth/logout")
        assert client.get("/photos/"+photo_id).status_code == 401
