import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin

RFQ_STATUSES = ("draft", "inviting", "bidding", "evaluating", "awarded", "cancelled")
RFQ_TRADES = ("knx", "electrical", "solar", "security", "hvac", "network", "general")
INVITATION_STATUSES = ("sent", "viewed", "declined", "bid_submitted", "expired")
BID_STATUSES = ("submitted", "shortlisted", "awarded", "rejected", "withdrawn")


class RFQ(Base, UUIDMixin, TimestampMixin):
    """Request-for-quote: one trade package sent to matching partners."""

    __tablename__ = "rfqs"

    region_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("regions.id"))
    lead_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("leads.id"), index=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), index=True)
    solution_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("solutions.id"))
    trade: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    scope_json: Mapped[dict | None] = mapped_column(JSONB)
    budget_hint: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(10), default="EUR", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False, index=True)
    bid_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    awarded_bid_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    # Procurement Phase 1 (C07) — nullable for legacy RFQs
    procurement_package_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("procurement_packages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    commercial_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("commercial_snapshots.id", ondelete="RESTRICT"),
        nullable=True,
    )
    portal_key: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    revision: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "procurement_package_id",
            "revision",
            name="uq_rfqs_procurement_package_revision",
        ),
    )


class RFQInvitation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "rfq_invitations"
    __table_args__ = (
        UniqueConstraint("rfq_id", "partner_id", name="uq_rfq_invitations_rfq_partner"),
    )

    rfq_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rfqs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("service_partners.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(50), default="sent", nullable=False)
    sent_via: Mapped[str | None] = mapped_column(String(50))
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PartnerBid(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "partner_bids"

    rfq_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rfqs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("service_partners.id"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="EUR", nullable=False)
    lead_time_days: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    attachments_json: Mapped[list | None] = mapped_column(JSONB)
    ai_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    ai_score_breakdown_json: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(50), default="submitted", nullable=False, index=True)


class PartnerMetricSnapshot(Base, UUIDMixin, TimestampMixin):
    """Append-only daily history of partner scores — the time series the
    future Risk Engine reads ("score declining three runs in a row").
    Never updated, never deleted: lost days cannot be backfilled."""

    __tablename__ = "partner_metric_snapshots"
    __table_args__ = (
        Index("ix_partner_metric_snapshots_partner_date", "partner_id", "snapshot_date"),
    )

    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("service_partners.id"), nullable=False, index=True
    )
    composite_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    breakdown_json: Mapped[dict | None] = mapped_column(JSONB)
    snapshot_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PartnerMetric(Base, UUIDMixin, TimestampMixin):
    """Daily-recomputed composite partner score feeding RFQ ranking."""

    __tablename__ = "partner_metrics"

    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("service_partners.id"), nullable=False, unique=True
    )
    response_hours_avg: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    completion_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    cancellation_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    on_time_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    warranty_claim_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    customer_review_avg: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    revenue_total: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    ai_risk_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    composite_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), index=True)
    breakdown_json: Mapped[dict | None] = mapped_column(JSONB)
    computed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
