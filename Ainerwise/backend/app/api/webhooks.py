"""Public webhook receivers (signature-verified, no JWT).

/webhooks/stripe must be reachable by Stripe in production (nginx route);
verification uses the webhook secret from Admin → Integrations → stripe.
"""
from fastapi import APIRouter, Header, HTTPException, Request

from app.api.deps import DB
from app.services.integrations import get_config

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/stripe")
async def stripe_webhook(request: Request, db: DB, stripe_signature: str = Header(None, alias="Stripe-Signature")):
    import stripe as stripe_lib

    from app.services.stripe_payments import handle_stripe_event, verify_webhook

    cfg = await get_config(db, "stripe")
    webhook_secret = cfg.get("webhook_secret")
    if not webhook_secret:
        raise HTTPException(status_code=503, detail="Stripe webhook not configured")
    payload = await request.body()
    try:
        event = verify_webhook(payload, stripe_signature or "", webhook_secret)
    except (stripe_lib.error.SignatureVerificationError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid signature") from None
    return await handle_stripe_event(db, event)
