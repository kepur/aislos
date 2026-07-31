"""MI06: Marketing must not call media generation providers inline."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient

from app.db.session import async_session_factory, engine
from app.main import app
from app.models.marketing import MarketingCreativeBrief


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _admin_headers() -> dict:
    async with _client() as client:
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@ainerwise.com", "password": "admin123456"},
        )
        assert login.status_code == 200, login.text
        return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_no_images_generations_in_marketing_paths():
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    pattern = re.compile(r"images/generations|image_model|video_model")
    hits: list[str] = []
    for sub in ("api", "services"):
        base = root / "app" / sub
        for path in base.rglob("*.py"):
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if pattern.search(line):
                    hits.append(f"{path.relative_to(root)}:{lineno}:{line.strip()}")
    assert not hits, "Forbidden media provider refs:\n" + "\n".join(hits)


def test_generate_image_deprecated_creates_brief():
    async def _run():
        await engine.dispose()
        headers = await _admin_headers()
        async with _client() as client:
            resp = await client.post(
                "/api/v1/admin/marketing/generate-image",
                headers=headers,
                json={"prompt": "Luxury villa smart home hero shot"},
            )
        assert resp.status_code == 202, resp.text
        body = resp.json()
        assert body["deprecated"] is True
        assert body.get("brief_id")
        assert body.get("version_id")
        assert "asset_id" not in body
        assert "media_key" not in body

        async with async_session_factory() as db:
            brief = await db.get(MarketingCreativeBrief, uuid.UUID(body["brief_id"]))
            assert brief is not None
            assert brief.status == "draft"

    asyncio.run(_run())
