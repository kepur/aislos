"""2Hands second-hand marketplace — condition, provenance and controlled
pickup-address disclosure.

Extends the shared `supplier_listings` row 1:1 rather than duplicating a
catalogue: a second-hand item is still a listing (same search, orders,
messaging, syndication), it just carries condition/provenance facts and a
pickup address that must not be public.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin

# Cosmetic/functional grade shown to buyers; drives pricing and ad copy.
CONDITION_GRADES = ("A", "B", "C", "D")

FULFILLMENT_MODES = (
    "SELLER_PICKUP",    # buyer collects at the seller's address
    "PICKUP_POINT",     # neutral collection point / locker
    "PARTNER_CHANNEL",  # a channel partner holds and hands over the goods
    "SHIP",             # shipped to the buyer
)

# Provenance identifier — required in the EU for high-value used goods and the
# main defence against re-listing stolen items.
SERIAL_TYPES = ("SERIAL", "IMEI", "VIN", "NONE")

DISCLOSURE_STATUSES = ("requested", "granted", "revoked")

# Records-first: the platform never holds funds. A deal records what the two
# parties agreed and settled directly, which is also the analytics anchor
# ("which SKUs actually sell") once the event spine lands.
DEAL_STATUSES = ("reserved", "picked_up", "cancelled")
PAYMENT_METHODS = ("CASH", "BANK_TRANSFER", "OTHER")


class SecondhandListing(Base, UUIDMixin, TimestampMixin):
    """Second-hand detail for one supplier listing.

    PRIVACY: `pickup_address`, `pickup_note` and `contact_phone` are restricted.
    Public/search endpoints must serialize only `pickup_country/city/area`.
    Full values are released per-buyer via SecondhandAddressDisclosure, which
    records who received what and when.
    """

    __tablename__ = "secondhand_listings"

    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True, index=True
    )
    supplier_listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("supplier_listings.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # ── Condition & provenance ────────────────────────────────────────────
    condition_grade: Mapped[str] = mapped_column(String(2), default="B", nullable=False, index=True)
    purchase_year: Mapped[int | None] = mapped_column(Integer)
    usage_note: Mapped[str | None] = mapped_column(String(255))
    serial_type: Mapped[str] = mapped_column(String(16), default="NONE", nullable=False)
    # Indexed, deliberately NOT unique: an item may legitimately be resold
    # later. Duplicate *active* listings on one serial are flagged in the API.
    serial_no: Mapped[str | None] = mapped_column(String(120), index=True)
    warranty_left_months: Mapped[int | None] = mapped_column(Integer)
    original_packaging: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # [{"type": "scratch", "note": "...", "image_url": "..."}]
    defects_json: Mapped[list | None] = mapped_column(JSONB)
    inspection_json: Mapped[dict | None] = mapped_column(JSONB)

    # ── Fulfilment ────────────────────────────────────────────────────────
    fulfillment_mode: Mapped[str] = mapped_column(
        String(32), default="SELLER_PICKUP", nullable=False, index=True
    )
    pickup_country: Mapped[str | None] = mapped_column(String(2), index=True)
    pickup_city: Mapped[str | None] = mapped_column(String(120), index=True)   # public
    pickup_area: Mapped[str | None] = mapped_column(String(120))               # public, coarse
    pickup_address: Mapped[str | None] = mapped_column(Text)                   # RESTRICTED
    pickup_note: Mapped[str | None] = mapped_column(Text)                      # RESTRICTED
    contact_phone: Mapped[str | None] = mapped_column(String(60))              # RESTRICTED

    # Second-hand stock is unique: selling one must delist it everywhere.
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    sold_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SecondhandAddressDisclosure(Base, UUIDMixin, TimestampMixin):
    """Audit trail for releasing a seller's pickup address to one buyer.

    Written whenever restricted fields are handed over, so a seller can see
    (and revoke) exactly who holds their address — GDPR accountability.
    """

    __tablename__ = "secondhand_address_disclosures"
    __table_args__ = (
        UniqueConstraint(
            "secondhand_listing_id", "buyer_user_id", name="uq_secondhand_disclosure_buyer"
        ),
    )

    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True, index=True
    )
    secondhand_listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("secondhand_listings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    buyer_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    granted_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    commerce_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("commerce_orders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(24), default="requested", nullable=False, index=True)
    disclosed_fields_json: Mapped[list | None] = mapped_column(JSONB)
    granted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reason: Mapped[str | None] = mapped_column(String(255))


class SecondhandDeal(Base, UUIDMixin, TimestampMixin):
    """A C2C second-hand transaction.

    Deliberately NOT a CommerceOrder: that model requires a procurement
    request (B2B RFQ flow) which does not exist here. Records-first — money
    changes hands directly between buyer and seller; this row is the receipt
    trail and the per-SKU sales signal for later analytics.
    """

    __tablename__ = "secondhand_deals"

    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True, index=True
    )
    secondhand_listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("secondhand_listings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Denormalized so SKU-level reporting does not need a second join.
    supplier_listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("supplier_listings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    seller_company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True, index=True
    )
    buyer_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agreed_price_minor: Mapped[int | None] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    fulfillment_mode: Mapped[str] = mapped_column(String(32), default="SELLER_PICKUP", nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="reserved", nullable=False, index=True)
    payment_method: Mapped[str | None] = mapped_column(String(24))
    payment_reference: Mapped[str | None] = mapped_column(String(255))
    picked_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    note: Mapped[str | None] = mapped_column(Text)
