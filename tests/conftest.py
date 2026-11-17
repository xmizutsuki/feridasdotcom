"""Test-only synthetic secrets. Never use with patient data."""
import os
import tempfile
from cryptography.fernet import Fernet
from app.security import hash_password

os.environ["FERIDAS_PASSWORD_HASH"] = hash_password("TEST-ONLY-password-123")
os.environ["FERIDAS_SESSION_SECRET"] = "test-only-secret-keep-out-of-production-1234567890"
os.environ["FERIDAS_IMAGE_KEY"] = Fernet.generate_key().decode()
os.environ["FERIDAS_STORAGE_DIR"] = tempfile.mkdtemp(prefix="feridas-media-tests-")

def authenticate(client):
    response = client.post("/auth/login", json={"password": "TEST-ONLY-password-123"})
    assert response.status_code == 200
    client.headers.update({"X-CSRF-Token": response.json()["csrf"]})
