"""Non-destructive Legacy-to-Core cutover readiness reporting."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.legacy_bridge import LegacyIdentityMapping
from app.models.legacy_migration import LegacyMigrationRecord, LegacyMigrationRun


async def _count(db: AsyncSession, model, *conditions) -> int:
    stmt = select(func.count()).select_from(model)
    for condition in conditions:
        stmt = stmt.where(condition)
    return int((await db.execute(stmt)).scalar() or 0)


async def build_legacy_cutover_readiness(
    db: AsyncSession,
    *,
    source_system: str = "cebu",
) -> dict:
    """Report migration readiness without stopping or deleting Legacy resources."""
    runs_total = await _count(
        db, LegacyMigrationRun, LegacyMigrationRun.source_system == source_system
    )
    runs_completed = await _count(
        db,
        LegacyMigrationRun,
        LegacyMigrationRun.source_system == source_system,
        LegacyMigrationRun.status == "COMPLETED",
    )
    runs_active_or_failed = await _count(
        db,
        LegacyMigrationRun,
        LegacyMigrationRun.source_system == source_system,
        LegacyMigrationRun.status != "COMPLETED",
    )
    records_total = await _count(
        db, LegacyMigrationRecord, LegacyMigrationRecord.source_system == source_system
    )
    records_failed = await _count(
        db,
        LegacyMigrationRecord,
        LegacyMigrationRecord.source_system == source_system,
        LegacyMigrationRecord.status != "SUCCESS",
    )
    archive_only_records = await _count(
        db,
        LegacyMigrationRecord,
        LegacyMigrationRecord.source_system == source_system,
        LegacyMigrationRecord.operation == "archived",
    )
    unmapped_typed_records = await _count(
        db,
        LegacyMigrationRecord,
        LegacyMigrationRecord.source_system == source_system,
        LegacyMigrationRecord.operation != "archived",
        LegacyMigrationRecord.core_entity_id.is_(None),
    )
    identity_total = await _count(
        db,
        LegacyIdentityMapping,
        LegacyIdentityMapping.legacy_system == source_system,
    )
    identity_incomplete = await _count(
        db,
        LegacyIdentityMapping,
        LegacyIdentityMapping.legacy_system == source_system,
        LegacyIdentityMapping.core_user_id.is_(None),
        LegacyIdentityMapping.core_company_id.is_(None),
    )

    blockers: list[str] = []
    if runs_completed == 0:
        blockers.append("No completed historical migration run exists.")
    if runs_active_or_failed:
        blockers.append(f"{runs_active_or_failed} migration run(s) are active, partial, or failed.")
    if records_failed:
        blockers.append(f"{records_failed} migration record(s) did not succeed.")
    if archive_only_records:
        blockers.append(
            f"{archive_only_records} object(s) are archive-only and still need typed Core ownership."
        )
    if unmapped_typed_records:
        blockers.append(f"{unmapped_typed_records} typed object(s) have no Core entity mapping.")
    if identity_total == 0:
        blockers.append("No Legacy identity mappings exist.")
    elif identity_incomplete:
        blockers.append(f"{identity_incomplete} identity mapping(s) have no Core user or company.")
    blockers.extend(
        [
            "Independent parity, migration replay, and rollback verification is required.",
            "Founder approval is required before any Legacy retirement action.",
        ]
    )

    implementation_ready = bool(
        runs_completed
        and not runs_active_or_failed
        and not records_failed
        and not archive_only_records
        and not unmapped_typed_records
        and identity_total
        and not identity_incomplete
    )
    return {
        "source_system": source_system,
        "implementation_ready": implementation_ready,
        "retirement_allowed": False,
        "legacy_runtime_action": "keep_read_only_reference",
        "runs": {
            "total": runs_total,
            "completed": runs_completed,
            "active_or_failed": runs_active_or_failed,
        },
        "records": {
            "total": records_total,
            "failed": records_failed,
            "archive_only": archive_only_records,
            "unmapped_typed": unmapped_typed_records,
        },
        "identities": {
            "total": identity_total,
            "incomplete": identity_incomplete,
        },
        "blockers": blockers,
    }
