"""Shared helpers and orchestrator fixtures for procurement Phase 1 E2E (C09)."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.core.permissions import UserRole
from app.core.security import create_access_token, hash_password
from app.db.session import async_session_factory
from app.main import app
from app.models.portal_policy import PHASE1_PROJECT_TYPES
from app.services.portal_policy import (
    activate_policy,
    create_policy_version,
    ensure_default_policies,
    retire_active_policy,
)

BASE = "/api/v1/procurement"


def client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def auth(token: str, portal: str = "aislos") -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        settings.PROCUREMENT_PORTAL_HEADER: portal,
    }


async def seed_policies() -> None:
    async with async_session_factory() as db:
        await ensure_default_policies(db)
        await db.commit()


async def restore_default_portal_policies() -> None:
    """Retire test-mutated policies and re-seed frozen C01 defaults."""
    async with async_session_factory() as db:
        for portal_key in ("aislos", "cebu"):
            await retire_active_policy(db, portal_key)
        await ensure_default_policies(db)
        await db.commit()


async def ensure_portal_policy(portal_key: str, mode: str) -> None:
    async with async_session_factory() as db:
        await retire_active_policy(db, portal_key)
        policy = await create_policy_version(
            db,
            portal_key,
            default_procurement_mode=mode,
            allowed_project_types_json=list(PHASE1_PROJECT_TYPES),
            price_visibility_rule="customer_totals_only"
            if mode == "managed"
            else "line_estimates",
            supplier_visibility_rule="hidden"
            if mode == "managed"
            else "visible_when_self_service",
        )
        await activate_policy(db, policy)
        await db.commit()


async def register_user(role: str = UserRole.BUYER.value) -> tuple[str, str]:
    email = f"e2e-{uuid.uuid4().hex[:8]}@test.local"
    async with async_session_factory() as db:
        from app.models.user import User

        user = User(
            email=email,
            password_hash=hash_password("testpass123"),
            full_name="E2E User",
            role=role,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return str(user.id), create_access_token(str(user.id), role)


def tier_options(
    *,
    supply: bool = True,
    install: bool = False,
    maintain: bool = False,
) -> list[dict[str, Any]]:
    opts = []
    for tier, price in (("budget", 100), ("standard", 200), ("premium", 300)):
        opts.append(
            {
                "tier": tier,
                "capability": f"{tier} package",
                "unit_price_min": price,
                "unit_price_max": price + 50,
                "currency": "USD",
                "supply_included": supply,
                "install_included": install,
                "maintain_included": maintain,
            }
        )
    return opts


def boq_item(
    *,
    category: str,
    name: str,
    trade: str | None = None,
    confidence: float = 0.9,
    supply: bool = True,
    install: bool = False,
    maintain: bool = False,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "category": category,
        "name": name,
        "qty": "1",
        "unit": "lot",
        "quantity_basis": "per scope",
        "confidence": confidence,
        "included": True,
        "options": tier_options(supply=supply, install=install, maintain=maintain),
    }
    if trade:
        payload["trade"] = trade
    return payload


def orch_response(
    *,
    scenario: str = "high",
    items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    conf_map = {
        "low": 0.55,
        "edge_600": 0.6,
        "high": 0.85,
    }
    conf = conf_map.get(scenario, 0.85)
    default_items = items or [
        boq_item(category="lighting", name="Villa lighting", supply=True),
        boq_item(
            category="network",
            name="Network install",
            trade="network",
            supply=True,
            install=True,
        ),
        boq_item(
            category="hvac",
            name="HVAC maintenance",
            trade="hvac",
            supply=False,
            maintain=True,
        ),
    ]
    data = {
        "project_summary": "E2E scenario",
        "extracted_facts": [
            {"key": "property_area_sqm", "value": 300, "source": "ai", "confidence": conf}
        ],
        "missing_questions": [{"key": "target_budget", "importance": "critical", "reason": "x"}]
        if scenario == "low"
        else [],
        "boq_items": default_items if conf >= 0.6 else [],
        "risks": [],
        "exclusions": [],
    }
    return {"workflow": "procurement_analyze", "status": "completed", "data": data}


def commercial_terms() -> dict[str, Any]:
    expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    return {
        "currency": "USD",
        "exchange_rate_snapshot_json": {"base": "USD", "quote": "PHP", "rate": "56.5"},
        "tax_mode": "exclusive",
        "margin_rule_json": {"type": "percent", "value": "0.15"},
        "service_fee_json": {"platform_fee_percent": "0.05"},
        "warranty_rule_json": {"months": 12},
        "delivery_region_json": {"country": "PH"},
        "quote_expiry": expiry,
        "payment_terms_json": {"net_days": 30},
    }


async def confirm_all_facts(project_id: str, token: str, portal: str) -> None:
    async with client() as ac:
        facts = await ac.get(f"{BASE}/projects/{project_id}/facts", headers=auth(token, portal))
        for fact in facts.json():
            await ac.patch(
                f"{BASE}/projects/{project_id}/facts/{fact['id']}",
                json={"value_json": "confirmed", "user_confirmed": True},
                headers=auth(token, portal),
            )


async def approve_review(admin_token: str, review_id: str) -> None:
    async with client() as ac:
        resp = await ac.post(
            f"/api/v1/admin/ai-reviews/{review_id}/approve",
            json={"notes": "e2e approved"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200, resp.text


async def freeze_reviewed_boq(
    project_id: str,
    buyer_token: str,
    admin_token: str,
    portal: str,
    *,
    version_id: str | None = None,
) -> str:
    async with client() as ac:
        if version_id is None:
            boq = await ac.get(f"{BASE}/projects/{project_id}/boq", headers=auth(buyer_token, portal))
            version_id = boq.json()["version_id"]
        review = await ac.post(
            f"{BASE}/projects/{project_id}/boq/review",
            json={"boq_version_id": version_id},
            headers=auth(buyer_token, portal),
        )
        assert review.status_code == 200, review.text
        await approve_review(admin_token, review.json()["review_id"])
        frozen = await ac.post(
            f"{BASE}/projects/{project_id}/boq/freeze",
            json={"boq_version_id": version_id},
            headers=auth(buyer_token, portal),
        )
        assert frozen.status_code == 200, frozen.text
        return version_id
