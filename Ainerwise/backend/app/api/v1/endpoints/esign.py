"""Public signing endpoints (token-authenticated) + admin send-for-signature."""
import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import DB, AdminUser
from app.models.content import DocumentSignature, GeneratedDocument
from app.services.esign import apply_signature, load_for_signing, send_for_signature, signing_url

router = APIRouter(tags=["esign"])


class SendForSignatureRequest(BaseModel):
    signer_name: str
    signer_email: str | None = None


class SignRequest(BaseModel):
    signature_data_url: str
    signer_name: str | None = None
    agreed: bool = False


@router.post("/admin/documents/{id}/send-for-signature")
async def send_document_for_signature(id: uuid.UUID, data: SendForSignatureRequest, db: DB, admin: AdminUser):
    document = await db.get(GeneratedDocument, id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    try:
        signature = await send_for_signature(
            db, document, signer_name=data.signer_name, signer_email=data.signer_email
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    await db.commit()
    return {
        "signature_id": str(signature.id),
        "signing_url": signing_url(signature.token),
        "expires_at": signature.expires_at.isoformat() if signature.expires_at else None,
    }


@router.get("/admin/documents/{id}/signatures")
async def list_document_signatures(id: uuid.UUID, db: DB, admin: AdminUser):
    rows = (
        await db.execute(
            select(DocumentSignature).where(DocumentSignature.document_id == id)
            .order_by(DocumentSignature.created_at.desc())
        )
    ).scalars().all()
    return {
        "items": [
            {"id": str(s.id), "signer_name": s.signer_name, "signer_email": s.signer_email,
             "status": s.status, "signed_at": s.signed_at.isoformat() if s.signed_at else None,
             "signing_url": signing_url(s.token) if s.status in ("sent", "viewed") else None,
             "document_sha256": s.document_sha256}
            for s in rows
        ]
    }


@router.get("/sign/{token}")
async def get_signing_view(token: str, db: DB):
    try:
        signature, document = await load_for_signing(db, token)
    except LookupError:
        raise HTTPException(status_code=404, detail="Invalid signing link") from None
    except ValueError as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from None
    await db.commit()
    return {
        "title": document.title,
        "body_md": document.body_md,
        "signer_name": signature.signer_name,
        "expires_at": signature.expires_at.isoformat() if signature.expires_at else None,
    }


@router.post("/sign/{token}")
async def sign_document(token: str, data: SignRequest, request: Request, db: DB):
    if not data.agreed:
        raise HTTPException(status_code=400, detail="Consent checkbox is required")
    try:
        signature = await apply_signature(
            db, token,
            signature_data_url=data.signature_data_url,
            signer_name=data.signer_name,
            signer_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except LookupError:
        raise HTTPException(status_code=404, detail="Invalid signing link") from None
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    return {"signed": True, "signed_at": signature.signed_at.isoformat()}
