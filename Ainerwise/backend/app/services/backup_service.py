"""Backup archive creation and retention for the unified platform."""
from __future__ import annotations

import json
import os
import re
import uuid
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.backup import BackupJob, BackupSchedule
from app.models.commerce import CommerceOrder, ProcurementRequest
from app.models.file import FileAsset
from app.models.project import Project
from app.models.user import Company, User


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _bounded(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, int(value)))


def next_run_at_for_schedule(schedule: BackupSchedule, now: datetime | None = None) -> datetime:
    now = now or utc_now()
    base = now.replace(second=0, microsecond=0)
    if schedule.frequency == "WEEKLY":
        weekday = _bounded(schedule.day_of_week if schedule.day_of_week is not None else 0, 0, 6)
        candidate = base.replace(hour=_bounded(schedule.hour, 0, 23), minute=_bounded(schedule.minute, 0, 59))
        delta = (weekday - candidate.weekday()) % 7
        return candidate + timedelta(days=delta or (7 if candidate <= now else 0))
    if schedule.frequency == "MONTHLY":
        day = _bounded(schedule.day_of_month if schedule.day_of_month is not None else 1, 1, 28)
        candidate = base.replace(day=day, hour=_bounded(schedule.hour, 0, 23), minute=_bounded(schedule.minute, 0, 59))
        if candidate <= now:
            year = candidate.year + (1 if candidate.month == 12 else 0)
            month = 1 if candidate.month == 12 else candidate.month + 1
            candidate = candidate.replace(year=year, month=month, day=day)
        return candidate
    every_n = re.match(r"^\*/(\d{1,3}) \* \* \* \*$", (schedule.cron_expr or "").strip())
    if every_n:
        return now + timedelta(minutes=_bounded(int(every_n.group(1)), 1, 180))
    return now + timedelta(days=1)


async def _metadata(db: AsyncSession, job: BackupJob) -> dict:
    counts = {}
    for name, model in (
        ("users", User),
        ("companies", Company),
        ("projects", Project),
        ("procurement_requests", ProcurementRequest),
        ("commerce_orders", CommerceOrder),
        ("file_assets", FileAsset),
    ):
        counts[name] = int((await db.execute(select(func.count()).select_from(model))).scalar() or 0)
    files = list((await db.execute(select(FileAsset).order_by(FileAsset.created_at.desc()).limit(5000))).scalars())
    return {
        "generated_at": utc_now().isoformat(),
        "job_id": str(job.id),
        "schedule_id": str(job.schedule_id) if job.schedule_id else None,
        "record_counts": counts,
        "files": [
            {
                "id": str(row.id),
                "filename": row.original_name,
                "storage_key": row.storage_path,
                "mime_type": row.mime_type,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in files
        ],
    }


async def create_backup_archive(
    db: AsyncSession, *, schedule_id: uuid.UUID | None = None, created_by: uuid.UUID | None = None
) -> BackupJob:
    job = BackupJob(schedule_id=schedule_id, status="RUNNING", started_at=utc_now(), created_by=created_by)
    db.add(job)
    await db.flush()
    backup_dir = Path(settings.BACKUP_DIR)
    upload_dir = Path(settings.UPLOAD_DIR)
    backup_dir.mkdir(parents=True, exist_ok=True)
    archive_path = backup_dir / f"ainerwise-{utc_now().strftime('%Y%m%d-%H%M%S')}-{job.id}.zip"
    try:
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("metadata.json", json.dumps(await _metadata(db, job), indent=2))
            if upload_dir.exists():
                for path in upload_dir.rglob("*"):
                    if path.is_file():
                        try:
                            archive.write(path, arcname=f"uploads/{path.relative_to(upload_dir)}")
                        except OSError:
                            continue
        job.status = "SUCCESS"
        job.archive_path = str(archive_path)
        job.archive_size_bytes = archive_path.stat().st_size
    except Exception as exc:  # noqa: BLE001 - failure must remain visible in job ledger
        job.status = "FAILED"
        job.error_message = str(exc)[:2000]
    job.finished_at = utc_now()
    await db.flush()
    return job


async def apply_retention(db: AsyncSession, schedule: BackupSchedule) -> None:
    jobs = list(
        (
            await db.execute(
                select(BackupJob)
                .where(BackupJob.schedule_id == schedule.id, BackupJob.status == "SUCCESS")
                .order_by(BackupJob.created_at.desc())
            )
        ).scalars()
    )
    threshold = utc_now() - timedelta(days=_bounded(schedule.retention_days, 1, 3650))
    for index, job in enumerate(jobs):
        if index < _bounded(schedule.retention_count, 1, 120) and job.created_at >= threshold:
            continue
        if job.archive_path and os.path.exists(job.archive_path):
            try:
                os.remove(job.archive_path)
            except OSError:
                pass
        await db.delete(job)


async def run_due_backup_schedules(db: AsyncSession) -> dict:
    now = utc_now()
    schedules = list(
        (
            await db.execute(
                select(BackupSchedule).where(
                    BackupSchedule.enabled.is_(True),
                    (BackupSchedule.next_run_at.is_(None)) | (BackupSchedule.next_run_at <= now),
                )
            )
        ).scalars()
    )
    for schedule in schedules:
        await create_backup_archive(db, schedule_id=schedule.id, created_by=schedule.created_by)
        schedule.last_run_at = now
        schedule.next_run_at = next_run_at_for_schedule(schedule, now)
        await apply_retention(db, schedule)
    await db.commit()
    return {"ran": len(schedules)}
