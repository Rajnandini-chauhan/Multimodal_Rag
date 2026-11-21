import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import get_settings

settings = get_settings()

PDF_MAGIC_BYTES = b"%PDF-"


class InvalidPDFError(Exception):
    """Raised when an uploaded file fails PDF validation."""


def validate_pdf(file: UploadFile, contents: bytes) -> None:
    """Validate that an uploaded file is actually a PDF, within size limits.

    Checks:
    - filename ends with .pdf
    - file starts with the PDF magic bytes (not just trusting the extension)
    - file size does not exceed the configured limit
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise InvalidPDFError("Only .pdf files are accepted")

    if not contents.startswith(PDF_MAGIC_BYTES):
        raise InvalidPDFError("File content does not look like a valid PDF")

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(contents) > max_bytes:
        raise InvalidPDFError(
            f"File exceeds the maximum allowed size of {settings.max_upload_size_mb}MB"
        )


def save_pdf(owner_id: uuid.UUID, contents: bytes) -> str:
    """Save validated PDF bytes to local disk, namespaced by owner, and return
    the storage path (relative to the configured upload directory's parent)."""
    owner_dir = Path(settings.upload_dir) / str(owner_id)
    owner_dir.mkdir(parents=True, exist_ok=True)

    file_id = uuid.uuid4()
    file_path = owner_dir / f"{file_id}.pdf"
    file_path.write_bytes(contents)

    return str(file_path)