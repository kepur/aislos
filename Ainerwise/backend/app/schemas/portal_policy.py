import uuid
from datetime import datetime

from app.schemas.base import BaseSchema


class PortalPolicyPublic(BaseSchema):
    """Customer-visible view of the active Portal Policy.

    Deliberately excludes internal fields such as lead routing rules and
    creator identity. Never add internal economics here.
    """

    portal_key: str
    version: int
    default_procurement_mode: str
    allowed_project_types: list[str]
    price_visibility_rule: str
    supplier_visibility_rule: str
    visible_categories: list | None = None
    confidence_gate: dict

    @classmethod
    def from_policy(cls, policy) -> "PortalPolicyPublic":
        return cls(
            portal_key=policy.portal_key,
            version=policy.version,
            default_procurement_mode=policy.default_procurement_mode,
            allowed_project_types=list(policy.allowed_project_types_json or []),
            price_visibility_rule=policy.price_visibility_rule,
            supplier_visibility_rule=policy.supplier_visibility_rule,
            visible_categories=policy.visible_categories_json,
            confidence_gate=dict(policy.confidence_gate_json or {}),
        )


class PortalPolicyRead(BaseSchema):
    """Full internal/admin view of a Portal Policy."""

    id: uuid.UUID
    portal_key: str
    version: int
    status: str
    default_procurement_mode: str
    allowed_project_types_json: list
    price_visibility_rule: str
    supplier_visibility_rule: str
    visible_categories_json: list | None = None
    lead_routing_rule_json: dict | None = None
    confidence_gate_json: dict
    created_by: uuid.UUID | None = None
    activated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
