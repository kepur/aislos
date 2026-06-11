import uuid
from datetime import datetime

from app.schemas.base import BaseSchema


class SolutionRead(BaseSchema):
    id: uuid.UUID
    title: str
    slug: str
    category: str | None = None
    solution_line: str | None = None
    target_scenarios_json: list | None = None
    description: str | None = None
    pain_points_json: list | None = None
    architecture_json: dict | None = None
    recommended_products_json: list | None = None
    service_packages_json: list | None = None
    budget_tiers_json: dict | None = None
    delivery_flow_json: list | None = None
    lifecycle_content_json: dict | None = None
    regions_json: list | None = None
    hero_image_url: str | None = None
    icon: str | None = None
    public_visible: bool
    sort_order: int
    created_at: datetime


class SolutionCreate(BaseSchema):
    title: str
    slug: str | None = None
    category: str | None = None
    solution_line: str | None = None
    target_scenarios_json: list | None = None
    description: str | None = None
    pain_points_json: list | None = None
    architecture_json: dict | None = None
    recommended_products_json: list | None = None
    service_packages_json: list | None = None
    budget_tiers_json: dict | None = None
    delivery_flow_json: list | None = None
    lifecycle_content_json: dict | None = None
    regions_json: list | None = None
    hero_image_url: str | None = None
    icon: str | None = None
    public_visible: bool = True
    sort_order: int = 0


class SolutionUpdate(BaseSchema):
    title: str | None = None
    category: str | None = None
    solution_line: str | None = None
    target_scenarios_json: list | None = None
    description: str | None = None
    pain_points_json: list | None = None
    architecture_json: dict | None = None
    recommended_products_json: list | None = None
    service_packages_json: list | None = None
    budget_tiers_json: dict | None = None
    delivery_flow_json: list | None = None
    lifecycle_content_json: dict | None = None
    regions_json: list | None = None
    hero_image_url: str | None = None
    icon: str | None = None
    public_visible: bool | None = None
    sort_order: int | None = None
