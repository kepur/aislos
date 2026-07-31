"""ZL10 shared middleware convergence gates."""

import asyncio
import uuid

from app.crud.lead import crud_lead
from app.db.session import async_session_factory, engine
from app.models.integration import IntegrationEvent
from app.models.legacy_bridge import LegacyIdentityMapping
from app.models.legacy_migration import LegacyMigrationRecord, LegacyMigrationRun
from app.models.lead import Lead
from app.services.event_bus import emit_event
from app.services.integration_events import deliver_telegram_event, queue_admin_telegram
from app.services.legacy_cutover import build_legacy_cutover_readiness
from app.tasks.celery_app import celery_app


def test_business_row_and_outbox_commit_or_rollback_together():
    async def _run():
        await engine.dispose()
        rollback_email = f"zl10-rollback-{uuid.uuid4().hex}@test.local"
        commit_email = f"zl10-commit-{uuid.uuid4().hex}@test.local"

        async with async_session_factory() as db:
            lead = await crud_lead.create_in_transaction(
                db,
                obj_in={"contact_email": rollback_email, "status": "new"},
            )
            event = await emit_event(
                db,
                "lead.created",
                {"lead_id": str(lead.id)},
                aggregate_type="lead",
                aggregate_id=lead.id,
            )
            rollback_lead_id, rollback_event_id = lead.id, event.id
            await db.rollback()

        async with async_session_factory() as db:
            assert await db.get(Lead, rollback_lead_id) is None
            assert await db.get(IntegrationEvent, rollback_event_id) is None

            lead = await crud_lead.create_in_transaction(
                db,
                obj_in={"contact_email": commit_email, "status": "new"},
            )
            event = await emit_event(
                db,
                "lead.created",
                {"lead_id": str(lead.id)},
                aggregate_type="lead",
                aggregate_id=lead.id,
            )
            commit_lead_id, commit_event_id = lead.id, event.id
            await db.commit()

        async with async_session_factory() as db:
            assert await db.get(Lead, commit_lead_id) is not None
            assert await db.get(IntegrationEvent, commit_event_id) is not None
            await db.delete(await db.get(IntegrationEvent, commit_event_id))
            await db.delete(await db.get(Lead, commit_lead_id))
            await db.commit()

    asyncio.run(_run())


def test_telegram_queue_and_delivery_do_not_hide_commits(monkeypatch):
    async def _no_credentials(_db):
        return None, None

    monkeypatch.setattr("app.services.integrations.telegram_credentials", _no_credentials)

    async def _run():
        await engine.dispose()
        marker = uuid.uuid4()
        async with async_session_factory() as db:
            event = await queue_admin_telegram(
                db,
                event_type="zl10.delivery.test",
                payload={"marker": str(marker)},
                aggregate_type="test",
                aggregate_id=marker,
            )
            event_id = event.id
            assert event.target_channel == "telegram_admin"
            assert event.status == "pending"
            await db.commit()

        async with async_session_factory() as db:
            event = await db.get(IntegrationEvent, event_id)
            await deliver_telegram_event(db, event)
            assert event.status == "skipped"
            await db.rollback()

        async with async_session_factory() as db:
            event = await db.get(IntegrationEvent, event_id)
            assert event.status == "pending"
            await db.delete(event)
            await db.commit()

    asyncio.run(_run())


def test_notification_outbox_dispatch_is_scheduled():
    celery_app.loader.import_default_modules()
    assert "dispatch_pending_telegram_events" in celery_app.tasks
    schedule = celery_app.conf.beat_schedule["dispatch-pending-telegram-events"]
    assert schedule["task"] == "dispatch_pending_telegram_events"


def test_core_producers_no_longer_use_legacy_immediate_commit_helper():
    from pathlib import Path

    app_root = Path(__file__).parents[1] / "app"
    callers = []
    for path in app_root.rglob("*.py"):
        if path.name == "integration_events.py":
            continue
        if "create_integration_event" in path.read_text():
            callers.append(str(path.relative_to(app_root)))
    assert callers == []


def test_dispute_emits_one_shared_outbox_event_shape():
    from app.services import commerce_trade

    source = commerce_trade.open_dispute.__code__
    assert "queue_admin_telegram" not in source.co_names
    assert "emit_event" in source.co_names


def test_legacy_cutover_gate_reports_blockers_without_retiring_legacy():
    async def _run():
        await engine.dispose()
        source = f"zl10-{uuid.uuid4().hex}"
        async with async_session_factory() as db:
            run = LegacyMigrationRun(
                source_system=source,
                portal_key="cebu",
                batch_key=f"batch-{uuid.uuid4().hex}",
                checksum="a" * 64,
                status="COMPLETED",
                total_records=2,
                succeeded_records=2,
                failed_records=0,
            )
            db.add(run)
            await db.flush()
            db.add_all(
                [
                    LegacyMigrationRecord(
                        run_id=run.id,
                        source_system=source,
                        entity_type="users",
                        legacy_id="user-1",
                        payload_hash="b" * 64,
                        operation="created",
                        status="SUCCESS",
                        core_entity_id=uuid.uuid4(),
                    ),
                    LegacyMigrationRecord(
                        run_id=run.id,
                        source_system=source,
                        entity_type="future_objects",
                        legacy_id="future-1",
                        payload_hash="c" * 64,
                        operation="archived",
                        status="SUCCESS",
                    ),
                    LegacyIdentityMapping(
                        portal_key="cebu",
                        legacy_system=source,
                        legacy_user_id="user-1",
                        core_user_id=uuid.uuid4(),
                    ),
                ]
            )
            await db.commit()

        async with async_session_factory() as db:
            result = await build_legacy_cutover_readiness(db, source_system=source)
            assert result["records"]["archive_only"] == 1
            assert result["implementation_ready"] is False
            assert result["retirement_allowed"] is False
            assert result["legacy_runtime_action"] == "keep_read_only_reference"
            assert any("Founder approval" in blocker for blocker in result["blockers"])
            for row in (await db.execute(
                select(LegacyMigrationRecord).where(LegacyMigrationRecord.source_system == source)
            )).scalars():
                await db.delete(row)
            for row in (await db.execute(
                select(LegacyIdentityMapping).where(LegacyIdentityMapping.legacy_system == source)
            )).scalars():
                await db.delete(row)
            for row in (await db.execute(
                select(LegacyMigrationRun).where(LegacyMigrationRun.source_system == source)
            )).scalars():
                await db.delete(row)
            await db.commit()

    from sqlalchemy import select

    asyncio.run(_run())
