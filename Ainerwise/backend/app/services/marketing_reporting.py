"""Weekly Marketing Agent report from real operational metrics."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import AgentRun, AIReview
from app.models.content import PublishJob
from app.models.lead import Lead
from app.models.marketing import MarketingAsset, MarketingCampaign
from app.services.agent_runtime import require_agent


async def generate_weekly_marketing_report(db: AsyncSession) -> AgentRun:
    await require_agent(
        db,
        "marketing-agent",
        scopes=("ads", "customer_data"),
        workflow="marketing_weekly_report",
    )
    since = datetime.now(timezone.utc) - timedelta(days=7)

    async def count(model, *where) -> int:
        return int((await db.execute(select(func.count()).select_from(model).where(*where))).scalar() or 0)

    metrics = {
        "period_start": since.isoformat(),
        "leads_created": await count(Lead, Lead.created_at >= since),
        "campaigns_active": await count(MarketingCampaign, MarketingCampaign.status == "active"),
        "assets_created": await count(MarketingAsset, MarketingAsset.created_at >= since),
        "assets_pending_review": await count(MarketingAsset, MarketingAsset.status == "in_review"),
        "posts_published": await count(PublishJob, PublishJob.published_at >= since),
        "publish_failures": await count(
            PublishJob,
            PublishJob.created_at >= since,
            PublishJob.status.in_(("failed", "manual_required")),
        ),
    }
    recommendations = []
    if metrics["leads_created"] == 0:
        recommendations.append("Run one focused campaign tied to a measurable project-assessment CTA.")
    if metrics["assets_pending_review"]:
        recommendations.append("Clear the content review queue before generating more assets.")
    if metrics["publish_failures"]:
        recommendations.append("Resolve failed/manual publishing jobs before expanding channels.")
    if not recommendations:
        recommendations.append("Continue the current cadence and compare lead quality by source.")

    output = {
        "metrics": metrics,
        "recommendations": recommendations,
        "preliminary": True,
        "summary": (
            f"Last 7 days: {metrics['leads_created']} leads, "
            f"{metrics['posts_published']} published posts, "
            f"{metrics['assets_pending_review']} assets awaiting review."
        ),
    }
    run = AgentRun(
        agent_slug="marketing-agent",
        workflow="marketing_weekly_report",
        input_json={"period_days": 7},
        output_json=output,
        status="completed",
    )
    db.add(run)
    await db.flush()
    db.add(
        AIReview(
            run_id=run.id,
            target_type="marketing_weekly_report",
            target_id=run.id,
            draft_json=output,
            status="preliminary",
        )
    )
    await db.flush()
    return run
