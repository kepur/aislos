"""Phase 2 Cebu trade domain — listings, requests, offers, orders (Core-owned)."""
import uuid
from datetime import datetime

from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin

PROCUREMENT_REQUEST_STATUSES = (
    "draft",
    "published",
    "matching",
    "offer_received",
    "awarded",
    "closed",
    "cancelled",
)
OFFER_STATUSES = ("draft", "submitted", "withdrawn", "awarded", "rejected")
ORDER_STATUSES = ("pending", "confirmed", "in_delivery", "completed", "disputed", "cancelled")
DELIVERY_STATUSES = ("scheduled", "shipped", "in_transit", "delivered", "accepted", "failed", "returned")
DISPUTE_STATUSES = ("open", "under_review", "resolved_buyer", "resolved_supplier", "closed", "withdrawn")
RISK_FLAG_STATUSES = ("open", "resolved", "dismissed")
PAYMENT_INTENT_STATUSES = ("draft", "pending", "funded", "completed", "cancelled")
SETTLEMENT_STATUSES = ("pending", "funded", "settled", "reconciled", "mismatch")
RECONCILIATION_STATUSES = ("running", "completed", "failed")

DELIVERY_TRANSITIONS: dict[str, set[str]] = {
    "scheduled": {"shipped", "failed"},
    "shipped": {"in_transit", "failed"},
    "in_transit": {"delivered", "failed"},
    "delivered": {"accepted", "returned", "failed"},
    "accepted": set(),
    "failed": set(),
    "returned": set(),
}


class TradeCategorySchema(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "trade_category_schemas"

    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[int] = mapped_column(default=1, nullable=False)
    schema_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)


class SupplierListing(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "supplier_listings"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True
    )
    region_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regions.id"), nullable=True, index=True
    )
    category_schema_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trade_category_schemas.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    attributes_json: Mapped[dict | None] = mapped_column(JSONB)
    price_minor: Mapped[int | None] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False, index=True)
    legacy_catalog_item_id: Mapped[str | None] = mapped_column(String(120), index=True)


class BuyerWatchlistItem(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "buyer_watchlist_items"
    __table_args__ = (
        UniqueConstraint("buyer_user_id", "supplier_listing_id", name="uq_buyer_watchlist_listing"),
    )

    buyer_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    supplier_listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("supplier_listings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_price_minor: Mapped[int | None] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False, index=True)


class ProcurementRequest(Base, UUIDMixin, TimestampMixin):
    """Cebu Intent equivalent — buyer procurement demand."""

    __tablename__ = "procurement_requests"

    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True, index=True
    )
    buyer_company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True, index=True
    )
    buyer_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    portal_key: Mapped[str] = mapped_column(String(64), default="cebu", nullable=False, index=True)
    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leads.id"), nullable=True, index=True
    )
    category_schema_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trade_category_schemas.id"), nullable=True
    )
    region_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regions.id"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    requirements_json: Mapped[dict | None] = mapped_column(JSONB)
    attrs_json: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    legacy_request_id: Mapped[str | None] = mapped_column(String(120), unique=True, nullable=True)


class SupplierOffer(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "supplier_offers"
    __table_args__ = (
        UniqueConstraint("procurement_request_id", "supplier_company_id", name="uq_offer_per_supplier"),
    )

    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True, index=True
    )
    procurement_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("procurement_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    supplier_listing_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("supplier_listings.id"), nullable=True
    )
    supplier_company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True
    )
    price_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    terms_json: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(50), default="submitted", nullable=False, index=True)
    legacy_offer_id: Mapped[str | None] = mapped_column(String(120), index=True)


