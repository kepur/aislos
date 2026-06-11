"""Telegram admin bot command handler (5.15).

Processes /leads, /lead <id>, and /help commands from the configured admin chat
via a webhook. Read-only CRM lookups; only the configured admin chat is served.
"""
from __future__ import annotations

import uuid
from typing import Any

import httpx
from sqlalchemy import cast, desc, select
from sqlalchemy import String as SAString
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.lead import Lead

HELP_TEXT = (
    "AinerWise admin bot\n"
    "/leads - latest leads\n"
    "/lead <id> - lead detail (full or short id)\n"
    "/help - this message"
)


async def send_message(chat_id: str, text: str) -> None:
    if not settings.TELEGRAM_BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json={"chat_id": chat_id, "text": text, "disable_web_page_preview": True})
    except Exception:
        pass


def _fmt_lead_line(l: Lead) -> str:
    return (
        f"{str(l.id)[:8]} | {l.contact_name or l.contact_email or '-'} | "
        f"{l.project_type or '-'} | {l.status} | "
        f"RR {l.recurring_revenue_score if l.recurring_revenue_score is not None else '-'}"
    )


def _fmt_lead_detail(l: Lead) -> str:
    ai = l.ai_analysis_json or {}
    classification = (ai.get("classification") or {}).get("project_class", "-")
    return (
        f"Lead {str(l.id)[:8]}\n"
        f"Contact: {l.contact_name or '-'} ({l.contact_email or '-'})\n"
        f"Project: {l.project_type or '-'}\n"
        f"Location: {l.country or '-'} {l.city or ''}\n"
        f"Status: {l.status}\n"
        f"Solution line: {l.solution_line or '-'}\n"
        f"Classification: {classification}\n"
        f"Recurring score: {l.recurring_revenue_score if l.recurring_revenue_score is not None else '-'}\n"
        f"Estimated ARR: {('EUR ' + str(round(l.estimated_arr))) if l.estimated_arr else '-'}\n"
        f"Compliance risk: {l.compliance_risk_level or '-'} | AMC potential: {l.amc_potential or '-'}"
    )


async def _cmd_leads(db: AsyncSession) -> str:
    result = await db.execute(select(Lead).order_by(desc(Lead.created_at)).limit(5))
    leads = list(result.scalars().all())
    if not leads:
        return "No leads yet."
    return "Latest leads:\n" + "\n".join(_fmt_lead_line(l) for l in leads)


async def _cmd_lead(db: AsyncSession, arg: str) -> str:
    arg = arg.strip()
    if not arg:
        return "Usage: /lead <id>"
    lead = None
    try:
        lead = await db.get(Lead, uuid.UUID(arg))
    except (ValueError, TypeError):
        # short-id prefix lookup
        result = await db.execute(
            select(Lead).where(cast(Lead.id, SAString).ilike(f"{arg}%")).limit(2)
        )
        rows = list(result.scalars().all())
        if len(rows) == 1:
            lead = rows[0]
        elif len(rows) > 1:
            return "Multiple leads match that prefix; provide more characters."
    if lead is None:
        return "Lead not found."
    return _fmt_lead_detail(lead)


async def handle_update(db: AsyncSession, update: dict[str, Any]) -> dict[str, Any]:
    """Process a Telegram webhook update. Only the admin chat is served."""
    message = update.get("message") or update.get("edited_message") or {}
    chat = message.get("chat") or {}
    chat_id = str(chat.get("id", ""))
    text = (message.get("text") or "").strip()

    admin_chat = str(settings.TELEGRAM_ADMIN_CHAT_ID or "")
    if not admin_chat or chat_id != admin_chat:
        return {"ok": True, "ignored": "unauthorized_chat"}
    if not text.startswith("/"):
        return {"ok": True, "ignored": "not_a_command"}

    parts = text.split(maxsplit=1)
    command = parts[0].lower().split("@")[0]
    arg = parts[1] if len(parts) > 1 else ""

    if command == "/leads":
        reply = await _cmd_leads(db)
    elif command == "/lead":
        reply = await _cmd_lead(db, arg)
    else:
        reply = HELP_TEXT

    await send_message(chat_id, reply)
    return {"ok": True, "command": command, "reply": reply}
