from sqlalchemy import Boolean, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin


class Solution(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "solutions"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    slug: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String(100))
    solution_line: Mapped[str | None] = mapped_column(String(50))  # see constants.SOLUTION_LINES
    target_scenarios_json: Mapped[list | None] = mapped_column(JSONB)
    description: Mapped[str | None] = mapped_column(Text)
    pain_points_json: Mapped[list | None] = mapped_column(JSONB)
    architecture_json: Mapped[dict | None] = mapped_column(JSONB)
    recommended_products_json: Mapped[list | None] = mapped_column(JSONB)
    service_packages_json: Mapped[list | None] = mapped_column(JSONB)
    budget_tiers_json: Mapped[dict | None] = mapped_column(JSONB)
    delivery_flow_json: Mapped[list | None] = mapped_column(JSONB)
    lifecycle_content_json: Mapped[dict | None] = mapped_column(JSONB)
    regions_json: Mapped[list | None] = mapped_column(JSONB)
    language_content_json: Mapped[dict | None] = mapped_column(JSONB)
    hero_image_url: Mapped[str | None] = mapped_column(String(500))
    icon: Mapped[str | None] = mapped_column(String(100))
    public_visible: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class SolutionPackage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "solution_packages"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    slug: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)
    target_customer_type: Mapped[str | None] = mapped_column(String(100))
    suitable_regions_json: Mapped[list | None] = mapped_column(JSONB)
    included_systems_json: Mapped[list | None] = mapped_column(JSONB)
    recommended_products_json: Mapped[list | None] = mapped_column(JSONB)
    required_service_partner_types_json: Mapped[list | None] = mapped_column(JSONB)
    base_price_rule_json: Mapped[dict | None] = mapped_column(JSONB)
    estimated_timeline_days: Mapped[int | None] = mapped_column(Integer)
    risk_notes: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    public_visible: Mapped[bool] = mapped_column(Boolean, default=True)
    language_content_json: Mapped[dict | None] = mapped_column(JSONB)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
