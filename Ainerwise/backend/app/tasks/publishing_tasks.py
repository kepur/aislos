from app.tasks.celery_app import celery_app
from app.db.session import run_db_task


@celery_app.task(name="dispatch_publish_jobs")
def dispatch_publish_jobs():
    """Send due publish jobs to the social aggregator (Ayrshare-style API).

    No aggregator configured -> jobs flip to manual_required so the admin
    posts by hand and nothing silently rots in the queue.
    """
    from datetime import datetime, timezone

    import httpx
    from sqlalchemy import select

    from app.models.ai import AgentRun
    from app.models.content import PublishJob
    from app.models.marketing import MarketingAsset
    from app.services.agent_runtime import AgentAuthorizationError, require_agent
    from app.services.integrations import get_config

    async def _run(db):
        try:
            await require_agent(
                db,
                "marketing-agent",
                scopes=("ads",),
                workflow="publish",
            )
        except AgentAuthorizationError as exc:
            return {"dispatched": 0, "skipped": True, "reason": str(exc)}
        jobs = (
            await db.execute(
                select(PublishJob).where(
                    PublishJob.status == "scheduled",
                    PublishJob.scheduled_at <= datetime.now(timezone.utc),
                ).limit(20)
            )
        ).scalars().all()
        if not jobs:
            return {"dispatched": 0}

        cfg = await get_config(db, "social")
        configured = bool(cfg.get("_enabled") and cfg.get("api_key") and cfg.get("base_url"))
        dispatched = 0
        for job in jobs:
            asset = await db.get(MarketingAsset, job.asset_id)
            if asset is None or asset.status not in ("approved", "scheduled", "published"):
                job.status = "cancelled"
                job.error_message = "asset missing or not approved"
                db.add(job)
                continue
            if not configured:
                job.status = "manual_required"
                job.error_message = "no social aggregator configured (Admin → Integrations → social)"
                db.add(job)
                continue
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.post(
                        cfg["base_url"].rstrip("/") + "/post",
                        headers={"Authorization": f"Bearer {cfg['api_key']}"},
                        json={
                            "post": f"{asset.title}\n\n{asset.content}" if asset.title else asset.content,
                            "platforms": [job.platform],
                        },
                    )
                    response.raise_for_status()
                    body = response.json()
                job.status = "published"
                job.published_at = datetime.now(timezone.utc)
                job.external_post_id = str(body.get("id") or body.get("postIds") or "")[:255]
                asset.status = "published"
                db.add(asset)
            except Exception as exc:  # noqa: BLE001 — keep the job visible with its error
                job.status = "failed"
                job.error_message = str(exc)[:500]
            db.add(job)
            dispatched += 1
        db.add(
            AgentRun(
                agent_slug="marketing-agent",
                workflow="publish",
                input_json={"due_jobs": len(jobs)},
                output_json={"dispatched": dispatched},
                status="completed",
            )
        )
        await db.commit()
        return {"dispatched": dispatched}

    return run_db_task(_run)
