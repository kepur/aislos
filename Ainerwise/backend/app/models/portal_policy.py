"""Versioned Portal Policy: the trusted source of per-portal procurement behavior.

AISLOS and Cebu are not just different brands; backend behavior (procurement
mode, price/supplier visibility, allowed project types, confidence gate) is
driven by the active PortalPolicy of the request's trusted Portal Context.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin

PORTAL_POLICY_STATUSES = ("draft", "active", "retired")
PROCUREMENT_MODES = ("managed", "self_service")
PHASE1_PROJECT_TYPES = ("villa_smart_home", "small_hotel_smart_upgrade")

# Frozen confidence gate (PROCUREMENT_PHASE1_EXECUTION_TASKS.md §4.2).
# Thresholds are stored as strings so gate comparisons stay exact Decimals.
# Portals may never loosen these values.
FROZEN_CONFIDENCE_GATE = {
    "ask_below": "0.600",
    "estimate_min": "0.600",
    "estimate_max": "0.800",
    "review_above": "0.800",
    "freeze_min_critical_confidence": "0.800",
    "score_decimals": 3,
    "aggregation": "min",
}


class PortalPolicy(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "portal_policies"

    portal_key: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")

    visible_categories_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    default_procurement_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    allowed_project_types_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    price_visibility_rule: Mapped[str] = mapped_column(String(50), nullable=False)
    supplier_visibility_rule: Mapped[str] = mapped_column(String(50), nullable=False)
    lead_routing_rule_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    confidence_gate_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("portal_key", "version", name="uq_portal_policies_key_version"),
        # At most one active policy per portal, enforced at the database level.
        Index(
            "uq_portal_policies_one_active",
            "portal_key",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
    )
