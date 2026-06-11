import uuid
from datetime import timedelta

from fastapi import APIRouter, HTTPException, Query
from minio import Minio

from app.api.deps import CurrentUser, DB
from app.core.config import settings

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

    object_name = f"uploads/{uuid.uuid4()}/{filename}"
    url = client.presigned_put_object(
        BUCKET_NAME, object_name, expires=timedelta(hours=1)
    )
    return {"upload_url": url, "object_name": object_name}


@router.get("/download-url")
async def get_download_url(
    object_name: str = Query(...),
    user: CurrentUser = None,
):
    client = get_minio_client()
    url = client.presigned_get_object(
        BUCKET_NAME, object_name, expires=timedelta(hours=1)
    )
    return {"download_url": url}
