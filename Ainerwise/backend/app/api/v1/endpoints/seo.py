"""SEO Engine v1.

Two layers live here:
- SEO pages: AI-assisted keyword landing pages rendered at /insights/{slug}.
- SEO control center: global public-site meta strategy, regional overrides, and
  batch optimization drafts for PC/H5/Store. Drafts are review-first; this API
  never publishes generated SEO automatically.
"""
import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.api.deps import DB, AdminUser
from app.api.v1.endpoints.localization import _localization_payload
from app.core.config import settings
from app.models.ai import AIReview
from app.models.admin_config import PlatformSetting
from app.models.content import SeoPage
from app.services import ai_agent
from app.services.agent_runtime import AgentAuthorizationError, require_agent

router = APIRouter(tags=["seo"])

SEO_CONFIG_KEY = "seo_automation_v1"
SEO_BATCH_DRAFT_KEY = "seo_last_batch_draft_v1"

STATIC_PAGE_CATALOG: list[dict[str, Any]] = [
    {
        "path": "/",
        "key": "home",
        "priority": 1.0,
        "title": {
            "en": "AinerWise | AI Smart Building, Procurement and Lifecycle Service",
            "zh": "AinerWise | AI 智能建筑、采购与全生命周期服务",
            "sr": "AinerWise | AI pametne zgrade, nabavka i servis",
            "pl": "AinerWise | AI inteligentne budynki, zakupy i serwis",
        },
        "description": {
            "en": "Tell AinerWise what you need. AI helps design, source, compare, procure, deliver and maintain smart building solutions.",
            "zh": "告诉 AinerWise 你的需求，AI 协助完成方案设计、采购比价、交付安装和长期维护。",
            "sr": "Recite AinerWise šta vam treba. AI pomaže u dizajnu, nabavci, poređenju, isporuci i održavanju pametnih zgrada.",
            "pl": "Powiedz AinerWise, czego potrzebujesz. AI pomaga projektować, kupować, porównywać, wdrażać i utrzymywać inteligentne budynki.",
        },
    },
    {
        "path": "/solutions",
        "key": "solutions",
        "priority": 0.9,
        "title": {
            "en": "Smart Building Solutions | AinerWise",
            "zh": "智能建筑解决方案 | AinerWise",
            "sr": "Rešenja za pametne zgrade | AinerWise",
            "pl": "Rozwiązania inteligentnych budynków | AinerWise",
        },
        "description": {
            "en": "AI-assisted smart building solutions for villas, hotels, offices, retail, solar, energy, CCTV, access control, HVAC and KNX projects.",
            "zh": "面向别墅、酒店、办公室、零售、光伏、能源、监控、门禁、暖通和 KNX 项目的 AI 智能建筑解决方案。",
            "sr": "AI rešenja za vile, hotele, kancelarije, maloprodaju, solar, energiju, CCTV, pristup, HVAC i KNX projekte.",
            "pl": "Rozwiązania AI dla willi, hoteli, biur, sklepów, fotowoltaiki, energii, CCTV, kontroli dostępu, HVAC i KNX.",
        },
    },
    {
        "path": "/products",
        "key": "products",
        "priority": 0.9,
        "title": {
            "en": "Verified Smart Building Product Catalog | AinerWise",
            "zh": "认证智能建筑产品目录 | AinerWise",
            "sr": "Provereni katalog proizvoda za pametne zgrade | AinerWise",
            "pl": "Zweryfikowany katalog produktów smart building | AinerWise",
        },
        "description": {
            "en": "Explore verified smart building hardware with AI procurement, China supply chain, local installation and lifecycle support.",
            "zh": "浏览认证智能建筑硬件，支持 AI 采购、中国供应链、本地安装和生命周期服务。",
            "sr": "Pregledajte provereni hardver za pametne zgrade uz AI nabavku, kineski lanac dobave, lokalnu instalaciju i servis.",
            "pl": "Przeglądaj zweryfikowany sprzęt smart building z zakupami AI, chińskim łańcuchem dostaw, lokalnym montażem i serwisem.",
        },
    },
    {
        "path": "/ai-building-brain",
        "key": "ai_brain",
        "priority": 0.85,
        "title": {
            "en": "AI Building Brain L1-L6 | AinerWise",
            "zh": "AI 建筑大脑 L1-L6 | AinerWise",
            "sr": "AI mozak zgrade L1-L6 | AinerWise",
            "pl": "AI mózg budynku L1-L6 | AinerWise",
        },
        "description": {
            "en": "Understand the AinerWise AI Building Brain: connected control, sensors, optimization, AI assistance, local AI and autonomous operations.",
            "zh": "了解 AinerWise AI 建筑大脑：联网控制、传感器、优化运行、AI 辅助、本地 AI 与未来自主运营。",
            "sr": "Upoznajte AinerWise AI mozak zgrade: kontrola, senzori, optimizacija, AI asistencija, lokalni AI i autonomne operacije.",
            "pl": "Poznaj AinerWise AI Building Brain: sterowanie, sensory, optymalizacja, asysta AI, lokalne AI i autonomiczne operacje.",
        },
    },
    {
        "path": "/services",
        "key": "services",
        "priority": 0.8,
        "title": {
            "en": "Smart Building Service Packages | AinerWise",
            "zh": "智能建筑服务套餐 | AinerWise",
            "sr": "Servisni paketi za pametne zgrade | AinerWise",
            "pl": "Pakiety serwisowe smart building | AinerWise",
        },
        "description": {
            "en": "Installation, commissioning, remote support, preventive maintenance, AMC and lifecycle upgrade packages for smart buildings.",
            "zh": "智能建筑安装、调试、远程支持、预防性维护、AMC 和生命周期升级服务套餐。",
            "sr": "Instalacija, puštanje u rad, daljinska podrška, preventivno održavanje, AMC i nadogradnje za pametne zgrade.",
            "pl": "Instalacja, uruchomienie, wsparcie zdalne, konserwacja, AMC i modernizacje cyklu życia dla smart building.",
        },
    },
    {
        "path": "/submit-requirement",
        "key": "submit_requirement",
        "priority": 0.75,
        "title": {
            "en": "Submit a Smart Building Requirement | AinerWise",
            "zh": "提交智能建筑需求 | AinerWise",
            "sr": "Pošaljite zahtev za pametnu zgradu | AinerWise",
            "pl": "Wyślij wymagania smart building | AinerWise",
        },
        "description": {
            "en": "Start with a requirement. AinerWise AI collects facts, finds missing details, drafts BOQ and routes the project for review.",
            "zh": "从一句需求开始。AinerWise AI 收集事实、追问缺口、生成 BOQ 草案，并进入人工审核。",
            "sr": "Počnite od zahteva. AinerWise AI prikuplja činjenice, nalazi praznine, pravi BOQ nacrt i šalje na pregled.",
            "pl": "Zacznij od wymagań. AinerWise AI zbiera fakty, wykrywa braki, tworzy szkic BOQ i kieruje projekt do weryfikacji.",
        },
    },
    {
        "path": "/about",
        "key": "about",
        "priority": 0.65,
        "title": {
            "en": "About AinerWise | AI Solution & Procurement Platform",
            "zh": "关于 AinerWise | AI 方案与采购平台",
            "sr": "O AinerWise | AI platforma za rešenja i nabavku",
            "pl": "O AinerWise | Platforma AI rozwiązań i zakupów",
        },
        "description": {
            "en": "AinerWise is the customer experience layer for AI shopping, procurement, smart building solutions, delivery and lifecycle service.",
            "zh": "AinerWise 是面向客户的 AI Shopping、AI Procurement、智能建筑方案、交付和生命周期服务入口。",
            "sr": "AinerWise je korisnički sloj za AI kupovinu, nabavku, rešenja za pametne zgrade, isporuku i servis.",
            "pl": "AinerWise to warstwa klienta dla zakupów AI, zakupów, rozwiązań smart building, dostaw i serwisu.",
        },
    },
    {
        "path": "/contact",
        "key": "contact",
        "priority": 0.6,
        "title": {
            "en": "Contact AinerWise | Smart Building Project Intake",
            "zh": "联系 AinerWise | 智能建筑项目咨询",
            "sr": "Kontakt AinerWise | Upit za projekat pametne zgrade",
            "pl": "Kontakt AinerWise | Zapytanie o projekt smart building",
        },
        "description": {
            "en": "Contact AinerWise for smart building, AI procurement, supplier, partner, installation and lifecycle support inquiries.",
            "zh": "联系 AinerWise，咨询智能建筑、AI 采购、供应商、合作伙伴、安装和生命周期服务。",
            "sr": "Kontaktirajte AinerWise za pametne zgrade, AI nabavku, dobavljače, partnere, instalaciju i servis.",
            "pl": "Skontaktuj się z AinerWise w sprawie smart building, zakupów AI, dostawców, partnerów, montażu i serwisu.",
        },
    },
]

