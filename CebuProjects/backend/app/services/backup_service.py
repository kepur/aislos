import json
import os
import re
import shutil
import uuid
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.backup import BackupFrequency, BackupJob, BackupJobStatus, BackupSchedule
from app.models.company_document import CompanyDocument


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _safe_int(value: int, min_value: int, max_value: int) -> int:
    return max(min_value, min(max_value, int(value)))


def next_run_at_for_schedule(schedule: BackupSchedule, now: datetime | None = None) -> datetime:
    now = now or _utc_now()
    base = now.replace(second=0, microsecond=0)

    if schedule.frequency == BackupFrequency.WEEKLY:
        target_weekday = _safe_int(schedule.day_of_week if schedule.day_of_week is not None else 0, 0, 6)
        candidate = base.replace(hour=_safe_int(schedule.hour, 0, 23), minute=_safe_int(schedule.minute, 0, 59))
        delta = (target_weekday - candidate.weekday()) % 7
        if delta == 0 and candidate <= now:
            delta = 7
        return candidate + timedelta(days=delta)

    if schedule.frequency == BackupFrequency.MONTHLY:
        target_dom = _safe_int(schedule.day_of_month if schedule.day_of_month is not None else 1, 1, 28)
        candidate = base.replace(day=target_dom, hour=_safe_int(schedule.hour, 0, 23), minute=_safe_int(schedule.minute, 0, 59))
        if candidate <= now:
            year = candidate.year + (1 if candidate.month == 12 else 0)
            month = 1 if candidate.month == 12 else candidate.month + 1
            candidate = candidate.replace(year=year, month=month, day=target_dom)
        return candidate

    expr = (schedule.cron_expr or "").strip()
    # Supports only: "M H * * *" and "*/N * * * *" as a lightweight custom mode.
    every_n = re.match(r"^\*/(\d{1,3}) \* \* \* \*$", expr)
    if every_n:
        minutes = _safe_int(int(every_n.group(1)), 1, 180)
        return now + timedelta(minutes=minutes)

    basic = re.match(r"^(\d{1,2}) (\d{1,2}) \* \* \*$", expr)
    if basic:
        minute = _safe_int(int(basic.group(1)), 0, 59)
        hour = _safe_int(int(basic.group(2)), 0, 23)
        candidate = base.replace(hour=hour, minute=minute)
        if candidate <= now:
            candidate = candidate + timedelta(days=1)
        return candidate

    return now + timedelta(days=1)


async def create_backup_archive(db: AsyncSession, *, schedule_id: uuid.UUID | None = None, created_by: uuid.UUID | None = None) -> BackupJob:
    job = BackupJob(
        schedule_id=schedule_id,
        status=BackupJobStatus.RUNNING,
        started_at=_utc_now(),
        created_by=created_by,
    )
    db.add(job)
    await db.flush()

    uploads_dir = Path(settings.UPLOAD_DIR)
    backups_dir = uploads_dir / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)
    archive_path = backups_dir / f"backup-{_utc_now().strftime('%Y%m%d-%H%M%S')}-{job.id}.zip"

    try:
        docs_result = await db.execute(select(CompanyDocument.id, CompanyDocument.file_url, CompanyDocument.doc_type, CompanyDocument.created_at))
        docs = [
            {
                "id": str(r.id),
                "file_url": r.file_url,
                "doc_type": r.doc_type.value if r.doc_type else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in docs_result
        ]

        metadata = {
            "generated_at": _utc_now().isoformat(),
            "job_id": str(job.id),
            "schedule_id": str(schedule_id) if schedule_id else None,
            "upload_dir": str(uploads_dir),
            "documents": docs,
        }

        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("metadata.json", json.dumps(metadata, ensure_ascii=False, indent=2))

            if uploads_dir.exists():
                for path in uploads_dir.rglob("*"):
                    if path.is_dir():
                        continue
                    if path == archive_path:
                        continue
                    try:
                        zf.write(path, arcname=str(path.relative_to(uploads_dir)))
                    except Exception:
                        continue

        job.status = BackupJobStatus.SUCCESS
        job.archive_path = str(archive_path)
        job.archive_size_bytes = archive_path.stat().st_size if archive_path.exists() else 0
        job.finished_at = _utc_now()
    except Exception as exc:
        job.status = BackupJobStatus.FAILED
        job.error_message = str(exc)
        job.finished_at = _utc_now()

    await db.flush()
    return job


async def apply_retention(db: AsyncSession, schedule: BackupSchedule | None = None) -> None:
    if schedule is None:
        return

    result = await db.execute(
        select(BackupJob)
        .where(BackupJob.schedule_id == schedule.id, BackupJob.status == BackupJobStatus.SUCCESS)
        .order_by(BackupJob.created_at.desc())
    )
    jobs = result.scalars().all()

    keep_count = _safe_int(schedule.retention_count, 1, 120)
    keep_days = _safe_int(schedule.retention_days, 1, 3650)
    threshold = _utc_now() - timedelta(days=keep_days)

    for idx, job in enumerate(jobs):
        should_remove = idx >= keep_count or (job.created_at and job.created_at < threshold)
        if not should_remove:
            continue
        if job.archive_path and os.path.exists(job.archive_path):
            try:
                os.remove(job.archive_path)
            except Exception:
                pass
        await db.delete(job)


async def run_due_backup_schedules(db: AsyncSession) -> int:
    now = _utc_now()
    result = await db.execute(select(BackupSchedule).where(BackupSchedule.enabled == True))
    schedules = result.scalars().all()

    ran = 0
    for schedule in schedules:
        due = schedule.next_run_at is None or schedule.next_run_at <= now
        if not due:
            continue

        await create_backup_archive(db, schedule_id=schedule.id, created_by=schedule.created_by)
        schedule.last_run_at = now
        schedule.next_run_at = next_run_at_for_schedule(schedule, now)
        await apply_retention(db, schedule)
        ran += 1

    if ran:
        await db.commit()
    return ran
