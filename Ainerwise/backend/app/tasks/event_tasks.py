from app.tasks.celery_app import celery_app
from app.db.session import run_db_task


@celery_app.task(name="relay_outbox_events")
def relay_outbox_events():
    """Push unpublished integration events to the Redis Stream event bus."""
    from app.services.event_bus import publish_pending_events

    return run_db_task(publish_pending_events)
