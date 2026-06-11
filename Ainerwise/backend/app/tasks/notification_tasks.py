from app.tasks.celery_app import celery_app
from app.db.session import run_db_task
from app.models.integration import IntegrationEvent
from app.services.ai_analysis import analyze_lead
from app.services.integration_events import dispatch_telegram_event


@celery_app.task(name="send_telegram_notification")
def send_telegram_notification(event_id: str):
    """Retry a persisted Telegram integration event."""
    import uuid

    async def _run(db):
        event = await db.get(IntegrationEvent, uuid.UUID(event_id))
        if event is not None:
            await dispatch_telegram_event(db, event)

    return run_db_task(_run)


@celery_app.task(name="analyze_lead")
def analyze_lead_task(lead_id: str):
    """Run the MVP lead analysis workflow from a worker."""
    import uuid

    return run_db_task(lambda db: analyze_lead(db, lead_id=uuid.UUID(lead_id)))


@celery_app.task(name="scan_lifecycle_due")
def scan_lifecycle_due():
    """FI.8.4 — daily scan of due dates -> deduplicated lifecycle events."""
    from app.services.lifecycle_automation import scan_and_notify

    return run_db_task(scan_and_notify)


@celery_app.task(name="generate_monthly_report_jobs")
def generate_monthly_report_jobs():
    """FI.8.5 — schedule monthly compliance report jobs (pending review)."""
    from app.services.lifecycle_automation import generate_report_jobs

    return run_db_task(generate_report_jobs)


@celery_app.task(name="prepare_active_marketing_campaigns")
def prepare_active_marketing_campaigns():
    """Generate reviewable drafts for active, consent-safe campaigns."""
    from app.services.marketing_automation import prepare_active_campaigns

    return run_db_task(prepare_active_campaigns)


@celery_app.task(name="generate_weekly_marketing_report")
def generate_weekly_marketing_report_task():
    """Phase H: Marketing Agent weekly report, stored for human review."""
    from app.services.marketing_reporting import generate_weekly_marketing_report

    return run_db_task(generate_weekly_marketing_report)
