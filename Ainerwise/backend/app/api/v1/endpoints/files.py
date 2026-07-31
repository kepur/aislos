from datetime import timedelta

from fastapi import APIRouter, HTTPException, Query, status
from minio import Minio

from app.api.deps import CurrentUser
from app.core.config import settings
from app.core.object_storage import is_user_upload_key, new_user_upload_key
from app.core.permissions import UserRole

router = APIRouter(prefix="/files", tags=["files"])


def get_minio_client() -> Minio:
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ROOT_USER,
        secret_key=settings.MINIO_ROOT_PASSWORD,
        secure=settings.MINIO_USE_SSL,
    )


BUCKET_NAME = "ainerwise"


@router.post("/upload-url")
async def get_upload_url(
    filename: str = Query(...),
    content_type: str = Query("application/octet-stream"),
    user: CurrentUser = None,
):
    client = get_minio_client()
    if not client.bucket_exists(BUCKET_NAME):
        client.make_bucket(BUCKET_NAME)

    try:
        object_name = new_user_upload_key(user.id, filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Filename is required")
    url = client.presigned_put_object(
        BUCKET_NAME, object_name, expires=timedelta(hours=1)
    )
    return {"upload_url": url, "object_name": object_name}


@router.get("/download-url")
async def get_download_url(
    object_name: str = Query(...),
    user: CurrentUser = None,
):
    admin_roles = {UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value}
    if not is_user_upload_key(object_name, user.id) and user.role not in admin_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="File access denied",
        )
    client = get_minio_client()
    url = client.presigned_get_object(
        BUCKET_NAME, object_name, expires=timedelta(hours=1)
    )
    return {"download_url": url}
