"""Validation shared by electronic-signature capture flows."""
from __future__ import annotations

import base64
import binascii

MAX_SIGNATURE_BYTES = 2 * 1024 * 1024
PNG_DATA_URL_PREFIX = "data:image/png;base64,"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def validate_signature_data_url(value: str) -> bytes:
    if not value.startswith(PNG_DATA_URL_PREFIX):
        raise ValueError("signature_data_url must be a PNG data URL")
    try:
        image_bytes = base64.b64decode(
            value[len(PNG_DATA_URL_PREFIX):],
            validate=True,
        )
    except (ValueError, binascii.Error):
        raise ValueError("Invalid signature image") from None
    if not image_bytes.startswith(PNG_MAGIC):
        raise ValueError("Invalid signature image")
    if len(image_bytes) > MAX_SIGNATURE_BYTES:
        raise ValueError("Signature image exceeds 2 MB")
    return image_bytes
