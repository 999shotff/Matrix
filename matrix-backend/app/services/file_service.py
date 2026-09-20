from __future__ import annotations
import os
import uuid
from pathlib import Path

from fastapi import UploadFile
from pypdf import PdfReader
import docx

STORAGE_DIR = Path(os.getenv("STORAGE_DIR", "./storage"))
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def save_upload(file: UploadFile) -> str:
    """Save an uploaded file to disk and return its file_id (used later to
    reference it from a GenerateRequest)."""
    file_id = str(uuid.uuid4())
    ext = Path(file.filename or "").suffix
    dest = STORAGE_DIR / f"{file_id}{ext}"
    with open(dest, "wb") as f:
        f.write(file.file.read())
    return file_id + ext  # store extension in the id so extraction knows the type


def _find_path(file_ref: str) -> Path | None:
    p = STORAGE_DIR / file_ref
    return p if p.exists() else None


def extract_text(file_ref: str) -> str:
    """Best-effort text extraction. PDFs and DOCX are read directly.
    Images are noted but not OCR'd in this scaffold — wire in a real OCR
    (e.g. an NVIDIA NIM vision model, or Tesseract) before production."""
    path = _find_path(file_ref)
    if not path:
        return ""

    suffix = path.suffix.lower()
    try:
        if suffix == ".pdf":
            reader = PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        if suffix in (".docx",):
            d = docx.Document(str(path))
            return "\n".join(p.text for p in d.paragraphs)
        if suffix in (".txt", ".md"):
            return path.read_text(errors="ignore")
        if suffix in (".png", ".jpg", ".jpeg", ".webp"):
            return f"[Image file '{path.name}' — route this through an OCR / vision " \
                   f"model before it can be used as text source material.]"
    except Exception as e:
        return f"[Could not extract text from {path.name}: {e}]"

    return ""


def extract_text_many(file_refs: list[str]) -> str:
    return "\n\n".join(extract_text(ref) for ref in file_refs if ref)
