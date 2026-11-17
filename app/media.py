"""Validate and encrypt images; do not retain EXIF metadata."""
import hashlib
import io
import os
from pathlib import Path
from uuid import uuid4
from cryptography.fernet import Fernet, InvalidToken
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_UPLOAD = 8 * 1024 * 1024
MAX_PIXELS = 24_000_000

def process_photo(raw: bytes) -> tuple[bytes, str, int, int]:
    if not raw or len(raw) > MAX_UPLOAD:
        raise ValueError("Imagem vazia ou maior que 8 MB")
    try:
        with Image.open(io.BytesIO(raw)) as image:
            image.verify()
        with Image.open(io.BytesIO(raw)) as image:
            width, height = image.size
            if width * height > MAX_PIXELS or min(width, height) < 32:
                raise ValueError("Dimensões da imagem fora dos limites")
            if image.format not in {"JPEG", "PNG", "WEBP"}:
                raise ValueError("Formato inválido: use JPEG, PNG ou WebP")
            safe = ImageOps.exif_transpose(image).convert("RGB")
            output = io.BytesIO()
            safe.save(output, format="JPEG", quality=90, optimize=True)
            return output.getvalue(), "image/jpeg", safe.width, safe.height
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError("Arquivo não é uma imagem válida") from exc

def store_encrypted(raw: bytes, config: dict) -> tuple[str, str]:
    folder = Path(os.getenv("FERIDAS_STORAGE_DIR", "./storage")).resolve()
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    filename = uuid4().hex + ".bin"
    encrypted = Fernet(config["image_key"].encode()).encrypt(raw)
    tmp = folder / (filename + ".tmp")
    tmp.write_bytes(encrypted)
    os.chmod(tmp, 0o600)
    tmp.replace(folder / filename)
    return filename, hashlib.sha256(raw).hexdigest()

def read_encrypted(filename: str, config: dict) -> bytes:
    if not filename.endswith(".bin") or len(filename) != 36 or not all(c in "0123456789abcdef" for c in filename[:-4]):
        raise ValueError("Referência de imagem inválida")
    path = Path(os.getenv("FERIDAS_STORAGE_DIR", "./storage")).resolve() / filename
    try:
        return Fernet(config["image_key"].encode()).decrypt(path.read_bytes())
    except (FileNotFoundError, InvalidToken) as exc:
        raise ValueError("Imagem não disponível ou inválida") from exc
