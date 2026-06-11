import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.deps import AdminUser, DB
from app.crud.base import CRUDBase
from app.models.inquiry import Inquiry
from app.models.lead import Lead
from app.models.marketing import (
    MarketingActivity,
    MarketingCampaign,
    MarketingContact,
    MarketingCreativeBrief,
    MarketingCreativeBriefVersion,
)
from app.schemas.marketing import (
    BriefRejectAction,
    BriefReviewAction,
    CreativeBriefCreate,
    CreativeBriefExternalExport,
    CreativeBriefRead,
    CreativeBriefVersionCreate,
    CreativeBriefVersionRead,
    CreativeBriefVersionUpdate,
    MarketingActivityCreate,
    MarketingActivityRead,
    MarketingActivityUpdate,
    MarketingCampaignCreate,
    MarketingCampaignRead,
    MarketingCampaignUpdate,
    MarketingContactCreate,
    MarketingContactRead,
    MarketingContactUpdate,
    MediaRequestRead,
)
from app.services.marketing_automation import prepare_campaign_drafts
from app.services.marketing_briefs import (
    MarketingBriefError,
    approve_version,
    build_export_payload,
    copy_rejected_to_draft,
    create_brief,
    create_brief_version,
    create_media_requests_for_version,
    get_brief,
    get_version,
    list_media_requests_for_version,
    reject_version,
    submit_version_review,
    update_draft_version,
)

router = APIRouter(prefix="/marketing", tags=["marketing"])
admin_brief_router = APIRouter(prefix="/admin/marketing", tags=["marketing-briefs"])

crud_campaign = CRUDBase[MarketingCampaign](MarketingCampaign)
crud_contact = CRUDBase[MarketingContact](MarketingContact)
crud_activity = CRUDBase[MarketingActivity](MarketingActivity)


async def _get_or_404(crud, db: DB, id: uuid.UUID, label: str):
    obj = await crud.get(db, id)
    if not obj:
        raise HTTPException(status_code=404, detail=f"{label} not found")
    return obj


@router.get("/dashboard")
async def marketing_dashboard(db: DB, admin: AdminUser):
    now = datetime.now(timezone.utc)

    async def count(model, *filters):
        result = await db.execute(select(func.count()).select_from(model).where(*filters))
        return result.scalar() or 0

    campaigns = await db.execute(
        select(MarketingCampaign).order_by(MarketingCampaign.created_at.desc()).limit(20)
    )
    campaign_rows = []
    for campaign in campaigns.scalars().all():
        lead_count = await count(Lead, Lead.campaign_id == campaign.id)
        inquiry_count = await count(Inquiry, Inquiry.campaign_id == campaign.id)
        campaign_rows.append({
            "id": campaign.id,
            "name": campaign.name,
            "channel": campaign.channel,
            "status": campaign.status,
            "utm_campaign": campaign.utm_campaign,
            "conversions": lead_count + inquiry_count,
            "leads": lead_count,
            "inquiries": inquiry_count,
        })

    return {
        "counts": {
            "active_campaigns": await count(MarketingCampaign, MarketingCampaign.status == "active"),
            "contacts": await count(MarketingContact),
            "pending_approval": await count(
                MarketingActivity, MarketingActivity.status == "pending_approval"
            ),
            "due_follow_ups": await count(
                MarketingActivity,
                MarketingActivity.status.in_(("pending_approval", "scheduled")),
                MarketingActivity.scheduled_at <= now,
            ),
            "attributed_leads": await count(Lead, Lead.campaign_id.is_not(None)),
            "attributed_inquiries": await count(Inquiry, Inquiry.campaign_id.is_not(None)),
        },
        "campaigns": campaign_rows,
    }


@router.get("/campaigns")
async def list_campaigns(
    db: DB,
    admin: AdminUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status_filter: str | None = Query(None, alias="status"),
):
    filters = [MarketingCampaign.status == status_filter] if status_filter else None
    items, total = await crud_campaign.get_multi(db, skip=skip, limit=limit, filters=filters)
    return {"items": [MarketingCampaignRead.model_validate(i) for i in items], "total": total}


@router.post("/campaigns", response_model=MarketingCampaignRead, status_code=status.HTTP_201_CREATED)
async def create_campaign(data: MarketingCampaignCreate, db: DB, admin: AdminUser):
    obj = data.model_dump()
    obj["created_by"] = admin.id
    return await crud_campaign.create(db, obj_in=obj)


