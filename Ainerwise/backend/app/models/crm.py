"""CRM models (FI.6.6).

SupplierScorecard rates a supplier (company) across the long-term-fit
dimensions that matter for a recurring-revenue platform: quality, delivery,
response, warranty cooperation, documentation, price stability, and overall
long-term fit. `overall_score` is recomputed from the dimensions on save.
"""
import uuid

from sqlalchemy import Float, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin


SCORECARD_DIMENSIONS = (
    "quality",
    "delivery",
    "response",
    "warranty_cooperation",
    "documentation",
    "price_stability",
    "long_term_fit",
)


class SupplierScorecard(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "supplier_scorecards"

    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    supplier_name: Mapped[str | None] = mapped_column(Text)
    quality: Mapped[int | None] = mapped_column(Integer)  # 1-5
    delivery: Mapped[int | None] = mapped_column(Integer)
    response: Mapped[int | None] = mapped_column(Integer)
    warranty_cooperation: Mapped[int | None] = mapped_column(Integer)
    documentation: Mapped[int | None] = mapped_column(Integer)
    price_stability: Mapped[int | None] = mapped_column(Integer)
    long_term_fit: Mapped[int | None] = mapped_column(Integer)
    overall_score: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text)
