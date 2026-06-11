import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import AdminUser, CurrentUser, DB
from app.crud.lead import crud_lead
from app.crud.site_survey import crud_site_survey
from app.schemas.lead import LeadAssign, LeadCreate, LeadNotesUpdate, LeadRead, LeadStatusUpdate
from app.schemas.site_survey import SiteSurveyCreate, SiteSurveyRead, SiteSurveyUpdate
from app.services.ai_analysis import analyze_lead
from app.services.audit import log_action
from app.services.integration_events import create_integration_event
from app.services.marketing_automation import ensure_lead_follow_up, resolve_campaign_id

router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("", response_model=LeadRead, status_code=status.HTTP_201_CREATED)
async def create_lead(data: LeadCreate, db: DB):
    obj = data.model_dump()
    obj["status"] = "new"
    obj["source_channel"] = obj.get("source_channel") or (
        "campaign" if obj.get("utm_source") else "website"
    )
    if not obj.get("campaign_id"):
        obj["campaign_id"] = await resolve_campaign_id(db, obj.get("utm_campaign"))
    lead = await crud_lead.create(db, obj_in=obj)
    await create_integration_event(
        db,
        event_type="lead.created",
        payload={
            "lead_id": str(lead.id),
            "contact_name": lead.contact_name,
            "contact_email": lead.contact_email,
            "project_type": lead.project_type,
            "country": lead.country,
            "city": lead.city,
            "budget_range": lead.budget_range,
            "systems_needed": lead.systems_needed_json,
        },
    )
    final_lead = lead
    try:
        await analyze_lead(db, lead_id=lead.id)
        refreshed = await crud_lead.get(db, lead.id)
        final_lead = refreshed or lead
    except Exception:
        pass
    try:
        await ensure_lead_follow_up(db, final_lead)
    except Exception:
        pass
    return final_lead


@router.get("/my")
async def list_my_leads(
    db: DB,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    from app.models.lead import Lead

    filters = []
    if current_user.company_id:
        filters.append(Lead.buyer_company_id == current_user.company_id)
    else:
        filters.append(Lead.contact_email == current_user.email)
    items, total = await crud_lead.get_multi(db, skip=skip, limit=limit, filters=filters)
    return {"items": [LeadRead.model_validate(i) for i in items], "total": total}


@router.get("")
async def list_leads(
    db: DB,
    admin: AdminUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    solution_line: str | None = None,
    min_recurring_score: int | None = Query(None, ge=0, le=100),
    compliance_risk: str | None = None,
    amc_potential: str | None = None,
    consumable_potential: str | None = None,
    multi_site: bool | None = None,
    sort: str = Query("created_at", pattern="^(created_at|recurring_revenue_score|estimated_arr|estimated_ltv|lead_score)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
):
    """FI.6.3 — admin CRM list with recurring-revenue filters and sort order."""
    from app.models.lead import Lead

    filters = []
    if status_filter:
        filters.append(Lead.status == status_filter)
    if solution_line:
        filters.append(Lead.solution_line == solution_line)
    if min_recurring_score is not None:
        filters.append(Lead.recurring_revenue_score >= min_recurring_score)
    if compliance_risk:
        filters.append(Lead.compliance_risk_level == compliance_risk)
    if amc_potential:
        filters.append(Lead.amc_potential == amc_potential)
    if consumable_potential:
        filters.append(Lead.consumable_potential == consumable_potential)
    if multi_site is not None:
        filters.append(Lead.is_multi_site == multi_site)

    sort_col = getattr(Lead, sort)
    order_by = sort_col.asc() if order == "asc" else sort_col.desc()
    items, total = await crud_lead.get_multi(
        db, skip=skip, limit=limit, filters=filters or None, order_by=order_by
    )
    return {"items": [LeadRead.model_validate(i) for i in items], "total": total}


@router.get("/{id}", response_model=LeadRead)
async def get_lead(id: uuid.UUID, db: DB, admin: AdminUser):
    lead = await crud_lead.get(db, id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.post("/{id}/analyze", response_model=LeadRead)
async def analyze_lead_endpoint(id: uuid.UUID, db: DB, admin: AdminUser, use_graph: bool = Query(False)):
    lead = await crud_lead.get(db, id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    # use_graph=true runs the explicit graph orchestrator (5.14); default = rule-based MVP.
    workflow = "admin_manual_review_graph" if use_graph else "admin_manual_review"
    await analyze_lead(db, lead_id=id, workflow_name=workflow, use_graph=use_graph)
    refreshed = await crud_lead.get(db, id)
    return refreshed or lead


@router.patch("/{id}/status", response_model=LeadRead)
async def update_lead_status(id: uuid.UUID, data: LeadStatusUpdate, db: DB, admin: AdminUser):
    lead = await crud_lead.get(db, id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    old_status = lead.status
    result = await crud_lead.update(db, db_obj=lead, obj_in={"status": data.status})
    await log_action(
        db, actor_user_id=admin.id, action="status_change",
        entity_type="lead", entity_id=id,
        before={"status": old_status}, after={"status": data.status},
    )
    return result


@router.patch("/{id}/assign", response_model=LeadRead)
async def assign_lead(id: uuid.UUID, data: LeadAssign, db: DB, admin: AdminUser):
    lead = await crud_lead.get(db, id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return await crud_lead.update(db, db_obj=lead, obj_in={"assigned_admin_id": data.assigned_admin_id})


@router.patch("/{id}/notes", response_model=LeadRead)
async def update_lead_notes(id: uuid.UUID, data: LeadNotesUpdate, db: DB, admin: AdminUser):
    lead = await crud_lead.get(db, id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return await crud_lead.update(db, db_obj=lead, obj_in={"notes": data.notes})


# ── Site Surveys (nested under /leads/{id}) ───────────────────


@router.get("/{id}/surveys")
async def list_lead_surveys(id: uuid.UUID, db: DB, admin: AdminUser):
    from app.models.lead import SiteSurvey

    lead = await crud_lead.get(db, id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    items, total = await crud_site_survey.get_multi(
        db, filters=[SiteSurvey.lead_id == id], limit=50
    )
    return {"items": [SiteSurveyRead.model_validate(i) for i in items], "total": total}


@router.post("/{id}/surveys", response_model=SiteSurveyRead, status_code=status.HTTP_201_CREATED)
async def create_lead_survey(id: uuid.UUID, data: SiteSurveyCreate, db: DB, admin: AdminUser):
    lead = await crud_lead.get(db, id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    obj = data.model_dump()
    obj["lead_id"] = id
    obj["created_by"] = admin.id
    return await crud_site_survey.create(db, obj_in=obj)


@router.put("/{id}/surveys/{survey_id}", response_model=SiteSurveyRead)
async def update_lead_survey(
    id: uuid.UUID, survey_id: uuid.UUID, data: SiteSurveyUpdate, db: DB, admin: AdminUser
):
    survey = await crud_site_survey.get(db, survey_id)
    if not survey or survey.lead_id != id:
        raise HTTPException(status_code=404, detail="Survey not found for this lead")
    return await crud_site_survey.update(db, db_obj=survey, obj_in=data.model_dump(exclude_unset=True))


@router.delete("/{id}/surveys/{survey_id}")
async def delete_lead_survey(id: uuid.UUID, survey_id: uuid.UUID, db: DB, admin: AdminUser):
    survey = await crud_site_survey.get(db, survey_id)
    if not survey or survey.lead_id != id:
        raise HTTPException(status_code=404, detail="Survey not found for this lead")
    await crud_site_survey.delete(db, id=survey_id)
    return {"ok": True}
