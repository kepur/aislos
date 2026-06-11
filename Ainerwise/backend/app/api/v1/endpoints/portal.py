"""Buyer portal lifecycle workspace endpoints (FI.5.1 - FI.5.6).

Project-scoped, buyer-authenticated read access to the lifecycle data layer:
AMC contracts, warranties, monitoring points, reports/certificates, and tickets.
Every endpoint verifies the project belongs to the current user's company.
"""
import uuid
from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.api.deps import CurrentUser, DB
from app.models.file import FileAsset
from app.models.lifecycle import (
    AMCContract,
    CalibrationRecord,
    CustomerWarranty,
    MaintenanceSchedule,
    MonitoringPoint,
)
from app.models.notification import NotificationPreference
from app.models.project import Project
from app.models.ticket import Ticket
from app.schemas import lifecycle as ls
from app.schemas.notification import NotificationPreferenceRead, NotificationPreferenceUpdate
from app.schemas.ticket import TicketRead

router = APIRouter(prefix="/portal", tags=["portal-lifecycle"])


@router.get("/notification-preferences", response_model=NotificationPreferenceRead)
async def get_notification_preferences(db: DB, user: CurrentUser):
    """FI.8.3 — the current user's notification preferences (created on first read)."""
    result = await db.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == user.id)
    )
    pref = result.scalar_one_or_none()
    if pref is None:
        pref = NotificationPreference(user_id=user.id, company_id=user.company_id, email=user.email)
        db.add(pref)
        await db.commit()
        await db.refresh(pref)
    return pref


@router.put("/notification-preferences", response_model=NotificationPreferenceRead)
async def update_notification_preferences(data: NotificationPreferenceUpdate, db: DB, user: CurrentUser):
    result = await db.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == user.id)
    )
    pref = result.scalar_one_or_none()
    if pref is None:
        pref = NotificationPreference(user_id=user.id, company_id=user.company_id)
        db.add(pref)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(pref, field, value)
    await db.commit()
    await db.refresh(pref)
    return pref


async def _owned_project(db, project_id: uuid.UUID, user) -> Project:
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not user.company_id or project.buyer_company_id != user.company_id:
        raise HTTPException(status_code=403, detail="Not your project")
    return project


@router.get("/projects/{project_id}/amc-contracts")
async def project_amc(project_id: uuid.UUID, db: DB, user: CurrentUser):
    """FI.5.2 — AMC plans for a project (current plan, fee, scope, exclusions)."""
    project = await _owned_project(db, project_id, user)
    result = await db.execute(
        select(AMCContract).where(
            (AMCContract.project_id == project_id)
            | (AMCContract.customer_id == project.buyer_company_id)
        ).order_by(AMCContract.created_at.desc())
    )
    items = list(result.scalars().all())
    return {"items": [ls.AMCContractRead.model_validate(i) for i in items], "total": len(items)}


@router.get("/projects/{project_id}/warranties")
async def project_warranties(project_id: uuid.UUID, db: DB, user: CurrentUser):
    """FI.5.3 — Customer warranty coverage for a project."""
    project = await _owned_project(db, project_id, user)
    result = await db.execute(
        select(CustomerWarranty).where(
            (CustomerWarranty.project_id == project_id)
            | (CustomerWarranty.customer_id == project.buyer_company_id)
        ).order_by(CustomerWarranty.created_at.desc())
    )
    items = list(result.scalars().all())
    return {"items": [ls.CustomerWarrantyRead.model_validate(i) for i in items], "total": len(items)}


