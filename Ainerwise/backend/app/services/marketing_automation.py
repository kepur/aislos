from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inquiry import Inquiry
from app.models.lead import Lead
from app.models.marketing import MarketingActivity, MarketingCampaign, MarketingContact


PRELIMINARY_NOTICE = (
    "Preliminary follow-up draft. Review and approve before sending. "
    "Do not send promotional messages without the required consent."
)


def build_lead_follow_up_draft(lead: Lead) -> dict:
    name = lead.contact_name or "there"
    project = lead.project_type or "smart building project"
    language = (lead.language or "en").lower()
    if language == "zh":
        subject = f"AinerWise 已收到您的{project}需求"
        content = (
            f"{name}，您好：\n\n我们已收到您的{project}需求。"
            "下一步我们会由本地团队审核需求，并确认是否需要现场勘察或补充资料。\n\n"
            "此内容为初步跟进草稿，发送前需要人工审核。"
        )
    elif language == "sr":
        subject = f"AinerWise je primio vaš upit: {project}"
        content = (
            f"Poštovani/a {name},\n\nPrimili smo vaš upit za {project}. "
            "Naš lokalni tim će pregledati zahtev i potvrditi sledeći korak, "
            "uključujući eventualni obilazak lokacije ili dodatna pitanja.\n\n"
            "Ovo je preliminarni nacrt i zahteva odobrenje pre slanja."
        )
    else:
        subject = f"AinerWise received your {project} request"
        content = (
            f"Hello {name},\n\nWe received your request for {project}. "
            "Our local team will review it and confirm the next step, including "
            "whether a site visit or more information is needed.\n\n"
            "This is a preliminary draft and requires approval before sending."
        )
    return {"subject": subject, "content": content}


def follow_up_delay(lead_score: int | None, phase1_requested: bool = False) -> timedelta:
    if phase1_requested or (lead_score or 0) >= 70:
        return timedelta(minutes=15)
    if (lead_score or 0) >= 45:
        return timedelta(hours=4)
    return timedelta(hours=24)