REGION_FALLBACKS: dict[str, dict[str, Any]] = {
    "RS": {"name": "Serbia", "cities": ["Belgrade", "Novi Sad"], "currency": "EUR"},
    "PL": {"name": "Poland", "cities": ["Warsaw", "Krakow"], "currency": "PLN"},
    "RO": {"name": "Romania", "cities": ["Bucharest", "Cluj"], "currency": "RON"},
    "PH": {"name": "Philippines", "cities": ["Cebu", "Manila"], "currency": "PHP"},
    "CN": {"name": "China", "cities": ["Shenzhen", "Guangzhou"], "currency": "CNY"},
    "NZ": {"name": "New Zealand", "cities": ["Auckland", "Wellington"], "currency": "NZD"},
    "AU": {"name": "Australia", "cities": ["Sydney", "Melbourne"], "currency": "AUD"},
}

REGION_LOCALE_COPY: dict[str, dict[str, dict[str, Any]]] = {
    "RS": {
        "en": {"name": "Serbia", "cities": ["Belgrade", "Novi Sad"]},
        "zh": {"name": "塞尔维亚", "cities": ["贝尔格莱德", "诺维萨德"]},
        "sr": {"name": "Srbiju", "cities": ["Beograd", "Novi Sad"]},
        "pl": {"name": "Serbii", "cities": ["Belgrad", "Nowy Sad"]},
    },
    "PL": {
        "en": {"name": "Poland", "cities": ["Warsaw", "Krakow"]},
        "zh": {"name": "波兰", "cities": ["华沙", "克拉科夫"]},
        "sr": {"name": "Poljsku", "cities": ["Varšava", "Krakov"]},
        "pl": {"name": "Polski", "cities": ["Warszawa", "Kraków"]},
    },
    "RO": {
        "en": {"name": "Romania", "cities": ["Bucharest", "Cluj"]},
        "zh": {"name": "罗马尼亚", "cities": ["布加勒斯特", "克卢日"]},
        "sr": {"name": "Rumuniju", "cities": ["Bukurešt", "Kluž"]},
        "pl": {"name": "Rumunii", "cities": ["Bukareszt", "Kluż"]},
    },
    "PH": {
        "en": {"name": "Philippines", "cities": ["Cebu", "Manila"]},
        "zh": {"name": "菲律宾", "cities": ["宿务", "马尼拉"]},
        "sr": {"name": "Filipine", "cities": ["Sebu", "Manila"]},
        "pl": {"name": "Filipin", "cities": ["Cebu", "Manila"]},
    },
}

