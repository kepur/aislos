"""Phase 2: Cebu trade domain API (Core-owned)."""
import secrets
import uuid

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import or_, select

from app.api.deps import AdminUser, CurrentUser, DB, FinanceUser
from app.core.security import hash_password
from app.models.audit import AuditLog
from app.models.portal_access import WorkspaceMembership
from app.models.notification import NotificationPreference
from app.models.commerce import (
    CommerceOrder,
    CommercePaymentIntent,
    CommerceSettlement,
    CommerceThread,
    OrderDispute,
    ProcurementRequest,
    SupplierListing,
    SupplierOffer,
    TradeCategorySchema,
    TransactionReview,
    BuyerWatchlistItem,
)
from app.modules.commerce.access import (
    CommerceAccessDenied,
    CommerceResourceNotFound,
    customer_commerce_workspace_ids,
    require_procurement_request_owner,
    require_supplier_company,
    require_supplier_listing_owner,
    resolve_commerce_workspace,
    user_owns_procurement_request,
)
from app.schemas.commerce import (
    CategorySchemaCreate,
    CategorySchemaRead,
    CheckoutSessionRead,
    ConfirmFundingRequest,
    CommerceMessageCreate,
    CommerceMessageRead,
    CommerceOrderRead,
    CommerceThreadRead,
    DeliveryStatusUpdate,
    DisputeResolveRequest,
    FxQuoteRead,
    OrderDeliveryCreate,
    OrderDeliveryRead,
    OrderDisputeCreate,
    OrderDisputeRead,
    PaymentIntentCreate,
    PaymentIntentRead,
    PortalNotificationRead,
    ProcurementRequestCreate,
    ReconciliationRunCreate,
    ReconciliationRunRead,
    ProcurementRequestRead,
    SupplierListingCreate,
    SupplierListingRead,
    SupplierListingUpdate,
    SupplierTeamInvite,
    SupplierTeamUpdate,
    SupplierOfferCreate,
    SupplierOfferRead,
    CommerceSettlementRead,
    SettlementSettleRequest,
    RiskFlagRead,
    RiskFlagResolveRequest,
    TransactionReviewCreate,
    TransactionReviewRead,
    TrustProfileRead,
    BuyerAccountUpdate,
    BuyerWatchlistCreate,
)
from app.schemas.user import CompanyRead, UserRead
from app.services.portal_access import suspend_user_portal_access, sync_role_portal_access
from app.services.commerce_settlement import (
    CommerceSettlementError,
    confirm_order_funding,
    list_settlements,
    mark_settlement_settled,
    run_reconciliation,
)
from app.services.commerce_messaging import (
    CommerceMessagingAccessDenied,
    CommerceMessagingError,
    _thread_party,
    get_or_create_thread_for_order,
    list_thread_messages,
    list_user_notifications,
    mark_all_notifications_read,
    mark_notification_read,
    post_thread_message,
    unread_notification_count,
)
from app.services.commerce_trust import (
    CommerceTrustError,
    create_payment_intent,
    fx_quote_for_order,
    get_or_create_trust_profile,
    list_risk_flags,
    resolve_risk_flag,
    submit_transaction_review,
)
from app.services.commerce_trade import (
    CommerceTradeError,
    advance_delivery,
    award_offer,
    bind_listing_to_request,
    complete_order,
    create_delivery,
    create_listing,
    create_procurement_request,
    get_or_create_category,
    list_deliveries,
    list_orders_for_user,
    match_supplier_candidates,
    open_dispute,
    publish_request,
    resolve_dispute,
    submit_offer,
    _order_party,
)

router = APIRouter(prefix="/commerce", tags=["commerce-trade"])


def _supplier_company_or_403(user: CurrentUser, requested_company_id: uuid.UUID | None = None) -> uuid.UUID:
    try:
        return require_supplier_company(user, requested_company_id=requested_company_id)
    except CommerceAccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None


async def _owned_procurement_request(db: DB, user: CurrentUser, request_id: uuid.UUID):
    try:
        return await require_procurement_request_owner(db, user=user, request_id=request_id)
    except CommerceResourceNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    except CommerceAccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None


