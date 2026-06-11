"""SMTP email sending using admin-configured settings."""
from __future__ import annotations

import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.integrations import get_config


def _send_sync(cfg: dict[str, Any], to: list[str], subject: str, body: str, html: str | None) -> None:
    msg = MIMEMultipart("alternative")
    from_email = cfg.get("from_email") or cfg.get("username")
    from_name = cfg.get("from_name") or "AinerWise"
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = ", ".join(to)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))
    if html:
        msg.attach(MIMEText(html, "html", "utf-8"))

    host = cfg["host"]
    port = int(cfg.get("port") or 587)
    timeout = 15
    if cfg.get("use_ssl"):
        server = smtplib.SMTP_SSL(host, port, timeout=timeout)
    else:
        server = smtplib.SMTP(host, port, timeout=timeout)
        if cfg.get("use_tls", True):
            server.starttls()
    try:
        if cfg.get("username"):
            server.login(cfg["username"], cfg.get("password") or "")
        server.sendmail(from_email, to, msg.as_string())
    finally:
        server.quit()


async def send_email(db: AsyncSession, *, to: str | list[str], subject: str, body: str, html: str | None = None) -> dict[str, Any]:
    cfg = await get_config(db, "smtp")
    recipients = [to] if isinstance(to, str) else list(to)
    if not cfg.get("_enabled"):
        return {"sent": False, "reason": "smtp_disabled"}
    if not cfg.get("host") or not (cfg.get("from_email") or cfg.get("username")):
        return {"sent": False, "reason": "smtp_not_configured"}
    try:
        await asyncio.to_thread(_send_sync, cfg, recipients, subject, body, html)
    except Exception as exc:  # noqa: BLE001
        return {"sent": False, "reason": str(exc)}
    return {"sent": True, "to": recipients}
