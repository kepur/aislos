"""Workspace isolation for Procurement child resources."""
import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.portal_access import Workspace
from app.models.portal_policy import PortalPolicy
from app.models.procurement import (
    BoqVersion,
    ProcurementPackage,
    ProcurementProject,
    ProcurementProjectFact,
)
from app.models.user import User
from app.services.portal_access import ensure_membership
from app.services.portal_policy import ensure_default_policies
from app.services.procurement_boq import create_draft_boq
from app.services.procurement_packages import generate_packages_from_frozen_boq
from app.services.procurement_rfq import ProcurementRfqError, publish_package_rfq


def _headers(user: User) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {create_access_token(str(user.id), user.role)}",
        settings.PROCUREMENT_PORTAL_HEADER: "aislos",
    }


def _terms() -> dict:
    return {
        "currency": "USD",
        "exchange_rate_snapshot_json": {"base": "USD", "quote": "USD", "rate": "1"},
        "tax_mode": "exclusive",
        "margin_rule_json": {"type": "percent", "value": "0.15"},
        "service_fee_json": {"platform_fee_percent": "0.05"},
        "warranty_rule_json": {"months": 12},
        "delivery_region_json": {"country": "PH", "city": "Cebu"},
        "quote_expiry": datetime.now(timezone.utc) + timedelta(days=30),
        "payment_terms_json": {"net_days": 30},
    }


async def _seed_scope():
    await ensure_default_policies_for_test()
    suffix = uuid.uuid4().hex[:10]
    async with async_session_factory() as db:
        workspace_a = Workspace(name=f"Procurement child A {suffix}", slug=f"pc-a-{suffix}")
        workspace_b = Workspace(name=f"Procurement child B {suffix}", slug=f"pc-b-{suffix}")
        user = User(
            email=f"procurement-child-{suffix}@example.com",
            password_hash=hash_password("test-password"),
            role="buyer",
        )
        db.add_all([workspace_a, workspace_b, user])
        await db.flush()
        await ensure_membership(
            db,
            user_id=user.id,
            membership_type="customer_owner",
            workspace_id=workspace_a.id,
        )
        policy = (
            await db.execute(
                select(PortalPolicy).where(
                    PortalPolicy.portal_key == "aislos",
                    PortalPolicy.status == "active",
                )
            )
        ).scalar_one()
        project = ProcurementProject(
            workspace_id=workspace_a.id,
            owner_user_id=user.id,
            portal_key="aislos",
            portal_policy_id=policy.id,
            policy_snapshot_json={"default_procurement_mode": "managed"},
            project_type="villa_smart_home",
            title="Workspace child test",
            status="draft",
            created_by=user.id,
        )
        db.add(project)
        await db.flush()
        await db.commit()
        return {
            "workspace_a": workspace_a.id,
            "workspace_b": workspace_b.id,
            "user_id": user.id,
            "project_id": project.id,
            "headers": _headers(user),
        }


async def ensure_default_policies_for_test() -> None:
    async with async_session_factory() as db:
        await ensure_default_policies(db)
        await db.commit()


