import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin


class CertificationRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "certification_records"

    owner_type: Mapped[str] = mapped_column(String(50), nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    certification_name: Mapped[str] = mapped_column(String(255), nullable=False)
    issuer: Mapped[str | None] = mapped_column(String(255))
    country: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), default="planned", nullable=False)
    issue_date: Mapped[date | None] = mapped_column(Date)
    expiry_date: Mapped[date | None] = mapped_column(Date)
    certificate_file_url: Mapped[str | None] = mapped_column(String(500))
    public_visible: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text)


class WarrantyPolicy(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "warranty_policies"

    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=True
    )
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    region: Mapped[str | None] = mapped_column(String(100))
    manufacturer_warranty_months: Mapped[int | None] = mapped_column(Integer)
    platform_support_months: Mapped[int | None] = mapped_column(Integer)
    local_installation_warranty_months: Mapped[int | None] = mapped_column(Integer)
    spare_parts_policy_json: Mapped[dict | None] = mapped_column(JSONB)
    response_sla_json: Mapped[dict | None] = mapped_column(JSONB)
    exclusions_text: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
