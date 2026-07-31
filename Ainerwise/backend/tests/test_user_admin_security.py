"""Security boundaries for global and Cebu user administration."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.security import create_access_token, hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.audit import AuditLog
from app.models.portal_access import PortalGrant, WorkspaceMembership
from app.models.user import User
from app.services.portal_access import sync_role_portal_access


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _create_user(role: str) -> tuple[uuid.UUID, dict]:
    suffix = uuid.uuid4().hex[:10]
    async with async_session_factory() as db:
        row = User(
            email=f"user-admin-{role}-{suffix}@example.com",
            password_hash=hash_password("user-admin-security-123"),
            full_name=f"User Admin {role}",
            role=role,
            is_active=True,
        )
        db.add(row)
        await db.flush()
        await sync_role_portal_access(db, user_id=row.id, role=row.role)
        await db.commit()
        return row.id, {
            "Authorization": f"Bearer {create_access_token(str(row.id), row.role)}"
        }


def test_user_admin_role_and_active_lifecycle_is_secure():
    async def _run():
        await engine.dispose()
        admin_id, admin_headers = await _create_user("admin")
        super_id, super_headers = await _create_user("super_admin")
        target_id, target_headers = await _create_user("buyer")

        async with _client() as client:
            invalid_role = await client.patch(
                f"/api/v1/users/{target_id}/role",
                params={"role": "root"},
                headers=admin_headers,
            )
            assert invalid_role.status_code == 422, invalid_role.text

            self_role = await client.patch(
                f"/api/v1/users/{admin_id}/role",
                params={"role": "buyer"},
                headers=admin_headers,
            )
            assert self_role.status_code == 409, self_role.text

            promote = await client.patch(
                f"/api/v1/users/{target_id}/role",
                params={"role": "super_admin"},
                headers=admin_headers,
            )
            assert promote.status_code == 403, promote.text

            manage_super_role = await client.patch(
                f"/api/v1/users/{super_id}/role",
                params={"role": "admin"},
                headers=admin_headers,
            )
            assert manage_super_role.status_code == 403, manage_super_role.text

            manage_super_active = await client.patch(
                f"/api/v1/users/{super_id}/active",
                params={"is_active": False},
                headers=admin_headers,
            )
            assert manage_super_active.status_code == 403, manage_super_active.text

            cebu_manage_super_active = await client.patch(
                f"/api/v1/admin/cebu/users/{super_id}/active",
                headers=admin_headers,
                json={"status": "inactive", "reason": "must be rejected"},
            )
            assert cebu_manage_super_active.status_code == 403, cebu_manage_super_active.text

            self_deactivate = await client.patch(
                f"/api/v1/users/{admin_id}/active",
                params={"is_active": False},
                headers=admin_headers,
            )
            assert self_deactivate.status_code == 409, self_deactivate.text

            deactivate = await client.patch(
                f"/api/v1/users/{target_id}/active",
                params={"is_active": False},
                headers=admin_headers,
            )
            assert deactivate.status_code == 200, deactivate.text
            assert deactivate.json()["is_active"] is False

            old_token = await client.get("/api/v1/auth/me/portals", headers=target_headers)
            assert old_token.status_code == 401, old_token.text

        async with async_session_factory() as db:
            memberships = list(
                (
                    await db.execute(
                        select(WorkspaceMembership).where(
                            WorkspaceMembership.user_id == target_id
                        )
                    )
                ).scalars()
            )
            grants = list(
                (
                    await db.execute(
                        select(PortalGrant).where(PortalGrant.user_id == target_id)
                    )
                ).scalars()
            )
            assert memberships and all(row.status == "suspended" for row in memberships)
            assert grants and all(not row.granted and row.revoked_at is not None for row in grants)

        async with _client() as client:
            reactivate = await client.patch(
                f"/api/v1/users/{target_id}/active",
                params={"is_active": True},
                headers=admin_headers,
            )
            assert reactivate.status_code == 200, reactivate.text
            assert reactivate.json()["is_active"] is True

            change_role = await client.patch(
                f"/api/v1/users/{target_id}/role",
                params={"role": "vendor"},
                headers=super_headers,
            )
            assert change_role.status_code == 200, change_role.text
            assert change_role.json()["role"] == "vendor"

            restored_portals = await client.get("/api/v1/auth/me/portals", headers=target_headers)
            assert restored_portals.status_code == 200, restored_portals.text
            portal_keys = {item["portal_key"] for item in restored_portals.json()["items"]}
            assert {"supplier_pc", "supplier_h5"} <= portal_keys
            assert "customer_pc" not in portal_keys

        async with async_session_factory() as db:
            actions = set(
                (
                    await db.execute(
                        select(AuditLog.action).where(
                            AuditLog.entity_id == target_id,
                            AuditLog.action.in_(
                                ("identity.user_active_changed", "identity.user_role_changed")
                            ),
                        )
                    )
                ).scalars()
            )
            assert actions == {"identity.user_active_changed", "identity.user_role_changed"}

    asyncio.run(_run())
