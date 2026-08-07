from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.deps import AdminUser, DB
from app.models.admin_config import PlatformSetting
from app.models.region import Region
from app.schemas.region import RegionPublicRead
from app.services import ai_agent

router = APIRouter(prefix="/localization", tags=["localization"])

LOCALE_OPTIONS = [
    {"code": "EN", "locale": "en", "uri_prefix": "en", "label": "English"},
    {"code": "ZH", "locale": "zh", "uri_prefix": "cn", "label": "中文"},
    {"code": "SR", "locale": "sr", "uri_prefix": "rs", "label": "Srpski"},
    {"code": "BS", "locale": "bs", "uri_prefix": "ba", "label": "Bosanski"},
    {"code": "PL", "locale": "pl", "uri_prefix": "pl", "label": "Polski"},
    {"code": "DE", "locale": "de", "uri_prefix": "de", "label": "Deutsch"},
    {"code": "RO", "locale": "ro", "uri_prefix": "ro", "label": "Romana"},
]

LOCALE_BY_PREFIX = {item["uri_prefix"]: item for item in LOCALE_OPTIONS}

LOCALIZATION_DEFAULTS: dict[str, dict[str, Any]] = {
    "enabled_locale_prefixes": {
        "value": ["en", "cn", "rs", "pl"],
        "description": "Enabled URI language prefixes for every public/admin portal. Example: /cn, /rs.",
    },
    "default_locale_prefix": {
        "value": "en",
        "description": "Default URI language prefix used when no user preference exists.",
    },
    "enabled_region_codes": {
        "value": ["RS", "PL", "RO", "CN", "PH", "NZ", "AU"],
        "description": "Regions that can be selected by frontends and admin localization controls.",
    },
    "machine_translation_enabled": {
        "value": False,
        "description": "Allow admin-triggered AI translation drafts. Drafts still require human review.",
    },
    "translation_review_required": {
        "value": True,
        "description": "AI translations are never published automatically.",
    },
    "translation_provider_category": {
        "value": "ai",
        "description": "Integration category used for translation drafts.",
    },
}

LEGACY_MARKET_SETTING_MAP = {
    "enabled_locale_prefixes": "market_enabled_locale_prefixes",
    "default_locale_prefix": "market_default_locale_prefix",
    "enabled_region_codes": "market_enabled_region_codes",
}


def _setting_value(row: PlatformSetting | None, default: Any) -> Any:
    if row is None:
        return default
    payload = row.value_json or {}
    if isinstance(payload, dict) and "value" in payload:
        return payload["value"]
    return payload


def _as_list(value: Any, *, upper: bool = False) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        items = [item.strip() for item in value.split(",")]
    elif isinstance(value, (list, tuple, set)):
        items = [str(item).strip() for item in value]
    else:
        items = [str(value).strip()]
    normalized = [item.upper() if upper else item.lower() for item in items if item]
    return list(dict.fromkeys(normalized))


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on", "enabled"}
    return bool(value)


async def _localization_rows(db: DB) -> dict[str, PlatformSetting]:
    keys = set(LOCALIZATION_DEFAULTS.keys()) | set(LEGACY_MARKET_SETTING_MAP.values())
    rows = list(
        (
            await db.execute(
                select(PlatformSetting).where(
                    PlatformSetting.portal_key.in_(["global", "admin_cebu"]),
                    PlatformSetting.key.in_(keys),
                )
            )
        ).scalars()
    )
    by_key: dict[str, PlatformSetting] = {}
    for row in rows:
        if row.portal_key == "global":
            by_key[row.key] = row
        elif row.key in LEGACY_MARKET_SETTING_MAP.values():
            # Legacy AISLOS Market settings remain a read fallback until global settings are saved.
            global_key = next(key for key, legacy_key in LEGACY_MARKET_SETTING_MAP.items() if legacy_key == row.key)
            by_key.setdefault(global_key, row)
    return by_key


async def _localization_payload(db: DB) -> dict[str, Any]:
    row_by_key = await _localization_rows(db)
    defaults = {key: payload["value"] for key, payload in LOCALIZATION_DEFAULTS.items()}
    enabled_prefixes = [
        prefix
        for prefix in _as_list(_setting_value(row_by_key.get("enabled_locale_prefixes"), defaults["enabled_locale_prefixes"]))
        if prefix in LOCALE_BY_PREFIX
    ]
    if not enabled_prefixes:
        enabled_prefixes = ["en"]
    default_prefix = str(_setting_value(row_by_key.get("default_locale_prefix"), defaults["default_locale_prefix"])).strip().lower() or "en"
    if default_prefix not in enabled_prefixes:
        default_prefix = enabled_prefixes[0]
    enabled_region_codes = _as_list(
        _setting_value(row_by_key.get("enabled_region_codes"), defaults["enabled_region_codes"]),
        upper=True,
    )
    machine_translation_enabled = _as_bool(
        _setting_value(row_by_key.get("machine_translation_enabled"), defaults["machine_translation_enabled"])
    )
    translation_review_required = _as_bool(
        _setting_value(row_by_key.get("translation_review_required"), defaults["translation_review_required"])
    )
    translation_provider_category = str(
        _setting_value(row_by_key.get("translation_provider_category"), defaults["translation_provider_category"])
    )

    region_query = select(Region).where(Region.is_active.is_(True)).order_by(Region.name.asc())
    if enabled_region_codes:
        region_query = region_query.where(Region.code.in_(enabled_region_codes))
    regions = list((await db.execute(region_query)).scalars())

    return {
        "default_locale_prefix": default_prefix,
        "supported_locales": [LOCALE_BY_PREFIX[prefix] for prefix in enabled_prefixes],
        "enabled_region_codes": enabled_region_codes,
        "supported_regions": [RegionPublicRead.model_validate(region) for region in regions],
        "translation_policy": {
            "machine_translation_enabled": machine_translation_enabled,
            "review_required": translation_review_required,
            "provider_category": translation_provider_category,
            "ai_output_policy": "draft_only",
        },
    }


