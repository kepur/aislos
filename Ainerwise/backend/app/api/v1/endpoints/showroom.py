"""Experience Center (Portal 10) API.

Two surfaces in one router:

- /showroom/kiosk/*  — tablet endpoints. Auth = revocable device token
  (X-Kiosk-Token). Tablets are dumb terminals: this token can only reach the
  showroom tool set; every tool call also passes the Phase G require_agent
  gate for the persona bound to the device. Constitution red lines: AI
  self-discloses (Art.50, not configurable), transcripts only (no raw audio).
- /admin/showroom/*  — stores/devices/sessions/orders management and the POS
  confirmation flow (stock deduction + double-entry ledger).
"""
import hashlib
import secrets
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import httpx
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import desc, or_, select

from app.api.deps import DB, AdminUser
from app.core.config import settings
from app.models.ai import Conversation, ConversationMessage
from app.models.lead import Lead
from app.models.lifecycle import InventoryItem, StockMovement
from app.models.payment import LedgerEntry
from app.models.product import Product
from app.models.showroom import KioskDevice, ShowroomOrder, ShowroomSession, Store
from app.models.agent import Agent
from app.services.agent_runtime import AgentAuthorizationError, require_agent
from app.services.audit import log_action

router = APIRouter(prefix="/showroom", tags=["showroom"])
admin_router = APIRouter(prefix="/admin/showroom", tags=["showroom-admin"])

# AI Act Art.50 — hardcoded on purpose; persona config cannot override it.
AI_DISCLOSURE = "You are talking to an AI assistant."

KIOSK_SCOPES = ("product_data",)
PUBLIC_PRODUCT_STATUSES_EXCLUDED = ("draft", "pending", "archived")

REALTIME_TOOLS = [
    {
        "type": "function",
        "name": "search_products",
        "description": "Search the live public product catalog. Use before making product claims.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}},
            "required": ["query"],
        },
    },
    {
        "type": "function",
        "name": "compare_products",
        "description": "Compare two to four product IDs using live catalog specifications.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_ids": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 4}
            },
            "required": ["product_ids"],
        },
    },
    {
        "type": "function",
        "name": "check_stock",
        "description": "Check current store and warehouse availability for a product ID.",
        "parameters": {
            "type": "object",
            "properties": {"product_id": {"type": "string"}},
            "required": ["product_id"],
        },
    },
    {
        "type": "function",
        "name": "show_on_screen",
        "description": "Ask the deterministic kiosk canvas to display a supported view.",
        "parameters": {
            "type": "object",
            "properties": {
                "view": {"type": "string", "enum": ["welcome", "products", "compare", "stock", "lead"]},
            },
            "required": ["view"],
        },
    },
]


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _new_pickup_code() -> str:
    alphabet = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # no 0/O/1/I/L
    return "".join(secrets.choice(alphabet) for _ in range(6))


async def _get_device(db, x_kiosk_token: str | None) -> KioskDevice:
    if not x_kiosk_token:
        raise HTTPException(status_code=401, detail="Missing kiosk device token")
    device = (
        await db.execute(
            select(KioskDevice).where(KioskDevice.device_token_hash == _hash_token(x_kiosk_token))
        )
    ).scalar_one_or_none()
    if device is None:
        raise HTTPException(status_code=401, detail="Invalid kiosk device token")
    if device.status != "active":
        raise HTTPException(status_code=403, detail=f"Device is {device.status}")
    device.last_seen_at = datetime.now(timezone.utc)
    db.add(device)
    return device


async def _gate(db, device: KioskDevice, *extra_scopes: str) -> Agent:
    try:
        return await require_agent(
            db, device.agent_slug, scopes=(*KIOSK_SCOPES, *extra_scopes), workflow="showroom"
        )
    except AgentAuthorizationError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


def _product_card(p: Product) -> dict:
    return {
        "id": str(p.id),
        "name": p.public_name or p.name,
        "brand": p.brand,
        "description": p.description,
        "list_price": p.list_price,
        "currency": p.currency,
        "specs": p.specs_json or {},
        "images": p.images_json or [],
        "warranty_years": p.warranty_years,
    }


# ---------------------------------------------------------------------------
# Kiosk surface (device token)
# ---------------------------------------------------------------------------

