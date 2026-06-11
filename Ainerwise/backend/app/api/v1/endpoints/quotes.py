import uuid

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel

from datetime import date, timedelta

from app.api.deps import AdminUser, CurrentUser, DB
from app.crud.quote import crud_quote
from app.schemas.quote import QuoteCreate, QuoteRead, QuoteStatusUpdate, QuoteUpdate
from app.services import finance as finance_svc
from app.services.audit import log_action

router = APIRouter(prefix="/quotes", tags=["quotes"])


@router.get("")
async def list_quotes(
    db: DB,
    admin: AdminUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
):
    filters = []
    if status_filter:
        from app.models.quote import Quote

        filters.append(Quote.status == status_filter)
    items, total = await crud_quote.get_multi(db, skip=skip, limit=limit, filters=filters or None)
    return {"items": [QuoteRead.model_validate(i) for i in items], "total": total}


@router.get("/my")
async def list_my_quotes(
    db: DB,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    from app.models.lead import Lead
    from app.models.quote import Quote
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    # Get quotes linked to leads belonging to this user's company
    filters = []
    if current_user.company_id:
        filters.append(Quote.lead_id.in_(
            select(Lead.id).where(Lead.buyer_company_id == current_user.company_id)
        ))
    else:
        # User without company — return empty
        return {"items": [], "total": 0}
    items, total = await crud_quote.get_multi(db, skip=skip, limit=limit, filters=filters)
    return {"items": [QuoteRead.model_validate(i) for i in items], "total": total}


@router.get("/{id}", response_model=QuoteRead)
async def get_quote(id: uuid.UUID, db: DB, current_user: CurrentUser):
    quote = await crud_quote.get(db, id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote


@router.post("", response_model=QuoteRead, status_code=201)
async def create_quote(data: QuoteCreate, db: DB, admin: AdminUser):
    return await crud_quote.create(db, obj_in=data.model_dump())


@router.put("/{id}", response_model=QuoteRead)
async def update_quote(id: uuid.UUID, data: QuoteUpdate, db: DB, admin: AdminUser):
    quote = await crud_quote.get(db, id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return await crud_quote.update(db, db_obj=quote, obj_in=data.model_dump(exclude_unset=True))


@router.patch("/{id}/status", response_model=QuoteRead)
async def update_quote_status(id: uuid.UUID, data: QuoteStatusUpdate, db: DB, current_user: CurrentUser):
    quote = await crud_quote.get(db, id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return await crud_quote.update(db, db_obj=quote, obj_in={"status": data.status})


class CustomerViewRequest(BaseModel):
    amounts: dict[str, float] | None = None
    annual_recurring_total: float | None = None


@router.post("/{id}/build-customer-view", response_model=QuoteRead)
async def build_customer_view(id: uuid.UUID, data: CustomerViewRequest, db: DB, admin: AdminUser):
    """FI.4.4 — split the quote into customer-facing packaged line items.

    Uses explicit `amounts` if provided, otherwise derives packages from the
    quote's component fees. Never includes supplier cost or internal model.
    """
    quote = await crud_quote.get(db, id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    amounts = data.amounts or {
        "hardware_package": quote.device_total or 0,
        "integration": quote.service_total or 0,
        "platform": quote.platform_fee or 0,
        "spare_reserve": quote.spare_parts_fee or 0,
        "first_year_support": quote.support_package_fee or 0,
    }
    items = finance_svc.build_customer_line_items(amounts, quote.currency or "EUR")
    first_year_total = round(sum(i["amount"] for i in items if not i["optional"]), 2)
    annual = data.annual_recurring_total if data.annual_recurring_total is not None else (quote.annual_recurring_total or 0)

    quote = await crud_quote.update(db, db_obj=quote, obj_in={
        "customer_line_items_json": items,
        "first_year_total": first_year_total,
        "annual_recurring_total": annual,
    })
    return quote


@router.get("/{id}/internal-economics")
async def quote_internal_economics(id: uuid.UUID, db: DB, admin: AdminUser):
    """FI.4.5 — admin-only internal economics (supplier, cost, margin, risk)."""
    quote = await crud_quote.get(db, id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return {
        "quote_id": str(quote.id),
        "internal_economics": quote.internal_economics_json or finance_svc.internal_economics_scaffold(),
    }


@router.get("/{id}/pdf")
async def download_quote_pdf(id: uuid.UUID, db: DB, current_user: CurrentUser):
    """Generate and download a PDF for this quote."""
    from app.services.quote_pdf import generate_quote_pdf

    quote = await crud_quote.get(db, id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    quote_dict = QuoteRead.model_validate(quote).model_dump(mode="json")

    lead_dict = None
    if quote.lead_id:
        from app.crud.lead import crud_lead
        lead = await crud_lead.get(db, quote.lead_id)
        if lead:
            from app.schemas.lead import LeadRead
            lead_dict = LeadRead.model_validate(lead).model_dump(mode="json")

    pdf_bytes = generate_quote_pdf(quote_dict, lead_dict)
    quote_ref = str(quote.id)[:8].upper()
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="quote-{quote_ref}.pdf"'},
    )


@router.post("/draft-from-lead/{lead_id}", response_model=QuoteRead, status_code=201)
async def draft_quote_from_lead(lead_id: uuid.UUID, db: DB, admin: AdminUser):
    """Generate a draft quote pre-populated from a lead's data and AI analysis."""
    from app.crud.lead import crud_lead
    from app.crud.site_survey import crud_site_survey
    from app.models.lead import SiteSurvey

    lead = await crud_lead.get(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Collect site survey data if available
    surveys, _ = await crud_site_survey.get_multi(
        db, filters=[SiteSurvey.lead_id == lead_id], limit=1
    )
    survey = surveys[0] if surveys else None
    survey_data = survey.survey_json if survey else {}

    # Build quote items from AI analysis + lead systems
    ai = lead.ai_analysis_json or {}
    systems = lead.systems_needed_json or []
    items = []
    for system in systems:
        items.append({
            "description": f"{system} system",
            "category": "device",
            "quantity": 1,
            "unit_price": 0,
            "subtotal": 0,
            "notes": "Price TBD after detailed specification",
        })

    # Add service line items from matched solutions
    matched = ai.get("matched_solutions", [])
    for sol in matched[:2]:
        items.append({
            "description": f"Solution: {sol.get('title', 'Custom')}",
            "category": "service",
            "quantity": 1,
            "unit_price": 0,
            "subtotal": 0,
            "notes": "Engineering and integration service",
        })

    # Build notes from AI summary
    classification = ai.get("classification", {}).get("project_class", "")
    completeness = ai.get("completeness", {}).get("score", 0)
    notes_parts = [
        f"Draft quote for: {lead.project_type or classification or 'Smart Building Project'}",
        f"Location: {lead.country or ''} {lead.city or ''}".strip(),
        f"Budget range: {lead.budget_range or 'Not specified'}",
        f"AI completeness score: {completeness}%",
    ]
    if survey_data:
        area = survey_data.get("area", "")
        rooms = survey_data.get("rooms", "")
        floors = survey_data.get("floors", "")
        if area:
            notes_parts.append(f"Site area: {area} sqm")
        if rooms:
            notes_parts.append(f"Rooms/zones: {rooms}")
        if floors:
            notes_parts.append(f"Floors: {floors}")

    quote_obj = {
        "lead_id": lead.id,
        "quote_items_json": items,
        "device_total": 0,
        "service_total": 0,
        "platform_fee": 0,
        "support_package_fee": 0,
        "spare_parts_fee": 0,
        "logistics_fee": 0,
        "tax_fee": 0,
        "discount": 0,
        "total": 0,
        "currency": "EUR",
        "status": "draft",
        "valid_until": date.today() + timedelta(days=30),
        "notes": "\n".join(notes_parts),
    }
    quote = await crud_quote.create(db, obj_in=quote_obj)

    # Update lead status to quotation_drafting
    await crud_lead.update(db, db_obj=lead, obj_in={"status": "quotation_drafting"})
    await log_action(
        db, actor_user_id=admin.id, action="draft_quote",
        entity_type="quote", entity_id=quote.id,
        after={"lead_id": str(lead.id), "items_count": len(items)},
    )
    return quote
