import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin


class ServicePackage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "service_packages"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    years: Mapped[int | None] = mapped_column(Integer)
    description: Mapped[str | None] = mapped_column(Text)
    included_services_json: Mapped[list | None] = mapped_column(JSONB)
    sla_json: Mapped[dict | None] = mapped_column(JSONB)
    price_rule_json: Mapped[dict | None] = mapped_column(JSONB)
    public_visible: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    language_content_json: Mapped[dict | None] = mapped_column(JSONB)


class ServicePartner(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "service_partners"

    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    partner_type: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str | None] = mapped_column(String(100))
    city: Mapped[str | None] = mapped_column(String(100))
    service_radius_km: Mapped[int | None] = mapped_column(Integer)
    languages_json: Mapped[list | None] = mapped_column(JSONB)
    skills_json: Mapped[list | None] = mapped_column(JSONB)
    certifications_json: Mapped[list | None] = mapped_column(JSONB)
    hourly_rate: Mapped[float | None] = mapped_column(Float)
    day_rate: Mapped[float | None] = mapped_column(Float)
    project_rate_rule_json: Mapped[dict | None] = mapped_column(JSONB)
    availability_status: Mapped[str] = mapped_column(String(50), default="available")
    rating_internal: Mapped[float | None] = mapped_column(Float)
    public_visible: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_status: Mapped[str] = mapped_column(String(50), default="pending")
    telegram_chat_id: Mapped[str | None] = mapped_column(String(100))
    stripe_account_id: Mapped[str | None] = mapped_column(String(255))  # Connect (Phase E)
    notes_internal: Mapped[str | None] = mapped_column(Text)


class PartnerCapability(Base, UUIDMixin, TimestampMixin):
    """Structured partner skills for procurement package matching (C06)."""

    __tablename__ = "partner_capabilities"

    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("service_partners.id", ondelete="CASCADE"), nullable=False, index=True
    )
    trade: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    capability_keys_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    supported_regions_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    supply: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    install: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    maintain: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    verification_status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
