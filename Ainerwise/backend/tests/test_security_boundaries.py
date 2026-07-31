"""Release-gate tests for commerce objects and workspace-scoped portal grants."""
import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.portal_access import PortalGrant, Workspace, WorkspaceMembership
from app.models.user import Company, User
from app.services.portal_access import (
    ensure_grant,
    list_memberships,
    list_user_portals,
    resolve_workspace_scope,
    switch_portal_audit,
    user_has_grant,
)


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _create_identity(*, role: str, with_company: bool = True) -> tuple[str, str, uuid.UUID | None]:
    suffix = uuid.uuid4().hex[:10]
    email = f"security-{role}-{suffix}@example.com"
    password = "security123"
    async with async_session_factory() as db:
        company_id = None
        if with_company:
            company = Company(
                name=f"Security {role} {suffix}",
                type="supplier" if role == "vendor" else "buyer",
                verification_status="verified",
            )
            db.add(company)
            await db.flush()
            company_id = company.id
        db.add(
            User(
                email=email,
                password_hash=hash_password(password),
                full_name=f"Security {role}",
                role=role,
                company_id=company_id,
                is_active=True,
            )
        )
        await db.commit()
    return email, password, company_id


async def _login(email: str, password: str) -> dict:
    async with _client() as client:
        response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_commerce_objects_cannot_be_managed_or_impersonated_cross_company():
    async def _run():
        await engine.dispose()
        buyer_a_email, password, _ = await _create_identity(role="buyer")
        buyer_b_email, _, _ = await _create_identity(role="buyer")
        supplier_a_email, _, supplier_a_company = await _create_identity(role="vendor")
        supplier_b_email, _, supplier_b_company = await _create_identity(role="vendor")

        buyer_a = await _login(buyer_a_email, password)
        buyer_b = await _login(buyer_b_email, password)
        supplier_a = await _login(supplier_a_email, password)
        supplier_b = await _login(supplier_b_email, password)

        async with _client() as client:
            request = await client.post(
                "/api/v1/commerce/procurement-requests",
                headers=buyer_a,
                json={"title": "Authorization boundary", "portal_key": "cebu"},
            )
            assert request.status_code == 201, request.text
            request_id = request.json()["id"]

            listing_a = await client.post(
                "/api/v1/commerce/supplier-listings",
                headers=supplier_a,
                json={"company_id": str(supplier_a_company), "title": "Supplier A listing"},
            )
            assert listing_a.status_code == 201, listing_a.text

            for method, path in (
                ("GET", f"/api/v1/commerce/procurement-requests/{request_id}"),
                ("POST", f"/api/v1/commerce/procurement-requests/{request_id}/publish"),
                ("GET", f"/api/v1/commerce/procurement-requests/{request_id}/supplier-candidates"),
                ("POST", f"/api/v1/cebu-compat/intents/{request_id}/publish"),
                ("GET", f"/api/v1/cebu-compat/intents/{request_id}/supplier-candidates"),
            ):
                response = await client.request(method, path, headers=buyer_b)
                assert response.status_code == 403, (method, path, response.text)

            impersonated_listing = await client.post(
                "/api/v1/commerce/supplier-listings",
                headers=supplier_b,
                json={"company_id": str(supplier_a_company), "title": "Impersonated listing"},
            )
            assert impersonated_listing.status_code == 403

            own_listing = await client.post(
                "/api/v1/commerce/supplier-listings",
                headers=supplier_b,
                json={"company_id": str(supplier_b_company), "title": "Supplier B listing"},
            )
            assert own_listing.status_code == 201, own_listing.text

            publish = await client.post(
                f"/api/v1/commerce/procurement-requests/{request_id}/publish", headers=buyer_a
            )
            assert publish.status_code == 200, publish.text

            impersonated_offer = await client.post(
                f"/api/v1/commerce/procurement-requests/{request_id}/offers",
                headers=supplier_b,
                json={
                    "supplier_company_id": str(supplier_a_company),
                    "supplier_listing_id": listing_a.json()["id"],
                    "price_minor": 10000,
                },
            )
            assert impersonated_offer.status_code == 403

            other_listing_offer = await client.post(
                f"/api/v1/commerce/procurement-requests/{request_id}/offers",
                headers=supplier_b,
                json={
                    "supplier_company_id": str(supplier_b_company),
                    "supplier_listing_id": listing_a.json()["id"],
                    "price_minor": 10000,
                },
            )
            assert other_listing_offer.status_code == 403

            own_offer = await client.post(
                f"/api/v1/commerce/procurement-requests/{request_id}/offers",
                headers=supplier_b,
                json={
                    "supplier_company_id": str(supplier_b_company),
                    "supplier_listing_id": own_listing.json()["id"],
                    "price_minor": 10000,
                },
            )
            assert own_offer.status_code == 201, own_offer.text

            cross_buyer_award = await client.post(
                f"/api/v1/commerce/offers/{own_offer.json()['id']}/award", headers=buyer_b
            )
            assert cross_buyer_award.status_code == 403

            owner_award = await client.post(
                f"/api/v1/commerce/offers/{own_offer.json()['id']}/award", headers=buyer_a
            )
            assert owner_award.status_code == 200, owner_award.text

    asyncio.run(_run())


