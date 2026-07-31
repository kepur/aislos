"""Public projections must not expose future internal pricing or identifiers."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token, hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.service import ServicePackage
from app.models.user import User


def test_service_package_public_projection_filters_internal_pricing():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            package = ServicePackage(
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
            admin = User(
                email=f"projection-admin-{uuid.uuid4().hex[:8]}@example.com",
                password_hash=hash_password("projection-test"),
                role="admin",
                is_active=True,
            )
            db.add_all([package, admin])
            await db.commit()
            admin_headers = {
                "Authorization": f"Bearer {create_access_token(str(admin.id), admin.role)}"
            }
            package_id = str(package.id)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            public = await client.get("/api/v1/service-packages")
            assert public.status_code == 200, public.text
            row = next(item for item in public.json() if item["id"] == package_id)
            assert row["price_rule_json"] == {"billing": "annual", "term_label": "Annual"}
            assert "public_visible" not in row

            admin = await client.get(
                "/api/v1/service-packages/admin/all", headers=admin_headers
            )
            assert admin.status_code == 200, admin.text
            admin_row = next(item for item in admin.json() if item["id"] == package_id)
            assert admin_row["price_rule_json"]["margin_percent"] == 45

    asyncio.run(_run())