@router.get("/campaigns/{id}", response_model=MarketingCampaignRead)
async def get_campaign(id: uuid.UUID, db: DB, admin: AdminUser):
    return await _get_or_404(crud_campaign, db, id, "Campaign")


@router.post("/campaigns/{id}/prepare")
async def prepare_campaign(id: uuid.UUID, db: DB, admin: AdminUser):
    campaign = await _get_or_404(crud_campaign, db, id, "Campaign")
    return await prepare_campaign_drafts(db, campaign)


@router.put("/campaigns/{id}", response_model=MarketingCampaignRead)
async def update_campaign(id: uuid.UUID, data: MarketingCampaignUpdate, db: DB, admin: AdminUser):
    obj = await _get_or_404(crud_campaign, db, id, "Campaign")
    return await crud_campaign.update(db, db_obj=obj, obj_in=data.model_dump(exclude_unset=True))


@router.delete("/campaigns/{id}")
async def delete_campaign(id: uuid.UUID, db: DB, admin: AdminUser):
    if not await crud_campaign.delete(db, id=id):
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"ok": True}


@router.get("/contacts")
async def list_contacts(
    db: DB,
    admin: AdminUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status_filter: str | None = Query(None, alias="status"),
    segment: str | None = None,
    consent_status: str | None = None,
):
    filters = []
    if status_filter:
        filters.append(MarketingContact.status == status_filter)
    if segment:
        filters.append(MarketingContact.segment == segment)
    if consent_status:
        filters.append(MarketingContact.consent_status == consent_status)
    items, total = await crud_contact.get_multi(
        db, skip=skip, limit=limit, filters=filters or None
    )
    return {"items": [MarketingContactRead.model_validate(i) for i in items], "total": total}


@router.post("/contacts", response_model=MarketingContactRead, status_code=status.HTTP_201_CREATED)
async def create_contact(data: MarketingContactCreate, db: DB, admin: AdminUser):
    return await crud_contact.create(db, obj_in=data.model_dump())


@router.get("/contacts/{id}", response_model=MarketingContactRead)
async def get_contact(id: uuid.UUID, db: DB, admin: AdminUser):
    return await _get_or_404(crud_contact, db, id, "Contact")


@router.put("/contacts/{id}", response_model=MarketingContactRead)
async def update_contact(id: uuid.UUID, data: MarketingContactUpdate, db: DB, admin: AdminUser):
    obj = await _get_or_404(crud_contact, db, id, "Contact")
    return await crud_contact.update(db, db_obj=obj, obj_in=data.model_dump(exclude_unset=True))


@router.delete("/contacts/{id}")
async def delete_contact(id: uuid.UUID, db: DB, admin: AdminUser):
    if not await crud_contact.delete(db, id=id):
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"ok": True}


@router.get("/activities")
async def list_activities(
    db: DB,
    admin: AdminUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status_filter: str | None = Query(None, alias="status"),
    channel: str | None = None,
):
    filters = []
    if status_filter:
        filters.append(MarketingActivity.status == status_filter)
    if channel:
        filters.append(MarketingActivity.channel == channel)
    items, total = await crud_activity.get_multi(
        db,
        skip=skip,
        limit=limit,
        filters=filters or None,
        order_by=MarketingActivity.scheduled_at.asc().nullslast(),
    )
    return {"items": [MarketingActivityRead.model_validate(i) for i in items], "total": total}


@router.post("/activities", response_model=MarketingActivityRead, status_code=status.HTTP_201_CREATED)
async def create_activity(data: MarketingActivityCreate, db: DB, admin: AdminUser):
    obj = data.model_dump()
    obj["created_by"] = admin.id
    return await crud_activity.create(db, obj_in=obj)


@router.get("/activities/{id}", response_model=MarketingActivityRead)
async def get_activity(id: uuid.UUID, db: DB, admin: AdminUser):
    return await _get_or_404(crud_activity, db, id, "Activity")


