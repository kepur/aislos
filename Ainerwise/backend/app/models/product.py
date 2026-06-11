import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import Base, TimestampMixin, UUIDMixin


class ProductCategory(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "product_categories"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_categories.id"), nullable=True
    )
    icon: Mapped[str | None] = mapped_column(String(100))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    parent: Mapped["ProductCategory | None"] = relationship(
        "ProductCategory", remote_side="ProductCategory.id"
    )
    products: Mapped[list["Product"]] = relationship("Product", back_populates="category")


class Product(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "products"

    owner_company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    source_type: Mapped[str] = mapped_column(String(50), default="official", nullable=False)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_categories.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    slug: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)
    brand: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    specs_json: Mapped[dict | None] = mapped_column(JSONB)
    images_json: Mapped[list | None] = mapped_column(JSONB)
    cost_price: Mapped[float | None] = mapped_column(Float)
    list_price: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(10), default="EUR")
    moq: Mapped[int] = mapped_column(Integer, default=1)
    lead_time_days: Mapped[int | None] = mapped_column(Integer)
    warranty_years: Mapped[int | None] = mapped_column(Integer)
    spare_policy_json: Mapped[dict | None] = mapped_column(JSONB)
    service_available: Mapped[bool] = mapped_column(Boolean, default=False)
    service_term_years_json: Mapped[list | None] = mapped_column(JSONB)
    price_options_json: Mapped[list | None] = mapped_column(JSONB)
    lifecycle_pricing_json: Mapped[list | None] = mapped_column(JSONB)
    project_pricing_mode: Mapped[str | None] = mapped_column(String(100))
    service_pricing_note: Mapped[str | None] = mapped_column(Text)
    supply_tier: Mapped[str | None] = mapped_column(String(255))
    supplier_ecosystem_json: Mapped[list | None] = mapped_column(JSONB)
    supported_regions_json: Mapped[list | None] = mapped_column(JSONB)
    certifications_json: Mapped[list | None] = mapped_column(JSONB)
    protocol_json: Mapped[list | None] = mapped_column(JSONB)  # ["KNX","MQTT","Modbus",...]
    scenario_tags_json: Mapped[list | None] = mapped_column(JSONB)  # ["villa","school","office",...]
    intelligence_level_min: Mapped[int | None] = mapped_column(Integer)  # L1=1 .. L6=6
    intelligence_level_max: Mapped[int | None] = mapped_column(Integer)
    feature_status: Mapped[str | None] = mapped_column(String(50))  # available_now|project_dependent|advanced_custom|future_ready|concept_demo
    risk_level: Mapped[str | None] = mapped_column(String(50))  # low|medium|high
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)

    # FI.2.2 — recurring-revenue / lifecycle fields. Public site shows public_name
    # and packages; internal_model, supplier_id, and cost stay admin-only.
    solution_line: Mapped[str | None] = mapped_column(String(50))  # see constants.SOLUTION_LINES
    public_name: Mapped[str | None] = mapped_column(String(500))
    internal_model: Mapped[str | None] = mapped_column(String(255))
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    recurring_revenue_types_json: Mapped[list | None] = mapped_column(JSONB)  # see constants.RECURRING_REVENUE_TYPES
    consumable_cycle_months: Mapped[int | None] = mapped_column(Integer)
    calibration_cycle_months: Mapped[int | None] = mapped_column(Integer)
    expected_lifetime_months: Mapped[int | None] = mapped_column(Integer)
    replacement_margin_percent: Mapped[float | None] = mapped_column(Float)
    required_for_compliance: Mapped[bool] = mapped_column(Boolean, default=False)
    report_template_available: Mapped[bool] = mapped_column(Boolean, default=False)
    amc_required: Mapped[bool] = mapped_column(Boolean, default=False)
    amc_recommended: Mapped[bool] = mapped_column(Boolean, default=False)
    service_dependency_level: Mapped[str | None] = mapped_column(String(50))  # low|medium|high

    category: Mapped[ProductCategory | None] = relationship("ProductCategory", back_populates="products")
    compatibility: Mapped[list["ProductCompatibility"]] = relationship(
        "ProductCompatibility", back_populates="product"
    )


class ProductCompatibility(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "product_compatibility"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=False
    )
    protocol: Mapped[str] = mapped_column(String(100), nullable=False)
    compatibility_level: Mapped[str] = mapped_column(String(50), default="unknown")
    tested_by: Mapped[str | None] = mapped_column(String(50))
    test_status: Mapped[str | None] = mapped_column(String(50))
    notes: Mapped[str | None] = mapped_column(Text)
    test_artifact_url: Mapped[str | None] = mapped_column(String(500))

    product: Mapped[Product] = relationship("Product", back_populates="compatibility")
