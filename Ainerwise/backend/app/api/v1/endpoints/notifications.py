"""Admin notifications + report-job endpoints (FI.8.4, FI.8.5)."""
import uuid

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import AdminUser, DB
from app.crud.base import CRUDBase
from app.models.notification import ReportJob
from app.schemas.notification import ReportJobRead, ReportJobReview
from app.services import lifecycle_automation

router = APIRouter(tags=["notifications"])

crud_report_job = CRUDBase[ReportJob](ReportJob)


@router.post("/admin/lifecycle-scan")
async def run_lifecycle_scan(db: DB, admin: AdminUser, within_days: int = Query(90, ge=1, le=365)):
    """FI.8.4 — manually trigger the due-date scan (also runs daily via Celery beat)."""
    emitted = await lifecycle_automation.scan_and_notify(db, within_days=within_days)
    return {"emitted": emitted}


@router.post("/admin/report-jobs/generate")
async def run_report_generation(db: DB, admin: AdminUser, period_label: str | None = None):
    """FI.8.5 — manually create this period's monthly compliance report jobs."""
    created = await lifecycle_automation.generate_report_jobs(db, period_label=period_label)
    return {"created": created}


@router.get("/report-jobs")
async def list_report_jobs(
    db: DB,
    admin: AdminUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    review_status: str | None = None,
):
    filters = []
    if review_status:
        filters.append(ReportJob.review_status == review_status)
    items, total = await crud_report_job.get_multi(db, skip=skip, limit=limit, filters=filters or None)
    return {"items": [ReportJobRead.model_validate(i) for i in items], "total": total}


@router.post("/report-jobs/{id}/review", response_model=ReportJobRead)
async def review_report_job(id: uuid.UUID, data: ReportJobReview, db: DB, admin: AdminUser):
    """FI.8.5 — approve/reject a report before customer delivery."""
    job = await crud_report_job.get(db, id)
    if not job:
        raise HTTPException(status_code=404, detail="Report job not found")
    status = "approved" if data.review_status == "approved" else "pending"
    updates = {"review_status": data.review_status, "status": status}
    if data.notes:
        updates["notes"] = data.notes
    return await crud_report_job.update(db, db_obj=job, obj_in=updates)
