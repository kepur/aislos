"""Public projections must not expose future internal pricing or identifiers."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.core.security import create_access_token, hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.service import ServicePackage
from app.models.user import User


def test_service_package_public_projection_filters_internal_pricing():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            projection = ServicePackage(
                name=f"Projection {uuid.uuid4().hex[:8]}",
                slug=f"projection-{uuid.uuid4().hex}",
                public_visible=True,
                sort_order=0,
                price_rule_json={
                    "billing": "annual",
                    "term_label": "Annual",
                    "margin_percent": 45,
                    "supplier_cost": 100,
                },
            )
            package = ServicePackage(
                name=f"Published support {uuid.uuid4().hex[:8]}",
                slug=f"published-support-{uuid.uuid4().hex}",
                public_visible=True,
                sort_order=1,
                price_rule_json={
                    "billing": "annual",
                    "term_label": "Annual",
                    "margin_percent": 45,
                    "supplier_cost": 100,
                },
            )
            admin = User(
                email=f"projection-admin-{uuid.uuid4().hex[:8]}@example.com",
                password_hash=hash_password("projection-test"),
                role="admin",
                is_active=True,
            )
            db.add_all([projection, package, admin])
            await db.commit()
            admin_headers = {
                "Authorization": f"Bearer {create_access_token(str(admin.id), admin.role)}"
            }
            projection_id = str(projection.id)
            package_id = str(package.id)
            admin_id = str(admin.id)

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                public = await client.get("/api/v1/service-packages")
                assert public.status_code == 200, public.text
                assert not any(item["id"] == projection_id for item in public.json())
                row = next(item for item in public.json() if item["id"] == package_id)
                assert row["price_rule_json"] == {"billing": "annual", "term_label": "Annual"}
                assert "public_visible" not in row

                admin = await client.get(
                    "/api/v1/service-packages/admin/all", headers=admin_headers
                )
                assert admin.status_code == 200, admin.text
                assert any(item["id"] == projection_id for item in admin.json())
                admin_row = next(item for item in admin.json() if item["id"] == package_id)
                assert admin_row["price_rule_json"]["margin_percent"] == 45
        finally:
            async with async_session_factory() as db:
                await db.execute(
                    delete(ServicePackage).where(
                        ServicePackage.id.in_([uuid.UUID(projection_id), uuid.UUID(package_id)])
                    )
                )
                await db.execute(delete(User).where(User.id == uuid.UUID(admin_id)))
                await db.commit()

    asyncio.run(_run())
