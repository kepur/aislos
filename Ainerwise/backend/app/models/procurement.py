"""Procurement Phase 1 models: projects, templates, facts and BOQ."""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin

PROCUREMENT_PROJECT_STATUSES = (
    "draft",
    "collecting",
    "analyzing",
    "needs_information",
    "estimate_ready",
    "review_ready",
    "in_review",
    "review_approved",
    "boq_frozen",
    "packaged",
    "rfq_published",
)

PROCUREMENT_TEMPLATE_STATUSES = ("draft", "active", "retired")

FACT_SOURCES = ("user", "ai", "file", "system")

BOQ_VERSION_STATUSES = (
    "draft",
    "estimate",
    "in_review",
    "approved",
    "frozen",
    "superseded",
)

BOQ_TIERS = ("budget", "standard", "premium")


class ProcurementTemplate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "procurement_templates"

    project_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    fact_definitions_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    boq_rules_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        UniqueConstraint("project_type", "version", name="uq_procurement_templates_type_version"),
        Index(
            "uq_procurement_templates_one_active",
            "project_type",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
    )


class ProcurementProject(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "procurement_projects"

    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    portal_key: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    portal_policy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("portal_policies.id", ondelete="RESTRICT"), nullable=False
    )
    policy_snapshot_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    project_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    facts_score: Mapped[Decimal] = mapped_column(
        Numeric(6, 3), nullable=False, default=Decimal("0")
    )
    boq_score: Mapped[Decimal] = mapped_column(
        Numeric(6, 3), nullable=False, default=Decimal("0")
    )
    overall_confidence: Mapped[Decimal] = mapped_column(
        Numeric(6, 3), nullable=False, default=Decimal("0")
    )
    current_boq_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("boq_versions.id", ondelete="SET NULL", use_alter=True, name="fk_procurement_projects_current_boq_version"),
        nullable=True,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )


class ProcurementProjectFact(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "procurement_project_facts"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("procurement_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    template_key: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    value_json: Mapped[dict | list | str | int | float | bool | None] = mapped_column(
        JSONB, nullable=True
    )
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    critical: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False, default=Decimal("1"))
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="system")
    source_ref_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    confidence: Mapped[Decimal] = mapped_column(
        Numeric(6, 3), nullable=False, default=Decimal("0")
    )
    user_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    assumption: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("project_id", "template_key", name="uq_procurement_facts_project_key"),
    )


class BoqVersion(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "boq_versions"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("procurement_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    source_run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    facts_score: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False, default=Decimal("0"))
    boq_score: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False, default=Decimal("0"))
    overall_confidence: Mapped[Decimal] = mapped_column(
        Numeric(6, 3), nullable=False, default=Decimal("0")
    )
    disclaimer: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai.ai_reviews.id", ondelete="SET NULL"),
        nullable=True,
    )
    frozen_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    frozen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("project_id", "version", name="uq_boq_versions_project_version"),
    )


class BoqItem(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "boq_items"

    boq_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("boq_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    trade: Mapped[str | None] = mapped_column(String(100), nullable=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    specs: Mapped[str | None] = mapped_column(Text, nullable=True)
    qty: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False, default=Decimal("1"))
    unit: Mapped[str] = mapped_column(String(50), nullable=False, default="ea")
    quantity_basis: Mapped[str | None] = mapped_column(Text, nullable=True)
    assumptions: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False, default=Decimal("0"))
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="system")
    source_ref_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    critical: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False, default=Decimal("1"))
    included: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class BoqItemOption(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "boq_item_options"

    boq_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("boq_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tier: Mapped[str] = mapped_column(String(20), nullable=False)
    capability: Mapped[str] = mapped_column(String(500), nullable=False)
    recommended_brand: Mapped[str | None] = mapped_column(String(255), nullable=True)
    unit_price_min: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    unit_price_max: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    total_price_min: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    total_price_max: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    supply_included: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    install_included: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    maintain_included: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("boq_item_id", "tier", name="uq_boq_item_options_item_tier"),
    )


class SolutionPlan(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "solution_plans"

    boq_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("boq_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tier: Mapped[str] = mapped_column(String(20), nullable=False)
    total_min: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    total_max: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    assumptions: Mapped[str | None] = mapped_column(Text, nullable=True)
    exclusions: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimate_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint("boq_version_id", "tier", name="uq_solution_plans_version_tier"),
    )


COMMERCIAL_TYPES = ("equipment", "installation", "maintenance")
PACKAGE_TRADES = ("network", "security", "access", "lighting", "hvac", "energy", "general")
PACKAGE_STATUSES = ("draft", "ready", "published", "closed")
PROCUREMENT_MODES = ("managed", "self_service")


class ProcurementPackage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "procurement_packages"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("procurement_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    boq_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("boq_versions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    trade: Mapped[str] = mapped_column(String(50), nullable=False)
    commercial_type: Mapped[str] = mapped_column(String(30), nullable=False)
    procurement_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    compatibility_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    delivery_constraints_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    __table_args__ = (
        UniqueConstraint("project_id", "boq_version_id", "trade", "commercial_type", "revision",
                         name="uq_procurement_packages_project_boq_trade_type_rev"),
    )


class ProcurementPackageItem(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "procurement_package_items"

    package_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("procurement_packages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    boq_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("boq_items.id", ondelete="RESTRICT"),
        nullable=False,
    )
    boq_item_option_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("boq_item_options.id", ondelete="SET NULL"),
        nullable=True,
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)

    __table_args__ = (
        UniqueConstraint("package_id", "boq_item_id", name="uq_procurement_package_items_pkg_boq"),
    )


class CommercialSnapshot(Base, UUIDMixin, TimestampMixin):
    """Immutable commercial terms frozen at RFQ publish (C07)."""

    __tablename__ = "commercial_snapshots"

    portal_key: Mapped[str] = mapped_column(String(50), nullable=False)
    portal_policy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("portal_policies.id", ondelete="RESTRICT"), nullable=False
    )
    procurement_project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("procurement_projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    boq_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("boq_versions.id", ondelete="RESTRICT"), nullable=False
    )
    package_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("procurement_packages.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    package_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    exchange_rate_snapshot_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    tax_mode: Mapped[str] = mapped_column(String(50), nullable=False)
    margin_rule_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    service_fee_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    warranty_rule_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    delivery_region_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    quote_expiry: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payment_terms_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    terms_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("package_id", "package_revision", name="uq_commercial_snapshots_package_rev"),
    )