@router.put("/activities/{id}", response_model=MarketingActivityRead)
async def update_activity(id: uuid.UUID, data: MarketingActivityUpdate, db: DB, admin: AdminUser):
    obj = await _get_or_404(crud_activity, db, id, "Activity")
    changes = data.model_dump(exclude_unset=True)
    if changes.get("status") in {"sent", "completed"} and "completed_at" not in changes:
        changes["completed_at"] = datetime.now(timezone.utc)
        if obj.contact_id:
            contact = await crud_contact.get(db, obj.contact_id)
            if contact:
                contact.last_contacted_at = changes["completed_at"]
                db.add(contact)
    return await crud_activity.update(db, db_obj=obj, obj_in=changes)


@router.delete("/activities/{id}")
async def delete_activity(id: uuid.UUID, db: DB, admin: AdminUser):
    if not await crud_activity.delete(db, id=id):
        raise HTTPException(status_code=404, detail="Activity not found")
    return {"ok": True}


def _brief_error(exc: MarketingBriefError) -> HTTPException:
    return HTTPException(status_code=409, detail=str(exc))


async def _brief_read(db: DB, brief: MarketingCreativeBrief) -> CreativeBriefRead:
    current = None
    if brief.current_version_id:
        current = await get_version(db, brief.current_version_id)
    return CreativeBriefRead(
        id=brief.id,
        campaign_id=brief.campaign_id,
        region_id=brief.region_id,
        title=brief.title,
        objective=brief.objective,
        status=brief.status,
        current_version_id=brief.current_version_id,
        created_by=brief.created_by,
        approved_by=brief.approved_by,
        approved_at=brief.approved_at,
        created_at=brief.created_at,
        updated_at=brief.updated_at,
        current_version=CreativeBriefVersionRead.model_validate(current) if current else None,
    )


@admin_brief_router.post("/creative-briefs", response_model=CreativeBriefRead, status_code=status.HTTP_201_CREATED)
async def create_creative_brief(data: CreativeBriefCreate, db: DB, admin: AdminUser):
    try:
        brief, _version = await create_brief(
            db,
            actor=admin,
            title=data.title,
            objective=data.objective,
            campaign_id=data.campaign_id,
            region_id=data.region_id,
            version_data=data.version.model_dump(),
        )
        await db.commit()
        await db.refresh(brief)
        return await _brief_read(db, brief)
    except MarketingBriefError as exc:
        await db.rollback()
        raise _brief_error(exc) from exc


@admin_brief_router.get("/creative-briefs")
async def list_creative_briefs(
    db: DB,
    admin: AdminUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status_filter: str | None = Query(None, alias="status"),
):
    filters = []
    if status_filter:
        filters.append(MarketingCreativeBrief.status == status_filter)
    query = select(MarketingCreativeBrief)
    count_query = select(func.count()).select_from(MarketingCreativeBrief)
    for f in filters:
        query = query.where(f)
        count_query = count_query.where(f)
    total = (await db.execute(count_query)).scalar() or 0
    rows = (
        await db.execute(query.order_by(MarketingCreativeBrief.created_at.desc()).offset(skip).limit(limit))
    ).scalars().all()
    items = [await _brief_read(db, row) for row in rows]
    return {"items": items, "total": total}


@admin_brief_router.get("/creative-briefs/{brief_id}", response_model=CreativeBriefRead)
async def get_creative_brief(brief_id: uuid.UUID, db: DB, admin: AdminUser):
    brief = await get_brief(db, brief_id)
    if not brief:
        raise HTTPException(status_code=404, detail="Creative brief not found")
    return await _brief_read(db, brief)