def test_companyless_buyers_do_not_share_null_company_scope():
    async def _run():
        await engine.dispose()
        owner_email, password, _ = await _create_identity(role="buyer", with_company=False)
        stranger_email, _, _ = await _create_identity(role="buyer", with_company=False)
        owner = await _login(owner_email, password)
        stranger = await _login(stranger_email, password)

        async with _client() as client:
            request = await client.post(
                "/api/v1/commerce/procurement-requests",
                headers=owner,
                json={"title": "No company ownership", "portal_key": "cebu"},
            )
            assert request.status_code == 201, request.text
            request_id = request.json()["id"]

            detail = await client.get(
                f"/api/v1/commerce/procurement-requests/{request_id}", headers=stranger
            )
            assert detail.status_code == 403

            listing = await client.get("/api/v1/commerce/procurement-requests", headers=stranger)
            assert listing.status_code == 200
            assert request_id not in {item["id"] for item in listing.json()["items"]}

    asyncio.run(_run())


def test_portal_grants_are_scoped_and_audit_grant_is_not_admin_wildcard():
    async def _run():
        await engine.dispose()
        email, _, _ = await _create_identity(role="buyer")
        async with async_session_factory() as db:
            from sqlalchemy import select

            user = (await db.execute(select(User).where(User.email == email))).scalar_one()
            suffix = uuid.uuid4().hex[:8]
            workspace_a = Workspace(name=f"Workspace A {suffix}", slug=f"ws-a-{suffix}")
            workspace_b = Workspace(name=f"Workspace B {suffix}", slug=f"ws-b-{suffix}")
            db.add_all([workspace_a, workspace_b])
            await db.flush()
            db.add_all(
                [
                    WorkspaceMembership(
                        workspace_id=workspace_a.id,
                        user_id=user.id,
                        company_id=user.company_id,
                        membership_type="admin_operator",
                        status="active",
                    ),
                    WorkspaceMembership(
                        workspace_id=workspace_b.id,
                        user_id=user.id,
                        company_id=user.company_id,
                        membership_type="admin_operator",
                        status="active",
                    ),
                    PortalGrant(
                        user_id=user.id,
                        workspace_id=workspace_a.id,
                        portal_key="admin_audit",
                        grant_key="admin.audit.read",
                        granted=True,
                    ),
                    PortalGrant(
                        user_id=user.id,
                        workspace_id=workspace_a.id,
                        portal_key="admin_finance",
                        grant_key="admin.finance.read",
                        granted=True,
                    ),
                ]
            )
            await db.commit()

            assert await user_has_grant(
                db,
                user.id,
                "admin.audit.read",
                workspace_id=workspace_a.id,
                portal_key="admin_audit",
            )
            assert not await user_has_grant(
                db,
                user.id,
                "admin.audit.read",
                workspace_id=workspace_b.id,
                portal_key="admin_audit",
            )
            assert not await user_has_grant(
                db,
                user.id,
                "admin.audit.read",
                workspace_id=workspace_a.id,
                portal_key="admin_finance",
            )
            assert not await user_has_grant(
                db,
                user.id,
                "admin.project.read",
                workspace_id=workspace_a.id,
                portal_key="admin_project",
            )

            portals = {item["portal_key"] for item in await list_user_portals(db, user.id)}
            assert "admin_audit" in portals
            assert "admin_finance" in portals
            assert "admin_project" not in portals
            assert "admin_executive" not in portals

            with pytest.raises(ValueError, match="workspace_id is required"):
                await resolve_workspace_scope(db, user_id=user.id, requested_workspace_id=None)
            with pytest.raises(PermissionError, match="Missing grants"):
                await switch_portal_audit(
                    db,
                    user_id=user.id,
                    portal_key="admin_finance",
                    workspace_id=workspace_b.id,
                )

    asyncio.run(_run())