async def resolve_campaign_id(db: AsyncSession, utm_campaign: str | None):
    if not utm_campaign:
        return None
    result = await db.execute(
        select(MarketingCampaign.id)
        .where(MarketingCampaign.utm_campaign == utm_campaign)
        .order_by(MarketingCampaign.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


def _render_campaign_text(template: str, contact: MarketingContact) -> str:
    return (
        template.replace("{name}", contact.contact_name or "there")
        .replace("{company}", contact.company_name or "your company")
    )


async def prepare_campaign_drafts(
    db: AsyncSession, campaign: MarketingCampaign
) -> dict[str, int]:
    """Create reviewable outreach drafts only for contacts with explicit opt-in."""
    audience = campaign.audience_json or {}
    segments = audience.get("segments") or []
    query = select(MarketingContact).where(
        MarketingContact.consent_status == "opted_in",
        MarketingContact.status != "unsubscribed",
        or_(MarketingContact.email.is_not(None), MarketingContact.phone.is_not(None)),
    )
    if segments:
        query = query.where(MarketingContact.segment.in_(segments))
    contacts = list((await db.execute(query)).scalars().all())
    content = campaign.content_json or {}
    subject_template = content.get("subject") or f"{campaign.name}: local AinerWise update"
    body_template = content.get("body") or (
        "Hello {name},\n\nAinerWise is sharing a local smart-building update "
        "that may be relevant to {company}. Reply if you would like a short consultation."
    )
    created = 0
    skipped = 0
    for contact in contacts:
        existing = await db.execute(
            select(MarketingActivity.id)
            .where(
                MarketingActivity.campaign_id == campaign.id,
                MarketingActivity.contact_id == contact.id,
                MarketingActivity.activity_type == "campaign_outreach",
            )
            .limit(1)
        )
        if existing.scalar_one_or_none():
            skipped += 1
            continue
        activity = MarketingActivity(
            campaign_id=campaign.id,
            contact_id=contact.id,
            activity_type="campaign_outreach",
            channel="email" if contact.email else "call",
            status="pending_approval",
            subject=_render_campaign_text(subject_template, contact),
            content=f"{_render_campaign_text(body_template, contact)}\n\n{PRELIMINARY_NOTICE}",
            scheduled_at=campaign.starts_at or datetime.now(timezone.utc),
            result_json={
                "automation": "campaign_draft_generation",
                "origin_channel": campaign.channel,
                "requires_human_review": True,
            },
        )
        db.add(activity)
        created += 1
    await db.commit()
    return {"eligible": len(contacts), "created": created, "skipped_existing": skipped}


async def prepare_active_campaigns(db: AsyncSession) -> dict[str, int]:
    """Prepare review drafts for currently active campaigns; intended for Celery beat."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(MarketingCampaign).where(
            MarketingCampaign.status == "active",
            or_(MarketingCampaign.starts_at.is_(None), MarketingCampaign.starts_at <= now),
            or_(MarketingCampaign.ends_at.is_(None), MarketingCampaign.ends_at >= now),
        )
    )
    campaigns = list(result.scalars().all())
    created = 0
    for campaign in campaigns:
        summary = await prepare_campaign_drafts(db, campaign)
        created += summary["created"]
    return {"active_campaigns": len(campaigns), "created": created}


async def _upsert_contact(
    db: AsyncSession,
    *,
    contact_name: str | None,
    email: str | None,
    phone: str | None,
    language: str,
    source: str | None,
    lead_id=None,
) -> MarketingContact:
    contact = None
    if email and "unknown@" not in email:
        result = await db.execute(
            select(MarketingContact).where(MarketingContact.email == email).limit(1)
        )
        contact = result.scalar_one_or_none()
    if contact is None:
        contact = MarketingContact(
            contact_name=contact_name,
            email=email if email and "unknown@" not in email else None,
            phone=phone,
            language=language or "en",
            source=source or "website",
            status="engaged",
            consent_status="inquiry_only",
            lead_id=lead_id,
        )
    else:
        contact.contact_name = contact_name or contact.contact_name
        contact.phone = phone or contact.phone
        if contact.consent_status != "unsubscribed":
            contact.status = "engaged"
        contact.lead_id = lead_id or contact.lead_id
    db.add(contact)
    await db.flush()
    return contact


async def ensure_lead_follow_up(db: AsyncSession, lead: Lead) -> MarketingActivity:
    result = await db.execute(
        select(MarketingActivity)
        .where(
            MarketingActivity.lead_id == lead.id,
            MarketingActivity.activity_type == "lead_follow_up",
        )
        .limit(1)
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    contact = await _upsert_contact(
        db,
        contact_name=lead.contact_name,
        email=lead.contact_email,
        phone=lead.contact_phone,
        language=lead.language,
        source=lead.source_channel,
        lead_id=lead.id,
    )
    draft = build_lead_follow_up_draft(lead)
    site_info = lead.site_info_json or {}
    scheduled_at = datetime.now(timezone.utc) + follow_up_delay(
        lead.lead_score, bool(site_info.get("phase1_requested"))
    )
    contact.next_follow_up_at = scheduled_at
    activity = MarketingActivity(
        campaign_id=lead.campaign_id,
        contact_id=contact.id,
        lead_id=lead.id,
        activity_type="lead_follow_up",
        channel="email" if contact.email else "call",
        status="pending_approval",
        subject=draft["subject"],
        content=f'{draft["content"]}\n\n{PRELIMINARY_NOTICE}',
        scheduled_at=scheduled_at,
        result_json={"automation": "new_lead_follow_up", "requires_human_review": True},
    )
    db.add(activity)
    await db.commit()
    await db.refresh(activity)
    return activity


async def ensure_inquiry_follow_up(db: AsyncSession, inquiry: Inquiry) -> MarketingActivity:
    result = await db.execute(
        select(MarketingActivity)
        .where(
            MarketingActivity.inquiry_id == inquiry.id,
            MarketingActivity.activity_type == "inquiry_follow_up",
        )
        .limit(1)
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    contact = await _upsert_contact(
        db,
        contact_name=inquiry.contact_name,
        email=inquiry.contact_email,
        phone=inquiry.contact_phone,
        language="en",
        source=inquiry.source_channel,
    )
    scheduled_at = datetime.now(timezone.utc) + timedelta(hours=4)
    contact.next_follow_up_at = scheduled_at
    activity = MarketingActivity(
        campaign_id=inquiry.campaign_id,
        contact_id=contact.id,
        inquiry_id=inquiry.id,
        activity_type="inquiry_follow_up",
        channel="email" if contact.email else "call",
        status="pending_approval",
        subject="AinerWise product inquiry follow-up",
        content=(
            f"Hello {inquiry.contact_name or 'there'},\n\n"
            "Thank you for your product inquiry. We will confirm compatibility, "
            "availability, local installation options, and the best next step.\n\n"
            f"{PRELIMINARY_NOTICE}"
        ),
        scheduled_at=scheduled_at,
        result_json={"automation": "new_inquiry_follow_up", "requires_human_review": True},
    )
    db.add(activity)
    await db.commit()
    await db.refresh(activity)
    return activity