DEFAULT_SEO_CONFIG: dict[str, Any] = {
    "site_name": "AinerWise",
    "brand_tagline": "AI Solution & Procurement Platform",
    "default_region_code": "RS",
    "enabled_region_codes": ["RS", "PL"],
    "enabled_locales": ["en", "zh", "sr", "pl"],
    "target_portals": ["pc", "h5", "store"],
    "llm_automation_enabled": False,
    "review_required": True,
    "region_overrides": {},
    "page_overrides": {},
    "keyword_rules": [
        "AI smart building",
        "KNX integration",
        "AI procurement",
        "local installation",
        "lifecycle maintenance",
    ],
    "batch_policy": {
        "max_items": 80,
        "include_static_pages": True,
        "include_products": True,
        "include_solutions": True,
        "publish_automatically": False,
    },
}


def _slugify(value: str) -> str:
    slug = re.sub(r"[^\w]+", "-", value.lower()).strip("-")
    return re.sub(r"-{2,}", "-", slug)[:200]


class SeoGenerateRequest(BaseModel):
    target_keyword: str
    lang: str = "en"
    region_id: uuid.UUID | None = None
    context_hint: str | None = None


class SeoPageUpdate(BaseModel):
    title: str | None = None
    meta_description: str | None = None
    content_md: str | None = None


