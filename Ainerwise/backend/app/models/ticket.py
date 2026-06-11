import uuid

from sqlalchemy import Boolean, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin


class Ticket(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tickets"

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True
    )
    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id"), nullable=True, index=True
    )
    buyer_company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    buyer_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    issue_type: Mapped[str | None] = mapped_column(String(100))
    priority: Mapped[str] = mapped_column(String(50), default="medium", nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    files_json: Mapped[list | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(50), default="open", nullable=False)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # FI.2.4 — coverage fields so a ticket resolves to warranty / AMC / paid service.
    affected_device: Mapped[str | None] = mapped_column(String(500))
    monitoring_point_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("monitoring_points.id"), nullable=True
    )
    warranty_related: Mapped[bool] = mapped_column(Boolean, default=False)
    amc_covered: Mapped[bool] = mapped_column(Boolean, default=False)
    is_paid_service: Mapped[bool] = mapped_column(Boolean, default=False)
    coverage_type: Mapped[str | None] = mapped_column(String(50))  # pass_through_warranty|managed_warranty|amc|paid_service
    estimated_cost: Mapped[float | None] = mapped_column(Float)
    resolution: Mapped[str | None] = mapped_column(Text)
