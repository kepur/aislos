import uuid
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin

PROPERTY_TYPES = ("villa", "apartment", "office", "hotel", "factory", "retail", "other")


class CaseStudy(Base, UUIDMixin, TimestampMixin):
    """Structured delivered-project case: sales weapon + moat asset.

    Margin fields are internal-only — never exposed on public reads.
    The summary is embedded into the knowledge base (source_type=case_study)
    so consult/RAG can cite similar cases.
    """

    __tablename__ = "cases"

    region_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("regions.id"))
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    country: Mapped[str | None] = mapped_column(String(100))
    city: Mapped[str | None] = mapped_column(String(100))
    property_type: Mapped[str | None] = mapped_column(String(50), index=True)
    area_sqm: Mapped[int | None] = mapped_column(Integer)
    budget: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(10), default="EUR", nullable=False)
    products_json: Mapped[list | None] = mapped_column(JSONB)
    partner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("service_partners.id"))
    duration_days: Mapped[int | None] = mapped_column(Integer)
    gross_margin_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    rework_count: Mapped[int | None] = mapped_column(Integer)
    satisfaction_score: Mapped[Decimal | None] = mapped_column(Numeric(2, 1))
    ai_summary: Mapped[str | None] = mapped_column(Text)
    photos_json: Mapped[list | None] = mapped_column(JSONB)
    customer_feedback: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    public_visible: Mapped[bool] = mapped_column(Boolean, default=False)
    embedding_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai.knowledge_documents.id")
    )
