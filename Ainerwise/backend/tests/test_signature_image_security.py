import base64

import pytest

from app.core.signature_image import MAX_SIGNATURE_BYTES, validate_signature_data_url


PNG = b"\x89PNG\r\n\x1a\n" + b"test"


def test_signature_data_url_accepts_small_png_only():
    value = "data:image/png;base64," + base64.b64encode(PNG).decode()
    assert validate_signature_data_url(value) == PNG

    with pytest.raises(ValueError):
        validate_signature_data_url("data:image/jpeg;base64," + base64.b64encode(PNG).decode())
    with pytest.raises(ValueError):
        validate_signature_data_url("data:image/png;base64,not-base64")
    with pytest.raises(ValueError):
        validate_signature_data_url(
            "data:image/png;base64,"
            + base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"x" * MAX_SIGNATURE_BYTES).decode()
        )