@router.get("/projects/{project_id}/monitoring-points")
async def project_monitoring_points(project_id: uuid.UUID, db: DB, user: CurrentUser):
    """FI.5.5 — Monitoring-points summary: site grouping, alert/maintenance/calibration state."""
    await _owned_project(db, project_id, user)
    result = await db.execute(
        select(MonitoringPoint).where(MonitoringPoint.project_id == project_id)
        .order_by(MonitoringPoint.site, MonitoringPoint.device_name)
    )
    points = list(result.scalars().all())

    soon = date.today() + timedelta(days=60)
    sites: dict[str, dict] = {}
    active = alerts = calibration_due = 0
    for p in points:
        bucket = sites.setdefault(p.site or "Unassigned", {"site": p.site or "Unassigned", "total": 0, "active": 0, "alerts": 0, "calibration_due": 0})
        bucket["total"] += 1
        if p.status == "active":
            bucket["active"] += 1
            active += 1
        if p.status == "fault":
            bucket["alerts"] += 1
            alerts += 1
        if p.next_calibration_at and p.next_calibration_at <= soon:
            bucket["calibration_due"] += 1
            calibration_due += 1

    return {
        "summary": {
            "total": len(points),
            "active": active,
            "alerts": alerts,
            "calibration_due": calibration_due,
            "sites": list(sites.values()),
        },
        "items": [ls.MonitoringPointRead.model_validate(p) for p in points],
    }


@router.get("/projects/{project_id}/reports")
async def project_reports(project_id: uuid.UUID, db: DB, user: CurrentUser):
    """FI.5.6 — Report library: compliance reports, calibration / maintenance certificates, files."""
    project = await _owned_project(db, project_id, user)

    cal_result = await db.execute(
        select(CalibrationRecord).where(CalibrationRecord.project_id == project_id)
        .order_by(CalibrationRecord.calibration_date.desc())
    )
    calibration_certificates = [ls.CalibrationRecordRead.model_validate(c) for c in cal_result.scalars().all()]

    maint_result = await db.execute(
        select(MaintenanceSchedule).where(
            MaintenanceSchedule.project_id == project_id,
            MaintenanceSchedule.status == "done",
        ).order_by(MaintenanceSchedule.due_date.desc())
    )
    maintenance_certificates = [ls.MaintenanceScheduleRead.model_validate(m) for m in maint_result.scalars().all()]

    file_result = await db.execute(
        select(FileAsset).where(
            FileAsset.entity_type == "project", FileAsset.entity_id == project_id
        ).order_by(FileAsset.created_at.desc())
    )
    files = [
        {
            "id": str(f.id),
            "original_name": f.original_name,
            "file_type": f.file_type,
            "mime_type": f.mime_type,
            "size_bytes": f.size_bytes,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in file_result.scalars().all()
    ]

    # Sample monthly report (from the project plan, tagged sample) until
    # customer-specific report generation is implemented.
    plan = project.project_plan_json or {}
    sample_report = plan.get("report_preview") if isinstance(plan, dict) else None

    return {
        "calibration_certificates": calibration_certificates,
        "maintenance_certificates": maintenance_certificates,
        "files": files,
        "sample_report": sample_report,
    }


@router.get("/projects/{project_id}/tickets")
async def project_tickets(project_id: uuid.UUID, db: DB, user: CurrentUser):
    """FI.5.4 support — tickets for a project belonging to the buyer."""
    await _owned_project(db, project_id, user)
    result = await db.execute(
        select(Ticket).where(
            Ticket.project_id == project_id,
            Ticket.buyer_company_id == user.company_id,
        ).order_by(Ticket.created_at.desc())
    )
    items = list(result.scalars().all())
    return {"items": [TicketRead.model_validate(i) for i in items], "total": len(items)}


@router.get("/projects/{project_id}/workspace")
async def project_workspace(project_id: uuid.UUID, db: DB, user: CurrentUser):
    """FI.5.1 — aggregate counts for the workspace navigation badges."""
    await _owned_project(db, project_id, user)

    async def _count(model, *where):
        from sqlalchemy import func
        q = select(func.count()).select_from(model).where(*where)
        return (await db.execute(q)).scalar() or 0

    return {
        "amc": await _count(AMCContract, AMCContract.project_id == project_id),
        "warranties": await _count(CustomerWarranty, CustomerWarranty.project_id == project_id),
        "monitoring_points": await _count(MonitoringPoint, MonitoringPoint.project_id == project_id),
        "calibration_records": await _count(CalibrationRecord, CalibrationRecord.project_id == project_id),
        "tickets": await _count(Ticket, Ticket.project_id == project_id, Ticket.buyer_company_id == user.company_id),
    }