def test_procurement_child_reads_fail_closed_on_workspace_mismatch():
    async def _run():
        await engine.dispose()
        scope = await _seed_scope()
        async with async_session_factory() as db:
            fact_a = ProcurementProjectFact(
                workspace_id=scope["workspace_a"],
                project_id=scope["project_id"],
                template_key="matching",
                label="Matching",
            )
            fact_b = ProcurementProjectFact(
                workspace_id=scope["workspace_b"],
                project_id=scope["project_id"],
                template_key="mismatched",
                label="Mismatched",
            )
            version_a = BoqVersion(
                workspace_id=scope["workspace_a"],
                project_id=scope["project_id"],
                version=1,
                status="frozen",
            )
            version_b = BoqVersion(
                workspace_id=scope["workspace_b"],
                project_id=scope["project_id"],
                version=2,
                status="frozen",
            )
            db.add_all([fact_a, fact_b, version_a, version_b])
            await db.flush()
            package_a = ProcurementPackage(
                workspace_id=scope["workspace_a"],
                project_id=scope["project_id"],
                boq_version_id=version_a.id,
                title="Matching package",
                trade="lighting",
                commercial_type="equipment",
                procurement_mode="managed",
                status="ready",
                revision=1,
            )
            package_b = ProcurementPackage(
                workspace_id=scope["workspace_b"],
                project_id=scope["project_id"],
                boq_version_id=version_a.id,
                title="Mismatched package",
                trade="network",
                commercial_type="equipment",
                procurement_mode="managed",
                status="ready",
                revision=1,
            )
            db.add_all([package_a, package_b])
            project = await db.get(ProcurementProject, scope["project_id"])
            project.current_boq_version_id = version_b.id
            await db.commit()
            ids = {
                "fact_a": str(fact_a.id),
                "fact_b": str(fact_b.id),
                "package_a": str(package_a.id),
                "package_b": str(package_b.id),
            }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            facts = await client.get(
                f"/api/v1/procurement/projects/{scope['project_id']}/facts",
                headers=scope["headers"],
            )
            assert facts.status_code == 200, facts.text
            assert {item["id"] for item in facts.json()} == {ids["fact_a"]}

            denied_fact = await client.patch(
                f"/api/v1/procurement/projects/{scope['project_id']}/facts/{ids['fact_b']}",
                headers=scope["headers"],
                json={"user_confirmed": True},
            )
            assert denied_fact.status_code == 404, denied_fact.text

            packages = await client.get(
                f"/api/v1/procurement/projects/{scope['project_id']}/packages",
                headers=scope["headers"],
            )
            assert packages.status_code == 200, packages.text
            assert {item["id"] for item in packages.json()} == {ids["package_a"]}

            denied_package = await client.patch(
                f"/api/v1/procurement/projects/{scope['project_id']}/packages/{ids['package_b']}",
                headers=scope["headers"],
                json={"status": "draft"},
            )
            assert denied_package.status_code == 404, denied_package.text

            denied_boq = await client.get(
                f"/api/v1/procurement/projects/{scope['project_id']}/boq",
                headers=scope["headers"],
            )
            assert denied_boq.status_code == 404, denied_boq.text

    asyncio.run(_run())


def test_procurement_generated_children_and_rfq_inherit_project_workspace():
    async def _run():
        await engine.dispose()
        scope = await _seed_scope()
        async with async_session_factory() as db:
            project = await db.get(ProcurementProject, scope["project_id"])
            user = await db.get(User, scope["user_id"])
            version, items, options, plans = await create_draft_boq(
                db,
                project=project,
                facts=[],
                items_payload=[
                    {
                        "category": "lighting",
                        "name": "Smart lighting",
                        "options": [
                            {
                                "tier": "standard",
                                "capability": "dimmable",
                                "unit_price_min": "100",
                                "unit_price_max": "120",
                            }
                        ],
                    }
                ],
            )
            assert version.workspace_id == scope["workspace_a"]
            assert {item.workspace_id for item in items} == {scope["workspace_a"]}
            assert {option.workspace_id for option in options} == {scope["workspace_a"]}
            assert {plan.workspace_id for plan in plans} == {scope["workspace_a"]}
            version.status = "frozen"
            project.status = "boq_frozen"
            packages, package_items, _ = await generate_packages_from_frozen_boq(
                db, project=project, boq_version=version
            )
            package = packages[0]
            assert package.workspace_id == scope["workspace_a"]
            assert {item.workspace_id for item in package_items} == {scope["workspace_a"]}
            package.status = "ready"
            snapshot, rfq, created = await publish_package_rfq(
                db,
                project=project,
                package=package,
                user_id=user.id,
                terms=_terms(),
            )
            assert created is True
            assert snapshot.workspace_id == scope["workspace_a"]
            assert rfq.workspace_id == scope["workspace_a"]

            package.workspace_id = scope["workspace_b"]
            with pytest.raises(ProcurementRfqError, match="different Workspaces"):
                await publish_package_rfq(
                    db,
                    project=project,
                    package=package,
                    user_id=user.id,
                    terms=_terms(),
                )

    asyncio.run(_run())
