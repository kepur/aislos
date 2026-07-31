"""Shared supplier branch and service coverage models."""
import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin


class CompanyBranch(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "company_branches"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str | None] = mapped_column(Text)
    lat: Mapped[float | None] = mapped_column(Float)
    lng: Mapped[float | None] = mapped_column(Float)
    radius_km: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    delivery_methods_json: Mapped[list | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False, index=True)


class ServiceArea(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "service_areas"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    region_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regions.id"), nullable=True, index=True
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True
    )
    coverage_type: Mapped[str] = mapped_column(String(32), default="RADIUS", nullable=False)
    center_lat: Mapped[float | None] = mapped_column(Float)
    center_lng: Mapped[float | None] = mapped_column(Float)
    radius_km: Mapped[int | None] = mapped_column(Integer)
    polygon_json: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)