class SeoAutomationConfig(BaseModel):
    site_name: str = Field(default="AinerWise", max_length=120)
    brand_tagline: str = Field(default="AI Solution & Procurement Platform", max_length=180)
    default_region_code: str = Field(default="RS", max_length=10)
    enabled_region_codes: list[str] = Field(default_factory=lambda: ["RS", "PL"])
    enabled_locales: list[str] = Field(default_factory=lambda: ["en", "zh", "sr", "pl"])
    target_portals: list[str] = Field(default_factory=lambda: ["pc", "h5", "store"])
    llm_automation_enabled: bool = False
    review_required: bool = True
    region_overrides: dict[str, Any] = Field(default_factory=dict)
    page_overrides: dict[str, Any] = Field(default_factory=dict)
    keyword_rules: list[str] = Field(default_factory=list)
    batch_policy: dict[str, Any] = Field(default_factory=dict)


class SeoBatchRequest(BaseModel):
    locales: list[str] | None = None
    region_codes: list[str] | None = None
    page_paths: list[str] | None = None
    use_ai: bool = False
    save_draft: bool = False
    prompt_hint: str | None = Field(default=None, max_length=1500)


def _as_upper_codes(values: list[str] | None, fallback: list[str]) -> list[str]:
    source = values if values is not None else fallback
    return list(dict.fromkeys(str(item).strip().upper() for item in source if str(item).strip()))


def _as_locale_codes(values: list[str] | None, fallback: list[str]) -> list[str]:
    source = values if values is not None else fallback
    return list(dict.fromkeys(str(item).strip().lower() for item in source if str(item).strip()))


def _merge_config(value: dict | None) -> dict[str, Any]:
    merged = json.loads(json.dumps(DEFAULT_SEO_CONFIG))
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, dict) and isinstance(merged.get(key), dict):
                merged[key].update(item)
            else:
                merged[key] = item
    merged["enabled_region_codes"] = _as_upper_codes(merged.get("enabled_region_codes"), DEFAULT_SEO_CONFIG["enabled_region_codes"])
    merged["enabled_locales"] = _as_locale_codes(merged.get("enabled_locales"), DEFAULT_SEO_CONFIG["enabled_locales"])
    merged["target_portals"] = _as_locale_codes(merged.get("target_portals"), DEFAULT_SEO_CONFIG["target_portals"])
    return merged


async def _get_platform_setting(db: DB, key: str) -> PlatformSetting | None:
    return (
        await db.execute(
            select(PlatformSetting).where(
                PlatformSetting.portal_key == "global",
                PlatformSetting.key == key,
            )
        )
    ).scalar_one_or_none()


async def _save_platform_setting(db: DB, key: str, value: Any, *, admin: AdminUser, description: str) -> PlatformSetting:
    row = await _get_platform_setting(db, key)
    if row is None:
        row = PlatformSetting(
            portal_key="global",
            key=key,
            value_json={"value": value},
            description=description,
            updated_by=admin.id,
        )
    else:
        row.value_json = {"value": value}
        row.description = description
        row.updated_by = admin.id
    db.add(row)
    await db.flush()
    return row


async def _seo_config(db: DB) -> dict[str, Any]:
    row = await _get_platform_setting(db, SEO_CONFIG_KEY)
    payload = row.value_json if row else {}
    value = payload.get("value") if isinstance(payload, dict) else payload
    return _merge_config(value if isinstance(value, dict) else {})


def _region_context(code: str, config: dict[str, Any]) -> dict[str, Any]:
    normalized = code.upper()
    data = {**REGION_FALLBACKS.get(normalized, {"name": normalized, "cities": [], "currency": "EUR"})}
    override = config.get("region_overrides", {}).get(normalized) or config.get("region_overrides", {}).get(normalized.lower())
    if isinstance(override, dict):
        data.update(override)
    data["code"] = normalized
    return data


def _localized(value: dict[str, str], lang: str) -> str:
    return value.get(lang) or value.get("en") or next(iter(value.values()))


def _localized_region(lang: str, region: dict[str, Any]) -> tuple[str, list[str]]:
    code = region.get("code")
    fallback = REGION_LOCALE_COPY.get(code, {}).get(lang, {})
    override_names = region.get("localized_names") if isinstance(region.get("localized_names"), dict) else {}
    override_cities = region.get("localized_cities") if isinstance(region.get("localized_cities"), dict) else {}
    name = override_names.get(lang) or fallback.get("name") or region.get("name") or code
    cities = override_cities.get(lang) if isinstance(override_cities.get(lang), list) else fallback.get("cities")
    return name, list(cities or region.get("cities") or [])


