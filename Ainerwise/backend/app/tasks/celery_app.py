from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "ainerwise",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    imports=(
        "app.tasks.notification_tasks",
        "app.tasks.event_tasks",
        "app.tasks.ingestion_tasks",
        "app.tasks.event_consumers",
        "app.tasks.briefing_tasks",
        "app.tasks.publishing_tasks",
    ),
    # Queue split: `default` = user-facing latency (notifications, outbox relay),
    # `ai_ingestion` = heavy/backloggable embedding work,
    # `automation` = scheduled lifecycle/marketing batch jobs.
    # Workers must listen with: celery worker -Q default,ai_ingestion,automation
    task_default_queue="default",
    task_routes={
        "ingest_knowledge_document": {"queue": "ai_ingestion"},
        "scan_lifecycle_due": {"queue": "automation"},
        "generate_monthly_report_jobs": {"queue": "automation"},
        "prepare_active_marketing_campaigns": {"queue": "automation"},
        "consume_domain_events": {"queue": "automation"},
        "recompute_partner_metrics": {"queue": "automation"},
        "release_due_retentions": {"queue": "automation"},
        "send_daily_briefing": {"queue": "automation"},
        "dispatch_publish_jobs": {"queue": "automation"},
        "generate_weekly_marketing_report": {"queue": "automation"},
    },
    # FI.8.4 / FI.8.5 — scheduled lifecycle automation (requires `celery beat`).
    beat_schedule={
        "relay-outbox-events": {
            "task": "relay_outbox_events",
            "schedule": 30.0,  # outbox -> Redis Stream latency ceiling
        },
        "consume-domain-events": {
            "task": "consume_domain_events",
            "schedule": 30.0,  # stream -> automation handlers
        },
        "send-daily-briefing": {
            "task": "send_daily_briefing",
            "schedule": crontab(hour=6, minute=30),  # Business Brain morning report
        },
        "dispatch-publish-jobs": {
            "task": "dispatch_publish_jobs",
            "schedule": 300.0,  # scheduled social/SEO publishing
        },
        "recompute-partner-metrics-daily": {
            "task": "recompute_partner_metrics",
            "schedule": crontab(hour=4, minute=30),
        },
        "release-due-retentions-daily": {
            "task": "release_due_retentions",
            "schedule": crontab(hour=8, minute=0),
        },
        "scan-lifecycle-due-daily": {
            "task": "scan_lifecycle_due",
            "schedule": crontab(hour=6, minute=0),  # daily 06:00 UTC
        },
        "generate-monthly-report-jobs": {
            "task": "generate_monthly_report_jobs",
            "schedule": crontab(hour=5, minute=0, day_of_month=1),  # monthly
        },
        "prepare-active-marketing-campaigns": {
            "task": "prepare_active_marketing_campaigns",
            "schedule": crontab(hour=7, minute=0),  # daily review-draft generation
        },
        "generate-weekly-marketing-report": {
            "task": "generate_weekly_marketing_report",
            "schedule": crontab(hour=7, minute=30, day_of_week=1),  # Monday
        },
    },
)

celery_app.autodiscover_tasks(["app.tasks"])
