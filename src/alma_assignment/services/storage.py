import os
import uuid
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from alma_assignment.core.config import settings

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


async def save_resume(lead_id: uuid.UUID, file: UploadFile) -> str:
    """Save uploaded resume and return its relative path."""
    if settings.storage_backend == "s3":
        return await _save_to_s3(lead_id, file)
    return await _save_locally(lead_id, file)


async def _save_locally(lead_id: uuid.UUID, file: UploadFile) -> str:
    base_dir = Path(settings.uploads_dir) / str(lead_id)
    base_dir.mkdir(parents=True, exist_ok=True)

    safe_filename = Path(file.filename or "resume").name
    dest = base_dir / safe_filename

    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise ValueError("File exceeds 10 MB limit")

    async with aiofiles.open(dest, "wb") as f:
        await f.write(content)

    return str(Path(str(lead_id)) / safe_filename)


async def _save_to_s3(lead_id: uuid.UUID, file: UploadFile) -> str:
    # Stub: wire up boto3 / aiobotocore here when STORAGE_BACKEND=s3
    raise NotImplementedError("S3 storage not yet implemented")


def get_resume_path(relative_path: str) -> Path:
    return Path(settings.uploads_dir) / relative_path