def _region_phrase(lang: str, region: dict[str, Any]) -> str:
    name, cities = _localized_region(lang, region)
    city_part = ", ".join(cities)
    suffix = f" ({city_part})" if city_part else ""
    phrases = {
        "zh": f"面向{name}{suffix}本地项目优化，突出当地服务、采购、安装和长期维护。",
        "sr": f"Optimizovano za {name}{suffix}: lokalni servis, nabavka, instalacija i dugoročno održavanje.",
        "pl": f"Zoptymalizowane dla {name}{suffix}: lokalny serwis, zakupy, montaż i utrzymanie cyklu życia.",
        "en": f"Optimized for {name}{suffix}: local service, procurement, installation and lifecycle support.",
    }
    return phrases.get(lang, phrases["en"])


def _static_page_items(config: dict[str, Any], *, locales: list[str], region_codes: list[str], page_paths: list[str] | None) -> list[dict[str, Any]]:
    selected_paths = set(page_paths or [])
    pages = [page for page in STATIC_PAGE_CATALOG if not selected_paths or page["path"] in selected_paths or page["key"] in selected_paths]
    items: list[dict[str, Any]] = []
    for page in pages:
        page_override = config.get("page_overrides", {}).get(page["path"]) or config.get("page_overrides", {}).get(page["key"]) or {}
        for lang in locales:
            for region_code in region_codes:
                region = _region_context(region_code, config)
                title = page_override.get("title", {}).get(lang) if isinstance(page_override.get("title"), dict) else None
                description = page_override.get("description", {}).get(lang) if isinstance(page_override.get("description"), dict) else None
                title = title or _localized(page["title"], lang)
                description = description or _localized(page["description"], lang)
                region_phrase = _region_phrase(lang, region)
                items.append({
                    "scope": "static_page",
                    "page_key": page["key"],
                    "path": page["path"],
                    "locale": lang,
                    "region_code": region["code"],
                    "region_name": region.get("name"),
                    "title": title,
                    "meta_description": f"{description} {region_phrase}"[:300],
                    "keywords": list(dict.fromkeys([
                        *(config.get("keyword_rules") or []),
                        page["key"].replace("_", " "),
                        region.get("name"),
                        *(region.get("cities") or []),
                    ])),
                    "status": "draft",
                    "review_required": bool(config.get("review_required", True)),
                })
    return items


async def _ai_optimize_items(db: DB, items: list[dict[str, Any]], config: dict[str, Any], hint: str | None) -> tuple[list[dict[str, Any]], str | None]:
    if not config.get("llm_automation_enabled"):
        return items, "llm_automation_disabled"
    if not await ai_agent.is_configured(db):
        return items, "ai_integration_not_configured"
    prompt_payload = {
        "brand": config.get("site_name", "AinerWise"),
        "brand_tagline": config.get("brand_tagline"),
        "hint": hint or "",
        "items": items[: int(config.get("batch_policy", {}).get("max_items", 80) or 80)],
    }
    raw = await ai_agent.chat(
        db,
        [
            {
                "role": "system",
                "content": (
                    "You are AinerWise's international SEO editor. Improve title, meta_description, "
                    "and keywords for each item. Keep the same locale and region_code. "
                    "Do not invent unsupported countries, prices, awards, partners, or guarantees. "
                    "Respect B2B smart-building positioning: AI solution, procurement, local service, "
                    "installation, lifecycle maintenance. Return compact JSON only: "
                    '{"items":[{"path":"...","locale":"...","region_code":"...",'
                    '"title":"...","meta_description":"...","keywords":["..."]}]}'
                ),
            },
            {"role": "user", "content": json.dumps(prompt_payload, ensure_ascii=False)},
        ],
        temperature=0.25,
        max_tokens=7000,
        response_json=True,
    )
    if raw is None:
        return items, "ai_call_failed"
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return items, "ai_invalid_json"
    optimized = parsed.get("items")
    if not isinstance(optimized, list):
        return items, "ai_missing_items"
    by_key = {
        (item.get("path"), item.get("locale"), item.get("region_code")): item
        for item in optimized if isinstance(item, dict)
    }
    merged: list[dict[str, Any]] = []
    for item in items:
        ai_item = by_key.get((item["path"], item["locale"], item["region_code"]))
        if ai_item:
            next_item = {**item}
            for key in ("title", "meta_description", "keywords"):
                if ai_item.get(key):
                    next_item[key] = ai_item[key]
            next_item["ai_generated"] = True
            merged.append(next_item)
        else:
            merged.append(item)
    return merged, None


