"""Analytics projection tasks.

Runs on the automation queue: the platform's own outbox is translated into the
analytics spine on a schedule, so no existing producer has to change.
"""
from app.db.session import run_db_task
from app.tasks.celery_app import celery_app


@celery_app.task(name="project_analytics_events")
def project_analytics_events():
    """Translate new integration_events rows into analytics events."""
    from app.services.analytics_projection import project_outbox_events

    return run_db_task(project_outbox_events)
