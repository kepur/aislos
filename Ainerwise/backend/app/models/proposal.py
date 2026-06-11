import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import Base, TimestampMixin, UUIDMixin


PROPOSAL_TIERS = ("budget", "standard", "premium_ai", "future_autonomous")


class ProposalPlan(Base, UUIDMixin, TimestampMixin):
    """One of the four proposal tiers generated for a lead/project."""
    __tablename__ = "proposal_plans"

    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leads.id"), nullable=True
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True
    )
    tier: Mapped[str] = mapped_column(String(50), nullable=False)  # budget|standard|premium_ai|future_autonomous
    intelligence_level_min: Mapped[int | None] = mapped_column(Integer)
    intelligence_level_max: Mapped[int | None] = mapped_column(Integer)
    device_cost_estimate: Mapped[float] = mapped_column(Float, default=0)
    design_fee_estimate: Mapped[float] = mapped_column(Float, default=0)
    installation_fee_estimate: Mapped[float] = mapped_column(Float, default=0)
    platform_fee_estimate: Mapped[float] = mapped_column(Float, default=0)
    maintenance_fee_estimate: Mapped[float] = mapped_column(Float, default=0)
    spare_parts_reserve: Mapped[float] = mapped_column(Float, default=0)
    total_min: Mapped[float] = mapped_column(Float, default=0)
    total_max: Mapped[float] = mapped_column(Float, default=0)
    currency: Mapped[str] = mapped_column(String(10), default="EUR")
    complexity: Mapped[str | None] = mapped_column(String(50))  # low|medium|high|very_high
    risk_level: Mapped[str | None] = mapped_column(String(50))  # low|medium|high
    recommended_next_step: Mapped[str | None] = mapped_column(Text)
    estimate_only: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text)

    # FI.4.3 — recurring-cost breakdown + first-year / annual totals.
    amc_fee: Mapped[float] = mapped_column(Float, default=0)
    consumable_fee: Mapped[float] = mapped_column(Float, default=0)
    calibration_fee: Mapped[float] = mapped_column(Float, default=0)
    reporting_fee: Mapped[float] = mapped_column(Float, default=0)
    alarm_monitoring_fee: Mapped[float] = mapped_column(Float, default=0)
    first_year_total: Mapped[float] = mapped_column(Float, default=0)
    annual_recurring_total: Mapped[float] = mapped_column(Float, default=0)
    recommended_contract_term_years: Mapped[int | None] = mapped_column(Integer)

    bom_items: Mapped[list["BOMItem"]] = relationship("BOMItem", back_populates="proposal_plan")


class BOMItem(Base, UUIDMixin, TimestampMixin):
    """Individual line item in an editable BOM sheet."""
    __tablename__ = "bom_items"

    proposal_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("proposal_plans.id"), nullable=False
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=True
    )
    category: Mapped[str | None] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(255))
    qty: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[float] = mapped_column(Float, default=0)
    device_cost: Mapped[float] = mapped_column(Float, default=0)
    installation_cost: Mapped[float] = mapped_column(Float, default=0)
    service_fee: Mapped[float] = mapped_column(Float, default=0)
    maintenance_years: Mapped[int | None] = mapped_column(Integer)
    already_owned: Mapped[bool] = mapped_column(Boolean, default=False)
    need_ainerwise_supply: Mapped[bool] = mapped_column(Boolean, default=True)
    need_installation: Mapped[bool] = mapped_column(Boolean, default=True)
    design_only: Mapped[bool] = mapped_column(Boolean, default=False)
    total: Mapped[float] = mapped_column(Float, default=0)
    notes: Mapped[str | None] = mapped_column(Text)

    proposal_plan: Mapped[ProposalPlan] = relationship("ProposalPlan", back_populates="bom_items")
