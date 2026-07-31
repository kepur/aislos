import asyncio
import uuid

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.notification import NotificationPreference
from app.models.portal_access import PortalGrant, Workspace, WorkspaceMembership
from app.models.user import User


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _create_user(role: str = "buyer") -> tuple[User, str]:
    password = "privacy123"
    async with async_session_factory() as db:
        user = User(
            email=f"privacy-{uuid.uuid4().hex[:10]}@example.com",
            phone="+381601234567",
            password_hash=hash_password(password),
            full_name="Privacy User",
            role=role,
            is_active=True,
        )
        db.add(user)
        await db.flush()
        workspace = Workspace(name=f"Privacy {user.id}", slug=f"privacy-{uuid.uuid4().hex[:10]}")
        db.add(workspace)
        await db.flush()
        db.add_all(
            [
                WorkspaceMembership(
                    workspace_id=workspace.id,
                    user_id=user.id,
                    membership_type="customer_owner",
                    status="active",
                ),
                PortalGrant(
                    workspace_id=workspace.id,
                    user_id=user.id,
                    portal_key="customer_h5",
                    grant_key="customer.projects.read",
                    granted=True,
                ),
                NotificationPreference(
                    user_id=user.id,
                    email_enabled=True,
                    email=user.email,
                    whatsapp_enabled=True,
                    whatsapp_number=user.phone,
                ),
            ]
        )
        await db.commit()
        await db.refresh(user)
        return user, password


async def _login(email: str, password: str) -> dict:
    async with _client() as client:
        response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_privacy_export_is_owned_and_excludes_password_hash():
    async def _run():
        await engine.dispose()
        owner, password = await _create_user()
        stranger, stranger_password = await _create_user()
        owner_headers = await _login(owner.email, password)
        stranger_headers = await _login(stranger.email, stranger_password)

        async with _client() as client:
            created = await client.post("/api/v1/privacy/export", headers=owner_headers)
            assert created.status_code == 200, created.text
            request_id = created.json()["id"]

            denied = await client.get(f"/api/v1/privacy/exports/{request_id}", headers=stranger_headers)
            assert denied.status_code == 404

            downloaded = await client.get(f"/api/v1/privacy/exports/{request_id}", headers=owner_headers)
            assert downloaded.status_code == 200, downloaded.text
            payload = downloaded.json()
            assert payload["user_id"] == str(owner.id)
            assert payload["data"]["profile"]["email"] == owner.email
            assert "password_hash" not in payload["data"]["profile"]
            assert payload["data"]["workspace_memberships"]

    asyncio.run(_run())


def test_deletion_requires_admin_and_anonymizes_access_without_deleting_user():
    async def _run():
        await engine.dispose()
        target, password = await _create_user()
        stranger, stranger_password = await _create_user()
        target_headers = await _login(target.email, password)
        stranger_headers = await _login(stranger.email, stranger_password)
        admin_headers = await _login("admin@ainerwise.com", "admin123456")

        async with _client() as client:
            requested = await client.post("/api/v1/privacy/delete-request", headers=target_headers)
            assert requested.status_code == 200, requested.text
            request_id = requested.json()["id"]

            forbidden = await client.post(
                f"/api/v1/admin/privacy/requests/{request_id}/complete",
                headers=stranger_headers,
                json={"reason": "not allowed"},
            )
            assert forbidden.status_code == 403

            completed = await client.post(
                f"/api/v1/admin/privacy/requests/{request_id}/complete",
                headers=admin_headers,
                json={"reason": "Identity verified"},
            )
            assert completed.status_code == 200, completed.text
            assert completed.json()["status"] == "completed"

        async with async_session_factory() as db:
            user = await db.get(User, target.id)
            assert user is not None
            assert user.is_active is False
            assert user.email == f"deleted+{target.id}@privacy.invalid"
            memberships = (
                await db.execute(select(WorkspaceMembership).where(WorkspaceMembership.user_id == target.id))
            ).scalars().all()
            grants = (
                await db.execute(select(PortalGrant).where(PortalGrant.user_id == target.id))
            ).scalars().all()
            pref = (
                await db.execute(select(NotificationPreference).where(NotificationPreference.user_id == target.id))
            ).scalar_one()
            assert memberships and all(item.status == "inactive" for item in memberships)
            assert grants and all(item.granted is False for item in grants)
            assert pref.email is None and pref.whatsapp_number is None

        async with _client() as client:
            login = await client.post(
                "/api/v1/auth/login",
                json={"email": target.email, "password": password},
            )
            assert login.status_code == 401

    asyncio.run(_run())


def test_user_can_cancel_pending_deletion_request():
    async def _run():
        await engine.dispose()
        user, password = await _create_user()
        headers = await _login(user.email, password)
        async with _client() as client:
            requested = await client.post("/api/v1/privacy/delete-request", headers=headers)
            request_id = requested.json()["id"]
            cancelled = await client.post(
                f"/api/v1/privacy/requests/{request_id}/cancel",
                headers=headers,
            )
            assert cancelled.status_code == 200
            assert cancelled.json()["status"] == "cancelled"

    asyncio.run(_run())


def test_admin_cannot_approve_own_deletion_or_delete_super_admin():
    async def _run():
        await engine.dispose()
        admin, admin_password = await _create_user(role="admin")
        super_admin, super_admin_password = await _create_user(role="super_admin")
        admin_headers = await _login(admin.email, admin_password)
        super_admin_headers = await _login(super_admin.email, super_admin_password)

        async with _client() as client:
            own_request = await client.post("/api/v1/privacy/delete-request", headers=admin_headers)
            own_result = await client.post(
                f"/api/v1/admin/privacy/requests/{own_request.json()['id']}/complete",
                headers=admin_headers,
                json={"reason": "self approval"},
            )
            assert own_result.status_code == 409

            super_request = await client.post("/api/v1/privacy/delete-request", headers=super_admin_headers)
            elevated_result = await client.post(
                f"/api/v1/admin/privacy/requests/{super_request.json()['id']}/complete",
                headers=admin_headers,
                json={"reason": "insufficient privilege"},
            )
            assert elevated_result.status_code == 403

        async with async_session_factory() as db:
            preserved_admin = await db.get(User, admin.id)
            preserved_super_admin = await db.get(User, super_admin.id)
            assert preserved_admin is not None and preserved_admin.is_active is True
            assert preserved_super_admin is not None and preserved_super_admin.is_active is True

    asyncio.run(_run())
