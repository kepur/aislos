import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin

PLAN_STATUSES = ("draft", "active", "completed", "cancelled")
MILESTONE_STATUSES = ("pending", "invoiced", "funded", "released", "refunded")
MILESTONE_TRIGGERS = ("on_accept", "on_schedule", "on_acceptance", "days_after_acceptance")
DEPOSIT_STATUSES = ("requested", "held", "partially_forfeited", "refunded")

# Ledger accounts are strings: customer:{id} | partner:{id} | platform:revenue
# | escrow:psp | bank:offline — "wallets" are views over this ledger; real money
# never sits in our system (PSD2/NBS licensing).


class PaymentPlan(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "payment_plans"

    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), index=True)
    quote_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("quotes.id"))
    currency: Mapped[str] = mapped_column(String(10), default="EUR", nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    retention_pct: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    retention_release_days: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class PaymentMilestone(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "payment_milestones"

    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payment_plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    trigger: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False, index=True)
    funded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    release_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    external_ref: Mapped[str | None] = mapped_column(String(255))


class LedgerEntry(Base, UUIDMixin, TimestampMixin):
    """Double-entry bookkeeping. Every business movement writes a balanced
    group of entries (same entry_group); money itself stays at the bank/PSP."""

    __tablename__ = "ledger_entries"

    entry_group: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    account: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)  # debit|credit
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="EUR", nullable=False)
    milestone_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payment_milestones.id"), index=True
    )
    memo: Mapped[str | None] = mapped_column(Text)


class PartnerDeposit(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "partner_deposits"

    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("service_partners.id"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="EUR", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="requested", nullable=False)
    external_ref: Mapped[str | None] = mapped_column(String(255))
    forfeiture_log_json: Mapped[list | None] = mapped_column(JSONB)
