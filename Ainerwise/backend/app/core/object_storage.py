"""Object-storage key ownership rules shared by upload and business APIs."""
from __future__ import annotations

import uuid
from pathlib import Path


def safe_upload_filename(filename: str) -> str:
    safe_name = Path(filename).name
    return "" if safe_name in {"", ".", ".."} else safe_name


def user_upload_prefix(user_id: uuid.UUID) -> str:
    return f"uploads/{user_id}/"


def new_user_upload_key(user_id: uuid.UUID, filename: str) -> str:
    safe_filename = safe_upload_filename(filename)
    if not safe_filename:
        raise ValueError("Filename is required")
    return f"{user_upload_prefix(user_id)}{uuid.uuid4()}/{safe_filename}"


def is_user_upload_key(object_name: str, user_id: uuid.UUID) -> bool:
    return object_name.startswith(user_upload_prefix(user_id))
