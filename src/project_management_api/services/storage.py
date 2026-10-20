import os
import re
import uuid
import zipfile
import io
from pathlib import Path
from fastapi import HTTPException, status
from project_management_api.config import get_settings

settings = get_settings()

UPLOAD_BASE_DIR = Path(os.getenv("UPLOAD_DIR", "uploads")).resolve()
AVATARS_DIR = UPLOAD_BASE_DIR / "avatars"
ATTACHMENTS_DIR = UPLOAD_BASE_DIR / "attachments"

# Ensure directories exist
AVATARS_DIR.mkdir(parents=True, exist_ok=True)
ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)

# Allowed MIME types and extensions
ALLOWED_IMAGE_MIMES = {
    "image/jpeg": [".jpg", ".jpeg"],
    "image/png": [".png"],
    "image/webp": [".webp"],
    "image/gif": [".gif"],
}

ALLOWED_DOCUMENT_MIMES = {
    "application/pdf": [".pdf"],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
}

ALLOWED_ATTACHMENT_MIMES = {**ALLOWED_IMAGE_MIMES, **ALLOWED_DOCUMENT_MIMES}

# File signatures (magic bytes)
def detect_file_mime(content: bytes) -> str | None:
    """Detects MIME type using magic bytes inspection to prevent disguised files."""
    if len(content) < 4:
        return None

    # JPEG: starts with FF D8 FF
    if content[:3] == b"\xff\xd8\xff":
        return "image/jpeg"

    # PNG: starts with 89 50 4E 47 0D 0A 1A 0A
    if content[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"

    # GIF: starts with GIF87a or GIF89a
    if content[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"

    # WebP: starts with RIFF....WEBP
    if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "image/webp"

    # PDF: starts with %PDF-
    if content[:5] == b"%PDF-":
        return "application/pdf"

    # DOCX: ZIP archive header PK\x03\x04 containing word/ or [Content_Types].xml
    if content[:4] == b"PK\x03\x04":
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                names = zf.namelist()
                if "[Content_Types].xml" in names and any(n.startswith("word/") for n in names):
                    return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        except Exception:
            pass

    return None


def sanitize_filename(filename: str) -> str:
    """Sanitizes user filename to prevent path traversal or problematic characters."""
    base = os.path.basename(filename)
    clean = re.sub(r"[^a-zA-Z0-9_.-]", "_", base)
    return clean[:200] if clean else "file"


class StorageService:
    @staticmethod
    def validate_avatar(content: bytes, filename: str) -> tuple[str, str]:
        """Validates that the file is an allowed image under 5MB."""
        max_size = 5 * 1024 * 1024  # 5MB
        if len(content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Avatar file exceeds the maximum allowed size of 5MB.",
            )

        detected_mime = detect_file_mime(content)
        if not detected_mime or detected_mime not in ALLOWED_IMAGE_MIMES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid avatar format. Only JPEG, PNG, WebP, and GIF images are supported.",
            )

        ext = ALLOWED_IMAGE_MIMES[detected_mime][0]
        return detected_mime, ext

    @staticmethod
    def validate_attachment(content: bytes, filename: str) -> tuple[str, str]:
        """Validates that the file is an allowed image or document under 10MB."""
        max_size = 10 * 1024 * 1024  # 10MB
        if len(content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Attachment '{filename}' exceeds the maximum allowed size of 10MB.",
            )

        detected_mime = detect_file_mime(content)
        if not detected_mime or detected_mime not in ALLOWED_ATTACHMENT_MIMES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{filename}' has an unsupported or disguised format. Allowed formats: JPEG, PNG, WebP, GIF, PDF, DOCX.",
            )

        ext = ALLOWED_ATTACHMENT_MIMES[detected_mime][0]
        return detected_mime, ext

    @staticmethod
    def save_avatar(content: bytes, extension: str) -> str:
        """Saves an avatar image and returns its storage key."""
        key = f"avatars/{uuid.uuid4().hex}{extension}"
        target_path = UPLOAD_BASE_DIR / key
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(content)
        return key

    @staticmethod
    def save_attachment(content: bytes, extension: str) -> str:
        """Saves a comment attachment and returns its storage key."""
        key = f"attachments/{uuid.uuid4().hex}{extension}"
        target_path = UPLOAD_BASE_DIR / key
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(content)
        return key

    @staticmethod
    def get_file_path(storage_key: str) -> Path:
        """Resolves storage key to absolute Path with strict path traversal verification."""
        resolved = (UPLOAD_BASE_DIR / storage_key).resolve()
        try:
            # Must be inside UPLOAD_BASE_DIR
            resolved.relative_to(UPLOAD_BASE_DIR)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid file path access.",
            )

        if not resolved.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found in storage.",
            )
        return resolved

    @staticmethod
    def delete_file(storage_key: str | None) -> bool:
        """Deletes file from storage safely."""
        if not storage_key:
            return False
        try:
            path = StorageService.get_file_path(storage_key)
            if path.exists():
                path.unlink()
                return True
        except Exception:
            pass
        return False