@router.get("/kiosk/bootstrap")
async def kiosk_bootstrap(db: DB, x_kiosk_token: str | None = Header(default=None)):
    """Device claims its persona, store and language on boot."""
    device = await _get_device(db, x_kiosk_token)
    store = (await db.execute(select(Store).where(Store.id == device.store_id))).scalar_one()
    agent = (
        await db.execute(select(Agent).where(Agent.slug == device.agent_slug))
    ).scalar_one_or_none()
    await db.commit()
    return {
        "device": {"id": str(device.id), "name": device.name,
                   "default_lang": device.default_lang, "voice_mode": device.voice_mode},
        "store": {"id": str(store.id), "name": store.name, "city": store.city,
                  "country": store.country},
        "agent": {
            "slug": device.agent_slug,
            "name": agent.name if agent else device.agent_slug,
            "role_title": agent.role_title if agent else None,
            "status": agent.status if agent else "missing",
            "persona": (agent.config_json or {}) if agent else {},
        },
        "ai_disclosure": AI_DISCLOSURE,
        "languages": ["sr", "en", "zh", "pl", "de"],
    }


class SessionStart(BaseModel):
    lang: str | None = None


@router.post("/kiosk/sessions", status_code=201)
async def start_session(data: SessionStart, db: DB, x_kiosk_token: str | None = Header(default=None)):
    device = await _get_device(db, x_kiosk_token)
    await _gate(db, device)
    conversation = Conversation(
        channel="showroom", lang=data.lang or device.default_lang,
        meta_json={"device_id": str(device.id), "agent_slug": device.agent_slug},
    )
    db.add(conversation)
    await db.flush()
    session = ShowroomSession(
        device_id=device.id, conversation_id=conversation.id,
        lang=data.lang or device.default_lang,
        started_at=datetime.now(timezone.utc), products_viewed_json=[],
    )
    db.add(session)
    await db.commit()
    return {"id": str(session.id), "conversation_id": str(conversation.id),
            "ai_disclosure": AI_DISCLOSURE}


class SessionEnd(BaseModel):
    outcome: str | None = Field(default=None, pattern="^(purchase|lead|browse|abandoned)$")
    need_category: str | None = None
    budget_hint: Decimal | None = None


@router.patch("/kiosk/sessions/{session_id}")
async def end_session(session_id: uuid.UUID, data: SessionEnd, db: DB,
                      x_kiosk_token: str | None = Header(default=None)):
    device = await _get_device(db, x_kiosk_token)
    session = await _own_session(db, device, session_id)
    if data.outcome is not None:
        session.outcome = data.outcome
    if data.need_category is not None:
        session.need_category = data.need_category
    if data.budget_hint is not None:
        session.budget_hint = data.budget_hint
    if session.ended_at is None:
        session.ended_at = datetime.now(timezone.utc)
    db.add(session)
    await db.commit()
    return {"id": str(session.id), "outcome": session.outcome}


async def _own_session(db, device: KioskDevice, session_id: uuid.UUID) -> ShowroomSession:
    session = (
        await db.execute(select(ShowroomSession).where(ShowroomSession.id == session_id))
    ).scalar_one_or_none()
    if session is None or session.device_id != device.id:
        raise HTTPException(status_code=404, detail="Session not found for this device")
    return session


def _track_products(session: ShowroomSession, product_ids: list[str]) -> None:
    viewed = list(session.products_viewed_json or [])
    for pid in product_ids:
        if pid not in viewed:
            viewed.append(pid)
    session.products_viewed_json = viewed


class TranscriptTurn(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=8000)


@router.post("/kiosk/sessions/{session_id}/messages", status_code=201)
async def log_transcript(session_id: uuid.UUID, data: TranscriptTurn, db: DB,
                         x_kiosk_token: str | None = Header(default=None)):
    """Transcript only — raw audio is never uploaded or stored (red line)."""
    device = await _get_device(db, x_kiosk_token)
    session = await _own_session(db, device, session_id)
    message = ConversationMessage(
        conversation_id=session.conversation_id, role=data.role, content=data.content
    )
    db.add(message)
    await db.commit()
    return {"id": str(message.id)}


@router.get("/kiosk/products")
async def search_products(db: DB, q: str = "", limit: int = 8,
                          x_kiosk_token: str | None = Header(default=None)):
    device = await _get_device(db, x_kiosk_token)
    await _gate(db, device)
    stmt = select(Product).where(Product.status.notin_(PUBLIC_PRODUCT_STATUSES_EXCLUDED))
    if q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(
            Product.name.ilike(like), Product.public_name.ilike(like),
            Product.brand.ilike(like), Product.description.ilike(like),
        ))
    products = (await db.execute(stmt.limit(min(limit, 20)))).scalars().all()
    await db.commit()
    return {"items": [_product_card(p) for p in products]}