@router.get("/config")
async def localization_config(db: DB):
    return await _localization_payload(db)


class LocalizationConfigUpdate(BaseModel):
    enabled_locale_prefixes: list[str] | str | None = None
    default_locale_prefix: str | None = None
    enabled_region_codes: list[str] | str | None = None
    machine_translation_enabled: bool | None = None
    translation_review_required: bool | None = None
    translation_provider_category: str | None = Field(default=None, max_length=50)


async def _upsert_setting(db: DB, key: str, value: Any) -> None:
    row = (
        await db.execute(
            select(PlatformSetting).where(
                PlatformSetting.portal_key == "global",
                PlatformSetting.key == key,
            )
        )
    ).scalar_one_or_none()
    description = LOCALIZATION_DEFAULTS[key]["description"]
    if row is None:
        row = PlatformSetting(
            portal_key="global",
            key=key,
            value_json={"value": value},
            description=description,
        )
        db.add(row)
    else:
        row.value_json = {"value": value}
        row.description = description


@router.put("/config")
async def update_localization_config(data: LocalizationConfigUpdate, db: DB, admin: AdminUser):
    current = await _localization_payload(db)

    enabled_prefixes = _as_list(
        data.enabled_locale_prefixes if data.enabled_locale_prefixes is not None
        else [item["uri_prefix"] for item in current["supported_locales"]],
    )
    enabled_prefixes = [prefix for prefix in enabled_prefixes if prefix in LOCALE_BY_PREFIX]
    if not enabled_prefixes:
        raise HTTPException(status_code=400, detail="At least one supported locale prefix is required")

    default_prefix = (data.default_locale_prefix or current["default_locale_prefix"]).strip().lower()
    if default_prefix not in enabled_prefixes:
        raise HTTPException(status_code=400, detail="Default locale prefix must be enabled")

    region_codes = _as_list(
        data.enabled_region_codes if data.enabled_region_codes is not None
        else current["enabled_region_codes"],
        upper=True,
    )
    machine_translation_enabled = (
        data.machine_translation_enabled
        if data.machine_translation_enabled is not None
        else current["translation_policy"]["machine_translation_enabled"]
    )
    translation_review_required = (
        data.translation_review_required
        if data.translation_review_required is not None
        else current["translation_policy"]["review_required"]
    )
    provider_category = (
        data.translation_provider_category
        or current["translation_policy"]["provider_category"]
        or "ai"
    )

    await _upsert_setting(db, "enabled_locale_prefixes", enabled_prefixes)
    await _upsert_setting(db, "default_locale_prefix", default_prefix)
    await _upsert_setting(db, "enabled_region_codes", region_codes)
    await _upsert_setting(db, "machine_translation_enabled", bool(machine_translation_enabled))
    await _upsert_setting(db, "translation_review_required", bool(translation_review_required))
    await _upsert_setting(db, "translation_provider_category", provider_category)
    await db.commit()
    return await _localization_payload(db)


class TranslationDraftItem(BaseModel):
    key: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1, max_length=5000)


class TranslationDraftRequest(BaseModel):
    source_locale: str = Field(default="en", max_length=20)
    target_locale: str = Field(max_length=20)
    context: str | None = Field(default=None, max_length=1000)
    items: list[TranslationDraftItem] = Field(min_length=1, max_length=200)


@router.post("/admin/translate-draft")
async def translate_draft(data: TranslationDraftRequest, db: DB, admin: AdminUser):
    config = await _localization_payload(db)
    if not config["translation_policy"]["machine_translation_enabled"]:
        return {"configured": False, "reason": "machine_translation_disabled", "items": []}
    if not await ai_agent.is_configured(db):
        return {"configured": False, "reason": "ai_integration_not_configured", "items": []}

    source = data.source_locale.strip() or "en"
    target = data.target_locale.strip()
    prompt_payload = {
        "source_locale": source,
        "target_locale": target,
        "context": data.context or "AinerWise / AISLOS platform UI and content localization.",
        "items": [item.model_dump() for item in data.items],
    }
    raw = await ai_agent.chat(
        db,
        [
            {
                "role": "system",
                "content": (
                    "You are a professional software localization translator for AinerWise/AISLOS. "
                    "Translate UI labels, cards, demo copy, articles, and admin content faithfully. "
                    "Preserve placeholders like {name}, {{count}}, HTML tags, Markdown links, IDs, "
                    "product codes, URLs, and currency symbols. Return only compact JSON with "
                    '{"items":[{"key":"...","text":"..."}]}. Do not publish; this is an admin review draft.'
                ),
            },
            {"role": "user", "content": json.dumps(prompt_payload, ensure_ascii=False)},
        ],
        temperature=0.2,
        max_tokens=6000,
        response_json=True,
    )
    if raw is None:
        return {"configured": True, "reason": "ai_translation_failed", "items": []}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {"items": [{"key": item.key, "text": ""} for item in data.items], "raw": raw}
    return {
        "configured": True,
        "review_required": config["translation_policy"]["review_required"],
        "source_locale": source,
        "target_locale": target,
        "items": parsed.get("items", []),
    }
