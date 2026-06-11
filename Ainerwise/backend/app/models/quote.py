import uuid
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin


QUOTE_STATUSES = (
    "draft", "internal_review", "sent", "client_questions",
    "revised", "accepted", "rejected", "expired",
)


class Quote(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "quotes"

    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leads.id"), nullable=True
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True
    )
    quote_items_json: Mapped[list | None] = mapped_column(JSONB)
    device_total: Mapped[float] = mapped_column(Float, default=0)
    service_total: Mapped[float] = mapped_column(Float, default=0)
    platform_fee: Mapped[float] = mapped_column(Float, default=0)
    support_package_fee: Mapped[float] = mapped_column(Float, default=0)
    spare_parts_fee: Mapped[float] = mapped_column(Float, default=0)
    logistics_fee: Mapped[float] = mapped_column(Float, default=0)
    tax_fee: Mapped[float] = mapped_column(Float, default=0)
    discount: Mapped[float] = mapped_column(Float, default=0)
    total: Mapped[float] = mapped_column(Float, default=0)
    currency: Mapped[str] = mapped_column(String(10), default="EUR")
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)
    valid_until: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column()

    # FI.4.4 — customer-facing packaged line items (no supplier cost / model).
    customer_line_items_json: Mapped[list | None] = mapped_column(JSONB)
    # FI.4.5 — admin-only internal economics (supplier, real model, cost, margin,
    # lead time, warranty, alternatives, risk, recommended spares). NEVER exposed
    # on QuoteRead / customer PDF.
    internal_economics_json: Mapped[dict | None] = mapped_column(JSONB)
    first_year_total: Mapped[float] = mapped_column(Float, default=0)
    annual_recurring_total: Mapped[float] = mapped_column(Float, default=0)
