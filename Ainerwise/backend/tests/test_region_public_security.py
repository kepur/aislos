"""Public region discovery exposes active customer-safe projections only."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient

from app.db.session import async_session_factory, engine
from app.main import app
from app.models.region import Region


def test_public_regions_hide_inactive_and_tax_rules():
    async def _run():
        await engine.dispose()
        suffix = uuid.uuid4().hex[:6]
        async with async_session_factory() as db:
            active = Region(
                code=f"A{suffix}",
                name=f"Active {suffix}",
                is_active=True,
                tax_rules_json={"vat_rate": 99, "internal_rule": "secret"},
            )
            inactive = Region(
                code=f"I{suffix}",
                name=f"Inactive {suffix}",
                is_active=False,
                tax_rules_json={"vat_rate": 88},
            )
            db.add_all([active, inactive])
            await db.commit()
            active_id, inactive_id = active.id, inactive.id

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            listing = await client.get("/api/v1/regions?limit=100")
            assert listing.status_code == 200, listing.text
            rows = {row["id"]: row for row in listing.json()["items"]}
            assert str(active_id) in rows
            assert str(inactive_id) not in rows
            assert "tax_rules_json" not in rows[str(active_id)]
            assert "is_active" not in rows[str(active_id)]

            hidden = await client.get(f"/api/v1/regions/{inactive_id}")
            assert hidden.status_code == 404, hidden.text

    asyncio.run(_run())
