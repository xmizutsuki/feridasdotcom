"""Authentication, CSRF protection and encrypted photo endpoints for local single-owner MVP."""
import hmac
import time
from collections import defaultdict
from fastapi import UploadFile, File, Depends, HTTPException, Request, Response, APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from .db import get_db
from .models import Assessment, Photo, AuditEvent
from .security import settings, verify_password, new_session, read_session, SESSION_SECONDS
from .media import MAX_UPLOAD, process_photo, store_encrypted, read_encrypted
from .quality import inspect_quality

class LoginRequest(BaseModel):
    password: str = Field(min_length=1)

def install_security(app):
    config = settings()
    router = APIRouter()
    attempts = defaultdict(list)

    @app.middleware("http")
    async def require_owner(request: Request, call_next):
        path = request.url.path
        if path in ("/health", "/auth/login", "/") or path.startswith("/app/"):
            return await call_next(request)
        identity = read_session(config, request.cookies.get("feridas_session"))
        if identity is None:
            return JSONResponse({"detail": "Autenticação necessária"}, status_code=401)
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            token = request.headers.get("X-CSRF-Token", "")
            if not hmac.compare_digest(token, identity["csrf"]):
                return JSONResponse({"detail": "Token CSRF ausente ou inválido"}, status_code=403)
        request.state.actor = identity["sub"]
        return await call_next(request)

    @router.post("/auth/login")
    def login(payload: LoginRequest, request: Request, response: Response):
        remote = request.client.host if request.client else "unknown"
        now = time.monotonic()
        attempts[remote] = [t for t in attempts[remote] if now - t < 300]
        if len(attempts[remote]) >= 10:
            raise HTTPException(status_code=429, detail="Muitas tentativas. Tente novamente mais tarde.")
        if not verify_password(payload.password, config["password_hash"]):
            attempts[remote].append(now)
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
        attempts.pop(remote, None)
        cookie, csrf = new_session(config)
        response.set_cookie("feridas_session", cookie, httponly=True, secure=config["secure_cookie"],
                            samesite="strict", max_age=SESSION_SECONDS, path="/")
        response.headers["Cache-Control"] = "no-store"
        return {"authenticated": True, "csrf": csrf}

    @router.get("/auth/session")
    def session(request: Request, response: Response):
        identity = read_session(config, request.cookies.get("feridas_session"))
        response.headers["Cache-Control"] = "no-store"
        return {"authenticated": True, "csrf": identity["csrf"]}

    @router.post("/auth/logout")
    def logout(response: Response):
        response.delete_cookie("feridas_session", path="/")
        response.headers["Cache-Control"] = "no-store"
        return {"authenticated": False}

    @router.post("/assessments/{assessment_id}/photos", status_code=201)
    async def upload_photo(assessment_id: str, image: UploadFile = File(...), db: Session = Depends(get_db)):
        assessment = db.get(Assessment, assessment_id)
        if assessment is None:
            raise HTTPException(status_code=404, detail="Avaliação não encontrada")
        if assessment.status == "validated":
            raise HTTPException(status_code=409, detail="Avaliação finalizada; não anexar sem adendo")
        raw = await image.read(MAX_UPLOAD + 1)
        try:
            cleaned, mime, width, height = process_photo(raw)
            filename, digest = store_encrypted(cleaned, config)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        photo = Photo(assessment_id=assessment_id, filename=filename, sha256=digest,
                      width=width, height=height, media_type=mime)
        db.add(photo)
        db.flush()
        db.add(AuditEvent(entity_type="photo", entity_id=photo.id, action="uploaded",
                          actor="owner", detail="Image normalized, EXIF removed, encrypted"))
        db.commit()
        return {"id": photo.id, "assessment_id": assessment_id, "width": width, "height": height,
                "media_type": mime, "sha256": digest, "quality": inspect_quality(cleaned).model_dump()}

    @router.get("/assessments/{assessment_id}/photos")
    def list_photos(assessment_id: str, db: Session = Depends(get_db)):
        if db.get(Assessment, assessment_id) is None:
            raise HTTPException(status_code=404, detail="Avaliação não encontrada")
        photos = db.scalars(select(Photo).where(Photo.assessment_id == assessment_id).order_by(Photo.uploaded_at)).all()
        return [{"id": p.id, "assessment_id": p.assessment_id, "width": p.width,
                 "height": p.height, "uploaded_at": p.uploaded_at.isoformat()} for p in photos]

    @router.get("/photos/{photo_id}/quality")
    def photo_quality(photo_id: str, db: Session = Depends(get_db)):
        photo = db.get(Photo, photo_id)
        if photo is None:
            raise HTTPException(status_code=404, detail="Imagem não encontrada")
        try:
            data = read_encrypted(photo.filename, config)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="Imagem não disponível") from exc
        return inspect_quality(data).model_dump()

    @router.get("/photos/{photo_id}")
    def download_photo(photo_id: str, db: Session = Depends(get_db)):
        photo = db.get(Photo, photo_id)
        if photo is None:
            raise HTTPException(status_code=404, detail="Imagem não encontrada")
        try:
            data = read_encrypted(photo.filename, config)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="Imagem não disponível") from exc
        return Response(content=data, media_type=photo.media_type,
                        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
                                 "Content-Disposition": "inline; filename=lesao.jpg"})

    app.include_router(router)
