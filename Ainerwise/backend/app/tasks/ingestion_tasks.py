from app.tasks.celery_app import celery_app
from app.db.session import run_db_task


@celery_app.task(name="ingest_knowledge_document")
def ingest_knowledge_document(document_id: str):
    """Knowledge ingestion on the ai_ingestion queue: extract -> chunk -> embed."""
    import uuid

    from app.services.knowledge import ingest_document

    return run_db_task(lambda db: ingest_document(db, uuid.UUID(document_id)))