class CompareRequest(BaseModel):
    session_id: uuid.UUID | None = None
    product_ids: list[uuid.UUID] = Field(min_length=2, max_length=4)


@router.post("/kiosk/products/compare")
async def compare_products(data: CompareRequest, db: DB,
                           x_kiosk_token: str | None = Header(default=None)):
    device = await _get_device(db, x_kiosk_token)
    await _gate(db, device)
    products = (
        await db.execute(select(Product).where(Product.id.in_(data.product_ids)))
    ).scalars().all()
    if len(products) < 2:
        raise HTTPException(status_code=404, detail="Products not found")
    spec_keys: list[str] = []
    for p in products:
        for key in (p.specs_json or {}):
            if key not in spec_keys:
                spec_keys.append(key)
    rows = [
        {"key": key, "values": {str(p.id): (p.specs_json or {}).get(key) for p in products}}
        for key in spec_keys
    ]
    if data.session_id:
        session = await _own_session(db, device, data.session_id)
        _track_products(session, [str(p.id) for p in products])
        db.add(session)
    await db.commit()
    return {"products": [_product_card(p) for p in products], "spec_rows": rows}


@router.get("/kiosk/products/{product_id}/stock")
async def check_stock(product_id: uuid.UUID, db: DB,
                      x_kiosk_token: str | None = Header(default=None)):
    device = await _get_device(db, x_kiosk_token)
    await _gate(db, device)
    items = (
        await db.execute(select(InventoryItem).where(InventoryItem.product_id == product_id))
    ).scalars().all()
    locations = [
        {"location": item.location or "warehouse",
         "quantity": item.quantity, "reserved": item.reserved_quantity}
        for item in items
    ]
    available = sum(max(i.quantity - i.reserved_quantity, 0) for i in items)
    await db.commit()
    return {"product_id": str(product_id), "available": available, "locations": locations}


class OrderItem(BaseModel):
    product_id: uuid.UUID
    qty: int = Field(ge=1, le=99)


class OrderCreate(BaseModel):
    session_id: uuid.UUID
    items: list[OrderItem] = Field(min_length=1, max_length=20)
    notes: str | None = None


@router.post("/kiosk/orders", status_code=201)
async def create_showroom_order(data: OrderCreate, db: DB,
                                x_kiosk_token: str | None = Header(default=None)):
    """Order draft — owner confirms at the counter (POS card, no online payment)."""
    device = await _get_device(db, x_kiosk_token)
    await _gate(db, device, "quotes")
    session = await _own_session(db, device, data.session_id)
    products = {
        str(p.id): p for p in (
            await db.execute(
                select(Product).where(Product.id.in_([i.product_id for i in data.items]))
            )
        ).scalars().all()
    }
    items_json, total = [], Decimal("0")
    for item in data.items:
        product = products.get(str(item.product_id))
        if product is None:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        unit_price = Decimal(str(product.list_price or 0))
        items_json.append({
            "product_id": str(product.id), "name": product.public_name or product.name,
            "qty": item.qty, "unit_price": float(unit_price),
        })
        total += unit_price * item.qty
    order = ShowroomOrder(
        session_id=session.id, store_id=device.store_id, items_json=items_json,
        total=total, currency="EUR", status="draft",
        pickup_code=_new_pickup_code(), notes=data.notes,
    )
    db.add(order)
    await db.flush()
    session.order_id = order.id
    _track_products(session, [i["product_id"] for i in items_json])
    db.add(session)
    await db.commit()
    return {"id": str(order.id), "pickup_code": order.pickup_code,
            "total": float(order.total), "currency": order.currency,
            "status": order.status, "items": items_json}


class LeadCreate(BaseModel):
    session_id: uuid.UUID
    contact_name: str = Field(min_length=1, max_length=255)
    contact_phone: str | None = None
    contact_email: str | None = None
    description: str | None = None
    budget_range: str | None = None
    project_type: str | None = None