async def _is_supplier_owner(db: DB, user: CurrentUser) -> bool:
    company_id = _supplier_company_or_403(user)
    owner_id = (
        await db.execute(
            select(WorkspaceMembership.id)
            .where(
                WorkspaceMembership.user_id == user.id,
                WorkspaceMembership.company_id == company_id,
                WorkspaceMembership.membership_type == "supplier_owner",
                WorkspaceMembership.status == "active",
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    return owner_id is not None


async def _supplier_owner_company_or_403(db: DB, user: CurrentUser) -> uuid.UUID:
    company_id = _supplier_company_or_403(user)
    if not await _is_supplier_owner(db, user):
        raise HTTPException(status_code=403, detail="Supplier owner access required")
    return company_id


async def _is_customer_owner(db: DB, user: CurrentUser) -> bool:
    if user.company_id is None:
        return user.role == "buyer"
    owner_id = (
        await db.execute(
            select(WorkspaceMembership.id)
            .where(
                WorkspaceMembership.user_id == user.id,
                WorkspaceMembership.company_id == user.company_id,
                WorkspaceMembership.membership_type == "customer_owner",
                WorkspaceMembership.status == "active",
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    return owner_id is not None


@router.get("/category-schemas")
async def list_category_schemas(db: DB, user: CurrentUser):
    rows = list((await db.execute(select(TradeCategorySchema).where(TradeCategorySchema.status == "active"))).scalars())
    return {
        "items": [
            CategorySchemaRead(
                id=r.id,
                slug=r.slug,
                name=r.name,
                version=r.version,
                definition=r.schema_json or {},
                status=r.status,
            )
            for r in rows
        ],
        "total": len(rows),
    }


@router.get("/public/category-schemas")
async def list_public_category_schemas(db: DB):
    rows = list(
        (
            await db.execute(
                select(TradeCategorySchema)
                .where(TradeCategorySchema.status == "active")
                .order_by(TradeCategorySchema.name.asc())
            )
        ).scalars()
    )
    return {
        "items": [
            CategorySchemaRead(
                id=r.id,
                slug=r.slug,
                name=r.name,
                version=r.version,
                definition=r.schema_json or {},
                status=r.status,
            )
            for r in rows
        ],
        "total": len(rows),
    }


@router.post("/category-schemas", response_model=CategorySchemaRead, status_code=201)
async def create_category_schema(data: CategorySchemaCreate, db: DB, admin: AdminUser):
    row = await get_or_create_category(db, slug=data.slug, name=data.name, schema_json=data.definition)
    await db.commit()
    await db.refresh(row)
    return CategorySchemaRead(
        id=row.id,
        slug=row.slug,
        name=row.name,
        version=row.version,
        definition=row.schema_json or {},
        status=row.status,
    )


@router.post("/supplier-listings", response_model=SupplierListingRead, status_code=201)
async def post_supplier_listing(data: SupplierListingCreate, db: DB, user: CurrentUser):
    try:
        company_id = require_supplier_company(user, requested_company_id=data.company_id)
    except CommerceAccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None
    payload = data.model_dump(exclude={"company_id"})
    row = await create_listing(db, company_id=company_id, **payload)
    await db.commit()
    await db.refresh(row)
    return SupplierListingRead.model_validate(row)


@router.get("/supplier-listings")
async def list_supplier_listings(
    db: DB,
    user: CurrentUser,
    company_id: uuid.UUID | None = None,
    status: str | None = None,
):
    q = select(SupplierListing)
    if user.role in ("admin", "super_admin"):
        if company_id:
            q = q.where(SupplierListing.company_id == company_id)
    else:
        q = q.where(SupplierListing.company_id == _supplier_company_or_403(user, company_id))
    if status:
        q = q.where(SupplierListing.status == status)
    rows = list((await db.execute(q.order_by(SupplierListing.created_at.desc()).limit(50))).scalars())
    return {"items": [SupplierListingRead.model_validate(r) for r in rows], "total": len(rows)}


@router.patch("/supplier-listings/{listing_id}", response_model=SupplierListingRead)
async def update_supplier_listing(
    listing_id: uuid.UUID, data: SupplierListingUpdate, db: DB, user: CurrentUser
):
    company_id = _supplier_company_or_403(user)
    try:
        row = await require_supplier_listing_owner(
            db, supplier_company_id=company_id, listing_id=listing_id
        )
    except CommerceResourceNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    except CommerceAccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None
    values = data.model_dump(exclude_unset=True)
    if values.get("status") not in (None, "draft", "active", "inactive", "archived"):
        raise HTTPException(status_code=422, detail="Unsupported supplier listing status")
    for field, value in values.items():
        setattr(row, field, value)
    await db.commit()
    await db.refresh(row)
    return SupplierListingRead.model_validate(row)


@router.delete("/supplier-listings/{listing_id}", status_code=204)
async def archive_supplier_listing(listing_id: uuid.UUID, db: DB, user: CurrentUser):
    company_id = _supplier_company_or_403(user)
    try:
        row = await require_supplier_listing_owner(
            db, supplier_company_id=company_id, listing_id=listing_id
        )
    except CommerceResourceNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    except CommerceAccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None
    row.status = "archived"
    await db.commit()


@router.get("/public/listings")
async def list_public_supplier_listings(
    db: DB,
    category_schema_id: uuid.UUID | None = None,
    q: str | None = Query(default=None, max_length=120),
):
    stmt = select(SupplierListing).where(SupplierListing.status == "active")
    if category_schema_id:
        stmt = stmt.where(SupplierListing.category_schema_id == category_schema_id)
    if q:
        stmt = stmt.where(SupplierListing.title.ilike(f"%{q.strip()}%"))
    rows = list((await db.execute(stmt.order_by(SupplierListing.created_at.desc()).limit(100))).scalars())
    return {"items": [SupplierListingRead.model_validate(r) for r in rows], "total": len(rows)}


@router.get("/public/listings/{listing_id}", response_model=SupplierListingRead)
async def get_public_supplier_listing(listing_id: uuid.UUID, db: DB):
    row = await db.get(SupplierListing, listing_id)
    if row is None or row.status != "active":
        raise HTTPException(status_code=404, detail="Listing not found")
    return SupplierListingRead.model_validate(row)


@router.get("/buyer-account")
async def get_buyer_account(db: DB, user: CurrentUser):
    from app.models.user import Company

    company = await db.get(Company, user.company_id) if user.company_id else None
    return {
        "user": UserRead.model_validate(user),
        "company": CompanyRead.model_validate(company) if company else None,
        "permissions": {"manage_company": await _is_customer_owner(db, user)},
    }


@router.patch("/buyer-account")
async def update_buyer_account(data: BuyerAccountUpdate, db: DB, user: CurrentUser):
    from app.models.user import Company

    values = data.model_dump(exclude_unset=True)
    company_fields = {
        "company_name",
        "company_country",
        "company_city",
        "company_address",
        "company_description",
        "company_website",
    }
    includes_company_update = any(field in values for field in company_fields)
    for field in ("full_name", "phone", "language", "country"):
        if field in values:
            setattr(user, field, values[field])
    company = await db.get(Company, user.company_id) if user.company_id else None
    if company is None and values.get("company_name"):
        if user.role != "buyer":
            raise HTTPException(status_code=403, detail="Customer owner access required")
        company = Company(
            name=values["company_name"],
            type="buyer",
            country=values.get("company_country") or user.country,
            city=values.get("company_city"),
            address=values.get("company_address"),
            description=values.get("company_description"),
            website=values.get("company_website"),
        )
        db.add(company)
        await db.flush()
        user.company_id = company.id
        await sync_role_portal_access(
            db,
            user_id=user.id,
            role=user.role,
            company_id=company.id,
        )
    if company:
        if (
            includes_company_update
            and user.role in ("buyer", "customer_user")
            and not await _is_customer_owner(db, user)
        ):
            raise HTTPException(status_code=403, detail="Customer owner access required")
        company_fields = {
            "company_name": "name",
            "company_country": "country",
            "company_city": "city",
            "company_address": "address",
            "company_description": "description",
            "company_website": "website",
        }
        for source, target in company_fields.items():
            if source in values:
                setattr(company, target, values[source])
    await db.commit()
    await db.refresh(user)
    if company:
        await db.refresh(company)
    return {
        "user": UserRead.model_validate(user),
        "company": CompanyRead.model_validate(company) if company else None,
        "permissions": {"manage_company": await _is_customer_owner(db, user)},
    }


@router.get("/buyer-team")
async def list_buyer_team(db: DB, user: CurrentUser):
    from app.models.user import User

    if user.company_id is None:
        return {"items": [UserRead.model_validate(user)], "total": 1}
    rows = list(
        (
            await db.execute(
                select(User)
                .where(User.company_id == user.company_id, User.is_active.is_(True))
                .order_by(User.created_at.asc())
            )
        ).scalars()
    )
    return {"items": [UserRead.model_validate(row) for row in rows], "total": len(rows)}


@router.get("/supplier-account")
async def get_supplier_account(db: DB, user: CurrentUser):
    _supplier_company_or_403(user)
    account = await get_buyer_account(db, user)
    is_owner = await _is_supplier_owner(db, user)
    account["permissions"] = {
        "manage_company": is_owner,
        "manage_team": is_owner,
    }
    return account


@router.patch("/supplier-account")
async def update_supplier_account(data: BuyerAccountUpdate, db: DB, user: CurrentUser):
    _supplier_company_or_403(user)
    values = data.model_dump(exclude_unset=True)
    if any(field.startswith("company_") for field in values):
        await _supplier_owner_company_or_403(db, user)
    account = await update_buyer_account(data, db, user)
    is_owner = await _is_supplier_owner(db, user)
    account["permissions"] = {
        "manage_company": is_owner,
        "manage_team": is_owner,
    }
    return account


@router.get("/supplier-team")
async def list_supplier_team(db: DB, user: CurrentUser):
    from app.models.user import User

    company_id = _supplier_company_or_403(user)
    rows = list(
        (
            await db.execute(
                select(User)
                .where(User.company_id == company_id, User.role == "vendor")
                .order_by(User.is_active.desc(), User.created_at.asc())
            )
        ).scalars()
    )
    return {"items": [UserRead.model_validate(row) for row in rows], "total": len(rows)}


@router.post("/supplier-team", status_code=201)
async def invite_supplier_team_member(data: SupplierTeamInvite, db: DB, user: CurrentUser):
    from app.models.user import User

    company_id = await _supplier_owner_company_or_403(db, user)
    email = str(data.email).strip().lower()
    if (await db.execute(select(User).where(User.email == email))).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    row = User(
        email=email,
        full_name=data.full_name,
        phone=data.phone,
        role="vendor",
        company_id=company_id,
        password_hash=hash_password(secrets.token_urlsafe(48)),
        is_active=True,
    )
    db.add(row)
    await db.flush()
    await sync_role_portal_access(db, user_id=row.id, role=row.role, company_id=company_id)
    db.add(
        AuditLog(
            actor_user_id=user.id,
            portal_key="supplier",
            action="supplier.team.invited",
            entity_type="user",
            entity_id=row.id,
            after_json={"email": row.email, "role": row.role, "company_id": str(company_id)},
            reason="Password reset required",
            source="commerce_api",
        )
    )
    await db.commit()
    await db.refresh(row)
    return {"user": UserRead.model_validate(row), "password_reset_required": True}


@router.patch("/supplier-team/{member_id}")
async def update_supplier_team_member(
    member_id: uuid.UUID, data: SupplierTeamUpdate, db: DB, user: CurrentUser
):
    from app.models.user import User

    company_id = await _supplier_owner_company_or_403(db, user)
    row = await db.get(User, member_id)
    if row is None or row.company_id != company_id or row.role != "vendor":
        raise HTTPException(status_code=404, detail="Supplier team member not found")

    values = data.model_dump(exclude_unset=True)
    if values.get("is_active") is False and row.id == user.id:
        raise HTTPException(status_code=409, detail="Supplier team member cannot deactivate own account")
    before = {
        "full_name": row.full_name,
        "phone": row.phone,
        "is_active": row.is_active,
    }
    for field in ("full_name", "phone"):
        if field in values:
            setattr(row, field, values[field])
    if "is_active" in values and values["is_active"] != row.is_active:
        row.is_active = values["is_active"]
        if row.is_active:
            await sync_role_portal_access(db, user_id=row.id, role=row.role, company_id=company_id)
        else:
            await suspend_user_portal_access(db, user_id=row.id)
    db.add(
        AuditLog(
            actor_user_id=user.id,
            portal_key="supplier",
            action="supplier.team.updated",
            entity_type="user",
            entity_id=row.id,
            before_json=before,
            after_json={
                "full_name": row.full_name,
                "phone": row.phone,
                "is_active": row.is_active,
            },
            source="commerce_api",
        )
    )
    await db.commit()
    await db.refresh(row)
    return UserRead.model_validate(row)


@router.get("/supplier-pings")
async def list_supplier_pings(db: DB, user: CurrentUser):
    company_id = _supplier_company_or_403(user)
    listings = list(
        (
            await db.execute(
                select(SupplierListing).where(
                    SupplierListing.company_id == company_id,
                    SupplierListing.status == "active",
                )
            )
        ).scalars()
    )
    preference = (
        await db.execute(
            select(NotificationPreference).where(NotificationPreference.user_id == user.id)
        )
    ).scalar_one_or_none()
    preferred_category_ids = {
        uuid.UUID(str(item)) for item in (preference.supplier_category_ids_json or [])
    } if preference else set()
    preferred_region_ids = {
        uuid.UUID(str(item)) for item in (preference.supplier_region_ids_json or [])
    } if preference else set()
    category_ids = preferred_category_ids or {
        row.category_schema_id for row in listings if row.category_schema_id
    }
    stmt = select(ProcurementRequest).where(
        ProcurementRequest.status.in_(("published", "matching", "offer_received"))
    )
    if category_ids:
        stmt = stmt.where(ProcurementRequest.category_schema_id.in_(category_ids))
    if preferred_region_ids:
        stmt = stmt.where(ProcurementRequest.region_id.in_(preferred_region_ids))
    requests = list((await db.execute(stmt.order_by(ProcurementRequest.published_at.desc()).limit(100))).scalars())
    offers = list(
        (
            await db.execute(
                select(SupplierOffer).where(
                    SupplierOffer.supplier_company_id == company_id,
                    SupplierOffer.procurement_request_id.in_([row.id for row in requests]),
                )
            )
        ).scalars()
    ) if requests else []
    offer_by_request = {row.procurement_request_id: row for row in offers}
    matching_listing_ids: dict[uuid.UUID | None, list[uuid.UUID]] = {}
    for listing in listings:
        matching_listing_ids.setdefault(listing.category_schema_id, []).append(listing.id)
    return {
        "items": [
            {
                **ProcurementRequestRead.model_validate(row).model_dump(),
                "already_offered": row.id in offer_by_request,
                "offer_id": offer_by_request[row.id].id if row.id in offer_by_request else None,
                "matching_listing_ids": matching_listing_ids.get(row.category_schema_id, []),
            }
            for row in requests
        ],
        "total": len(requests),
    }


@router.get("/supplier-offers")
async def list_my_supplier_offers(db: DB, user: CurrentUser, status: str | None = None):
    company_id = _supplier_company_or_403(user)
    stmt = select(SupplierOffer).where(SupplierOffer.supplier_company_id == company_id)
    if status:
        stmt = stmt.where(SupplierOffer.status == status)
    rows = list((await db.execute(stmt.order_by(SupplierOffer.created_at.desc()).limit(100))).scalars())
    return {"items": [SupplierOfferRead.model_validate(row) for row in rows], "total": len(rows)}


@router.post("/offers/{offer_id}/withdraw", response_model=SupplierOfferRead)
async def withdraw_supplier_offer(offer_id: uuid.UUID, db: DB, user: CurrentUser):
    company_id = _supplier_company_or_403(user)
    offer = await db.get(SupplierOffer, offer_id)
    if offer is None:
        raise HTTPException(status_code=404, detail="Offer not found")
    if offer.supplier_company_id != company_id:
        raise HTTPException(status_code=403, detail="Cannot withdraw another supplier's offer")
    request = await db.get(ProcurementRequest, offer.procurement_request_id)
    if request is None or offer.workspace_id != request.workspace_id:
        raise HTTPException(status_code=409, detail="Offer and request belong to different Workspaces")
    if offer.status not in ("draft", "submitted"):
        raise HTTPException(status_code=409, detail="Only draft or submitted offers can be withdrawn")
    offer.status = "withdrawn"
    await db.commit()
    await db.refresh(offer)
    return SupplierOfferRead.model_validate(offer)


@router.get("/supplier-reviews")
async def list_my_supplier_reviews(db: DB, user: CurrentUser):
    company_id = _supplier_company_or_403(user)
    rows = list(
        (
            await db.execute(
                select(TransactionReview)
                .where(
                    TransactionReview.supplier_company_id == company_id,
                    TransactionReview.status == "published",
                )
                .order_by(TransactionReview.created_at.desc())
                .limit(100)
            )
        ).scalars()
    )
    return {"items": [TransactionReviewRead.model_validate(row) for row in rows], "total": len(rows)}


@router.get("/supplier-dashboard")
async def get_supplier_dashboard(db: DB, user: CurrentUser):
    company_id = _supplier_company_or_403(user)
    listings = list((await db.execute(select(SupplierListing).where(SupplierListing.company_id == company_id))).scalars())
    offers = list((await db.execute(select(SupplierOffer).where(SupplierOffer.supplier_company_id == company_id))).scalars())
    orders = list((await db.execute(select(CommerceOrder).where(CommerceOrder.supplier_company_id == company_id))).scalars())
    pings = await list_supplier_pings(db, user)
    return {
        "listings": len(listings),
        "active_listings": sum(row.status == "active" for row in listings),
        "offers": len(offers),
        "submitted_offers": sum(row.status == "submitted" for row in offers),
        "orders": len(orders),
        "active_orders": sum(row.status not in ("completed", "cancelled") for row in orders),
        "open_pings": pings["total"],
        "unread_notifications": await unread_notification_count(db, user.id),
    }


@router.get("/watchlist")
async def list_buyer_watchlist(db: DB, user: CurrentUser):
    rows = list(
        (
            await db.execute(
                select(BuyerWatchlistItem, SupplierListing)
                .join(SupplierListing, SupplierListing.id == BuyerWatchlistItem.supplier_listing_id)
                .where(BuyerWatchlistItem.buyer_user_id == user.id, BuyerWatchlistItem.status == "active")
                .order_by(BuyerWatchlistItem.created_at.desc())
            )
        ).all()
    )
    return {
        "items": [
            {
                "id": watch.id,
                "buyer_user_id": watch.buyer_user_id,
                "supplier_listing_id": watch.supplier_listing_id,
                "target_price_minor": watch.target_price_minor,
                "currency": watch.currency,
                "status": watch.status,
                "listing": SupplierListingRead.model_validate(listing),
                "created_at": watch.created_at,
            }
            for watch, listing in rows
        ],
        "total": len(rows),
    }


@router.post("/watchlist", status_code=201)
async def add_buyer_watchlist(data: BuyerWatchlistCreate, db: DB, user: CurrentUser):
    listing = await db.get(SupplierListing, data.supplier_listing_id)
    if listing is None or listing.status != "active":
        raise HTTPException(status_code=404, detail="Listing not found")
    row = (
        await db.execute(
            select(BuyerWatchlistItem).where(
                BuyerWatchlistItem.buyer_user_id == user.id,
                BuyerWatchlistItem.supplier_listing_id == data.supplier_listing_id,
            )
        )
    ).scalar_one_or_none()
    if row:
        row.target_price_minor = data.target_price_minor
        row.currency = data.currency
        row.status = "active"
    else:
        row = BuyerWatchlistItem(buyer_user_id=user.id, **data.model_dump())
        db.add(row)
    await db.commit()
    await db.refresh(row)
    return {
        "id": row.id,
        "buyer_user_id": row.buyer_user_id,
        "supplier_listing_id": row.supplier_listing_id,
        "target_price_minor": row.target_price_minor,
        "currency": row.currency,
        "status": row.status,
        "listing": SupplierListingRead.model_validate(listing),
        "created_at": row.created_at,
    }


@router.delete("/watchlist/{watchlist_id}", status_code=204)
async def remove_buyer_watchlist(watchlist_id: uuid.UUID, db: DB, user: CurrentUser):
    row = await db.get(BuyerWatchlistItem, watchlist_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    if row.buyer_user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your watchlist item")
    row.status = "removed"
    await db.commit()


@router.post("/procurement-requests", response_model=ProcurementRequestRead, status_code=201)
async def post_procurement_request(data: ProcurementRequestCreate, db: DB, user: CurrentUser):
    try:
        workspace_id = await resolve_commerce_workspace(
            db,
            user=user,
            requested_workspace_id=data.workspace_id,
        )
    except CommerceAccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None
    row = await create_procurement_request(
        db,
        workspace_id=workspace_id,
        buyer_user_id=user.id,
        buyer_company_id=user.company_id,
        **data.model_dump(exclude={"workspace_id"}),
    )
    await db.commit()
    await db.refresh(row)
    return ProcurementRequestRead.model_validate(row)


@router.get("/procurement-requests")
async def list_procurement_requests(db: DB, user: CurrentUser, status: str | None = None):
    q = select(ProcurementRequest)
    if user.role not in ("admin", "super_admin"):
        owner_scope = ProcurementRequest.buyer_user_id == user.id
        if user.company_id is not None:
            workspace_ids = await customer_commerce_workspace_ids(db, user)
            workspace_scope = (
                ProcurementRequest.workspace_id.in_(workspace_ids)
                if workspace_ids
                else ProcurementRequest.workspace_id.is_(None)
            )
            owner_scope = owner_scope | (
                (ProcurementRequest.buyer_company_id == user.company_id)
                & (workspace_scope | ProcurementRequest.workspace_id.is_(None))
            )
        q = q.where(owner_scope)
    if status:
        q = q.where(ProcurementRequest.status == status)
    rows = list((await db.execute(q.order_by(ProcurementRequest.created_at.desc()).limit(50))).scalars())
    return {"items": [ProcurementRequestRead.model_validate(r) for r in rows], "total": len(rows)}


@router.get("/procurement-requests/{request_id}", response_model=ProcurementRequestRead)
async def get_procurement_request(request_id: uuid.UUID, db: DB, user: CurrentUser):
    req = await _owned_procurement_request(db, user, request_id)
    return ProcurementRequestRead.model_validate(req)


@router.post("/procurement-requests/{request_id}/publish", response_model=ProcurementRequestRead)
async def publish_procurement_request(request_id: uuid.UUID, db: DB, user: CurrentUser):
    await _owned_procurement_request(db, user, request_id)
    try:
        row = await publish_request(db, request_id)
        await db.commit()
        await db.refresh(row)
        return ProcurementRequestRead.model_validate(row)
    except CommerceTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.get("/procurement-requests/{request_id}/supplier-candidates")
async def supplier_candidates(request_id: uuid.UUID, db: DB, user: CurrentUser):
    """Cebu parity: GET /intents/{id}/supplier-candidates"""
    await _owned_procurement_request(db, user, request_id)
    try:
        items = await match_supplier_candidates(db, request_id)
        return {
            "items": [SupplierListingRead.model_validate(i) for i in items],
            "total": len(items),
        }
    except CommerceTradeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None


@router.get("/procurement-requests/{request_id}/offers")
async def list_procurement_request_offers(request_id: uuid.UUID, db: DB, user: CurrentUser):
    request = await _owned_procurement_request(db, user, request_id)
    rows = list(
        (
            await db.execute(
                select(SupplierOffer)
                .where(
                    SupplierOffer.procurement_request_id == request_id,
                    SupplierOffer.workspace_id == request.workspace_id,
                )
                .order_by(SupplierOffer.price_minor.asc(), SupplierOffer.created_at.asc())
            )
        ).scalars()
    )
    return {"items": [SupplierOfferRead.model_validate(r) for r in rows], "total": len(rows)}


@router.post("/procurement-requests/{request_id}/supplier-candidates/{listing_id}/bind")
async def bind_supplier_candidate(request_id: uuid.UUID, listing_id: uuid.UUID, db: DB, user: CurrentUser):
    await _owned_procurement_request(db, user, request_id)
    try:
        row = await bind_listing_to_request(db, request_id, listing_id)
        await db.commit()
        return ProcurementRequestRead.model_validate(row)
    except CommerceTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from None


@router.post("/procurement-requests/{request_id}/offers", response_model=SupplierOfferRead, status_code=201)
async def create_offer(request_id: uuid.UUID, data: SupplierOfferCreate, db: DB, user: CurrentUser):
    try:
        supplier_company_id = require_supplier_company(
            user, requested_company_id=data.supplier_company_id
        )
        if data.supplier_listing_id:
            await require_supplier_listing_owner(
                db,
                supplier_company_id=supplier_company_id,
                listing_id=data.supplier_listing_id,
            )
    except CommerceResourceNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    except CommerceAccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None
    request = await db.get(ProcurementRequest, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Procurement request not found")
    if request.buyer_company_id and request.buyer_company_id == supplier_company_id:
        raise HTTPException(status_code=403, detail="Buyer company cannot bid on its own request")
    if request.status not in ("published", "matching", "offer_received"):
        raise HTTPException(status_code=409, detail="Procurement request is not open for offers")
    try:
        row = await submit_offer(
            db,
            procurement_request_id=request_id,
            supplier_company_id=supplier_company_id,
            supplier_listing_id=data.supplier_listing_id,
            price_minor=data.price_minor,
            currency=data.currency,
            terms_json=data.terms_json,
        )
        await db.commit()
        await db.refresh(row)
        return SupplierOfferRead.model_validate(row)
    except CommerceTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.post("/offers/{offer_id}/award", response_model=CommerceOrderRead)
async def award_supplier_offer(offer_id: uuid.UUID, db: DB, user: CurrentUser):
    offer = await db.get(SupplierOffer, offer_id)
    if offer is None:
        raise HTTPException(status_code=404, detail="Offer not found")
    await _owned_procurement_request(db, user, offer.procurement_request_id)
    try:
        order = await award_offer(db, offer_id)
        await db.commit()
        await db.refresh(order)
        return CommerceOrderRead.model_validate(order)
    except CommerceTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.get("/offers/{offer_id}", response_model=SupplierOfferRead)
async def get_supplier_offer(offer_id: uuid.UUID, db: DB, user: CurrentUser):
    offer = await db.get(SupplierOffer, offer_id)
    if offer is None:
        raise HTTPException(status_code=404, detail="Offer not found")
    if user.role not in ("admin", "super_admin"):
        request = await db.get(ProcurementRequest, offer.procurement_request_id)
        buyer = bool(request and await user_owns_procurement_request(db, user, request))
        supplier = bool(user.company_id and user.company_id == offer.supplier_company_id)
        if not buyer and not supplier:
            raise HTTPException(status_code=403, detail="Not a party to this offer")
    else:
        request = await db.get(ProcurementRequest, offer.procurement_request_id)
    if request is None or offer.workspace_id != request.workspace_id:
        raise HTTPException(status_code=409, detail="Offer and request belong to different Workspaces")
    return SupplierOfferRead.model_validate(offer)


async def _get_order_or_404(db: DB, order_id: uuid.UUID) -> CommerceOrder:
    order = await db.get(CommerceOrder, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.get("/orders")
async def list_commerce_orders(db: DB, user: CurrentUser, status: str | None = None):
    rows = await list_orders_for_user(db, user, status=status)
    return {"items": [CommerceOrderRead.model_validate(r) for r in rows], "total": len(rows)}


@router.get("/orders/{order_id}", response_model=CommerceOrderRead)
async def get_commerce_order(order_id: uuid.UUID, db: DB, user: CurrentUser):
    order = await _get_order_or_404(db, order_id)
    if user.role not in ("admin", "super_admin") and not await _order_party(db, user, order):
        raise HTTPException(status_code=403, detail="Not a party to this order")
    return CommerceOrderRead.model_validate(order)


@router.post("/orders/{order_id}/complete", response_model=CommerceOrderRead)
async def complete_commerce_order(order_id: uuid.UUID, db: DB, user: CurrentUser):
    order = await _get_order_or_404(db, order_id)
    party = await _order_party(db, user, order)
    if party not in ("buyer", "admin"):
        raise HTTPException(status_code=403, detail="Only buyer or admin can complete order")
    try:
        row = await complete_order(db, order_id=order_id)
        await db.commit()
        await db.refresh(row)
        return CommerceOrderRead.model_validate(row)
    except CommerceTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.get("/orders/{order_id}/deliveries")
async def list_order_deliveries(order_id: uuid.UUID, db: DB, user: CurrentUser):
    order = await _get_order_or_404(db, order_id)
    if user.role not in ("admin", "super_admin") and not await _order_party(db, user, order):
        raise HTTPException(status_code=403, detail="Not a party to this order")
    items = await list_deliveries(db, order)
    return {"items": [OrderDeliveryRead.model_validate(i) for i in items], "total": len(items)}


@router.post("/orders/{order_id}/deliveries", response_model=OrderDeliveryRead, status_code=201)
async def create_order_delivery(order_id: uuid.UUID, data: OrderDeliveryCreate, db: DB, user: CurrentUser):
    order = await _get_order_or_404(db, order_id)
    party = await _order_party(db, user, order)
    if party not in ("supplier", "admin"):
        raise HTTPException(status_code=403, detail="Only supplier can schedule delivery")
    try:
        row = await create_delivery(db, order_id, **data.model_dump())
        await db.commit()
        await db.refresh(row)
        return OrderDeliveryRead.model_validate(row)
    except CommerceTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.patch("/deliveries/{delivery_id}/status", response_model=OrderDeliveryRead)
async def update_delivery_status(delivery_id: uuid.UUID, data: DeliveryStatusUpdate, db: DB, user: CurrentUser):
    from app.models.commerce import OrderDelivery

    delivery = await db.get(OrderDelivery, delivery_id)
    if delivery is None:
        raise HTTPException(status_code=404, detail="Delivery not found")
    order = await _get_order_or_404(db, delivery.commerce_order_id)
    party = await _order_party(db, user, order)
    if data.status == "accepted" and party not in ("buyer", "admin"):
        raise HTTPException(status_code=403, detail="Only buyer can accept delivery")
    if data.status != "accepted" and party not in ("supplier", "admin"):
        raise HTTPException(status_code=403, detail="Only supplier can update shipment status")
    try:
        row = await advance_delivery(db, delivery_id, new_status=data.status, proof_json=data.proof_json)
        await db.commit()
        await db.refresh(row)
        return OrderDeliveryRead.model_validate(row)
    except CommerceTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.get("/orders/{order_id}/disputes")
async def list_order_disputes(order_id: uuid.UUID, db: DB, user: CurrentUser):
    order = await _get_order_or_404(db, order_id)
    if user.role not in ("admin", "super_admin") and not await _order_party(db, user, order):
        raise HTTPException(status_code=403, detail="Not a party to this order")
    rows = list(
        (
            await db.execute(
                select(OrderDispute)
                .where(
                    OrderDispute.commerce_order_id == order_id,
                    OrderDispute.workspace_id == order.workspace_id,
                )
                .order_by(OrderDispute.created_at.desc())
            )
        ).scalars()
    )
    return {"items": [OrderDisputeRead.model_validate(r) for r in rows], "total": len(rows)}


@router.get("/disputes")
async def list_my_order_disputes(db: DB, user: CurrentUser, status: str | None = None):
    stmt = (
        select(OrderDispute)
        .join(CommerceOrder, CommerceOrder.id == OrderDispute.commerce_order_id)
        .order_by(OrderDispute.created_at.desc())
        .limit(100)
    )
    if user.role not in ("admin", "super_admin"):
        if user.company_id is None:
            return {"items": [], "total": 0}
        workspace_ids = await customer_commerce_workspace_ids(db, user)
        buyer_workspace_scope = (
            CommerceOrder.workspace_id.in_(workspace_ids)
            if workspace_ids
            else CommerceOrder.workspace_id.is_(None)
        )
        stmt = stmt.where(
            (
                (CommerceOrder.buyer_company_id == user.company_id)
                & (buyer_workspace_scope | CommerceOrder.workspace_id.is_(None))
            )
            | (CommerceOrder.supplier_company_id == user.company_id)
        )
    if status:
        stmt = stmt.where(OrderDispute.status == status)
    rows = list((await db.execute(stmt)).scalars())
    return {"items": [OrderDisputeRead.model_validate(r) for r in rows], "total": len(rows)}


@router.post("/orders/{order_id}/disputes", response_model=OrderDisputeRead, status_code=201)
async def create_order_dispute(order_id: uuid.UUID, data: OrderDisputeCreate, db: DB, user: CurrentUser):
    order = await _get_order_or_404(db, order_id)
    if user.role not in ("admin", "super_admin") and not await _order_party(db, user, order):
        raise HTTPException(status_code=403, detail="Not a party to this order")
    try:
        row = await open_dispute(
            db,
            order_id=order_id,
            user=user,
            reason_code=data.reason_code,
            description=data.description,
        )
        await db.commit()
        await db.refresh(row)
        return OrderDisputeRead.model_validate(row)
    except CommerceTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.post("/disputes/{dispute_id}/resolve", response_model=OrderDisputeRead)
async def resolve_order_dispute(dispute_id: uuid.UUID, data: DisputeResolveRequest, db: DB, admin: AdminUser):
    try:
        row = await resolve_dispute(
            db, dispute_id, resolution=data.resolution, resolution_json=data.resolution_json
        )
        await db.commit()
        await db.refresh(row)
        return OrderDisputeRead.model_validate(row)
    except CommerceTradeError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.get("/trust-profiles/{company_id}", response_model=TrustProfileRead)
async def get_supplier_trust_profile(company_id: uuid.UUID, db: DB, user: CurrentUser):
    row = await get_or_create_trust_profile(db, company_id=company_id)
    await db.commit()
    await db.refresh(row)
    return TrustProfileRead.model_validate(row)


@router.get("/orders/{order_id}/reviews")
async def list_order_reviews(order_id: uuid.UUID, db: DB, user: CurrentUser):
    from app.models.commerce import TransactionReview

    order = await _get_order_or_404(db, order_id)
    if user.role not in ("admin", "super_admin") and not await _order_party(db, user, order):
        raise HTTPException(status_code=403, detail="Not a party to this order")
    rows = list(
        (
            await db.execute(
                select(TransactionReview)
                .where(
                    TransactionReview.commerce_order_id == order_id,
                    TransactionReview.workspace_id == order.workspace_id,
                )
                .order_by(TransactionReview.created_at.desc())
            )
        ).scalars()
    )
    return {"items": [TransactionReviewRead.model_validate(r) for r in rows], "total": len(rows)}


@router.post("/orders/{order_id}/reviews", response_model=TransactionReviewRead, status_code=201)
async def create_order_review(order_id: uuid.UUID, data: TransactionReviewCreate, db: DB, user: CurrentUser):
    order = await _get_order_or_404(db, order_id)
    party = await _order_party(db, user, order)
    if party not in ("buyer", "admin"):
        raise HTTPException(status_code=403, detail="Only buyer can review")
    try:
        row = await submit_transaction_review(
            db, order_id=order_id, user=user, rating=data.rating, comment=data.comment
        )
        await db.commit()
        await db.refresh(row)
        return TransactionReviewRead.model_validate(row)
    except CommerceTrustError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.get("/risk-flags")
async def list_commerce_risk_flags(
    db: DB, admin: AdminUser, status: str | None = Query(default="open")
):
    rows = await list_risk_flags(db, status=status)
    return {"items": [RiskFlagRead.model_validate(r) for r in rows], "total": len(rows)}


@router.post("/risk-flags/{flag_id}/resolve", response_model=RiskFlagRead)
async def resolve_commerce_risk_flag(
    flag_id: uuid.UUID, data: RiskFlagResolveRequest, db: DB, admin: AdminUser
):
    try:
        row = await resolve_risk_flag(db, flag_id, user=admin, resolution=data.resolution)
        await db.commit()
        await db.refresh(row)
        return RiskFlagRead.model_validate(row)
    except CommerceTrustError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.post("/orders/{order_id}/payment-intent", response_model=PaymentIntentRead, status_code=201)
async def create_order_payment_intent(
    order_id: uuid.UUID, data: PaymentIntentCreate, db: DB, user: CurrentUser
):
    order = await _get_order_or_404(db, order_id)
    party = await _order_party(db, user, order)
    if party not in ("buyer", "admin"):
        raise HTTPException(status_code=403, detail="Only buyer can create payment intent")
    try:
        row = await create_payment_intent(
            db,
            order_id=order_id,
            quote_currency=data.quote_currency,
            psp_provider=data.psp_provider,
        )
        await db.commit()
        await db.refresh(row)
        return PaymentIntentRead.model_validate(row)
    except CommerceTrustError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.get("/orders/{order_id}/payment-intent", response_model=PaymentIntentRead)
async def get_order_payment_intent(order_id: uuid.UUID, db: DB, user: CurrentUser):
    from app.models.commerce import CommercePaymentIntent

    order = await _get_order_or_404(db, order_id)
    if user.role not in ("admin", "super_admin") and not await _order_party(db, user, order):
        raise HTTPException(status_code=403, detail="Not a party to this order")
    row = (
        await db.execute(
            select(CommercePaymentIntent).where(
                CommercePaymentIntent.commerce_order_id == order_id,
                CommercePaymentIntent.workspace_id == order.workspace_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Payment intent not found")
    return PaymentIntentRead.model_validate(row)


@router.get("/orders/{order_id}/fx-quote", response_model=FxQuoteRead)
async def get_order_fx_quote(
    order_id: uuid.UUID, db: DB, user: CurrentUser, quote_currency: str = Query(..., min_length=3, max_length=3)
):
    order = await _get_order_or_404(db, order_id)
    if user.role not in ("admin", "super_admin") and not await _order_party(db, user, order):
        raise HTTPException(status_code=403, detail="Not a party to this order")
    try:
        data = await fx_quote_for_order(db, order_id=order_id, quote_currency=quote_currency)
        return FxQuoteRead.model_validate(data)
    except CommerceTrustError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None


@router.post("/orders/{order_id}/checkout", response_model=CheckoutSessionRead)
async def create_commerce_checkout(order_id: uuid.UUID, db: DB, user: CurrentUser):
    order = await _get_order_or_404(db, order_id)
    party = await _order_party(db, user, order)
    if party not in ("buyer", "admin"):
        raise HTTPException(status_code=403, detail="Only buyer can start checkout")
    from app.services.stripe_payments import create_commerce_order_checkout, is_configured, stripe_config

    cfg = await stripe_config(db)
    if not is_configured(cfg):
        return CheckoutSessionRead(
            configured=False,
            detail="Stripe not configured — use confirm-funding (offline) or Admin → Integrations",
        )
    try:
        url = await create_commerce_order_checkout(db, order_id=order_id)
        await db.commit()
        return CheckoutSessionRead(checkout_url=url, configured=True)
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.post("/orders/{order_id}/confirm-funding", response_model=CommerceSettlementRead)
async def confirm_commerce_order_funding(
    order_id: uuid.UUID, data: ConfirmFundingRequest, db: DB, admin: FinanceUser
):
    try:
        row = await confirm_order_funding(
            db,
            order_id=order_id,
            external_ref=data.external_ref,
            source_account=data.source_account,
        )
        await db.commit()
        await db.refresh(row)
        return CommerceSettlementRead.model_validate(row)
    except CommerceSettlementError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.get("/settlements")
async def list_commerce_settlements(db: DB, admin: FinanceUser, status: str | None = None):
    rows = await list_settlements(db, status=status)
    return {"items": [CommerceSettlementRead.model_validate(r) for r in rows], "total": len(rows)}


@router.get("/payment-ledger")
async def list_my_payment_ledger(db: DB, user: CurrentUser):
    order_scope = select(CommerceOrder.id)
    if user.role not in ("admin", "super_admin"):
        if user.company_id is None:
            return {"items": [], "total": 0}
        workspace_ids = await customer_commerce_workspace_ids(db, user)
        buyer_workspace_scope = (
            CommerceOrder.workspace_id.in_(workspace_ids)
            if workspace_ids
            else CommerceOrder.workspace_id.is_(None)
        )
        order_scope = order_scope.where(
            (
                (CommerceOrder.buyer_company_id == user.company_id)
                & (buyer_workspace_scope | CommerceOrder.workspace_id.is_(None))
            )
            | (CommerceOrder.supplier_company_id == user.company_id)
        )
    intents = list(
        (
            await db.execute(
                select(CommercePaymentIntent)
                .where(CommercePaymentIntent.commerce_order_id.in_(order_scope))
                .order_by(CommercePaymentIntent.created_at.desc())
            )
        ).scalars()
    )
    settlements = list(
        (
            await db.execute(
                select(CommerceSettlement)
                .where(CommerceSettlement.commerce_order_id.in_(order_scope))
                .order_by(CommerceSettlement.created_at.desc())
            )
        ).scalars()
    )
    items = [
        {
            "id": str(row.id),
            "order_id": str(row.commerce_order_id),
            "kind": "payment_intent",
            "status": row.status,
            "amount_minor": row.amount_minor,
            "currency": row.currency,
            "external_ref": row.external_ref,
            "created_at": row.created_at,
        }
        for row in intents
    ] + [
        {
            "id": str(row.id),
            "order_id": str(row.commerce_order_id),
            "kind": "settlement",
            "status": row.status,
            "amount_minor": row.amount_minor,
            "currency": row.currency,
            "external_ref": row.external_ref,
            "created_at": row.created_at,
        }
        for row in settlements
    ]
    items.sort(key=lambda item: item["created_at"], reverse=True)
    return {"items": items, "total": len(items)}


@router.post("/settlements/{settlement_id}/settle", response_model=CommerceSettlementRead)
async def settle_commerce_payment(
    settlement_id: uuid.UUID, data: SettlementSettleRequest, db: DB, admin: FinanceUser
):
    try:
        row = await mark_settlement_settled(
            db,
            settlement_id,
            psp_settlement_ref=data.psp_settlement_ref,
            platform_fee_minor=data.platform_fee_minor,
        )
        await db.commit()
        await db.refresh(row)
        return CommerceSettlementRead.model_validate(row)
    except CommerceSettlementError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.post("/reconciliation-runs", response_model=ReconciliationRunRead, status_code=201)
async def create_reconciliation_run(data: ReconciliationRunCreate, db: DB, admin: FinanceUser):
    try:
        row = await run_reconciliation(
            db,
            period_start=data.period_start,
            period_end=data.period_end,
            user=admin,
        )
        await db.commit()
        await db.refresh(row)
        return ReconciliationRunRead.model_validate(row)
    except CommerceSettlementError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.get("/notifications")
async def list_commerce_notifications(
    db: DB,
    user: CurrentUser,
    status: str | None = Query(default=None),
    portal_key: str | None = Query(default=None),
):
    rows = await list_user_notifications(db, user_id=user.id, portal_key=portal_key, status=status)
    return {"items": [PortalNotificationRead.model_validate(r) for r in rows], "total": len(rows)}


@router.get("/notifications/unread-count")
async def commerce_unread_count(db: DB, user: CurrentUser):
    count = await unread_notification_count(db, user.id)
    return {"count": count}


@router.post("/notifications/{notification_id}/read", response_model=PortalNotificationRead)
async def read_commerce_notification(notification_id: uuid.UUID, db: DB, user: CurrentUser):
    try:
        row = await mark_notification_read(db, notification_id, user.id)
        await db.commit()
        await db.refresh(row)
        return PortalNotificationRead.model_validate(row)
    except CommerceMessagingError as exc:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from None


@router.post("/notifications/read-all")
async def read_all_commerce_notifications(db: DB, user: CurrentUser):
    count = await mark_all_notifications_read(db, user.id)
    await db.commit()
    return {"marked_read": count}


@router.get("/orders/{order_id}/thread", response_model=CommerceThreadRead)
async def get_order_thread(order_id: uuid.UUID, db: DB, user: CurrentUser):
    order = await _get_order_or_404(db, order_id)
    if user.role not in ("admin", "super_admin") and not await _order_party(db, user, order):
        raise HTTPException(status_code=403, detail="Not a party to this order")
    row = await get_or_create_thread_for_order(db, order)
    await db.commit()
    await db.refresh(row)
    return CommerceThreadRead.model_validate(row)


@router.get("/threads")
async def list_my_commerce_threads(db: DB, user: CurrentUser):
    stmt = select(CommerceThread).order_by(CommerceThread.created_at.desc()).limit(100)
    rows = list((await db.execute(stmt)).scalars())
    if user.role not in ("admin", "super_admin"):
        if user.company_id is None:
            return {"items": [], "total": 0}
        rows = [thread for thread in rows if await _thread_party(db, user, thread) is not None]
    return {"items": [CommerceThreadRead.model_validate(r) for r in rows], "total": len(rows)}


@router.get("/threads/{thread_id}/messages")
async def list_commerce_thread_messages(thread_id: uuid.UUID, db: DB, user: CurrentUser):
    from app.models.commerce import CommerceThread

    thread = await db.get(CommerceThread, thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")
    if user.role not in ("admin", "super_admin"):
        if await _thread_party(db, user, thread) is None:
            raise HTTPException(status_code=403, detail="Not a participant")
    items = await list_thread_messages(db, thread)
    return {"items": [CommerceMessageRead.model_validate(m) for m in items], "total": len(items)}


@router.post("/threads/{thread_id}/messages", response_model=CommerceMessageRead, status_code=201)
async def post_commerce_thread_message(
    thread_id: uuid.UUID, data: CommerceMessageCreate, db: DB, user: CurrentUser
):
    try:
        row = await post_thread_message(
            db, thread_id=thread_id, user=user, body=data.body, attachments_json=data.attachments_json
        )
        await db.commit()
        await db.refresh(row)
        return CommerceMessageRead.model_validate(row)
    except CommerceMessagingAccessDenied as exc:
        await db.rollback()
        raise HTTPException(status_code=403, detail=str(exc)) from None
    except CommerceMessagingError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None
