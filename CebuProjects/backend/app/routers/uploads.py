import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/uploads", tags=["Uploads"])

ALLOWED_TYPES = {
    "image/jpeg", "image/png", "image/webp", "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MAX_BYTES = settings.UPLOAD_MAX_SIZE_MB * 1024 * 1024


@router.post("")
async def upload_file(file: UploadFile, user: User = Depends(get_current_user)) -> JSONResponse:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"File type not allowed: {file.content_type}")

    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(status_code=400, detail=f"File too large (max {settings.UPLOAD_MAX_SIZE_MB}MB)")

    ext = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "bin"
    filename = f"{uuid.uuid4().hex}.{ext}"
    dest = os.path.join(settings.UPLOAD_DIR, filename)

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    with open(dest, "wb") as f:
        f.write(content)

    url = f"{settings.PUBLIC_FILE_BASE_URL}/{filename}"
    return JSONResponse({"url": url, "filename": filename, "size": len(content), "content_type": file.content_type})