@router.post("/kiosk/leads", status_code=201)
async def create_showroom_lead(data: LeadCreate, db: DB,
                               x_kiosk_token: str | None = Header(default=None)):
    device = await _get_device(db, x_kiosk_token)
    await _gate(db, device, "customer_data")
    session = await _own_session(db, device, data.session_id)
    lead = Lead(
        contact_name=data.contact_name, contact_phone=data.contact_phone,
        contact_email=data.contact_email, description=data.description,
        budget_range=data.budget_range, project_type=data.project_type,
        language=session.lang or device.default_lang,
        status="new", source_channel="showroom",
        source_detail=f"kiosk:{device.name}",
    )
    db.add(lead)
    await db.flush()
    session.lead_id = lead.id
    session.outcome = session.outcome or "lead"
    db.add(session)
    await db.commit()
    return {"id": str(lead.id), "status": lead.status}


class KioskChat(BaseModel):
    session_id: uuid.UUID
    message: str = Field(min_length=1, max_length=2000)


@router.get("/kiosk/voice-config")
async def kiosk_voice_config(
    db: DB,
    lang: str | None = None,
    probe: bool = False,
    x_kiosk_token: str | None = Header(default=None),
):
    """Voice activation point (plan A). When the 'voice' integration is
    configured, mints a short-lived client secret server-side so the tablet
    can open a realtime WebRTC session — the long-lived key never leaves the
    server. Unconfigured devices stay in text mode (graceful degradation)."""
    from app.services.integrations import get_config

    device = await _get_device(db, x_kiosk_token)
    agent = await _gate(db, device)
    await db.commit()

    cfg = await get_config(db, "voice")
    if not (cfg.get("_enabled") and cfg.get("api_key") and cfg.get("base_url")):
        return {"enabled": False, "mode": "text",
                "reason": "voice integration not configured (Admin → Integrations → voice)"}
    if device.voice_mode == "text":
        return {"enabled": False, "mode": "text", "reason": "device is set to text mode"}
    if probe:
        return {
            "enabled": True,
            "mode": device.voice_mode,
            "provider": cfg.get("provider", "openai-realtime"),
            "model": cfg.get("model", "gpt-realtime"),
        }

    persona = agent.config_json or {}
    instructions = (
        f"{AI_DISCLOSURE} You are '{agent.name}' "
        f"({agent.role_title or 'showroom consultant'}). "
        f"Speak {lang or device.default_lang} by default; switch to the customer's language. "
        f"Personality: {persona.get('voice') or 'friendly and professional'}. "
        "Ground every fact in tool results; never invent prices or stock."
    )
    headers = {"Authorization": f"Bearer {cfg['api_key']}", "Content-Type": "application/json"}
    base = cfg["base_url"].rstrip("/")
    session_config = {
        "session": {
            "type": "realtime",
            "model": cfg.get("model", "gpt-realtime"),
            "instructions": instructions,
            "audio": {
                "input": {
                    "transcription": {
                        "model": cfg.get("transcription_model", "gpt-4o-mini-transcribe")
                    }
                },
                "output": {"voice": cfg.get("voice", "alloy")},
            },
            "tools": REALTIME_TOOLS,
            "tool_choice": "auto",
        }
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(f"{base}/realtime/client_secrets",
                                         json=session_config, headers=headers)
            if response.status_code == 404:  # older API surface
                response = await client.post(
                    f"{base}/realtime/sessions",
                    json={"model": cfg.get("model", "gpt-realtime"),
                          "instructions": instructions,
                          "voice": cfg.get("voice", "alloy")},
                    headers=headers,
                )
            response.raise_for_status()
            body = response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Voice provider error: {exc}") from None

    secret = body.get("value") or (body.get("client_secret") or {}).get("value")
    expires_at = body.get("expires_at") or (body.get("client_secret") or {}).get("expires_at")
    if not secret:
        raise HTTPException(status_code=502, detail="Voice provider returned no client secret")
    return {
        "enabled": True,
        "mode": device.voice_mode,
        "provider": cfg.get("provider", "openai-realtime"),
        "model": cfg.get("model", "gpt-realtime"),
        "webrtc_url": cfg.get("webrtc_url") or f"{base}/realtime/calls",
        "client_secret": secret,
        "expires_at": expires_at,
        "ai_disclosure": AI_DISCLOSURE,
    }


class RealtimeToolCall(BaseModel):
    session_id: uuid.UUID
    name: str = Field(pattern="^(search_products|compare_products|check_stock|show_on_screen)$")
    arguments: dict = {}


@router.post("/kiosk/realtime-tool-call")
async def realtime_tool_call(
    data: RealtimeToolCall,
    db: DB,
    x_kiosk_token: str | None = Header(default=None),
):
    """Allowlisted bridge for realtime voice function calls.

    The tablet can request only deterministic showroom reads and display
    changes. Every data tool is re-authorized against the device persona.
    """
    device = await _get_device(db, x_kiosk_token)
    await _gate(db, device)
    session = await _own_session(db, device, data.session_id)
    args = data.arguments or {}

    if data.name == "search_products":
        query = str(args.get("query") or "").strip()[:120]
        limit = min(max(int(args.get("limit") or 6), 1), 12)
        stmt = select(Product).where(Product.status.notin_(PUBLIC_PRODUCT_STATUSES_EXCLUDED))
        if query:
            like = f"%{query}%"
            stmt = stmt.where(or_(
                Product.name.ilike(like),
                Product.public_name.ilike(like),
                Product.brand.ilike(like),
                Product.description.ilike(like),
            ))
        products = (await db.execute(stmt.limit(limit))).scalars().all()
        _track_products(session, [str(p.id) for p in products])
        result = {"view": "products", "items": [_product_card(p) for p in products]}
    elif data.name == "compare_products":
        try:
            ids = [uuid.UUID(value) for value in (args.get("product_ids") or [])[:4]]
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="Invalid product IDs") from None
        if len(ids) < 2:
            raise HTTPException(status_code=400, detail="At least two product IDs are required")
        products = (await db.execute(select(Product).where(Product.id.in_(ids)))).scalars().all()
        spec_keys = list(dict.fromkeys(
            key for product in products for key in (product.specs_json or {})
        ))
        _track_products(session, [str(p.id) for p in products])
        result = {
            "view": "compare",
            "products": [_product_card(p) for p in products],
            "spec_rows": [
                {"key": key, "values": {str(p.id): (p.specs_json or {}).get(key) for p in products}}
                for key in spec_keys
            ],
        }
    elif data.name == "check_stock":
        try:
            product_id = uuid.UUID(str(args.get("product_id") or ""))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid product ID") from None
        items = (
            await db.execute(select(InventoryItem).where(InventoryItem.product_id == product_id))
        ).scalars().all()
        result = {
            "view": "stock",
            "product_id": str(product_id),
            "available": sum(max(item.quantity - item.reserved_quantity, 0) for item in items),
            "locations": [
                {
                    "location": item.location or "warehouse",
                    "quantity": item.quantity,
                    "reserved": item.reserved_quantity,
                }
                for item in items
            ],
        }
        _track_products(session, [str(product_id)])
    else:
        result = {"view": args.get("view", "welcome")}

    db.add(session)
    await db.commit()
    return result