@admin_brief_router.get("/creative-briefs/{brief_id}/export", response_model=CreativeBriefExternalExport)
async def export_creative_brief(brief_id: uuid.UUID, db: DB, admin: AdminUser):
    brief = await get_brief(db, brief_id)
    if not brief or not brief.current_version_id:
        raise HTTPException(status_code=404, detail="Creative brief not found")
    version = await get_version(db, brief.current_version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Creative brief version not found")
    payload = build_export_payload(brief, version)
    return CreativeBriefExternalExport(
        brief_id=brief.id,
        title=brief.title,
        objective=brief.objective,
        version=version.version,
        copy_block=payload["copy"],
        audience=payload["audience"],
        brand_constraints=payload["brand_constraints"],
        channel_specs=payload["channel_specs"],
        deliverables=payload["deliverables"],
        compliance=payload["compliance"],
        content_hash=version.content_hash,
    )


@admin_brief_router.post("/creative-briefs/{brief_id}/versions", response_model=CreativeBriefVersionRead, status_code=status.HTTP_201_CREATED)
async def create_creative_brief_version(
    brief_id: uuid.UUID, data: CreativeBriefVersionCreate, db: DB, admin: AdminUser
):
    try:
        version = await create_brief_version(
            db,
            actor=admin,
            brief_id=brief_id,
            version_data=data.model_dump(),
        )
        await db.commit()
        await db.refresh(version)
        return CreativeBriefVersionRead.model_validate(version)
    except MarketingBriefError as exc:
        await db.rollback()
        raise _brief_error(exc) from exc


@admin_brief_router.put("/creative-brief-versions/{version_id}", response_model=CreativeBriefVersionRead)
async def update_creative_brief_version(
    version_id: uuid.UUID, data: CreativeBriefVersionUpdate, db: DB, admin: AdminUser
):
    try:
        version = await update_draft_version(
            db,
            actor=admin,
            version_id=version_id,
            version_data=data.model_dump(exclude_unset=True),
        )
        await db.commit()
        await db.refresh(version)
        return CreativeBriefVersionRead.model_validate(version)
    except MarketingBriefError as exc:
        await db.rollback()
        raise _brief_error(exc) from exc


@admin_brief_router.post("/creative-brief-versions/{version_id}/submit-review", response_model=CreativeBriefVersionRead)
async def submit_creative_brief_review(version_id: uuid.UUID, db: DB, admin: AdminUser):
    try:
        version = await submit_version_review(db, actor=admin, version_id=version_id)
        await db.commit()
        await db.refresh(version)
        return CreativeBriefVersionRead.model_validate(version)
    except MarketingBriefError as exc:
        await db.rollback()
        raise _brief_error(exc) from exc


@admin_brief_router.post("/creative-brief-versions/{version_id}/approve", response_model=CreativeBriefVersionRead)
async def approve_creative_brief(version_id: uuid.UUID, data: BriefReviewAction, db: DB, admin: AdminUser):
    try:
        version = await approve_version(db, actor=admin, version_id=version_id, notes=data.notes)
        await db.commit()
        await db.refresh(version)
        return CreativeBriefVersionRead.model_validate(version)
    except MarketingBriefError as exc:
        await db.rollback()
        raise _brief_error(exc) from exc


@admin_brief_router.post("/creative-brief-versions/{version_id}/reject", response_model=CreativeBriefVersionRead)
async def reject_creative_brief(version_id: uuid.UUID, data: BriefRejectAction, db: DB, admin: AdminUser):
    try:
        version = await reject_version(db, actor=admin, version_id=version_id, reason=data.reason)
        await db.commit()
        await db.refresh(version)
        return CreativeBriefVersionRead.model_validate(version)
    except MarketingBriefError as exc:
        await db.rollback()
        raise _brief_error(exc) from exc


@admin_brief_router.post("/creative-brief-versions/{version_id}/copy-draft", response_model=CreativeBriefVersionRead, status_code=status.HTTP_201_CREATED)
async def copy_rejected_creative_brief(version_id: uuid.UUID, db: DB, admin: AdminUser):
    try:
        version = await copy_rejected_to_draft(db, actor=admin, version_id=version_id)
        await db.commit()
        await db.refresh(version)
        return CreativeBriefVersionRead.model_validate(version)
    except MarketingBriefError as exc:
        await db.rollback()
        raise _brief_error(exc) from exc


@admin_brief_router.get(
    "/creative-brief-versions/{version_id}/media-requests",
    response_model=list[MediaRequestRead],
)
async def list_media_requests(version_id: uuid.UUID, db: DB, admin: AdminUser):
    try:
        requests = await list_media_requests_for_version(db, version_id)
        return [MediaRequestRead.model_validate(r) for r in requests]
    except MarketingBriefError as exc:
        raise _brief_error(exc) from exc


@admin_brief_router.post(
    "/creative-brief-versions/{version_id}/create-media-requests",
    response_model=list[MediaRequestRead],
    status_code=status.HTTP_201_CREATED,
)
async def create_media_requests(version_id: uuid.UUID, db: DB, admin: AdminUser):
    try:
        requests = await create_media_requests_for_version(db, actor=admin, version_id=version_id)
        await db.commit()
        for req in requests:
            await db.refresh(req)
        return [MediaRequestRead.model_validate(r) for r in requests]
    except MarketingBriefError as exc:
        await db.rollback()
        raise _brief_error(exc) from exc
