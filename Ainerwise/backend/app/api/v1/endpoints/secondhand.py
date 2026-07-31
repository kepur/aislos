"""2Hands second-hand marketplace API.

Design rules enforced here:
  * PRIVACY — a seller's pickup address/phone are never returned by public or
    listing endpoints. They are released per-buyer only after the seller grants
    a disclosure, and every release is written to an audit trail the seller can
    inspect and revoke.
  * RECORDS-FIRST — the platform never holds funds. Buyer and seller settle
    directly (usually cash at pickup); a deal row records what happened.
  * UNIQUE STOCK — a second-hand item is one physical object. Selling it marks
    the listing sold so it can be delisted everywhere (channel fan-out lands
    in P1).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.api.deps import DB, CurrentUser
from app.models.commerce import SupplierListing, TradeCategorySchema
from app.models.secondhand import (
    CONDITION_GRADES,
    FULFILLMENT_MODES,
    PAYMENT_METHODS,
    SERIAL_TYPES,
    SecondhandAddressDisclosure,
    SecondhandDeal,
    SecondhandListing,
)
from app.models.user import Company, User

router = APIRouter(prefix="/secondhand", tags=["secondhand"])

SECONDHAND_CATEGORY_SLUG = "2hands"
RESTRICTED_FIELDS = ("address", "phone", "note")


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ─────────────────────────── payloads ────────────────────────────


class DefectIn(BaseModel):
    type: str | None = None
    note: str | None = None
    image_url: str | None = None


class ListingCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: str | None = None
    price_minor: int = Field(ge=0)
    currency: str = Field(default="EUR", max_length=3)
    images: list[str] = Field(default_factory=list)
    category_id: uuid.UUID | None = None

    condition_grade: str = "B"
    purchase_year: int | None = None
    usage_note: str | None = None
    serial_type: str = "NONE"
    serial_no: str | None = None
    warranty_left_months: int | None = None
    original_packaging: bool = False
    defects: list[DefectIn] = Field(default_factory=list)

    fulfillment_mode: str = "SELLER_PICKUP"
    pickup_country: str | None = Field(default=None, max_length=2)
    pickup_city: str | None = None
    pickup_area: str | None = None
    # Restricted — stored but never returned publicly.
    pickup_address: str | None = None
    pickup_note: str | None = None
    contact_phone: str | None = None


class ListingUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    price_minor: int | None = None
    images: list[str] | None = None
    condition_grade: str | None = None
    usage_note: str | None = None
    warranty_left_months: int | None = None
    original_packaging: bool | None = None
    defects: list[DefectIn] | None = None
    fulfillment_mode: str | None = None
    pickup_country: str | None = None
    pickup_city: str | None = None
    pickup_area: str | None = None
    pickup_address: str | None = None
    pickup_note: str | None = None
    contact_phone: str | None = None


class DisclosureRequest(BaseModel):
    message: str | None = Field(default=None, max_length=255)


class DisclosureGrant(BaseModel):
    fields: list[str] = Field(default_factory=lambda: ["address", "phone"])
    reason: str | None = None


class DealCreate(BaseModel):
    agreed_price_minor: int | None = None
    note: str | None = None


class PickupConfirm(BaseModel):
    payment_method: str = "CASH"
    payment_reference: str | None = None
    agreed_price_minor: int | None = None
    note: str | None = None


# ─────────────────────────── serializers ─────────────────────────


def _public_listing(listing: SupplierListing, detail: SecondhandListing, company_name: str | None) -> dict:
    """PUBLIC shape. Never includes pickup_address / pickup_note / contact_phone."""
    attrs = listing.attributes_json if isinstance(listing.attributes_json, dict) else {}
    return {
        "id": listing.id,
        "detail_id": detail.id,
        "title": listing.title,
        "description": attrs.get("description"),
        "images": attrs.get("images") or [],
        "price_minor": listing.price_minor or 0,
        "currency": listing.currency,
        "status": listing.status,
        "category_id": listing.category_schema_id,
        "seller_company_id": listing.company_id,
        "seller_name": company_name,
        "condition_grade": detail.condition_grade,
        "purchase_year": detail.purchase_year,
        "usage_note": detail.usage_note,
        "serial_type": detail.serial_type,
        "has_serial": bool(detail.serial_no),
        "warranty_left_months": detail.warranty_left_months,
        "original_packaging": detail.original_packaging,
        "defects": detail.defects_json or [],
        "fulfillment_mode": detail.fulfillment_mode,
        # Coarse location only — the exact address needs a disclosure.
        "pickup_country": detail.pickup_country,
        "pickup_city": detail.pickup_city,
        "pickup_area": detail.pickup_area,
        "quantity": detail.quantity,
        "sold_at": detail.sold_at,
        "created_at": listing.created_at,
    }


def _pickup_details(detail: SecondhandListing, disclosed: list[str]) -> dict:
    """RESTRICTED shape — only after a granted disclosure, only granted fields."""
    out: dict = {"listing_id": detail.supplier_listing_id, "disclosed_fields": disclosed}
    if "address" in disclosed:
        out["pickup_address"] = detail.pickup_address
    if "note" in disclosed:
        out["pickup_note"] = detail.pickup_note
    if "phone" in disclosed:
        out["contact_phone"] = detail.contact_phone
    return out


def _deal_as_dict(deal: SecondhandDeal) -> dict:
    return {
        "id": deal.id,
        "listing_id": deal.supplier_listing_id,
        "buyer_user_id": deal.buyer_user_id,
        "seller_company_id": deal.seller_company_id,
        "agreed_price_minor": deal.agreed_price_minor,
        "currency": deal.currency,
        "status": deal.status,
        "fulfillment_mode": deal.fulfillment_mode,
        "payment_method": deal.payment_method,
        "payment_reference": deal.payment_reference,
        "picked_up_at": deal.picked_up_at,
        "created_at": deal.created_at,
    }


# ─────────────────────────── helpers ─────────────────────────────


async def _load_pair(db: DB, listing_id: uuid.UUID) -> tuple[SupplierListing, SecondhandListing]:
    row = (
        await db.execute(
            select(SupplierListing, SecondhandListing)
            .join(SecondhandListing, SecondhandListing.supplier_listing_id == SupplierListing.id)
            .where(SupplierListing.id == listing_id)
        )
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    return row[0], row[1]


def _require_seller(listing: SupplierListing, user: User) -> None:
    if not user.company_id or listing.company_id != user.company_id:
        raise HTTPException(status_code=403, detail="Only the seller can perform this action")


async def _secondhand_category_id(db: DB) -> uuid.UUID | None:
    return (
        await db.execute(
            select(TradeCategorySchema.id).where(TradeCategorySchema.slug == SECONDHAND_CATEGORY_SLUG)
        )
    ).scalar_one_or_none()


# ─────────────────────────── public browse ───────────────────────


@router.get("/listings")
async def browse_listings(
    db: DB,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=24, ge=1, le=100),
    keyword: str | None = None,
    category_id: uuid.UUID | None = None,
    condition: str | None = None,
    city: str | None = None,
    country: str | None = None,
    price_min_minor: int | None = None,
    price_max_minor: int | None = None,
    sort: str = Query(default="newest"),
):
    stmt = (
        select(SupplierListing, SecondhandListing, Company.name)
        .join(SecondhandListing, SecondhandListing.supplier_listing_id == SupplierListing.id)
        .join(Company, Company.id == SupplierListing.company_id, isouter=True)
        .where(SupplierListing.status == "active")
    )
    if keyword:
        stmt = stmt.where(SupplierListing.title.ilike(f"%{keyword.strip()}%"))
    if category_id:
        stmt = stmt.where(SupplierListing.category_schema_id == category_id)
    if condition:
        stmt = stmt.where(SecondhandListing.condition_grade == condition.upper()[:2])
    if city:
        stmt = stmt.where(SecondhandListing.pickup_city.ilike(city.strip()))
    if country:
        stmt = stmt.where(SecondhandListing.pickup_country == country.upper()[:2])
    if price_min_minor is not None:
        stmt = stmt.where(SupplierListing.price_minor >= price_min_minor)
    if price_max_minor is not None:
        stmt = stmt.where(SupplierListing.price_minor <= price_max_minor)

    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar() or 0

    order = {
        "newest": SupplierListing.created_at.desc(),
        "price_asc": SupplierListing.price_minor.asc(),
        "price_desc": SupplierListing.price_minor.desc(),
        "condition": SecondhandListing.condition_grade.asc(),
    }.get(sort, SupplierListing.created_at.desc())

    rows = list(
        (await db.execute(stmt.order_by(order).offset((page - 1) * page_size).limit(page_size))).all()
    )
    items = [_public_listing(listing, detail, name) for listing, detail, name in rows]
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_next": (page - 1) * page_size + len(items) < total,
    }


@router.get("/listings/{listing_id}")
async def listing_detail(listing_id: uuid.UUID, db: DB):
    listing, detail = await _load_pair(db, listing_id)
    company_name = (
        await db.execute(select(Company.name).where(Company.id == listing.company_id))
    ).scalar_one_or_none()
    return _public_listing(listing, detail, company_name)


# ─────────────────────────── seller: listings ────────────────────


@router.post("/listings", status_code=201)
async def create_listing(data: ListingCreate, db: DB, user: CurrentUser):
    if not user.company_id:
        raise HTTPException(
            status_code=409,
            detail="A seller profile is required before listing. Complete your seller registration first.",
        )
    if data.condition_grade.upper() not in CONDITION_GRADES:
        raise HTTPException(status_code=422, detail=f"condition_grade must be one of {CONDITION_GRADES}")
    if data.fulfillment_mode not in FULFILLMENT_MODES:
        raise HTTPException(status_code=422, detail=f"fulfillment_mode must be one of {FULFILLMENT_MODES}")
    if data.serial_type not in SERIAL_TYPES:
        raise HTTPException(status_code=422, detail=f"serial_type must be one of {SERIAL_TYPES}")

    # Anti-theft / anti-duplicate: the same serial must not be live twice.
    if data.serial_no:
        clash = (
            await db.execute(
                select(SecondhandListing.id)
                .join(SupplierListing, SupplierListing.id == SecondhandListing.supplier_listing_id)
                .where(
                    SecondhandListing.serial_no == data.serial_no.strip(),
                    SupplierListing.status == "active",
                )
            )
        ).scalar_one_or_none()
        if clash is not None:
            raise HTTPException(
                status_code=409,
                detail="An active listing already exists for this serial number.",
            )

    category_id = data.category_id or await _secondhand_category_id(db)
    listing = SupplierListing(
        company_id=user.company_id,
        category_schema_id=category_id,
        title=data.title.strip(),
        price_minor=data.price_minor,
        currency=(data.currency or "EUR").upper(),
        status="active",
        attributes_json={
            "description": data.description,
            "images": data.images,
            "market_mode": "C2C",
            "secondhand": True,
        },
    )
    db.add(listing)
    await db.flush()

    detail = SecondhandListing(
        supplier_listing_id=listing.id,
        condition_grade=data.condition_grade.upper(),
        purchase_year=data.purchase_year,
        usage_note=data.usage_note,
        serial_type=data.serial_type,
        serial_no=(data.serial_no or "").strip() or None,
        warranty_left_months=data.warranty_left_months,
        original_packaging=data.original_packaging,
        defects_json=[d.model_dump() for d in data.defects],
        fulfillment_mode=data.fulfillment_mode,
        pickup_country=(data.pickup_country or "").upper()[:2] or None,
        pickup_city=data.pickup_city,
        pickup_area=data.pickup_area,
        pickup_address=data.pickup_address,
        pickup_note=data.pickup_note,
        contact_phone=data.contact_phone,
        quantity=1,
    )
    db.add(detail)
    await db.commit()
    await db.refresh(listing)
    await db.refresh(detail)
    return _public_listing(listing, detail, None)


@router.patch("/listings/{listing_id}")
async def update_listing(listing_id: uuid.UUID, data: ListingUpdate, db: DB, user: CurrentUser):
    listing, detail = await _load_pair(db, listing_id)
    _require_seller(listing, user)
    if detail.sold_at is not None:
        raise HTTPException(status_code=409, detail="A sold item can no longer be edited")

    attrs = dict(listing.attributes_json or {})
    if data.title is not None:
        listing.title = data.title.strip()
    if data.price_minor is not None:
        listing.price_minor = data.price_minor
    if data.description is not None:
        attrs["description"] = data.description
    if data.images is not None:
        attrs["images"] = data.images
    listing.attributes_json = attrs

    for field in (
        "condition_grade", "usage_note", "warranty_left_months", "original_packaging",
        "fulfillment_mode", "pickup_country", "pickup_city", "pickup_area",
        "pickup_address", "pickup_note", "contact_phone",
    ):
        value = getattr(data, field)
        if value is not None:
            setattr(detail, field, value)
    if data.defects is not None:
        detail.defects_json = [d.model_dump() for d in data.defects]

    await db.commit()
    await db.refresh(listing)
    await db.refresh(detail)
    return _public_listing(listing, detail, None)


@router.get("/me/listings")
async def my_listings(db: DB, user: CurrentUser):
    if not user.company_id:
        return {"items": [], "total": 0}
    rows = list(
        (
            await db.execute(
                select(SupplierListing, SecondhandListing)
                .join(SecondhandListing, SecondhandListing.supplier_listing_id == SupplierListing.id)
                .where(SupplierListing.company_id == user.company_id)
                .order_by(SupplierListing.created_at.desc())
            )
        ).all()
    )
    items = [_public_listing(listing, detail, None) for listing, detail in rows]
    return {"items": items, "total": len(items)}


# ─────────────────────── address disclosure ──────────────────────


@router.post("/listings/{listing_id}/disclosure-request", status_code=201)
async def request_disclosure(
    listing_id: uuid.UUID, data: DisclosureRequest, db: DB, user: CurrentUser
):
    """Buyer signals intent and asks for the pickup address."""
    listing, detail = await _load_pair(db, listing_id)
    if user.company_id and listing.company_id == user.company_id:
        raise HTTPException(status_code=409, detail="You cannot request your own listing")
    if detail.sold_at is not None:
        raise HTTPException(status_code=409, detail="This item is already sold")

    existing = (
        await db.execute(
            select(SecondhandAddressDisclosure).where(
                SecondhandAddressDisclosure.secondhand_listing_id == detail.id,
                SecondhandAddressDisclosure.buyer_user_id == user.id,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        # Re-asking after a revoke reopens the request; a live grant stands.
        if existing.status == "revoked":
            existing.status = "requested"
            existing.reason = data.message
            existing.revoked_at = None
            await db.commit()
            await db.refresh(existing)
        return {"id": existing.id, "status": existing.status}

    row = SecondhandAddressDisclosure(
        secondhand_listing_id=detail.id,
        buyer_user_id=user.id,
        status="requested",
        reason=data.message,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return {"id": row.id, "status": row.status}


@router.get("/listings/{listing_id}/disclosures")
async def list_disclosures(listing_id: uuid.UUID, db: DB, user: CurrentUser):
    """Seller view: who asked for / holds my address."""
    listing, detail = await _load_pair(db, listing_id)
    _require_seller(listing, user)
    rows = list(
        (
            await db.execute(
                select(SecondhandAddressDisclosure, User.full_name, User.email)
                .join(User, User.id == SecondhandAddressDisclosure.buyer_user_id)
                .where(SecondhandAddressDisclosure.secondhand_listing_id == detail.id)
                .order_by(SecondhandAddressDisclosure.created_at.desc())
            )
        ).all()
    )
    return {
        "items": [
            {
                "id": row.id,
                "buyer_user_id": row.buyer_user_id,
                "buyer_name": full_name or email,
                "status": row.status,
                "message": row.reason,
                "disclosed_fields": row.disclosed_fields_json or [],
                "granted_at": row.granted_at,
                "revoked_at": row.revoked_at,
                "requested_at": row.created_at,
            }
            for row, full_name, email in rows
        ]
    }


@router.post("/disclosures/{disclosure_id}/grant")
async def grant_disclosure(
    disclosure_id: uuid.UUID, data: DisclosureGrant, db: DB, user: CurrentUser
):
    """Seller releases the address to one buyer. Audited and revocable."""
    row = await db.get(SecondhandAddressDisclosure, disclosure_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Disclosure not found")
    detail = await db.get(SecondhandListing, row.secondhand_listing_id)
    listing = await db.get(SupplierListing, detail.supplier_listing_id)
    _require_seller(listing, user)

    fields = [f for f in data.fields if f in RESTRICTED_FIELDS] or ["address"]
    row.status = "granted"
    row.disclosed_fields_json = fields
    row.granted_at = _now()
    row.revoked_at = None
    row.granted_by_user_id = user.id
    if data.reason:
        row.reason = data.reason
    await db.commit()
    await db.refresh(row)
    return {"id": row.id, "status": row.status, "disclosed_fields": fields}


@router.post("/disclosures/{disclosure_id}/revoke")
async def revoke_disclosure(disclosure_id: uuid.UUID, db: DB, user: CurrentUser):
    row = await db.get(SecondhandAddressDisclosure, disclosure_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Disclosure not found")
    detail = await db.get(SecondhandListing, row.secondhand_listing_id)
    listing = await db.get(SupplierListing, detail.supplier_listing_id)
    _require_seller(listing, user)

    row.status = "revoked"
    row.revoked_at = _now()
    await db.commit()
    return {"id": row.id, "status": row.status}


@router.get("/listings/{listing_id}/my-disclosure")
async def my_disclosure_state(listing_id: uuid.UUID, db: DB, user: CurrentUser):
    """Buyer's own view of where their address request stands.

    Read-only so the UI can render the right call to action without POSTing.
    """
    listing, detail = await _load_pair(db, listing_id)
    if user.company_id and listing.company_id == user.company_id:
        return {"role": "seller", "status": "owner"}

    row = (
        await db.execute(
            select(SecondhandAddressDisclosure).where(
                SecondhandAddressDisclosure.secondhand_listing_id == detail.id,
                SecondhandAddressDisclosure.buyer_user_id == user.id,
            )
        )
    ).scalar_one_or_none()
    deal = (
        await db.execute(
            select(SecondhandDeal).where(
                SecondhandDeal.secondhand_listing_id == detail.id,
                SecondhandDeal.buyer_user_id == user.id,
                SecondhandDeal.status.in_(("reserved", "picked_up")),
            )
        )
    ).scalar_one_or_none()
    return {
        "role": "buyer",
        "status": row.status if row else "none",
        "disclosure_id": row.id if row else None,
        "disclosed_fields": (row.disclosed_fields_json or []) if row else [],
        "deal": _deal_as_dict(deal) if deal else None,
    }


@router.get("/listings/{listing_id}/pickup-details")
async def get_pickup_details(listing_id: uuid.UUID, db: DB, user: CurrentUser):
    """Restricted fields. 403 unless this buyer holds a live grant (or is the seller)."""
    listing, detail = await _load_pair(db, listing_id)

    if user.company_id and listing.company_id == user.company_id:
        return _pickup_details(detail, list(RESTRICTED_FIELDS))

    row = (
        await db.execute(
            select(SecondhandAddressDisclosure).where(
                SecondhandAddressDisclosure.secondhand_listing_id == detail.id,
                SecondhandAddressDisclosure.buyer_user_id == user.id,
                SecondhandAddressDisclosure.status == "granted",
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=403,
            detail="The seller has not released the pickup address to you yet.",
        )
    return _pickup_details(detail, row.disclosed_fields_json or ["address"])


# ─────────────────────────── deals & pickup ──────────────────────


@router.post("/listings/{listing_id}/reserve", status_code=201)
async def reserve(listing_id: uuid.UUID, data: DealCreate, db: DB, user: CurrentUser):
    """Buyer and seller agreed — hold the item pending pickup."""
    listing, detail = await _load_pair(db, listing_id)
    if detail.sold_at is not None:
        raise HTTPException(status_code=409, detail="This item is already sold")
    if user.company_id and listing.company_id == user.company_id:
        raise HTTPException(status_code=409, detail="You cannot reserve your own listing")

    live = (
        await db.execute(
            select(SecondhandDeal).where(
                SecondhandDeal.secondhand_listing_id == detail.id,
                SecondhandDeal.status.in_(("reserved", "picked_up")),
            )
        )
    ).scalar_one_or_none()
    if live is not None:
        raise HTTPException(status_code=409, detail="This item is already reserved")

    deal = SecondhandDeal(
        secondhand_listing_id=detail.id,
        supplier_listing_id=listing.id,
        seller_company_id=listing.company_id,
        buyer_user_id=user.id,
        agreed_price_minor=data.agreed_price_minor if data.agreed_price_minor is not None else listing.price_minor,
        currency=listing.currency,
        fulfillment_mode=detail.fulfillment_mode,
        status="reserved",
        note=data.note,
    )
    db.add(deal)
    await db.commit()
    await db.refresh(deal)
    return _deal_as_dict(deal)


@router.post("/deals/{deal_id}/confirm-pickup")
async def confirm_pickup(deal_id: uuid.UUID, data: PickupConfirm, db: DB, user: CurrentUser):
    """Buyer confirms collection and records how they paid the seller directly.

    The platform holds no funds — this only writes the receipt trail and
    marks the unique item sold.
    """
    deal = await db.get(SecondhandDeal, deal_id)
    if deal is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    listing = await db.get(SupplierListing, deal.supplier_listing_id)
    is_seller = bool(user.company_id and listing.company_id == user.company_id)
    if deal.buyer_user_id != user.id and not is_seller:
        raise HTTPException(status_code=403, detail="Only the buyer or seller can confirm this pickup")
    if deal.status == "cancelled":
        raise HTTPException(status_code=409, detail="This deal was cancelled")
    if data.payment_method not in PAYMENT_METHODS:
        raise HTTPException(status_code=422, detail=f"payment_method must be one of {PAYMENT_METHODS}")

    if deal.status != "picked_up":
        deal.status = "picked_up"
        deal.picked_up_at = _now()
    deal.payment_method = data.payment_method
    deal.payment_reference = data.payment_reference
    if data.agreed_price_minor is not None:
        deal.agreed_price_minor = data.agreed_price_minor
    if data.note:
        deal.note = data.note

    # Unique stock: mark sold so it can be delisted everywhere (P1 fan-out).
    detail = await db.get(SecondhandListing, deal.secondhand_listing_id)
    detail.sold_at = detail.sold_at or _now()
    listing.status = "sold"

    await db.commit()
    await db.refresh(deal)
    return _deal_as_dict(deal)


@router.post("/deals/{deal_id}/cancel")
async def cancel_deal(deal_id: uuid.UUID, db: DB, user: CurrentUser):
    deal = await db.get(SecondhandDeal, deal_id)
    if deal is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    listing = await db.get(SupplierListing, deal.supplier_listing_id)
    is_seller = bool(user.company_id and listing.company_id == user.company_id)
    if deal.buyer_user_id != user.id and not is_seller:
        raise HTTPException(status_code=403, detail="Only the buyer or seller can cancel this deal")
    if deal.status == "picked_up":
        raise HTTPException(status_code=409, detail="A completed pickup cannot be cancelled")

    deal.status = "cancelled"
    deal.cancelled_at = _now()
    await db.commit()
    return _deal_as_dict(deal)


@router.get("/me/deals")
async def my_deals(db: DB, user: CurrentUser):
    """Both sides of the table: what I am buying and what I am selling."""
    buying = list(
        (
            await db.execute(
                select(SecondhandDeal)
                .where(SecondhandDeal.buyer_user_id == user.id)
                .order_by(SecondhandDeal.created_at.desc())
            )
        ).scalars()
    )
    selling: list[SecondhandDeal] = []
    if user.company_id:
        selling = list(
            (
                await db.execute(
                    select(SecondhandDeal)
                    .where(SecondhandDeal.seller_company_id == user.company_id)
                    .order_by(SecondhandDeal.created_at.desc())
                )
            ).scalars()
        )
    return {
        "buying": [_deal_as_dict(d) for d in buying],
        "selling": [_deal_as_dict(d) for d in selling],
    }