@router.post("/kiosk/chat")
async def kiosk_chat(data: KioskChat, db: DB,
                     x_kiosk_token: str | None = Header(default=None)):
    """Text-mode pipeline (plan B). Proxies to the orchestrator with the
    device persona; degrades to a deterministic product search when AI is
    unavailable — retail rule #1: never freeze in front of a customer."""
    device = await _get_device(db, x_kiosk_token)
    await _gate(db, device)
    session = await _own_session(db, device, data.session_id)
    db.add(ConversationMessage(
        conversation_id=session.conversation_id, role="user", content=data.message
    ))
    answer, configured = None, False
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                settings.AI_ORCHESTRATOR_URL.rstrip("/") + "/agent/chat",
                json={
                    "message": data.message,
                    "conversation_id": str(session.conversation_id),
                    "visitor_id": f"kiosk:{device.id}",
                    "lang": session.lang or device.default_lang,
                    "channel": "showroom",
                    "agent_slug": device.agent_slug,  # persona identity + run attribution
                },
                headers={"X-Service-Token": settings.SERVICE_TOKEN},
            )
            response.raise_for_status()
            body = response.json()
            answer = body.get("answer")
            configured = bool(body.get("configured"))
    except Exception:  # noqa: BLE001 — orchestrator down => deterministic fallback
        pass
    fallback_products = []
    if not answer:
        like = f"%{data.message.strip()[:80]}%"
        products = (
            await db.execute(
                select(Product)
                .where(Product.status.notin_(PUBLIC_PRODUCT_STATUSES_EXCLUDED))
                .where(or_(Product.name.ilike(like), Product.description.ilike(like)))
                .limit(4)
            )
        ).scalars().all()
        fallback_products = [_product_card(p) for p in products]
    if answer:
        db.add(ConversationMessage(
            conversation_id=session.conversation_id, role="assistant", content=answer
        ))
    await db.commit()
    return {"configured": configured, "answer": answer,
            "fallback_products": fallback_products,
            "ai_disclosure": AI_DISCLOSURE}


