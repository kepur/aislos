"""Stripe Connect integration (Phase E). Constitution Article 3 intact:
money sits at Stripe, our system stays a ledger. Online funding replaces the
admin's manual "mark funded" with a verified webhook — the milestone state
machine and double-entry ledger are unchanged.

Requires an EU platform entity (Stripe does not serve Serbian entities).
Unconfigured -> callers get a clear error and the offline flow keeps working.
Credentials live in Admin → Integrations → stripe.
"""
from __future__ import annotations

import asyncio
from typing import Any

import stripe
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import PartnerDeposit, PaymentMilestone, PaymentPlan
from app.models.service import ServicePartner
from app.services.integrations import get_config
from app.services.payments import mark_milestone_funded

EVENT_CHECKOUT_COMPLETED = "checkout.session.completed"


async def stripe_config(db: AsyncSession) -> dict[str, Any]:
    return await get_config(db, "stripe")


def is_configured(cfg: dict[str, Any]) -> bool:
    return bool(cfg.get("_enabled") and cfg.get("secret_key"))


def _client(cfg: dict[str, Any]) -> stripe.StripeClient:
    return stripe.StripeClient(cfg["secret_key"])


async def create_milestone_checkout(db: AsyncSession, milestone: PaymentMilestone) -> str:
    cfg = await stripe_config(db)
    if not is_configured(cfg):
        raise ValueError("Stripe is not configured (Admin → Integrations → stripe)")
    if milestone.status not in ("pending", "invoiced"):
        raise ValueError(f"Milestone is {milestone.status}, cannot create checkout")
    plan = await db.get(PaymentPlan, milestone.plan_id)
    client = _client(cfg)
    session = await asyncio.to_thread(
        client.checkout.sessions.create,
        params={
            "mode": "payment",
            "line_items": [{
                "price_data": {
                    "currency": plan.currency.lower(),
                    "unit_amount": int(round(float(milestone.amount) * 100)),
                    "product_data": {"name": f"AinerWise — {milestone.label} (plan {str(plan.id)[:8]})"},
                },
                "quantity": 1,
            }],
            "metadata": {"kind": "milestone", "milestone_id": str(milestone.id)},
            "success_url": cfg.get("success_url") or "http://localhost:4099/?payment=success",
            "cancel_url": cfg.get("cancel_url") or "http://localhost:4099/?payment=cancelled",
        },
    )
    milestone.status = "invoiced"
    milestone.external_ref = session.id
    db.add(milestone)
    await db.commit()
    return session.url


async def create_deposit_checkout(db: AsyncSession, deposit: PartnerDeposit) -> str:
    cfg = await stripe_config(db)
    if not is_configured(cfg):
        raise ValueError("Stripe is not configured (Admin → Integrations → stripe)")
    client = _client(cfg)
    session = await asyncio.to_thread(
        client.checkout.sessions.create,
        params={
            "mode": "payment",
            "line_items": [{
                "price_data": {
                    "currency": deposit.currency.lower(),
                    "unit_amount": int(round(float(deposit.amount) * 100)),
                    "product_data": {"name": "AinerWise partner security deposit"},
                },
                "quantity": 1,
            }],
            "metadata": {"kind": "partner_deposit", "deposit_id": str(deposit.id)},
            "success_url": cfg.get("success_url") or "http://localhost:4098/partner?deposit=success",
            "cancel_url": cfg.get("cancel_url") or "http://localhost:4098/partner?deposit=cancelled",
        },
    )
    deposit.external_ref = session.id
    db.add(deposit)
    await db.commit()
    return session.url


async def create_partner_onboarding_link(db: AsyncSession, partner: ServicePartner) -> str:
    """Stripe Connect Express account + onboarding link for payouts."""
    cfg = await stripe_config(db)
    if not is_configured(cfg):
        raise ValueError("Stripe is not configured (Admin → Integrations → stripe)")
    client = _client(cfg)
    account_id = partner.stripe_account_id
    if not account_id:
        account = await asyncio.to_thread(
            client.accounts.create,
            params={"type": "express", "capabilities": {"transfers": {"requested": True}}},
        )
        account_id = account.id
        partner.stripe_account_id = account_id
        db.add(partner)
        await db.commit()
    link = await asyncio.to_thread(
        client.account_links.create,
        params={
            "account": account_id,
            "type": "account_onboarding",
            "refresh_url": cfg.get("cancel_url") or "http://localhost:4098/partner",
            "return_url": cfg.get("success_url") or "http://localhost:4098/partner",
        },
    )
    return link.url


async def transfer_to_partner(db: AsyncSession, milestone: PaymentMilestone, partner: ServicePartner) -> str:
    """Payout a released milestone to the partner's Connect account."""
    cfg = await stripe_config(db)
    if not is_configured(cfg):
        raise ValueError("Stripe is not configured (Admin → Integrations → stripe)")
    if not partner.stripe_account_id:
        raise ValueError("Partner has no Stripe Connect account — onboard first")
    if milestone.status != "released":
        raise ValueError("Release the milestone before transferring")
    plan = await db.get(PaymentPlan, milestone.plan_id)
    client = _client(cfg)
    transfer = await asyncio.to_thread(
        client.transfers.create,
        params={
            "amount": int(round(float(milestone.amount) * 100)),
            "currency": plan.currency.lower(),
            "destination": partner.stripe_account_id,
            "metadata": {"milestone_id": str(milestone.id)},
        },
    )
    from app.services.payments import _ledger_pair
    import uuid as _uuid
    from decimal import Decimal

    for entry in _ledger_pair(
        _uuid.uuid4(), "platform:revenue", f"partner:{partner.id}",
        Decimal(milestone.amount), plan.currency, milestone.id,
        f"stripe transfer {transfer.id} to partner",
    ):
        db.add(entry)
    await db.commit()
    return transfer.id


def verify_webhook(payload: bytes, signature_header: str, webhook_secret: str) -> stripe.Event:
    return stripe.Webhook.construct_event(payload, signature_header, webhook_secret)


async def handle_stripe_event(db: AsyncSession, event: stripe.Event) -> dict:
    if event["type"] != EVENT_CHECKOUT_COMPLETED:
        return {"handled": False, "type": event["type"]}
    session = event["data"]["object"]
    metadata = session.get("metadata") or {}
    kind = metadata.get("kind")
    if kind == "milestone" and metadata.get("milestone_id"):
        import uuid as _uuid

        milestone = await db.get(PaymentMilestone, _uuid.UUID(metadata["milestone_id"]))
        if milestone is None:
            return {"handled": False, "reason": "milestone not found"}
        if milestone.status == "funded":
            return {"handled": True, "idempotent": True}
        await mark_milestone_funded(
            db, milestone,
            memo=f"stripe checkout {session.get('id')}",
            source_account="escrow:psp",
            external_ref=str(session.get("payment_intent") or session.get("id")),
        )
        await db.commit()
        return {"handled": True, "milestone_id": metadata["milestone_id"]}
    if kind == "partner_deposit" and metadata.get("deposit_id"):
        import uuid as _uuid

        deposit = await db.get(PartnerDeposit, _uuid.UUID(metadata["deposit_id"]))
        if deposit is None:
            return {"handled": False, "reason": "deposit not found"}
        if deposit.status == "held":
            return {"handled": True, "idempotent": True}
        deposit.status = "held"
        deposit.external_ref = str(session.get("payment_intent") or session.get("id"))
        db.add(deposit)
        await db.commit()
        return {"handled": True, "deposit_id": metadata["deposit_id"]}
    return {"handled": False, "reason": "unknown metadata kind"}