def test_membership_lifecycle_and_workspace_status_fail_closed():
    async def _run():
        await engine.dispose()
        email, _, _ = await _create_identity(role="buyer")
        now = datetime.now(timezone.utc)
        async with async_session_factory() as db:
            user = (await db.execute(select(User).where(User.email == email))).scalar_one()
            suffix = uuid.uuid4().hex[:8]
            active = Workspace(name=f"Active {suffix}", slug=f"active-{suffix}", status="active")
            future = Workspace(name=f"Future {suffix}", slug=f"future-{suffix}", status="active")
            expired = Workspace(name=f"Expired {suffix}", slug=f"expired-{suffix}", status="active")
            stopped = Workspace(name=f"Stopped {suffix}", slug=f"stopped-{suffix}", status="suspended")
            db.add_all([active, future, expired, stopped])
            await db.flush()
            db.add_all(
                [
                    WorkspaceMembership(
                        workspace_id=active.id,
                        user_id=user.id,
                        membership_type="customer_owner",
                        status="active",
                        valid_from=now - timedelta(days=1),
                    ),
                    WorkspaceMembership(
                        workspace_id=future.id,
                        user_id=user.id,
                        membership_type="customer_owner",
                        status="active",
                        valid_from=now + timedelta(days=1),
                    ),
                    WorkspaceMembership(
                        workspace_id=expired.id,
                        user_id=user.id,
                        membership_type="customer_owner",
                        status="active",
                        valid_until=now - timedelta(seconds=1),
                    ),
                    WorkspaceMembership(
                        workspace_id=stopped.id,
                        user_id=user.id,
                        membership_type="customer_owner",
                        status="active",
                    ),
                ]
            )
            for workspace in (active, future, expired, stopped):
                db.add(
                    PortalGrant(
                        user_id=user.id,
                        workspace_id=workspace.id,
                        portal_key="customer_h5",
                        grant_key="portal.h5.customer",
                        granted=True,
                    )
                )
            await db.commit()

            memberships = await list_memberships(db, user.id)
            assert {membership.workspace_id for membership in memberships} == {active.id}
            assert await resolve_workspace_scope(
                db, user_id=user.id, requested_workspace_id=active.id
            ) == active.id
            for workspace in (future, expired, stopped):
                with pytest.raises(PermissionError, match="No active membership"):
                    await resolve_workspace_scope(
                        db, user_id=user.id, requested_workspace_id=workspace.id
                    )

    asyncio.run(_run())


def test_same_grant_key_can_be_scoped_to_independent_portals():
    async def _run():
        await engine.dispose()
        email, _, _ = await _create_identity(role="service_partner")
        async with async_session_factory() as db:
            user = (await db.execute(select(User).where(User.email == email))).scalar_one()
            suffix = uuid.uuid4().hex[:8]
            workspace = Workspace(name=f"Partner {suffix}", slug=f"partner-{suffix}")
            db.add(workspace)
            await db.flush()
            db.add(
                WorkspaceMembership(
                    workspace_id=workspace.id,
                    user_id=user.id,
                    membership_type="partner_company_owner",
                    status="active",
                )
            )
            pc = await ensure_grant(
                db,
                user_id=user.id,
                workspace_id=workspace.id,
                portal_key="partner_company_pc",
                grant_key="partner.rfq.read",
            )
            h5 = await ensure_grant(
                db,
                user_id=user.id,
                workspace_id=workspace.id,
                portal_key="partner_company_h5",
                grant_key="partner.rfq.read",
            )
            await db.commit()

            assert pc.id != h5.id
            assert await user_has_grant(
                db,
                user.id,
                "partner.rfq.read",
                workspace_id=workspace.id,
                portal_key="partner_company_pc",
            )
            assert await user_has_grant(
                db,
                user.id,
                "partner.rfq.read",
                workspace_id=workspace.id,
                portal_key="partner_company_h5",
            )

            pc.granted = False
            pc.revoked_at = datetime.now(timezone.utc)
            await db.commit()
            assert not await user_has_grant(
                db,
                user.id,
                "partner.rfq.read",
                workspace_id=workspace.id,
                portal_key="partner_company_pc",
            )
            assert await user_has_grant(
                db,
                user.id,
                "partner.rfq.read",
                workspace_id=workspace.id,
                portal_key="partner_company_h5",
            )

    asyncio.run(_run())