# ---------------------------------------------------------------------------
# Admin surface
# ---------------------------------------------------------------------------

class StoreCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    address: str | None = None
    city: str | None = None
    country: str | None = None
    timezone: str | None = None


class StoreUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    city: str | None = None
    country: str | None = None
    status: str | None = Field(default=None, pattern="^(active|closed)$")


@admin_router.get("/stores")
async def list_stores(db: DB, admin: AdminUser):
    stores = (await db.execute(select(Store).order_by(Store.created_at))).scalars().all()
    return {"items": [
        {"id": str(s.id), "name": s.name, "address": s.address, "city": s.city,
         "country": s.country, "status": s.status}
        for s in stores
    ]}


@admin_router.post("/stores", status_code=201)
async def create_store(data: StoreCreate, db: DB, admin: AdminUser):
    store = Store(**data.model_dump())
    db.add(store)
    await db.flush()
    await log_action(db, actor_user_id=admin.id, action="store_create",
                     entity_type="store", entity_id=store.id, after=data.model_dump())
    return {"id": str(store.id), "name": store.name, "status": store.status}


@admin_router.patch("/stores/{store_id}")
async def update_store(store_id: uuid.UUID, data: StoreUpdate, db: DB, admin: AdminUser):
    store = (await db.execute(select(Store).where(Store.id == store_id))).scalar_one_or_none()
    if store is None:
        raise HTTPException(status_code=404, detail="Store not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(store, field, value)
    db.add(store)
    await db.commit()
    return {"id": str(store.id), "name": store.name, "status": store.status}


class DeviceCreate(BaseModel):
    store_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    agent_slug: str
    default_lang: str = "en"
    voice_mode: str = Field(default="text", pattern="^(text|realtime|pipeline)$")


class DeviceUpdate(BaseModel):
    name: str | None = None
    agent_slug: str | None = None
    default_lang: str | None = None
    voice_mode: str | None = Field(default=None, pattern="^(text|realtime|pipeline)$")
    status: str | None = Field(default=None, pattern="^(active|paused|revoked)$")


def _device_dict(d: KioskDevice) -> dict:
    return {"id": str(d.id), "store_id": str(d.store_id), "name": d.name,
            "agent_slug": d.agent_slug, "default_lang": d.default_lang,
            "voice_mode": d.voice_mode, "status": d.status,
            "last_seen_at": d.last_seen_at.isoformat() if d.last_seen_at else None}


@admin_router.get("/devices")
async def list_devices(db: DB, admin: AdminUser):
    devices = (await db.execute(select(KioskDevice).order_by(KioskDevice.created_at))).scalars().all()
    return {"items": [_device_dict(d) for d in devices]}


@admin_router.post("/devices", status_code=201)
async def create_device(data: DeviceCreate, db: DB, admin: AdminUser):
    agent = (
        await db.execute(select(Agent).where(Agent.slug == data.agent_slug))
    ).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=400, detail=f"Agent '{data.agent_slug}' is not registered")
    token = secrets.token_urlsafe(32)
    device = KioskDevice(
        store_id=data.store_id, name=data.name, agent_slug=data.agent_slug,
        default_lang=data.default_lang, voice_mode=data.voice_mode,
        device_token_hash=_hash_token(token),
    )
    db.add(device)
    await db.flush()
    await log_action(db, actor_user_id=admin.id, action="kiosk_device_create",
                     entity_type="kiosk_device", entity_id=device.id,
                     after={"name": data.name, "agent_slug": data.agent_slug})
    # Plaintext token is returned exactly once; only the hash is stored.
    return {**_device_dict(device), "device_token": token}


@admin_router.patch("/devices/{device_id}")
async def update_device(device_id: uuid.UUID, data: DeviceUpdate, db: DB, admin: AdminUser):
    device = (
        await db.execute(select(KioskDevice).where(KioskDevice.id == device_id))
    ).scalar_one_or_none()
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(device, field, value)
    db.add(device)
    await db.commit()
    return _device_dict(device)