class CommerceOrder(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "commerce_orders"

    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True, index=True
    )
    procurement_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("procurement_requests.id"), nullable=False, index=True
    )
    winning_offer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("supplier_offers.id"), nullable=True
    )
    buyer_company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    supplier_company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False, index=True)
    total_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    delivery_json: Mapped[dict | None] = mapped_column(JSONB)
    legacy_order_id: Mapped[str | None] = mapped_column(String(120), unique=True, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class OrderDelivery(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "order_deliveries"

    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True, index=True
    )
    commerce_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("commerce_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    carrier: Mapped[str | None] = mapped_column(String(120))
    tracking_number: Mapped[str | None] = mapped_column(String(120), index=True)
    status: Mapped[str] = mapped_column(String(50), default="scheduled", nullable=False, index=True)
    ship_from_json: Mapped[dict | None] = mapped_column(JSONB)
    ship_to_json: Mapped[dict | None] = mapped_column(JSONB)
    estimated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    proof_json: Mapped[dict | None] = mapped_column(JSONB)
    legacy_delivery_id: Mapped[str | None] = mapped_column(String(120), index=True)


class OrderDispute(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "order_disputes"

    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True, index=True
    )
    commerce_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("commerce_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    opened_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    opened_by_role: Mapped[str] = mapped_column(String(32), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="open", nullable=False, index=True)
    resolution_json: Mapped[dict | None] = mapped_column(JSONB)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    legacy_dispute_id: Mapped[str | None] = mapped_column(String(120), unique=True, nullable=True)


class TrustProfile(Base, UUIDMixin, TimestampMixin):
    """Commerce-side supplier trust (Cebu TrustProfile parity)."""

    __tablename__ = "trust_profiles"
    __table_args__ = (UniqueConstraint("company_id", "portal_key", name="uq_trust_profile_company_portal"),)

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True
    )
    portal_key: Mapped[str] = mapped_column(String(64), default="cebu", nullable=False, index=True)
    completed_orders: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    dispute_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_rating: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    trust_score: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    metrics_json: Mapped[dict | None] = mapped_column(JSONB)


class TrustScoreEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "trust_score_events"

    trust_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trust_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    score_delta: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    before_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    after_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(500))
    related_entity_type: Mapped[str | None] = mapped_column(String(50), index=True)
    related_entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )


class TransactionReview(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "transaction_reviews"
    __table_args__ = (
        UniqueConstraint("commerce_order_id", "reviewer_user_id", name="uq_review_per_buyer_order"),
    )

    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True, index=True
    )
    commerce_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("commerce_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reviewer_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    supplier_company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True, index=True
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="published", nullable=False, index=True)


class RiskFlag(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "risk_flags"

    subject_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True, index=True
    )
    reason_code: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), default="medium", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="open", nullable=False, index=True)
    source_event: Mapped[str | None] = mapped_column(String(120))
    details_json: Mapped[dict | None] = mapped_column(JSONB)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )


class CommercePaymentIntent(Base, UUIDMixin, TimestampMixin):
    """PSP-facing payment intent — links order to PaymentPlan; platform does not hold funds."""

    __tablename__ = "commerce_payment_intents"

    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True, index=True
    )
    commerce_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("commerce_orders.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    payment_plan_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payment_plans.id"), nullable=True, index=True
    )
    psp_provider: Mapped[str] = mapped_column(String(32), default="stripe", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False, index=True)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    quote_currency: Mapped[str | None] = mapped_column(String(3))
    fx_rate: Mapped[Decimal | None] = mapped_column(Numeric(18, 8))
    quote_amount_minor: Mapped[int | None] = mapped_column(BigInteger)
    external_ref: Mapped[str | None] = mapped_column(String(255))


class CommerceThread(Base, UUIDMixin, TimestampMixin):
    """Buyer–supplier business thread (not AI conversation)."""

    __tablename__ = "commerce_threads"

    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True, index=True
    )
    portal_key: Mapped[str] = mapped_column(String(64), default="cebu", nullable=False, index=True)
    procurement_request_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("procurement_requests.id"), nullable=True, index=True
    )
    commerce_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("commerce_orders.id"), nullable=True, index=True
    )
    buyer_company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True, index=True
    )
    supplier_company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True, index=True
    )
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="open", nullable=False, index=True)


class CommerceMessage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "commerce_messages"

    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True, index=True
    )
    thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("commerce_threads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sender_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    sender_role: Mapped[str] = mapped_column(String(32), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    attachments_json: Mapped[dict | None] = mapped_column(JSONB)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CommerceSettlement(Base, UUIDMixin, TimestampMixin):
    """PSP settlement record for a commerce payment — ledger-first, no platform custody."""

    __tablename__ = "commerce_settlements"

    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True, index=True
    )
    commerce_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("commerce_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    payment_intent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("commerce_payment_intents.id"), nullable=True, index=True
    )
    payment_plan_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payment_plans.id"), nullable=True
    )
    milestone_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payment_milestones.id"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False, index=True)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    platform_fee_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    psp_provider: Mapped[str] = mapped_column(String(32), default="stripe", nullable=False)
    external_ref: Mapped[str | None] = mapped_column(String(255))
    psp_settlement_ref: Mapped[str | None] = mapped_column(String(255), index=True)
    funded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reconciled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)


class CommerceReconciliationRun(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "commerce_reconciliation_runs"

    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="running", nullable=False, index=True)
    matched_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mismatch_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pending_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    summary_json: Mapped[dict | None] = mapped_column(JSONB)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