def test_field_worker_assignment_does_not_bypass_workspace_grant():
    async def _run():
        await engine.dispose()
        email, password, _ = await _create_identity(role="partner_worker")
        async with async_session_factory() as db:
            from sqlalchemy import select

            from app.models.field_service import FieldTask, TaskAssignment, WorkPackage

            user = (await db.execute(select(User).where(User.email == email))).scalar_one()
            suffix = uuid.uuid4().hex[:8]
            workspace_a = Workspace(name=f"Field A {suffix}", slug=f"field-a-{suffix}")
            workspace_b = Workspace(name=f"Field B {suffix}", slug=f"field-b-{suffix}")
            db.add_all([workspace_a, workspace_b])
            await db.flush()
            db.add_all(
                [
                    WorkspaceMembership(
                        workspace_id=workspace_a.id,
                        user_id=user.id,
                        company_id=user.company_id,
                        membership_type="field_worker",
                        status="active",
                    ),
                    WorkspaceMembership(
                        workspace_id=workspace_b.id,
                        user_id=user.id,
                        company_id=user.company_id,
                        membership_type="field_worker",
                        status="active",
                    ),
                    PortalGrant(
                        user_id=user.id,
                        workspace_id=workspace_a.id,
                        portal_key="field_worker",
                        grant_key="field_task.read_assigned",
                        granted=True,
                    ),
                ]
            )
            package_a = WorkPackage(workspace_id=workspace_a.id, title="Allowed package")
            package_b = WorkPackage(workspace_id=workspace_b.id, title="Blocked package")
            db.add_all([package_a, package_b])
            await db.flush()
            task_a = FieldTask(
                work_package_id=package_a.id, task_type="install", title="Allowed task"
            )
            task_b = FieldTask(
                work_package_id=package_b.id, task_type="install", title="Blocked task"
            )
            db.add_all([task_a, task_b])
            await db.flush()
            db.add_all(
                [
                    TaskAssignment(
                        field_task_id=task_a.id, assignee_user_id=user.id, status="active"
                    ),
                    TaskAssignment(
                        field_task_id=task_b.id, assignee_user_id=user.id, status="active"
                    ),
                ]
            )
            await db.commit()
            allowed_task_id = str(task_a.id)
            blocked_task_id = str(task_b.id)

        headers = await _login(email, password)
        async with _client() as client:
            today = await client.get("/api/v1/field/tasks/today", headers=headers)
            assert today.status_code == 200, today.text
            assert {item["id"] for item in today.json()["items"]} == {allowed_task_id}

            blocked_detail = await client.get(
                f"/api/v1/field/tasks/{blocked_task_id}", headers=headers
            )
            assert blocked_detail.status_code == 403

            blocked_sync = await client.post(
                "/api/v1/field/sync",
                headers=headers,
                json={
                    "items": [
                        {
                            "type": "status",
                            "task_id": blocked_task_id,
                            "idempotency_key": f"blocked-{uuid.uuid4().hex}",
                            "status": "in_progress",
                            "offline_version": 0,
                        }
                    ]
                },
            )
            assert blocked_sync.status_code == 200
            assert blocked_sync.json()["items"][0]["status"] == "rejected"
            assert blocked_sync.json()["items"][0]["detail"] == "workspace_grant_revoked"

    asyncio.run(_run())


def test_field_ops_project_manager_is_scoped_to_granted_workspace():
    async def _run():
        await engine.dispose()
        email, password, _ = await _create_identity(role="project_manager")
        async with async_session_factory() as db:
            from sqlalchemy import select

            user = (await db.execute(select(User).where(User.email == email))).scalar_one()
            suffix = uuid.uuid4().hex[:8]
            workspace_a = Workspace(name=f"Ops A {suffix}", slug=f"ops-a-{suffix}")
            workspace_b = Workspace(name=f"Ops B {suffix}", slug=f"ops-b-{suffix}")
            db.add_all([workspace_a, workspace_b])
            await db.flush()
            db.add_all(
                [
                    WorkspaceMembership(
                        workspace_id=workspace_a.id,
                        user_id=user.id,
                        company_id=user.company_id,
                        membership_type="project_manager",
                        status="active",
                    ),
                    WorkspaceMembership(
                        workspace_id=workspace_b.id,
                        user_id=user.id,
                        company_id=user.company_id,
                        membership_type="project_manager",
                        status="active",
                    ),
                    PortalGrant(
                        user_id=user.id,
                        workspace_id=workspace_a.id,
                        portal_key="admin_field_ops",
                        grant_key="admin.field_ops.read",
                        granted=True,
                    ),
                ]
            )
            await db.commit()
            workspace_a_id = str(workspace_a.id)
            workspace_b_id = str(workspace_b.id)

        headers = await _login(email, password)
        async with _client() as client:
            allowed = await client.post(
                "/api/v1/admin/field-ops/work-packages",
                headers=headers,
                json={"workspace_id": workspace_a_id, "title": "Allowed package"},
            )
            assert allowed.status_code == 201, allowed.text

            blocked = await client.post(
                "/api/v1/admin/field-ops/work-packages",
                headers=headers,
                json={"workspace_id": workspace_b_id, "title": "Blocked package"},
            )
            assert blocked.status_code == 403

            unscoped_list = await client.get("/api/v1/admin/field-ops/work-packages", headers=headers)
            assert unscoped_list.status_code == 400

    asyncio.run(_run())
