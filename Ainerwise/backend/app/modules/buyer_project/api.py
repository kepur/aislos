"""Buyer Project API — AI Project Forge routes."""
import uuid

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, DB
from app.modules.buyer_project.schemas import (
    LineItemRead,
    LineItemUpdate,
    ProjectCreate,
    ProjectMessageCreate,
    ProjectMessageRead,
    ProjectMetricsUpdate,
    ProjectReportRowPatch,
    ProjectRead,
    ProjectUpdate,
)
from app.modules.buyer_project.service import (
    BuyerProjectError,
    add_message,
    create_project,
    get_project,
    list_line_items,
    list_messages,
    list_projects,
    get_metrics,
    update_metrics,
    estimate_prices,
    get_report,
    recalculate_report,
    report_detail,
    list_report_versions,
    freeze_report,
    update_report_row,
    update_line_item,
    update_project,
)
from app.services.audit import append_audit_event

router = APIRouter(prefix="/buyer/projects", tags=["buyer-projects"])


@router.get("")
async def list_my_projects(db: DB, user: CurrentUser):
    items = await list_projects(db, user.id)
    return {
        "items": [ProjectRead.model_validate(p).model_dump() for p in items],
        "total": len(items),
    }


@router.post("", response_model=ProjectRead, status_code=201)
async def create_my_project(data: ProjectCreate, db: DB, user: CurrentUser):
    project = await create_project(db, buyer_id=user.id, **data.model_dump())
    await db.commit()
    await db.refresh(project)
    return ProjectRead.model_validate(project)


@router.get("/{project_id}", response_model=ProjectRead)
async def get_my_project(project_id: uuid.UUID, db: DB, user: CurrentUser):
    try:
        project = await get_project(db, project_id, user.id)
        return ProjectRead.model_validate(project)
    except BuyerProjectError:
        raise HTTPException(status_code=404, detail="Project not found") from None


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_my_project(
    project_id: uuid.UUID, data: ProjectUpdate, db: DB, user: CurrentUser
):
    try:
        project = await update_project(
            db, project_id, user.id, **data.model_dump(exclude_unset=True)
        )
        await db.commit()
        await db.refresh(project)
        return ProjectRead.model_validate(project)
    except BuyerProjectError:
        raise HTTPException(status_code=404, detail="Project not found") from None


@router.get("/{project_id}/line-items")
async def get_project_line_items(project_id: uuid.UUID, db: DB, user: CurrentUser):
    try:
        await get_project(db, project_id, user.id)
    except BuyerProjectError:
        raise HTTPException(status_code=404, detail="Project not found") from None
    items = await list_line_items(db, project_id)
    return {
        "items": [LineItemRead.model_validate(i).model_dump() for i in items],
        "total": len(items),
    }


@router.patch("/{project_id}/line-items/{item_id}", response_model=LineItemRead)
async def update_project_line_item(
    project_id: uuid.UUID,
    item_id: uuid.UUID,
    data: LineItemUpdate,
    db: DB,
    user: CurrentUser,
):
    try:
        await get_project(db, project_id, user.id)
        item = await update_line_item(
            db, item_id, project_id, **data.model_dump(exclude_unset=True)
        )
        await db.commit()
        await db.refresh(item)
        return LineItemRead.model_validate(item)
    except BuyerProjectError as exc:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from None


@router.get("/{project_id}/messages")
async def get_project_messages(project_id: uuid.UUID, db: DB, user: CurrentUser):
    try:
        await get_project(db, project_id, user.id)
    except BuyerProjectError:
        raise HTTPException(status_code=404, detail="Project not found") from None
    msgs = await list_messages(db, project_id)
    return {
        "items": [ProjectMessageRead.model_validate(m).model_dump() for m in msgs],
        "total": len(msgs),
    }


@router.post("/{project_id}/messages", response_model=ProjectMessageRead, status_code=201)
async def send_project_message(
    project_id: uuid.UUID, data: ProjectMessageCreate, db: DB, user: CurrentUser
):
    try:
        await get_project(db, project_id, user.id)
    except BuyerProjectError:
        raise HTTPException(status_code=404, detail="Project not found") from None
    msg = await add_message(
        db,
        project_id=project_id,
        role="USER",
        content=data.content,
        workflow_node=data.workflow_node,
    )
    await db.commit()
    await db.refresh(msg)
    return ProjectMessageRead.model_validate(msg)


