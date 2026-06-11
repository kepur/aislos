"""C02: atomic procurement audit events (flush-only, transactional rollback)."""
import asyncio
import uuid

from sqlalchemy import func, select

from app.db.session import async_session_factory, engine
from app.models.audit import AuditLog
from app.services.audit import AuditEventError, append_audit_event, log_action


def test_append_audit_event_persists_on_commit():
    async def _run():
        await engine.dispose()
        user_id = uuid.uuid4()
        entity_id = uuid.uuid4()
        async with async_session_factory() as db:
            entry = await append_audit_event(
                db,
                actor_type="user",
                actor_user_id=user_id,
                portal_key="aislos",
                action="procurement.project.created",
                entity_type="procurement_project",
                entity_id=entity_id,
                before={"status": None},
                after={"status": "draft"},
                reason="created",
                source="test",
                correlation_id="corr-1",
                require_procurement_action=True,
            )
            assert entry.id is not None
            await db.commit()

        async with async_session_factory() as db:
            row = await db.get(AuditLog, entry.id)
            assert row is not None
            assert row.portal_key == "aislos"
            assert row.reason == "created"
            assert row.correlation_id == "corr-1"

    asyncio.run(_run())


def test_append_audit_event_rolls_back_with_transaction():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            before = (
                await db.execute(select(func.count()).select_from(AuditLog))
            ).scalar()
            try:
                await append_audit_event(
                    db,
                    actor_type="system",
                    action="procurement.fact.created",
                    entity_type="procurement_fact",
                    source="test",
                    require_procurement_action=True,
                )
                await db.flush()
                raise RuntimeError("simulate business failure")
            except RuntimeError:
                await db.rollback()

            after = (
                await db.execute(select(func.count()).select_from(AuditLog))
            ).scalar()
            assert after == before

    asyncio.run(_run())


def test_append_audit_event_validates_actor_and_action():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            try:
                await append_audit_event(
                    db,
                    actor_type="user",
                    action="procurement.project.created",
                    entity_type="procurement_project",
                )
                assert False, "expected AuditEventError"
            except AuditEventError:
                pass
            try:
                await append_audit_event(
                    db,
                    actor_type="agent",
                    agent_slug="x",
                    action="not-in-allowlist",
                    entity_type="procurement_project",
                    require_procurement_action=True,
                )
                assert False, "expected AuditEventError"
            except AuditEventError:
                pass

    asyncio.run(_run())


def test_log_action_still_commits_for_legacy_callers():
    async def _run():
        await engine.dispose()
        user_id = uuid.uuid4()
        async with async_session_factory() as db:
            entry = await log_action(
                db,
                actor_user_id=user_id,
                action="legacy_test_action",
                entity_type="product",
            )
            assert entry.source == "legacy.log_action"
            assert entry.actor_type == "user"

        async with async_session_factory() as db:
            assert await db.get(AuditLog, entry.id) is not None

    asyncio.run(_run())
