"""Deterministic PDF citation checking; no OCR, LLM, clinical interpretation.

PDFs are never passed to remote providers. Hard limits reduce parser abuse.
"""
import hashlib
import io
import re
from pypdf import PdfReader

MAX_PDF_BYTES = 6 * 1024 * 1024
MAX_PAGES = 100
MAX_PAGE_TEXT = 80_000

def read_pages(data: bytes) -> list[str]:
    if not data.startswith(b"%PDF-") or len(data) > MAX_PDF_BYTES:
        raise ValueError("PDF inválido ou maior que 6 MB")
    try:
        pdf = PdfReader(io.BytesIO(data), strict=True)
        if pdf.is_encrypted:
            raise ValueError("PDF protegido por senha não aceito")
        if len(pdf.pages) < 1 or len(pdf.pages) > MAX_PAGES:
            raise ValueError("PDF deve ter entre 1 e 100 páginas")
        pages = []
        for page in pdf.pages:
            text = page.extract_text() or ""
            if len(text) > MAX_PAGE_TEXT:
                raise ValueError("Texto da página ultrapassa o limite")
            pages.append(text)
        return pages
    except ValueError:
        raise
    except Exception as e:
        raise ValueError("Não foi possível extrair texto do PDF") from e

def normalize(s: str) -> str:
    # Handle PDF line wraps and whitespace; no fuzzy match that might fabricate a quote.
    return " ".join(re.sub(r"\s+", " ", s).split()).casefold()

def check_citation(data: bytes, page: int, excerpt: str) -> tuple[str, str]:
    pages = read_pages(data)
    if not 1 <= page <= len(pages):
        raise ValueError("Página fora do documento")
    if not pages[page - 1].strip():
        raise ValueError("Página sem texto extraível; exige conferência manual")
    normalized_excerpt = normalize(excerpt)
    if len(normalized_excerpt) < 20 or normalized_excerpt not in normalize(pages[page - 1]):
        raise ValueError("Citação não encontrada exatamente no texto extraído da página")
    return (
        hashlib.sha256(excerpt.encode("utf-8")).hexdigest(),
        hashlib.sha256(pages[page - 1].encode("utf-8")).hexdigest(),
    )