@router.get("/{project_id}/metrics")
async def get_project_metrics(project_id: uuid.UUID, db: DB, user: CurrentUser):
    try:
        project = await get_project(db, project_id, user.id)
    except BuyerProjectError:
        raise HTTPException(status_code=404, detail="Project not found") from None
    return await get_metrics(db, project)


@router.patch("/{project_id}/metrics")
async def patch_project_metrics(
    project_id: uuid.UUID, data: ProjectMetricsUpdate, db: DB, user: CurrentUser
):
    try:
        project = await get_project(db, project_id, user.id)
        result = await update_metrics(
            db, project, [metric.model_dump() for metric in data.metrics]
        )
        await db.commit()
        return result
    except BuyerProjectError:
        await db.rollback()
        raise HTTPException(status_code=404, detail="Project not found") from None


@router.post("/{project_id}/price-estimate")
async def create_project_price_estimate(project_id: uuid.UUID, db: DB, user: CurrentUser):
    try:
        project = await get_project(db, project_id, user.id)
        snapshots = await estimate_prices(db, project)
        await db.commit()
        return {
            "project_id": project.id,
            "items": [
                {column.name: getattr(row, column.name) for column in row.__table__.columns}
                for row in snapshots
            ],
        }
    except BuyerProjectError:
        await db.rollback()
        raise HTTPException(status_code=404, detail="Project not found") from None


@router.get("/{project_id}/report")
async def get_project_report(project_id: uuid.UUID, db: DB, user: CurrentUser):
    try:
        project = await get_project(db, project_id, user.id)
        result = await get_report(db, project, actor_id=user.id)
        await db.commit()
        return result
    except BuyerProjectError as exc:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from None


@router.get("/{project_id}/report/versions")
async def get_project_report_versions(project_id: uuid.UUID, db: DB, user: CurrentUser):
    try:
        project = await get_project(db, project_id, user.id)
        report = await get_report(db, project, actor_id=user.id)
        await db.commit()
        return {
            "items": await list_report_versions(db, report["id"]),
        }
    except BuyerProjectError as exc:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from None


@router.post("/{project_id}/report/recalculate")
async def recalculate_project_report(project_id: uuid.UUID, db: DB, user: CurrentUser):
    try:
        project = await get_project(db, project_id, user.id)
        report = await recalculate_report(db, project, actor_id=user.id)
        await append_audit_event(
            db,
            actor_type="user",
            actor_user_id=user.id,
            portal_key="ainerwise",
            action="buyer_project.report_recalculated",
            entity_type="buyer_project",
            entity_id=project.id,
            after={"report_id": str(report.id), "version_id": str(report.current_version_id)},
        )
        result = await report_detail(db, report)
        await db.commit()
        return result
    except BuyerProjectError as exc:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from None


@router.post("/{project_id}/report/freeze")
async def freeze_project_report(project_id: uuid.UUID, db: DB, user: CurrentUser):
    try:
        project = await get_project(db, project_id, user.id)
        report = await freeze_report(db, project, actor_id=user.id)
        await append_audit_event(
            db,
            actor_type="user",
            actor_user_id=user.id,
            portal_key="ainerwise",
            action="buyer_project.report_frozen",
            entity_type="buyer_project",
            entity_id=project.id,
            after={"report_id": str(report.id), "frozen_version_id": str(report.frozen_version_id)},
        )
        result = await report_detail(db, report)
        await db.commit()
        return result
    except BuyerProjectError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.patch("/{project_id}/report/rows/{row_id}")
async def patch_project_report_row(
    project_id: uuid.UUID,
    row_id: uuid.UUID,
    data: ProjectReportRowPatch,
    db: DB,
    user: CurrentUser,
):
    try:
        project = await get_project(db, project_id, user.id)
        report = await update_report_row(
            db,
            project,
            row_id,
            actor_id=user.id,
            fields=data.model_dump(exclude_unset=True),
        )
        result = await report_detail(db, report)
        await db.commit()
        return result
    except BuyerProjectError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from None
