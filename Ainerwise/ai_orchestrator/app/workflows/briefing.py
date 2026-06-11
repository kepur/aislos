"""AI Business Brain — daily CEO briefing.

Read-only SQL aggregates over the business schema + partner score trend from
the append-only snapshots, narrated by the LLM when configured (plain template
otherwise). Logged to ai.agent_runs; delivery (Telegram/dashboard) is the
backend's job.
"""
from __future__ import annotations

import json
import time
import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm import chat, get_ai_config, is_chat_configured

BRIEFING_SYSTEM = """You are the AI Business Brain of AinerWise, an AI general \
contractor platform. Write a short, factual morning briefing for the founder \
based ONLY on the metrics provided. Lead with yesterday's numbers, then risks \
and required approvals, then one concrete suggestion. No invented numbers. \
Keep it under 180 words, plain text, bullet style."""

METRICS_SQL: dict[str, str] = {
    "leads_yesterday": (
        "SELECT count(*) FROM leads WHERE created_at >= current_date - interval '1 day' "
        "AND created_at < current_date"
    ),
    "quotes_yesterday": (
        "SELECT count(*) FROM quotes WHERE created_at >= current_date - interval '1 day' "
        "AND created_at < current_date"
    ),
    "rfqs_awarded_yesterday": (
        "SELECT count(*) FROM rfqs WHERE status = 'awarded' "
        "AND updated_at >= current_date - interval '1 day' AND updated_at < current_date"
    ),
    "revenue_funded_yesterday": (
        "SELECT coalesce(sum(amount), 0) FROM payment_milestones "
        "WHERE funded_at >= current_date - interval '1 day' AND funded_at < current_date"
    ),
    "maintenance_due_7d": (
        "SELECT count(*) FROM maintenance_schedules WHERE due_date IS NOT NULL "
        "AND due_date <= current_date + interval '7 days' AND status NOT IN ('done', 'completed', 'cancelled')"
    ),
    "reviews_pending": "SELECT count(*) FROM ai.ai_reviews WHERE status = 'preliminary'",
    "leads_need_followup": (
        "SELECT count(*) FROM leads WHERE status IN ('new', 'need_more_info') "
        "AND created_at < now() - interval '3 days'"
    ),
    "open_rfqs_bidding": "SELECT count(*) FROM rfqs WHERE status IN ('bidding', 'evaluating')",
}

REGION_MARGIN_SQL = text(
    """
SELECT country, round(avg(gross_margin_pct), 1) AS avg_margin, count(*) AS cases
FROM cases
WHERE gross_margin_pct IS NOT NULL AND country IS NOT NULL
GROUP BY country
ORDER BY avg_margin DESC
LIMIT 6
"""
)

MARKETING_SQL: dict[str, str] = {
    "posts_published_yesterday": (
        "SELECT count(*) FROM publish_jobs WHERE status = 'published' "
        "AND published_at >= current_date - interval '1 day' AND published_at < current_date"
    ),
    "seo_pages_published": "SELECT count(*) FROM seo_pages WHERE status = 'published'",
}

LEADS_BY_SOURCE_SQL = text(
    """
SELECT coalesce(source_channel, 'unknown') AS source, count(*) AS leads
FROM leads
WHERE created_at >= current_date - interval '1 day' AND created_at < current_date
GROUP BY 1 ORDER BY 2 DESC LIMIT 5
"""
)

PARTNER_RISK_SQL = text(
    """
WITH ranked AS (
    SELECT partner_id, composite_score, snapshot_date,
           row_number() OVER (PARTITION BY partner_id ORDER BY snapshot_date DESC) AS rn
    FROM partner_metric_snapshots
)
SELECT cur.partner_id,
       cur.composite_score AS current_score,
       prev.composite_score AS previous_score
FROM ranked cur
JOIN ranked prev ON prev.partner_id = cur.partner_id AND prev.rn = 2
WHERE cur.rn = 1
  AND cur.composite_score IS NOT NULL AND prev.composite_score IS NOT NULL
  AND prev.composite_score - cur.composite_score >= 10
"""
)


