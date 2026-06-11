"""Tests for admin integration settings + AI assistant fallback."""
import asyncio

from app.db.session import async_session_factory, engine
from app.main import app
from app.services import ai_agent
from app.services.integrations import mask_config


def test_mask_config_hides_secrets():
    masked = mask_config("ai", {"base_url": "x", "api_key": "secret", "_enabled": True})
    assert masked["api_key_set"] is True
    assert "api_key" not in masked
    assert masked["base_url"] == "x"
    assert "_enabled" not in masked
    tg = mask_config("telegram", {"bot_token": "", "admin_chat_id": "123"})
    assert tg["bot_token_set"] is False and tg["admin_chat_id"] == "123"
    voice = mask_config("voice", {"api_key": "secret", "model": "gpt-realtime"})
    assert voice["api_key_set"] is True and "api_key" not in voice


def test_integration_routes_registered():
    paths = {r.path for r in app.routes}
    for p in (
        "/api/v1/admin/integrations",
        "/api/v1/admin/integrations/{category}",
        "/api/v1/admin/integrations/smtp/test",
        "/api/v1/admin/integrations/telegram/test",
        "/api/v1/admin/integrations/ai/test",
        "/api/v1/admin/integrations/voice/test",
        "/api/v1/ai/assistant",
        "/api/v1/ai/assistant/status",
    ):
        assert p in paths, p


def test_voice_is_a_separate_integration_category():
    from app.models.settings import INTEGRATION_CATEGORIES

    assert "ai" in INTEGRATION_CATEGORIES
    assert "voice" in INTEGRATION_CATEGORIES


def test_ai_assistant_fallback_when_unconfigured():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            # ensure ai disabled
            from app.services.integrations import upsert_config
            await upsert_config(db, "ai", config={}, is_enabled=False)
            res = await ai_agent.run_assistant(db, category="storage", messages=[{"role": "user", "content": "hi"}])
            assert res["configured"] is False
            assert await ai_agent.is_configured(db) is False
    asyncio.run(_run())


def test_category_fields_cover_storage_kitchen_water():
    for cat in ("storage", "kitchen", "water", "energy", "factory"):
        assert cat in ai_agent.CATEGORY_FIELDS and ai_agent.CATEGORY_FIELDS[cat]
