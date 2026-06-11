from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.platform_setting import PlatformSetting


MAP_SETTING_KEYS = {
    "MAPS_PROVIDER": settings.MAPS_PROVIDER,
    "GOOGLE_MAPS_API_KEY": settings.GOOGLE_MAPS_API_KEY,
    "GOOGLE_MAPS_REGION": "PH",
    "GOOGLE_MAPS_LANGUAGE": "en",
    "MAPS_CACHE_TTL_SECONDS": "86400",
    "MAPS_ENABLED": "true",
}


async def get_maps_config(db: AsyncSession) -> dict:
    result = await db.execute(select(PlatformSetting).where(PlatformSetting.key.in_(list(MAP_SETTING_KEYS.keys()))))
    kv = {row.key: row.value for row in result.scalars().all()}

    provider = (kv.get("MAPS_PROVIDER") or MAP_SETTING_KEYS["MAPS_PROVIDER"] or "LOCAL").upper()
    return {
        "provider": provider,
        "google_maps_api_key": kv.get("GOOGLE_MAPS_API_KEY") or MAP_SETTING_KEYS["GOOGLE_MAPS_API_KEY"] or "",
        "google_maps_region": (kv.get("GOOGLE_MAPS_REGION") or MAP_SETTING_KEYS["GOOGLE_MAPS_REGION"] or "PH").upper(),
        "google_maps_language": (kv.get("GOOGLE_MAPS_LANGUAGE") or MAP_SETTING_KEYS["GOOGLE_MAPS_LANGUAGE"] or "en"),
        "maps_cache_ttl_seconds": int(kv.get("MAPS_CACHE_TTL_SECONDS") or MAP_SETTING_KEYS["MAPS_CACHE_TTL_SECONDS"] or "86400"),
        "maps_enabled": (kv.get("MAPS_ENABLED") or MAP_SETTING_KEYS["MAPS_ENABLED"] or "true").lower() == "true",
    }
