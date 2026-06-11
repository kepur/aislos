"""Agent Runtime registry: role-oriented callers of business capabilities.

An Agent has an employee identity, persona, allowlisted workflows and explicit
permission grants. Business modules remain the durable capability/data
boundaries. Marketplace fields (vendor, price) are reserved for Phase I.
"""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin

AGENT_GRANT_SCOPES = (
    "product_data", "customer_data", "project_data", "quotes",
    "email", "ads", "payment", "partners",
)


class Agent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agents"

    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role_title: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    vendor: Mapped[str] = mapped_column(String(50), default="official", nullable=False, index=True)
    workflows_json: Mapped[list | None] = mapped_column(JSONB)
    config_json: Mapped[dict | None] = mapped_column(JSONB)  # persona: voice/audience/goals/forbidden
    price_monthly: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(10), default="EUR", nullable=False)
    region_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("regions.id"))
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False, index=True)


class AgentGrant(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agent_grants"
    __table_args__ = (UniqueConstraint("agent_id", "scope", name="uq_agent_grants_agent_scope"),)

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scope: Mapped[str] = mapped_column(String(50), nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    granted_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    granted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AgentObjectGrant(Base, UUIDMixin, TimestampMixin):
    """Least-privilege access to one concrete business object."""

    __tablename__ = "agent_object_grants"
    __table_args__ = (
        UniqueConstraint(
            "agent_id", "object_type", "object_id", "scope",
            name="uq_agent_object_grants_target_scope",
        ),
    )

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    object_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    object_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    scope: Mapped[str] = mapped_column(String(50), nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    granted_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    granted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
