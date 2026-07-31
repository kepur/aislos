"""Phase 2: Cebu trade domain services."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commerce import (
    DELIVERY_TRANSITIONS,
    CommerceOrder,
    OrderDelivery,
    OrderDispute,
    ProcurementRequest,
    SupplierListing,
    SupplierOffer,
    TradeCategorySchema,
)
from app.models.user import User
from app.models.lead import Lead
from app.modules.commerce.access import customer_commerce_workspace_ids, user_is_order_party
from app.services.event_bus import emit_event


class CommerceTradeError(ValueError):
    pass


async def get_or_create_category(
    db: AsyncSession, *, slug: str, name: str, schema_json: dict
) -> TradeCategorySchema:
    row = (
        await db.execute(select(TradeCategorySchema).where(TradeCategorySchema.slug == slug))
    ).scalar_one_or_none()
    if row:
        return row
    row = TradeCategorySchema(slug=slug, name=name, schema_json=schema_json)
    db.add(row)
    await db.flush()
    return row


async def create_listing(db: AsyncSession, **fields) -> SupplierListing:
    row = SupplierListing(**fields)
    db.add(row)
    await db.flush()
    return row


async def create_procurement_request(db: AsyncSession, **fields) -> ProcurementRequest:
    row = ProcurementRequest(**fields)
    db.add(row)
    await db.flush()
    return row


async def publish_request(db: AsyncSession, request_id: uuid.UUID) -> ProcurementRequest:
    row = await db.get(ProcurementRequest, request_id)
    if row is None:
        raise CommerceTradeError("request not found")
    if row.status not in ("draft", "matching"):
        raise CommerceTradeError(f"cannot publish from status {row.status!r}")
    row.status = "published"
    row.published_at = datetime.now(timezone.utc)
    await db.flush()
    await emit_event(
        db,
        "procurement.request.published",
        {"request_id": str(row.id), "portal_key": row.portal_key},
        aggregate_type="procurement_request",
        aggregate_id=row.id,
    )
    return row


async def match_supplier_candidates(
    db: AsyncSession, request_id: uuid.UUID, *, limit: int = 20
) -> list[SupplierListing]:
    req = await db.get(ProcurementRequest, request_id)
    if req is None:
        raise CommerceTradeError("request not found")
    q = select(SupplierListing).where(SupplierListing.status == "active")
    if req.category_schema_id:
        q = q.where(SupplierListing.category_schema_id == req.category_schema_id)
    if req.region_id:
        q = q.where(
            or_(SupplierListing.region_id == req.region_id, SupplierListing.region_id.is_(None))
        )
    q = q.order_by(SupplierListing.created_at.desc()).limit(limit)
    return list((await db.execute(q)).scalars().all())


async def bind_listing_to_request(
    db: AsyncSession, request_id: uuid.UUID, listing_id: uuid.UUID
) -> ProcurementRequest:
    req = await db.get(ProcurementRequest, request_id)
    listing = await db.get(SupplierListing, listing_id)
    if req is None or listing is None:
        raise CommerceTradeError("request or listing not found")
    attrs = dict(req.attrs_json or {})
    bindings = list(attrs.get("bound_listing_ids") or [])
    lid = str(listing_id)
    if lid not in bindings:
        bindings.append(lid)
    attrs["bound_listing_ids"] = bindings
    req.attrs_json = attrs
    req.status = "matching"
    await db.flush()
    return req


async def submit_offer(db: AsyncSession, **fields) -> SupplierOffer:
    req = await db.get(ProcurementRequest, fields["procurement_request_id"])
    if req is None:
        raise CommerceTradeError("request not found")
    if req.workspace_id is None:
        raise CommerceTradeError("procurement request requires a Workspace")
    existing = (
        await db.execute(
            select(SupplierOffer).where(
                SupplierOffer.procurement_request_id == fields["procurement_request_id"],
                SupplierOffer.supplier_company_id == fields["supplier_company_id"],
            )
        )
    ).scalar_one_or_none()
    if existing:
        raise CommerceTradeError("offer already exists for this supplier")
    row = SupplierOffer(workspace_id=req.workspace_id, **fields, status="submitted")
    db.add(row)
    await db.flush()
    if req.status == "published":
        req.status = "offer_received"
    await emit_event(
        db,
        "procurement.offer.submitted",
        {"offer_id": str(row.id), "request_id": str(fields["procurement_request_id"])},
        aggregate_type="supplier_offer",
        aggregate_id=row.id,
    )
    if req and req.buyer_company_id:
        from app.services.commerce_messaging import get_or_create_thread_for_request, notify_from_template

        await get_or_create_thread_for_request(db, req, supplier_company_id=row.supplier_company_id)
        await notify_from_template(
            db,
            event_type="procurement.offer.submitted",
            company_ids=[req.buyer_company_id],
            portal_key=req.portal_key,
            link_path=f"/commerce/procurement-requests/{req.id}",
            aggregate_type="procurement_request",
            aggregate_id=req.id,
        )
    return row


async def award_offer(db: AsyncSession, offer_id: uuid.UUID) -> CommerceOrder:
    offer = await db.get(SupplierOffer, offer_id)
    if offer is None:
        raise CommerceTradeError("offer not found")
    if offer.status not in ("submitted",):
        raise CommerceTradeError("offer not awardable")
    req = await db.get(ProcurementRequest, offer.procurement_request_id)
    if req is None:
        raise CommerceTradeError("request not found")
    if offer.workspace_id != req.workspace_id:
        raise CommerceTradeError("offer and request belong to different Workspaces")
    offer.status = "awarded"
    req.status = "awarded"
    order = CommerceOrder(
        workspace_id=req.workspace_id,
        procurement_request_id=req.id,
        winning_offer_id=offer.id,
        buyer_company_id=req.buyer_company_id,
        supplier_company_id=offer.supplier_company_id,
        status="confirmed",
        total_minor=offer.price_minor,
        currency=offer.currency,
    )
    db.add(order)
    await db.flush()
    await emit_event(
        db,
        "procurement.offer.awarded",
        {"order_id": str(order.id), "offer_id": str(offer.id)},
        aggregate_type="commerce_order",
        aggregate_id=order.id,
    )
    from app.services.commerce_messaging import get_or_create_thread_for_order, notify_from_template

    await get_or_create_thread_for_order(db, order)
    await notify_from_template(
        db,
        event_type="procurement.offer.awarded",
        company_ids=[offer.supplier_company_id] if offer.supplier_company_id else [],
        portal_key=req.portal_key,
        link_path=f"/commerce/orders/{order.id}",
        aggregate_type="commerce_order",
        aggregate_id=order.id,
    )
    if req.buyer_company_id:
        await notify_from_template(
            db,
            event_type="commerce.order.awarded",
            company_ids=[req.buyer_company_id],
            portal_key=req.portal_key,
            link_path=f"/commerce/orders/{order.id}",
            aggregate_type="commerce_order",
            aggregate_id=order.id,
        )
    return order


async def get_order(db: AsyncSession, order_id: uuid.UUID) -> CommerceOrder | None:
    return await db.get(CommerceOrder, order_id)


async def list_orders_for_user(
    db: AsyncSession, user: User, *, status: str | None = None, limit: int = 50
) -> list[CommerceOrder]:
    q = select(CommerceOrder).order_by(CommerceOrder.created_at.desc()).limit(limit)
    if user.role not in ("admin", "super_admin"):
        if not user.company_id:
            return []
        workspace_ids = await customer_commerce_workspace_ids(db, user)
        buyer_workspace_scope = (
            CommerceOrder.workspace_id.in_(workspace_ids)
            if workspace_ids
            else CommerceOrder.workspace_id.is_(None)
        )
        q = q.where(
            (
                (CommerceOrder.buyer_company_id == user.company_id)
                & (
                    buyer_workspace_scope
                    | CommerceOrder.workspace_id.is_(None)
                )
            )
            | (CommerceOrder.supplier_company_id == user.company_id)
        )
    if status:
        q = q.where(CommerceOrder.status == status)
    return list((await db.execute(q)).scalars())


async def _order_party(db: AsyncSession, user: User, order: CommerceOrder) -> str | None:
    return await user_is_order_party(db, user, order)


async def _has_open_dispute(db: AsyncSession, order_id: uuid.UUID) -> bool:
    row = (
        await db.execute(
            select(OrderDispute.id).where(
                OrderDispute.commerce_order_id == order_id,
                OrderDispute.status.in_(("open", "under_review")),
            )
        )
    ).first()
    return row is not None


async def list_deliveries(db: AsyncSession, order: CommerceOrder) -> list[OrderDelivery]:
    result = await db.execute(
        select(OrderDelivery)
        .where(
            OrderDelivery.commerce_order_id == order.id,
            OrderDelivery.workspace_id == order.workspace_id,
        )
        .order_by(OrderDelivery.created_at.asc())
    )
    return list(result.scalars().all())


async def create_delivery(db: AsyncSession, order_id: uuid.UUID, **fields) -> OrderDelivery:
    order = await db.get(CommerceOrder, order_id)
    if order is None:
        raise CommerceTradeError("order not found")
    if order.workspace_id is None:
        raise CommerceTradeError("commerce order requires a Workspace")
    if order.status not in ("confirmed", "in_delivery"):
        raise CommerceTradeError("order not ready for delivery")
    row = OrderDelivery(workspace_id=order.workspace_id, commerce_order_id=order_id, **fields)
    db.add(row)
    if order.status == "confirmed":
        order.status = "in_delivery"
    await db.flush()
    await emit_event(
        db,
        "commerce.delivery.scheduled",
        {"order_id": str(order_id), "delivery_id": str(row.id)},
        aggregate_type="order_delivery",
        aggregate_id=row.id,
    )
    return row


async def advance_delivery(
    db: AsyncSession,
    delivery_id: uuid.UUID,
    *,
    new_status: str,
    proof_json: dict | None = None,
) -> OrderDelivery:
    row = await db.get(OrderDelivery, delivery_id)
    if row is None:
        raise CommerceTradeError("delivery not found")
    order = await db.get(CommerceOrder, row.commerce_order_id)
    if order is None or row.workspace_id != order.workspace_id:
        raise CommerceTradeError("delivery and order belong to different Workspaces")
    allowed = DELIVERY_TRANSITIONS.get(row.status, set())
    if new_status not in allowed:
        raise CommerceTradeError(f"cannot transition {row.status!r} -> {new_status!r}")
    now = datetime.now(timezone.utc)
    row.status = new_status
    if proof_json:
        row.proof_json = proof_json
    if new_status == "shipped":
        row.shipped_at = now
    elif new_status == "delivered":
        row.delivered_at = now
    elif new_status == "accepted":
        row.accepted_at = now
    await db.flush()
    await emit_event(
        db,
        f"commerce.delivery.{new_status}",
        {"order_id": str(row.commerce_order_id), "delivery_id": str(row.id)},
        aggregate_type="order_delivery",
        aggregate_id=row.id,
    )
    if new_status in ("shipped", "delivered"):
        if order and order.buyer_company_id:
            from app.services.commerce_messaging import notify_from_template

            req = await db.get(ProcurementRequest, order.procurement_request_id)
            portal_key = req.portal_key if req else "cebu"
            await notify_from_template(
                db,
                event_type=f"commerce.delivery.{new_status}",
                company_ids=[order.buyer_company_id],
                portal_key=portal_key,
                link_path=f"/commerce/orders/{order.id}",
                aggregate_type="commerce_order",
                aggregate_id=order.id,
            )
    return row


async def open_dispute(
    db: AsyncSession,
    *,
    order_id: uuid.UUID,
    user: User,
    reason_code: str,
    description: str | None,
    legacy_dispute_id: str | None = None,
) -> OrderDispute:
    order = await db.get(CommerceOrder, order_id)
    if order is None:
        raise CommerceTradeError("order not found")
    if order.workspace_id is None:
        raise CommerceTradeError("commerce order requires a Workspace")
    party = await _order_party(db, user, order)
    if party not in ("buyer", "supplier", "admin"):
        raise CommerceTradeError("not a party to this order")
    if order.status in ("pending", "cancelled", "completed"):
        raise CommerceTradeError("order cannot be disputed in current status")
    if legacy_dispute_id:
        existing = (
            await db.execute(
                select(OrderDispute).where(OrderDispute.legacy_dispute_id == legacy_dispute_id)
            )
        ).scalar_one_or_none()
        if existing:
            return existing
    if await _has_open_dispute(db, order_id):
        raise CommerceTradeError("open dispute already exists")
    row = OrderDispute(
        workspace_id=order.workspace_id,
        commerce_order_id=order_id,
        opened_by_user_id=user.id,
        opened_by_role=party,
        reason_code=reason_code,
        description=description,
        status="open",
        legacy_dispute_id=legacy_dispute_id,
    )
    db.add(row)
    order.status = "disputed"
    await db.flush()
    from app.services.commerce_trust import record_dispute_opened
    from app.services.commerce_messaging import notify_from_template
    await record_dispute_opened(db, order=order, dispute=row)
    req = await db.get(ProcurementRequest, order.procurement_request_id)
    portal_key = req.portal_key if req else "cebu"
    notify_company = (
        order.supplier_company_id if party == "buyer" else order.buyer_company_id
    )
    if notify_company:
        await notify_from_template(
            db,
            event_type="commerce.dispute.opened",
            company_ids=[notify_company],
            portal_key=portal_key,
            link_path=f"/commerce/orders/{order.id}",
            aggregate_type="commerce_order",
            aggregate_id=order.id,
        )
    await emit_event(
        db,
        "commerce.dispute.opened",
        {
            "order_id": str(order_id),
            "dispute_id": str(row.id),
            "reason_code": reason_code,
            "opened_by_role": party,
        },
        aggregate_type="order_dispute",
        aggregate_id=row.id,
        target_channel="telegram_admin",
    )
    return row


async def resolve_dispute(
    db: AsyncSession,
    dispute_id: uuid.UUID,
    *,
    resolution: str,
    resolution_json: dict | None,
) -> OrderDispute:
    if resolution not in ("resolved_buyer", "resolved_supplier", "closed"):
        raise CommerceTradeError("invalid resolution")
    row = await db.get(OrderDispute, dispute_id)
    if row is None:
        raise CommerceTradeError("dispute not found")
    order = await db.get(CommerceOrder, row.commerce_order_id)
    if order is None or row.workspace_id != order.workspace_id:
        raise CommerceTradeError("dispute and order belong to different Workspaces")
    if row.status not in ("open", "under_review"):
        raise CommerceTradeError("dispute not resolvable")
    row.status = resolution
    row.resolution_json = resolution_json
    row.resolved_at = datetime.now(timezone.utc)
    if order and order.status == "disputed":
        order.status = "in_delivery"
    await db.flush()
    await emit_event(
        db,
        "commerce.dispute.resolved",
        {"dispute_id": str(row.id), "order_id": str(row.commerce_order_id), "resolution": resolution},
        aggregate_type="order_dispute",
        aggregate_id=row.id,
    )
    return row


async def complete_order(
    db: AsyncSession, *, order_id: uuid.UUID | None = None, legacy_order_id: str | None = None
) -> CommerceOrder:
    if order_id:
        order = await db.get(CommerceOrder, order_id)
    elif legacy_order_id:
        order = (
            await db.execute(
                select(CommerceOrder).where(CommerceOrder.legacy_order_id == legacy_order_id)
            )
        ).scalar_one_or_none()
    else:
        raise CommerceTradeError("order id required")
    if order is None:
        raise CommerceTradeError("order not found")
    if await _has_open_dispute(db, order.id):
        raise CommerceTradeError("cannot complete order with open dispute")
    deliveries = await list_deliveries(db, order)
    if deliveries and not any(d.status in ("delivered", "accepted") for d in deliveries):
        raise CommerceTradeError("delivery not yet delivered")
    order.status = "completed"
    order.completed_at = datetime.now(timezone.utc)
    await db.flush()
    from app.services.commerce_trust import record_order_completed
    from app.services.commerce_messaging import notify_from_template

    await record_order_completed(db, order)
    req = await db.get(ProcurementRequest, order.procurement_request_id)
    portal_key = req.portal_key if req else "cebu"
    companies = [c for c in (order.buyer_company_id, order.supplier_company_id) if c]
    if companies:
        await notify_from_template(
            db,
            event_type="commerce.order.completed",
            company_ids=companies,
            portal_key=portal_key,
            link_path=f"/commerce/orders/{order.id}",
            aggregate_type="commerce_order",
            aggregate_id=order.id,
        )
    await emit_event(
        db,
        "commerce.order.completed",
        {"order_id": str(order.id), "legacy_order_id": order.legacy_order_id},
        aggregate_type="commerce_order",
        aggregate_id=order.id,
    )
    return order


async def upsert_request_from_legacy(
    db: AsyncSession, payload: dict[str, Any], *, portal_key: str
) -> tuple[ProcurementRequest, Lead | None]:
    legacy_id = str(payload.get("legacy_request_id") or payload.get("legacy_id") or "")
    if legacy_id:
        existing = (
            await db.execute(
                select(ProcurementRequest).where(ProcurementRequest.legacy_request_id == legacy_id)
            )
        ).scalar_one_or_none()
        if existing:
            return existing, await db.get(Lead, existing.lead_id) if existing.lead_id else None

    from app.services.portal_access import get_default_workspace

    workspace = await get_default_workspace(db)
    if workspace is None or workspace.status != "active":
        raise CommerceTradeError("Lead intake Workspace is unavailable")
    lead = Lead(
        workspace_id=workspace.id,
        contact_name=payload.get("contact_name"),
        contact_email=payload.get("contact_email"),
        contact_phone=payload.get("contact_phone"),
        project_type=payload.get("project_type"),
        country=payload.get("country"),
        city=payload.get("city"),
        budget_range=payload.get("budget_range"),
        description=payload.get("description"),
        status="new",
        source_channel="cebu_legacy",
        source_detail=legacy_id,
        language=payload.get("language") or "en",
    )
    db.add(lead)
    await db.flush()

    req = ProcurementRequest(
        workspace_id=workspace.id,
        buyer_user_id=uuid.UUID(str(payload["buyer_user_id"])) if payload.get("buyer_user_id") else None,
        buyer_company_id=uuid.UUID(str(payload["buyer_company_id"]))
        if payload.get("buyer_company_id")
        else None,
        portal_key=portal_key,
        lead_id=lead.id,
        region_id=uuid.UUID(str(payload["region_id"])) if payload.get("region_id") else None,
        title=payload.get("title") or payload.get("description") or "Procurement request",
        description=payload.get("description"),
        requirements_json=payload.get("requirements"),
        status="draft",
        legacy_request_id=legacy_id or None,
    )
    db.add(req)
    await db.flush()
    return req, lead
