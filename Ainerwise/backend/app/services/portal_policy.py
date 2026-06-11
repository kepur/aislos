"""Portal Policy service: versioning, activation and default policy seeding.

All functions follow the procurement transaction rule: they only ``add()`` +
``flush()`` and never ``commit()``. The endpoint / application boundary owns
the transaction.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portal_policy import (
    FROZEN_CONFIDENCE_GATE,
    PHASE1_PROJECT_TYPES,
    PORTAL_POLICY_STATUSES,
    PROCUREMENT_MODES,
    PortalPolicy,
)


class PortalPolicyError(ValueError):
    """Raised when a portal policy operation violates the frozen rules."""


# Frozen default policies (PROCUREMENT_PHASE1_EXECUTION_TASKS.md C01).
DEFAULT_PORTAL_POLICIES: dict[str, dict] = {
    "aislos": {
        "default_procurement_mode": "managed",
        "allowed_project_types_json": list(PHASE1_PROJECT_TYPES),
        "price_visibility_rule": "customer_totals_only",
        "supplier_visibility_rule": "hidden",
        "lead_routing_rule_json": {"queue": "aislos_sales"},
        "visible_categories_json": None,
        "confidence_gate_json": dict(FROZEN_CONFIDENCE_GATE),
    },
    "cebu": {
        "default_procurement_mode": "self_service",
        "allowed_project_types_json": list(PHASE1_PROJECT_TYPES),
        "price_visibility_rule": "line_estimates",
        "supplier_visibility_rule": "visible_when_self_service",
        "lead_routing_rule_json": {"queue": "cebu_procurement"},
        "visible_categories_json": None,
        "confidence_gate_json": dict(FROZEN_CONFIDENCE_GATE),
    },
}


def validate_policy(policy: PortalPolicy) -> list[str]:
    """Return a list of problems; an empty list means the policy is legal."""
    problems: list[str] = []
    if policy.status not in PORTAL_POLICY_STATUSES:
        problems.append(f"invalid status: {policy.status!r}")
    if policy.default_procurement_mode not in PROCUREMENT_MODES:
        problems.append(f"invalid default_procurement_mode: {policy.default_procurement_mode!r}")
    if not policy.price_visibility_rule:
        problems.append("price_visibility_rule is required")
    if not policy.supplier_visibility_rule:
        problems.append("supplier_visibility_rule is required")

    allowed_types = policy.allowed_project_types_json or []
    if not isinstance(allowed_types, list) or not allowed_types:
        problems.append("allowed_project_types_json must be a non-empty list")
    else:
        unknown = [t for t in allowed_types if t not in PHASE1_PROJECT_TYPES]
        if unknown:
            problems.append(f"project types outside Phase 1 scope: {unknown}")

    # Portals may never loosen the frozen confidence gate.
    gate = policy.confidence_gate_json or {}
    if not isinstance(gate, dict):
        problems.append("confidence_gate_json must be an object")
    else:
        for key, frozen_value in FROZEN_CONFIDENCE_GATE.items():
            if gate.get(key) != frozen_value:
                problems.append(
                    f"confidence_gate_json[{key!r}] must equal frozen value {frozen_value!r}"
                )
    return problems


async def get_active_policy(db: AsyncSession, portal_key: str) -> PortalPolicy | None:
    result = await db.execute(
        select(PortalPolicy).where(
            PortalPolicy.portal_key == portal_key,
            PortalPolicy.status == "active",
        )
    )
    return result.scalar_one_or_none()


async def get_next_version(db: AsyncSession, portal_key: str) -> int:
    result = await db.execute(
        select(func.coalesce(func.max(PortalPolicy.version), 0)).where(
            PortalPolicy.portal_key == portal_key
        )
    )
    return int(result.scalar_one()) + 1


async def create_policy_version(
    db: AsyncSession,
    portal_key: str,
    *,
    default_procurement_mode: str,
    allowed_project_types_json: list,
    price_visibility_rule: str,
    supplier_visibility_rule: str,
    lead_routing_rule_json: dict | None = None,
    visible_categories_json: list | None = None,
    confidence_gate_json: dict | None = None,
    created_by: uuid.UUID | None = None,
) -> PortalPolicy:
    """Create a new draft policy version. flush() only, no commit()."""
    policy = PortalPolicy(
        portal_key=portal_key,
        version=await get_next_version(db, portal_key),
        status="draft",
        default_procurement_mode=default_procurement_mode,
        allowed_project_types_json=allowed_project_types_json,
        price_visibility_rule=price_visibility_rule,
        supplier_visibility_rule=supplier_visibility_rule,
        lead_routing_rule_json=lead_routing_rule_json,
        visible_categories_json=visible_categories_json,
        confidence_gate_json=confidence_gate_json
        if confidence_gate_json is not None
        else dict(FROZEN_CONFIDENCE_GATE),
        created_by=created_by,
    )
    problems = validate_policy(policy)
    if problems:
        raise PortalPolicyError("; ".join(problems))
    db.add(policy)
    await db.flush()
    return policy


async def activate_policy(db: AsyncSession, policy: PortalPolicy) -> PortalPolicy:
    """Activate a draft policy. Fails if another active policy exists.

    The previous active policy must be explicitly retired first; an active
    policy can never be silently replaced.
    """
    if policy.status == "active":
        return policy
    if policy.status == "retired":
        raise PortalPolicyError("a retired policy cannot be re-activated")

    problems = validate_policy(policy)
    if problems:
        raise PortalPolicyError("; ".join(problems))

    existing = await get_active_policy(db, policy.portal_key)
    if existing is not None and existing.id != policy.id:
        raise PortalPolicyError(
            f"portal {policy.portal_key!r} already has active policy version "
            f"{existing.version}; retire it before activating a new one"
        )

    policy.status = "active"
    policy.activated_at = datetime.now(timezone.utc)
    await db.flush()
    return policy


async def retire_active_policy(db: AsyncSession, portal_key: str) -> PortalPolicy | None:
    policy = await get_active_policy(db, portal_key)
    if policy is None:
        return None
    policy.status = "retired"
    await db.flush()
    return policy


async def ensure_default_policies(
    db: AsyncSession, created_by: uuid.UUID | None = None
) -> dict[str, PortalPolicy]:
    """Idempotently ensure each default portal has an active policy.

    Existing active policies are never modified (no silent drift).
    flush() only; caller owns the commit.
    """
    out: dict[str, PortalPolicy] = {}
    for portal_key, defaults in DEFAULT_PORTAL_POLICIES.items():
        active = await get_active_policy(db, portal_key)
        if active is None:
            policy = await create_policy_version(
                db,
                portal_key,
                default_procurement_mode=defaults["default_procurement_mode"],
                allowed_project_types_json=defaults["allowed_project_types_json"],
                price_visibility_rule=defaults["price_visibility_rule"],
                supplier_visibility_rule=defaults["supplier_visibility_rule"],
                lead_routing_rule_json=defaults["lead_routing_rule_json"],
                visible_categories_json=defaults["visible_categories_json"],
                confidence_gate_json=defaults["confidence_gate_json"],
                created_by=created_by,
            )
            active = await activate_policy(db, policy)
        out[portal_key] = active
    return out