def _template_text(metrics: dict[str, Any]) -> str:
    lines = [
        "Good morning. Yesterday:",
        f"• New leads: {metrics['leads_yesterday']}",
        f"• Quotes created: {metrics['quotes_yesterday']}",
        f"• RFQs awarded: {metrics['rfqs_awarded_yesterday']}",
        f"• Revenue funded: {metrics['revenue_funded_yesterday']}€",
        "",
        f"Open: {metrics['open_rfqs_bidding']} RFQs in bidding, "
        f"{metrics['reviews_pending']} AI drafts awaiting approval.",
        f"Maintenance due in 7 days: {metrics['maintenance_due_7d']}.",
        f"Leads needing follow-up (>3 days): {metrics['leads_need_followup']}.",
    ]
    if metrics["partner_risk"]:
        flagged = ", ".join(
            f"{r['partner_id'][:8]} ({r['previous_score']}→{r['current_score']})"
            for r in metrics["partner_risk"]
        )
        lines.append(f"⚠ Partner score drop: {flagged} — consider pausing dispatch.")
    if metrics.get("region_margin") and len(metrics["region_margin"]) >= 2:
        best, worst = metrics["region_margin"][0], metrics["region_margin"][-1]
        lines.append(
            f"Margin by region: {best['country']} {best['avg_margin_pct']}% vs "
            f"{worst['country']} {worst['avg_margin_pct']}% "
            f"({best['avg_margin_pct'] - worst['avg_margin_pct']:+.1f}pp)."
        )
    if metrics.get("leads_by_source_yesterday"):
        top = metrics["leads_by_source_yesterday"][0]
        lines.append(f"Top lead source yesterday: {top['source']} ({top['leads']}).")
    return "\n".join(lines)


async def run_briefing(db: AsyncSession) -> dict[str, Any]:
    started = time.monotonic()
    metrics: dict[str, Any] = {}
    for key, sql in METRICS_SQL.items():
        value = (await db.execute(text(sql))).scalar()
        metrics[key] = float(value) if key == "revenue_funded_yesterday" else int(value or 0)

    for key, sql in MARKETING_SQL.items():
        metrics[key] = int((await db.execute(text(sql))).scalar() or 0)
    metrics["region_margin"] = [
        {"country": row["country"], "avg_margin_pct": float(row["avg_margin"]), "cases": int(row["cases"])}
        for row in (await db.execute(REGION_MARGIN_SQL)).mappings().all()
    ]
    metrics["leads_by_source_yesterday"] = [
        {"source": row["source"], "leads": int(row["leads"])}
        for row in (await db.execute(LEADS_BY_SOURCE_SQL)).mappings().all()
    ]

    risk_rows = (await db.execute(PARTNER_RISK_SQL)).mappings().all()
    metrics["partner_risk"] = [
        {
            "partner_id": str(row["partner_id"]),
            "current_score": float(row["current_score"]),
            "previous_score": float(row["previous_score"]),
        }
        for row in risk_rows
    ]

    cfg = await get_ai_config(db)
    briefing_text = _template_text(metrics)
    model_used = None
    tokens_in = tokens_out = None
    error = None
    if is_chat_configured(cfg):
        try:
            result = await chat(
                cfg,
                [{"role": "system", "content": BRIEFING_SYSTEM},
                 {"role": "user", "content": json.dumps(metrics, ensure_ascii=False)}],
                max_tokens=500,
            )
            if result and result["content"].strip():
                briefing_text = result["content"].strip()
                model_used = result["model"]
                tokens_in, tokens_out = result["tokens_in"], result["tokens_out"]
        except Exception as exc:  # noqa: BLE001 — template already in place
            error = str(exc)[:300]

    latency_ms = int((time.monotonic() - started) * 1000)
    output = {"metrics": metrics, "text": briefing_text}
    await db.execute(
        text(
            "INSERT INTO ai.agent_runs (id, agent_slug, workflow, model_name, tokens_in, tokens_out, "
            "latency_ms, status, output_json, error_message) "
            "VALUES (:id, 'business-brain', 'daily_briefing', :model, :tin, :tout, :latency, :status, "
            "CAST(:output AS jsonb), :error)"
        ),
        {
            "id": uuid.uuid4(), "model": model_used, "tin": tokens_in, "tout": tokens_out,
            "latency": latency_ms, "status": "failed" if error else "completed",
            "output": json.dumps(output), "error": error,
        },
    )
    await db.commit()
    return output