@admin_router.post("/devices/{device_id}/rotate-token")
async def rotate_device_token(device_id: uuid.UUID, db: DB, admin: AdminUser):
    device = (
        await db.execute(select(KioskDevice).where(KioskDevice.id == device_id))
    ).scalar_one_or_none()
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    token = secrets.token_urlsafe(32)
    device.device_token_hash = _hash_token(token)
    db.add(device)
    await log_action(db, actor_user_id=admin.id, action="kiosk_token_rotate",
                     entity_type="kiosk_device", entity_id=device.id)
    return {"id": str(device.id), "device_token": token}


@admin_router.get("/sessions")
async def list_sessions(db: DB, admin: AdminUser, limit: int = 50):
    sessions = (
        await db.execute(
            select(ShowroomSession).order_by(desc(ShowroomSession.created_at)).limit(min(limit, 200))
        )
    ).scalars().all()
    return {"items": [
        {"id": str(s.id), "device_id": str(s.device_id), "lang": s.lang,
         "started_at": s.started_at.isoformat() if s.started_at else None,
         "ended_at": s.ended_at.isoformat() if s.ended_at else None,
         "need_category": s.need_category,
         "budget_hint": float(s.budget_hint) if s.budget_hint is not None else None,
         "products_viewed": s.products_viewed_json or [],
         "outcome": s.outcome,
         "order_id": str(s.order_id) if s.order_id else None,
         "lead_id": str(s.lead_id) if s.lead_id else None}
        for s in sessions
    ]}


@admin_router.get("/orders")
async def list_orders(db: DB, admin: AdminUser, status: str | None = None, limit: int = 50):
    stmt = select(ShowroomOrder).order_by(desc(ShowroomOrder.created_at)).limit(min(limit, 200))
    if status:
        stmt = stmt.where(ShowroomOrder.status == status)
    orders = (await db.execute(stmt)).scalars().all()
    return {"items": [
        {"id": str(o.id), "store_id": str(o.store_id), "items": o.items_json,
         "total": float(o.total), "currency": o.currency, "status": o.status,
         "pickup_code": o.pickup_code,
         "created_at": o.created_at.isoformat() if o.created_at else None}
        for o in orders
    ]}


@admin_router.post("/orders/{order_id}/confirm")
async def confirm_order(order_id: uuid.UUID, db: DB, admin: AdminUser):
    """Counter confirmation after the POS card payment: deduct stock, write a
    balanced ledger group (bank:pos_store / platform:revenue), close session."""
    order = (
        await db.execute(select(ShowroomOrder).where(ShowroomOrder.id == order_id))
    ).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status not in ("draft", "confirmed"):
        raise HTTPException(status_code=400, detail=f"Order is already {order.status}")

    for item in order.items_json:
        inventory = (
            await db.execute(
                select(InventoryItem)
                .where(InventoryItem.product_id == uuid.UUID(item["product_id"]))
                .order_by(desc(InventoryItem.quantity))
            )
        ).scalars().first()
        if inventory is not None:
            inventory.quantity = max(inventory.quantity - item["qty"], 0)
            db.add(inventory)
            db.add(StockMovement(
                inventory_item_id=inventory.id, movement_type="outbound",
                quantity=item["qty"], reference=f"showroom:{order.pickup_code}",
                created_by=admin.id,
            ))

    entry_group = uuid.uuid4()
    db.add(LedgerEntry(entry_group=entry_group, account="bank:pos_store",
                       direction="debit", amount=order.total, currency=order.currency,
                       memo=f"Showroom order {order.pickup_code}"))
    db.add(LedgerEntry(entry_group=entry_group, account="platform:revenue",
                       direction="credit", amount=order.total, currency=order.currency,
                       memo=f"Showroom order {order.pickup_code}"))

    order.status = "paid_in_store"
    order.confirmed_by = admin.id
    db.add(order)
    if order.session_id:
        session = (
            await db.execute(select(ShowroomSession).where(ShowroomSession.id == order.session_id))
        ).scalar_one_or_none()
        if session is not None:
            session.outcome = "purchase"
            session.order_id = order.id
            db.add(session)
    await log_action(db, actor_user_id=admin.id, action="showroom_order_confirm",
                     entity_type="showroom_order", entity_id=order.id,
                     after={"status": order.status, "total": float(order.total)})
    return {"id": str(order.id), "status": order.status, "pickup_code": order.pickup_code}
