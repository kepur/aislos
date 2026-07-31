"""Portal grants are exact Workspace/Portal/Region capabilities, never wildcards."""
import asyncio
import uuid

from app.core.security import hash_password
from app.db.session import async_session_factory, engine
from app.models.portal_access import PortalGrant, Workspace, WorkspaceMembership
from app.models.region import Region
from app.models.user import User
from app.services.portal_access import user_has_grant


def test_null_scope_grants_do_not_bypass_exact_scope_and_region():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            region_a = Region(code=f"A{uuid.uuid4().hex[:5]}", name="Region A", is_active=True)
            region_b = Region(code=f"B{uuid.uuid4().hex[:5]}", name="Region B", is_active=True)
            db.add_all([region_a, region_b])
            await db.flush()
            workspace = Workspace(
                name="Strict scope workspace",
                slug=f"strict-{uuid.uuid4().hex[:10]}",
                region_id=region_a.id,
                status="active",
            )
            user = User(
                email=f"strict-scope-{uuid.uuid4().hex[:10]}@example.com",
                password_hash=hash_password("strict-scope-123"),
                role="buyer",
                is_active=True,
            )
            db.add_all([workspace, user])
            await db.flush()
            db.add(
                WorkspaceMembership(
                    workspace_id=workspace.id,
                    user_id=user.id,
                    membership_type="customer_owner",
                    status="active",
                )
            )
            db.add_all(
                [
                    PortalGrant(
                        user_id=user.id,
                        workspace_id=None,
                        portal_key=None,
                        grant_key="scope.global.legacy",
                        granted=True,
                    ),
                    PortalGrant(
                        user_id=user.id,
                        workspace_id=workspace.id,
                        portal_key=None,
                        grant_key="scope.portal.legacy",
                        granted=True,
                    ),
                    PortalGrant(
                        user_id=user.id,
                        workspace_id=workspace.id,
                        portal_key="customer_h5",
                        grant_key="scope.region",
                        granted=True,
                        scope_json={"allowed_region_ids": [str(region_a.id)]},
                    ),
                ]
            )
            await db.commit()

            assert not await user_has_grant(
                db,
                user.id,
                "scope.global.legacy",
                workspace_id=workspace.id,
                portal_key="customer_h5",
            )
            assert not await user_has_grant(
                db,
                user.id,
                "scope.portal.legacy",
                workspace_id=workspace.id,
                portal_key="customer_h5",
            )
            assert not await user_has_grant(
                db,
                user.id,
                "scope.region",
                workspace_id=workspace.id,
                portal_key="customer_h5",
            )
            assert await user_has_grant(
                db,
                user.id,
                "scope.region",
                workspace_id=workspace.id,
                portal_key="customer_h5",
                region_id=region_a.id,
            )
            assert not await user_has_grant(
                db,
                user.id,
                "scope.region",
                workspace_id=workspace.id,
                portal_key="customer_h5",
                region_id=region_b.id,
            )

    asyncio.run(_run())
