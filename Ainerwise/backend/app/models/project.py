import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin


PROJECT_STATUSES = (
    "planning", "site_survey", "quotation_confirmed", "procurement",
    "delivery", "installation", "testing", "handover",
    "maintenance", "closed",
)


class Project(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "projects"

    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leads.id"), nullable=True
    )
    buyer_company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="planning", nullable=False)
    region: Mapped[str | None] = mapped_column(String(100))
    start_date: Mapped[date | None] = mapped_column(Date)
    expected_delivery_date: Mapped[date | None] = mapped_column(Date)
    project_plan_json: Mapped[dict | None] = mapped_column(JSONB)
    team_json: Mapped[list | None] = mapped_column(JSONB)
    telegram_chat_id: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column()