def _page_dict(p: SeoPage, *, internal: bool) -> dict:
    data = {
        "id": str(p.id), "slug": p.slug, "lang": p.lang, "title": p.title,
        "meta_description": p.meta_description, "content_md": p.content_md,
        "ai_generated": p.ai_generated,
        "published_at": p.published_at.isoformat() if p.published_at else None,
    }
    if internal:
        data["status"] = p.status
        data["target_keyword"] = p.target_keyword
        data["created_at"] = p.created_at.isoformat()
    return data


@router.get("/admin/seo/config")
async def get_seo_config(db: DB, admin: AdminUser):
    config = await _seo_config(db)
    localization = await _localization_payload(db)
    last_row = await _get_platform_setting(db, SEO_BATCH_DRAFT_KEY)
    last_payload = last_row.value_json.get("value") if last_row and isinstance(last_row.value_json, dict) else None
    return {
        "config": config,
        "localization": localization,
        "ai_configured": await ai_agent.is_configured(db),
        "static_pages": STATIC_PAGE_CATALOG,
        "last_batch_draft": last_payload,
    }


@router.put("/admin/seo/config")
async def update_seo_config(data: SeoAutomationConfig, db: DB, admin: AdminUser):
    payload = _merge_config(data.model_dump())
    await _save_platform_setting(
        db,
        SEO_CONFIG_KEY,
        payload,
        admin=admin,
        description="AinerWise public-site SEO automation, locale, region, and batch optimization policy.",
    )
    await db.commit()
    return {
        "config": payload,
        "ai_configured": await ai_agent.is_configured(db),
    }


@router.post("/admin/seo/batch/preview")
async def preview_seo_batch(data: SeoBatchRequest, db: DB, admin: AdminUser):
    config = await _seo_config(db)
    locales = _as_locale_codes(data.locales, config["enabled_locales"])
    regions = _as_upper_codes(data.region_codes, config["enabled_region_codes"])
    items = _static_page_items(config, locales=locales, region_codes=regions, page_paths=data.page_paths)
    return {
        "status": "preview",
        "ai_used": False,
        "ai_reason": "preview_is_rule_based",
        "review_required": True,
        "items": items,
        "total": len(items),
    }


@router.post("/admin/seo/batch/optimize")
async def optimize_seo_batch(data: SeoBatchRequest, db: DB, admin: AdminUser):
    config = await _seo_config(db)
    locales = _as_locale_codes(data.locales, config["enabled_locales"])
    regions = _as_upper_codes(data.region_codes, config["enabled_region_codes"])
    items = _static_page_items(config, locales=locales, region_codes=regions, page_paths=data.page_paths)
    ai_reason = None
    ai_used = False
    if data.use_ai:
        items, ai_reason = await _ai_optimize_items(db, items, config, data.prompt_hint)
        ai_used = ai_reason is None
    else:
        ai_reason = "ai_not_requested"

    draft = {
        "id": str(uuid.uuid4()),
        "status": "ready_for_review",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": str(admin.id),
        "ai_used": ai_used,
        "ai_reason": ai_reason,
        "review_required": True,
        "locales": locales,
        "region_codes": regions,
        "items": items,
        "total": len(items),
    }
    if data.save_draft:
        await _save_platform_setting(
            db,
            SEO_BATCH_DRAFT_KEY,
            draft,
            admin=admin,
            description="Last generated SEO batch draft. Review and copy into page overrides before publishing.",
        )
        await db.commit()
    return draft


@router.get("/seo/config")
async def get_public_seo_config(db: DB):
    config = await _seo_config(db)
    public_keys = (
        "site_name",
        "brand_tagline",
        "default_region_code",
        "enabled_region_codes",
        "enabled_locales",
        "region_overrides",
        "page_overrides",
    )
    return {key: config.get(key) for key in public_keys}


