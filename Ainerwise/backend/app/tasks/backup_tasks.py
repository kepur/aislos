from app.db.session import run_db_task
from app.tasks.celery_app import celery_app


@celery_app.task(name="run_due_backup_schedules")
def run_due_backup_schedules_task():
    from app.services.backup_service import run_due_backup_schedules

    return run_db_task(run_due_backup_schedules)
