"""Single-owner prototype authentication; configuration is mandatory, no default credentials."""
import base64
import hashlib
import hmac
import os
import secrets
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

SESSION_SECONDS = 8 * 60 * 60

def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 600_000)
    return "pbkdf2_sha256$600000$" + base64.urlsafe_b64encode(salt).decode() + "$" + base64.urlsafe_b64encode(digest).decode()

def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, iterations, salt, expected = stored.split("$")
        if algorithm != "pbkdf2_sha256" or int(iterations) != 600_000:
            return False
        calculated = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), base64.urlsafe_b64decode(salt), int(iterations))
        return hmac.compare_digest(calculated, base64.urlsafe_b64decode(expected))
    except (ValueError, TypeError):
        return False

def settings():
    secret = os.getenv("FERIDAS_SESSION_SECRET", "")
    password_hash = os.getenv("FERIDAS_PASSWORD_HASH", "")
    key = os.getenv("FERIDAS_IMAGE_KEY", "")
    if len(secret) < 32 or not password_hash or not key:
        raise RuntimeError("Configure FERIDAS_SESSION_SECRET, FERIDAS_PASSWORD_HASH e FERIDAS_IMAGE_KEY antes de iniciar")
    from cryptography.fernet import Fernet
    Fernet(key.encode())
    return {"secret": secret, "password_hash": password_hash, "image_key": key, "secure_cookie": os.getenv("FERIDAS_COOKIE_SECURE", "false").lower() == "true"}

def signer(config):
    return URLSafeTimedSerializer(config["secret"], salt="feridas-session-v1")

def new_session(config):
    csrf = secrets.token_urlsafe(32)
    return signer(config).dumps({"sub": "owner", "csrf": csrf}), csrf

def read_session(config, cookie: str | None):
    if not cookie:
        return None
    try:
        data = signer(config).loads(cookie, max_age=SESSION_SECONDS)
        return data if data.get("sub") == "owner" and data.get("csrf") else None
    except (BadSignature, SignatureExpired):
        return None

if __name__ == "__main__":
    import getpass
    password = getpass.getpass("Nova senha local (mínimo 12 caracteres): ")
    if len(password) < 12:
        raise SystemExit("A senha precisa ter pelo menos 12 caracteres")
    print("FERIDAS_PASSWORD_HASH=" + hash_password(password))
    print("FERIDAS_SESSION_SECRET=" + secrets.token_urlsafe(48))
    from cryptography.fernet import Fernet
    print("FERIDAS_IMAGE_KEY=" + Fernet.generate_key().decode())
