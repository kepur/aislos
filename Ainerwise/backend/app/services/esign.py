"""Online signing (eIDAS simple electronic signature).

Audit trail per signature: exact document hash at send time, signer identity,
IP, user agent, timestamp, drawn-signature image in MinIO. Sufficient for
typical B2B contracts; qualified signatures (QES) would come from an external
provider in a later phase if a market requires it.
"""
from __future__ import annotations

import base64
import hashlib
import io
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.content import DocumentSignature, GeneratedDocument
from app.services.documents import DOCUMENTS_BUCKET, store_pdf
from app.services.event_bus import emit_event
from app.services.knowledge import get_minio_client

EVENT_DOCUMENT_SENT = "document.sent_for_signature"
EVENT_DOCUMENT_SIGNED = "document.signed"
SIGNING_VALID_DAYS = 14


def document_hash(body_md: str) -> str:
    return hashlib.sha256(body_md.encode("utf-8")).hexdigest()


def signing_url(token: str) -> str:
    return f"{settings.SIGN_BASE_URL.rstrip('/')}/sign/{token}"


async def send_for_signature(
    db: AsyncSession,
    document: GeneratedDocument,
    *,
    signer_name: str,
    signer_email: str | None,
) -> DocumentSignature:
    if document.status not in ("final", "sent_for_signature"):
        raise ValueError("Finalize the document before sending for signature")
    if not document.body_md:
        raise ValueError("Document body is empty")
    signature = DocumentSignature(
        document_id=document.id,
        signer_name=signer_name,
        signer_email=signer_email,
        token=secrets.token_urlsafe(32)[:64],
        status="sent",
        document_sha256=document_hash(document.body_md),
        expires_at=datetime.now(timezone.utc) + timedelta(days=SIGNING_VALID_DAYS),
    )
    db.add(signature)
    document.status = "sent_for_signature"
    db.add(document)
    await db.flush()
    await emit_event(
        db, EVENT_DOCUMENT_SENT,
        {"document_id": str(document.id), "signature_id": str(signature.id),
         "signer_email": signer_email, "url": signing_url(signature.token)},
        aggregate_type="document", aggregate_id=document.id,
    )
    if signer_email:
        try:
            from app.services.email import send_email

            await send_email(
                db, to=[signer_email],
                subject=f"AinerWise — please sign: {document.title}",
                body=(f"Hello {signer_name},\n\nPlease review and sign the document "
                      f"'{document.title}':\n{signing_url(signature.token)}\n\n"
                      f"The link is valid for {SIGNING_VALID_DAYS} days.\n\nAinerWise"),
            )
        except Exception:  # noqa: BLE001 — link can always be shared manually
            pass
    return signature


async def load_for_signing(db: AsyncSession, token: str) -> tuple[DocumentSignature, GeneratedDocument]:
    signature = (
        await db.execute(select(DocumentSignature).where(DocumentSignature.token == token))
    ).scalar_one_or_none()
    if signature is None:
        raise LookupError("Invalid signing link")
    if signature.status == "signed":
        raise ValueError("Document already signed")
    if signature.status in ("cancelled", "expired"):
        raise ValueError(f"Signing link {signature.status}")
    if signature.expires_at and signature.expires_at < datetime.now(timezone.utc):
        signature.status = "expired"
        db.add(signature)
        await db.commit()
        raise ValueError("Signing link expired")
    document = await db.get(GeneratedDocument, signature.document_id)
    if document is None:
        raise LookupError("Document not found")
    if signature.status == "sent":
        signature.status = "viewed"
        db.add(signature)
        await db.flush()
    return signature, document


async def apply_signature(
    db: AsyncSession,
    token: str,
    *,
    signature_data_url: str,
    signer_name: str | None,
    signer_ip: str | None,
    user_agent: str | None,
) -> DocumentSignature:
    signature, document = await load_for_signing(db, token)
    if document_hash(document.body_md or "") != signature.document_sha256:
        raise ValueError("Document changed after it was sent — request a new signing link")

    # store the drawn signature image
    try:
        header, payload = signature_data_url.split(",", 1)
        if "image/" not in header:
            raise ValueError
        image_bytes = base64.b64decode(payload)
    except (ValueError, IndexError):
        raise ValueError("Invalid signature image") from None
    client = get_minio_client()
    if not client.bucket_exists(DOCUMENTS_BUCKET):
        client.make_bucket(DOCUMENTS_BUCKET)
    object_name = f"signatures/{uuid.uuid4()}.png"
    client.put_object(DOCUMENTS_BUCKET, object_name, io.BytesIO(image_bytes), len(image_bytes),
                      content_type="image/png")

    now = datetime.now(timezone.utc)
    signature.status = "signed"
    signature.signed_at = now
    signature.signer_ip = signer_ip
    signature.signer_user_agent = (user_agent or "")[:500]
    signature.signature_minio_key = object_name
    if signer_name:
        signature.signer_name = signer_name
    db.add(signature)

    attestation = (
        f"\n\n---\n## Electronic signature\n"
        f"Signed by: {signature.signer_name}\n"
        f"Date: {now:%Y-%m-%d %H:%M} UTC\n"
        f"Document SHA-256: {signature.document_sha256}\n"
        f"Signature ID: {signature.id}\n"
        f"Method: simple electronic signature (eIDAS SES)"
    )
    document.body_md = (document.body_md or "") + attestation
    document.pdf_minio_key = store_pdf(document.title, document.body_md)
    document.status = "signed"
    db.add(document)
    await db.flush()
    await emit_event(
        db, EVENT_DOCUMENT_SIGNED,
        {"document_id": str(document.id), "signature_id": str(signature.id),
         "signer_name": signature.signer_name, "title": document.title},
        aggregate_type="document", aggregate_id=document.id,
        target_channel="telegram_admin",
    )
    await db.commit()
    return signature