@router.post("/admin/seo/pages/generate")
async def generate_seo_page(data: SeoGenerateRequest, db: DB, admin: AdminUser):
    try:
        await require_agent(db, "marketing-agent", workflow="content_gen")
    except AgentAuthorizationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    slug = _slugify(data.target_keyword)
    existing = (await db.execute(select(SeoPage).where(SeoPage.slug == slug))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail=f"Page for slug '{slug}' already exists")

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                settings.AI_ORCHESTRATOR_URL.rstrip("/") + "/agent/generate",
                json={
                    "agent_slug": "marketing-agent",
                    "workflow": "content_gen",
                    "context": {"title": data.target_keyword,
                                "summary": data.context_hint or f"SEO landing page targeting: {data.target_keyword}"},
                    "channels": ["blog"], "langs": [data.lang],
                },
                headers={"X-Service-Token": settings.SERVICE_TOKEN},
            )
            response.raise_for_status()
            items = response.json().get("data", {}).get("items", [])
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Orchestrator unavailable: {exc}") from None

    item = items[0] if items else {"title": data.target_keyword, "content": ""}
    review = AIReview(target_type="seo_page", draft_json=item, status="preliminary")
    db.add(review)
    await db.flush()
    page = SeoPage(
        region_id=data.region_id, lang=data.lang, slug=slug,
        target_keyword=data.target_keyword,
        title=item.get("title") or data.target_keyword,
        meta_description=(item.get("content") or "")[:300],
        content_md=item.get("content"),
        ai_generated=True, review_id=review.id, status="in_review",
    )
    db.add(page)
    await db.flush()
    review.target_id = page.id
    db.add(review)
    await db.commit()
    await db.refresh(page)
    return _page_dict(page, internal=True)


@router.get("/admin/seo/pages")
async def list_seo_pages_admin(
    db: DB, admin: AdminUser,
    status: str | None = None,
    skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    query = select(SeoPage).order_by(SeoPage.created_at.desc())
    count_query = select(func.count()).select_from(SeoPage)
    if status:
        query = query.where(SeoPage.status == status)
        count_query = count_query.where(SeoPage.status == status)
    total = (await db.execute(count_query)).scalar() or 0
    rows = (await db.execute(query.offset(skip).limit(limit))).scalars().all()
    return {"items": [_page_dict(p, internal=True) for p in rows], "total": total}


@router.patch("/admin/seo/pages/{id}")
async def update_seo_page(id: uuid.UUID, data: SeoPageUpdate, db: DB, admin: AdminUser):
    page = await db.get(SeoPage, id)
    if page is None:
        raise HTTPException(status_code=404, detail="Page not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(page, key, value)
    db.add(page)
    await db.commit()
    await db.refresh(page)
    return _page_dict(page, internal=True)


@router.post("/admin/seo/pages/{id}/publish")
async def publish_seo_page(id: uuid.UUID, db: DB, admin: AdminUser):
    page = await db.get(SeoPage, id)
    if page is None:
        raise HTTPException(status_code=404, detail="Page not found")
    page.status = "published"
    page.published_at = datetime.now(timezone.utc)
    db.add(page)
    if page.review_id:
        review = await db.get(AIReview, page.review_id)
        if review and review.status == "preliminary":
            review.status = "approved"
            review.reviewed_by = admin.id
            review.reviewed_at = datetime.now(timezone.utc)
            db.add(review)
    await db.commit()
    return {"id": str(page.id), "status": page.status, "url": f"/insights/{page.slug}"}


# ── public (website) ───────────────────────────────────────────


@router.get("/seo/pages")
async def list_seo_pages_public(db: DB, lang: str | None = None, limit: int = Query(20, ge=1, le=50)):
    query = select(SeoPage).where(SeoPage.status == "published").order_by(SeoPage.published_at.desc())
    if lang:
        query = query.where(SeoPage.lang == lang)
    rows = (await db.execute(query.limit(limit))).scalars().all()
    return {"items": [_page_dict(p, internal=False) for p in rows]}


@router.get("/seo/pages/{slug}")
async def get_seo_page_public(slug: str, db: DB):
    page = (
        await db.execute(select(SeoPage).where(SeoPage.slug == slug, SeoPage.status == "published"))
    ).scalar_one_or_none()
    if page is None:
        raise HTTPException(status_code=404, detail="Page not found")
    return _page_dict(page, internal=False)
