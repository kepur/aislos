"""Phase A foundation tests: ai/channels schemas, outbox event bus, queue split.

ORM round-trips run against the live database and roll back so they leave no
residue; the relay test commits one event and cleans up after itself.
"""
import asyncio
import json
import uuid

import redis.asyncio as aioredis

from app.core.config import settings
from app.db.session import async_session_factory, engine
from app.models import (
    AgentRun,
    AIReview,
    ChannelAccount,
    ChannelDeliveryLog,
    ChannelMessage,
    ChannelThread,
    Conversation,
    ConversationMessage,
    DocumentChunk,
    IntegrationEvent,
    KnowledgeDocument,
)
from app.models.ai import EMBEDDING_DIM
from app.models.base_model import Base
from app.services.event_bus import (
    ALL_EVENT_TYPES,
    EVENT_STREAM_KEY,
    EventType,
    emit_event,
    publish_pending_events,
)
from app.tasks.celery_app import celery_app


# --- schema/table registration ----------------------------------------------

def test_ai_channels_tables_registered():
    expected = {
        "ai.knowledge_documents",
        "ai.document_chunks",
        "ai.conversations",
        "ai.messages",
        "ai.agent_runs",
        "ai.ai_reviews",
        "channels.channel_accounts",
        "channels.channel_threads",
        "channels.channel_messages",
        "channels.delivery_log",
    }
    assert expected.issubset(set(Base.metadata.tables))


def test_event_type_registry():
    assert EventType.LEAD_CREATED == "lead.created"
    assert EventType.KNOWLEDGE_UPLOADED == "knowledge.uploaded"
    assert "ai.draft_ready" in ALL_EVENT_TYPES
    # every event name follows the `domain.action` convention
    for name in ALL_EVENT_TYPES:
        domain, _, action = name.partition(".")
        assert domain and action, f"event {name} must be domain.action"


def test_celery_queue_split():
    assert celery_app.conf.task_default_queue == "default"
    routes = celery_app.conf.task_routes
    assert routes["ingest_knowledge_document"]["queue"] == "ai_ingestion"
    assert routes["scan_lifecycle_due"]["queue"] == "automation"
    assert routes["prepare_active_marketing_campaigns"]["queue"] == "automation"
    assert "relay-outbox-events" in celery_app.conf.beat_schedule


# --- ai schema ORM round-trip (rolled back) ----------------------------------

def test_ai_schema_orm_roundtrip():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            doc = KnowledgeDocument(source_type="pdf", title="KNX actuator manual", lang="en")
            convo = Conversation(channel="web", visitor_id="visitor-test", lang="en")
            db.add_all([doc, convo])
            await db.flush()

            chunk = DocumentChunk(
                document_id=doc.id,
                chunk_index=0,
                content="Mount the actuator on the DIN rail.",
                embedding=[0.1] * EMBEDDING_DIM,
            )
            msg = ConversationMessage(conversation_id=convo.id, role="user", content="hi")
            run = AgentRun(conversation_id=convo.id, workflow="consult", tokens_in=10, tokens_out=20)
            db.add_all([chunk, msg, run])
            await db.flush()

            review = AIReview(run_id=run.id, target_type="quote_draft", draft_json={"total": 100})
            db.add(review)
            await db.flush()

            assert doc.status == "pending"
            assert convo.status == "active"
            assert run.status == "running"
            assert review.status == "preliminary"
            assert chunk.document_id == doc.id

            # tsv is a stored generated column maintained by Postgres
            await db.refresh(chunk, ["tsv"])
            assert chunk.tsv is not None

            await db.rollback()

    asyncio.run(_run())


# --- channels schema ORM round-trip (rolled back) -----------------------------

def test_channels_schema_orm_roundtrip():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            account = ChannelAccount(channel="telegram", name="RS admin bot")
            db.add(account)
            await db.flush()

            thread = ChannelThread(account_id=account.id, external_thread_id="chat-42")
            db.add(thread)
            await db.flush()

            message = ChannelMessage(
                thread_id=thread.id, direction="in", external_message_id="m-1", content="hello"
            )
            db.add(message)
            await db.flush()

            log = ChannelDeliveryLog(message_id=message.id, status="sent")
            db.add(log)
            await db.flush()

            assert account.status == "active"
            assert message.status == "received"
            assert log.attempt == 1

            await db.rollback()

    asyncio.run(_run())


# --- outbox event bus ---------------------------------------------------------

def test_emit_event_is_transactional():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            event = await emit_event(
                db,
                EventType.LEAD_CREATED,
                {"lead_id": "x"},
                aggregate_type="lead",
                aggregate_id=uuid.uuid4(),
            )
            assert event.id is not None
            assert event.published_at is None
            assert event.status == "internal"  # no notification channel
            await db.rollback()  # caller owns the transaction

            assert await db.get(IntegrationEvent, event.id) is None

    asyncio.run(_run())


def test_outbox_relay_publishes_to_redis_stream():
    async def _run():
        await engine.dispose()
        marker = f"test-{uuid.uuid4()}"
        redis_client = aioredis.from_url(settings.REDIS_URL)
        try:
            async with async_session_factory() as db:
                event = await emit_event(
                    db, EventType.KNOWLEDGE_UPLOADED, {"marker": marker}
                )
                await db.commit()
                event_id = event.id

                published = await publish_pending_events(db, redis_client)
                assert published >= 1

                refreshed = await db.get(IntegrationEvent, event_id)
                assert refreshed is not None and refreshed.published_at is not None

                entries = await redis_client.xrange(EVENT_STREAM_KEY)
                ours = [
                    (entry_id, fields)
                    for entry_id, fields in entries
                    if fields.get(b"id") == str(event_id).encode()
                ]
                assert len(ours) == 1
                _, fields = ours[0]
                assert fields[b"type"] == EventType.KNOWLEDGE_UPLOADED.encode()
                assert json.loads(fields[b"payload"]) == {"marker": marker}

                # cleanup: remove our stream entry and the outbox row
                await redis_client.xdel(EVENT_STREAM_KEY, ours[0][0])
                await db.delete(refreshed)
                await db.commit()
        finally:
            await redis_client.aclose()

    asyncio.run(_run())
