"""Buyer Project service layer."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.buyer_project.models import (
    BuyerProject,
    ProjectFile,
    ProjectLineItem,
    ProjectMessage,
    ProjectMetricTemplate,
    ProjectMetricValue,
    ProjectPriceSnapshot,
    ProjectReport,
    ProjectReportChangeLog,
    ProjectReportColumn,
    ProjectReportRow,
    ProjectReportVersion,
)


class BuyerProjectError(ValueError):
    pass


async def create_project(
    db: AsyncSession, *, buyer_id: uuid.UUID, **fields
) -> BuyerProject:
    project = BuyerProject(buyer_id=buyer_id, **fields)
    db.add(project)
    await db.flush()
    return project


async def get_project(
    db: AsyncSession, project_id: uuid.UUID, buyer_id: uuid.UUID
) -> BuyerProject:
    project = await db.get(BuyerProject, project_id)
    if project is None or project.buyer_id != buyer_id:
        raise BuyerProjectError("Project not found")
    return project


async def list_projects(
    db: AsyncSession, buyer_id: uuid.UUID, limit: int = 50
) -> list[BuyerProject]:
    return list(
        (
            await db.execute(
                select(BuyerProject)
                .where(BuyerProject.buyer_id == buyer_id)
                .order_by(BuyerProject.created_at.desc())
                .limit(limit)
            )
        ).scalars().all()
    )


async def update_project(
    db: AsyncSession, project_id: uuid.UUID, buyer_id: uuid.UUID, **fields
) -> BuyerProject:
    project = await get_project(db, project_id, buyer_id)
    for k, v in fields.items():
        if v is not None:
            setattr(project, k, v)
    await db.flush()
    return project


async def list_line_items(
    db: AsyncSession, project_id: uuid.UUID
) -> list[ProjectLineItem]:
    return list(
        (
            await db.execute(
                select(ProjectLineItem)
                .where(ProjectLineItem.project_id == project_id)
                .order_by(ProjectLineItem.created_at.asc())
            )
        ).scalars().all()
    )


async def update_line_item(
    db: AsyncSession,
    item_id: uuid.UUID,
    project_id: uuid.UUID,
    **fields,
) -> ProjectLineItem:
    item = await db.get(ProjectLineItem, item_id)
    if item is None or item.project_id != project_id:
        raise BuyerProjectError("Line item not found")
    for k, v in fields.items():
        if v is not None:
            setattr(item, k, v)
    await db.flush()
    return item


async def add_message(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    role: str = "USER",
    content: str,
    workflow_node: str | None = None,
) -> ProjectMessage:
    msg = ProjectMessage(
        project_id=project_id,
        role=role,
        content=content,
        workflow_node=workflow_node,
    )
    db.add(msg)
    await db.flush()
    return msg


async def list_messages(
    db: AsyncSession, project_id: uuid.UUID
) -> list[ProjectMessage]:
    return list(
        (
            await db.execute(
                select(ProjectMessage)
                .where(ProjectMessage.project_id == project_id)
                .order_by(ProjectMessage.created_at.asc())
            )
        ).scalars().all()
    )


def _model_dict(row) -> dict:
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


async def get_metrics(db: AsyncSession, project: BuyerProject) -> dict:
    templates = list(
        (
            await db.execute(
                select(ProjectMetricTemplate)
                .where(
                    ProjectMetricTemplate.active.is_(True),
                    ProjectMetricTemplate.project_type.in_([project.project_type, "GENERAL"]),
                )
                .order_by(ProjectMetricTemplate.sort_order, ProjectMetricTemplate.key)
            )
        ).scalars()
    )
    values = list(
        (
            await db.execute(
                select(ProjectMetricValue)
                .where(ProjectMetricValue.project_id == project.id)
                .order_by(ProjectMetricValue.key)
            )
        ).scalars()
    )
    value_keys = {row.key for row in values if row.value_json is not None}
    return {
        "project_id": project.id,
        "project_type": project.project_type,
        "templates": [_model_dict(row) for row in templates],
        "values": [_model_dict(row) for row in values],
        "missing_required": [
            {"key": row.key, "label": row.label, "prompt": row.prompt}
            for row in templates
            if row.required and row.key not in value_keys
        ],
    }


async def update_metrics(
    db: AsyncSession, project: BuyerProject, metrics: list[dict]
) -> dict:
    for payload in metrics:
        key = str(payload["key"]).strip().lower()
        row = (
            await db.execute(
                select(ProjectMetricValue).where(
                    ProjectMetricValue.project_id == project.id,
                    ProjectMetricValue.key == key,
                )
            )
        ).scalar_one_or_none()
        if row is None:
            template = (
                await db.execute(
                    select(ProjectMetricTemplate).where(
                        ProjectMetricTemplate.project_type.in_([project.project_type, "GENERAL"]),
                        ProjectMetricTemplate.key == key,
                    )
                )
            ).scalars().first()
            row = ProjectMetricValue(
                project_id=project.id,
                template_id=template.id if template else None,
                key=key,
            )
            db.add(row)
        row.label = payload.get("label") or row.label
        value = payload.get("value")
        row.value_json = value if isinstance(value, dict) else {"value": value}
        row.source = str(payload.get("source") or "USER").upper()
        row.confidence = payload.get("confidence")
    await db.flush()
    return await get_metrics(db, project)


def _price_tiers(item: ProjectLineItem) -> dict:
    if item.price_tiers_json:
        return item.price_tiers_json
    unit = float(item.estimated_unit_price or 0)
    qty = float(item.qty or 1)
    return {
        "BUDGET": {"unit_price": round(unit * 0.8, 2), "total_price": round(unit * qty * 0.8, 2)},
        "MID_RANGE": {"unit_price": round(unit, 2), "total_price": round(unit * qty, 2)},
        "PREMIUM": {"unit_price": round(unit * 1.3, 2), "total_price": round(unit * qty * 1.3, 2)},
    }


async def estimate_prices(db: AsyncSession, project: BuyerProject) -> list[ProjectPriceSnapshot]:
    items = await list_line_items(db, project.id)
    snapshots: list[ProjectPriceSnapshot] = []
    for item in items:
        tiers = _price_tiers(item)
        item.price_tiers_json = tiers
        values = [
            float(data.get("unit_price") or 0)
            for data in tiers.values()
            if isinstance(data, dict) and data.get("unit_price") is not None
        ]
        snapshot = ProjectPriceSnapshot(
            project_id=project.id,
            line_item_id=item.id,
            currency=item.currency,
            sample_count=len(values),
            min_unit_price=min(values) if values else None,
            avg_unit_price=(sum(values) / len(values)) if values else None,
            median_unit_price=sorted(values)[len(values) // 2] if values else None,
            p20_unit_price=min(values) if values else None,
            p80_unit_price=max(values) if values else None,
            price_tiers_json=tiers,
            samples_json=[{"source": "CORE_ESTIMATE", "unit_price": value} for value in values],
            source_summary="Core estimate from current project line item",
        )
        db.add(snapshot)
        snapshots.append(snapshot)
    await db.flush()
    return snapshots


async def _next_report_version(db: AsyncSession, report_id: uuid.UUID) -> int:
    versions = list(
        (
            await db.execute(
                select(ProjectReportVersion.version_number).where(
                    ProjectReportVersion.report_id == report_id
                )
            )
        ).scalars()
    )
    return max(versions, default=0) + 1


async def recalculate_report(
    db: AsyncSession,
    project: BuyerProject,
    *,
    actor_id: uuid.UUID,
    source: str = "RECALCULATE",
) -> ProjectReport:
    report = (
        await db.execute(select(ProjectReport).where(ProjectReport.project_id == project.id))
    ).scalar_one_or_none()
    if report is None:
        report = ProjectReport(project_id=project.id)
        db.add(report)
        await db.flush()
    version = ProjectReportVersion(
        report_id=report.id,
        project_id=project.id,
        version_number=await _next_report_version(db, report.id),
        status="ESTIMATED",
        source=source,
        title=f"{project.title} BOQ",
        created_by=actor_id,
    )
    db.add(version)
    await db.flush()
    columns = (
        ("name", "Item", "text", 10, False, True),
        ("qty", "Quantity", "number", 20, True, True),
        ("unit", "Unit", "text", 30, True, True),
        ("selected_tier", "Tier", "text", 40, True, True),
        ("total_price", "Total", "money", 50, False, True),
    )
    db.add_all(
        [
            ProjectReportColumn(
                report_version_id=version.id,
                key=key,
                label=label,
                data_type=data_type,
                sort_order=sort_order,
                editable=editable,
                system=system,
            )
            for key, label, data_type, sort_order, editable, system in columns
        ]
    )
    totals: dict[str, float] = {}
    for index, item in enumerate(await list_line_items(db, project.id)):
        tiers = _price_tiers(item)
        selected_tier = item.quality_tier or "MID_RANGE"
        selected = tiers.get(selected_tier) or tiers.get("MID_RANGE") or {}
        total = float(selected.get("total_price") or item.estimated_total_price or 0)
        totals[item.currency] = totals.get(item.currency, 0) + total
        db.add(
            ProjectReportRow(
                report_version_id=version.id,
                project_id=project.id,
                line_item_id=item.id,
                category_id=item.category_id,
                name=item.name,
                description=item.description,
                specs_json=item.specs_json,
                qty=item.qty,
                unit=item.unit,
                currency=item.currency,
                quality_tier=item.quality_tier,
                selected_tier=selected_tier,
                include_in_total=item.include_in_estimate,
                selected_for_purchase=item.status != "REMOVED",
                price_tiers_json=tiers,
                match_status="MATCHED" if item.procurement_request_id else "UNMATCHED",
                price_source="CORE_ESTIMATE",
                sort_order=index,
            )
        )
    version.totals_json = totals
    version.summary_json = {"line_item_count": len(await list_line_items(db, project.id))}
    report.current_version_id = version.id
    db.add(
        ProjectReportChangeLog(
            project_id=project.id,
            report_id=report.id,
            version_id=version.id,
            actor_id=actor_id,
            change_type="RECALCULATE_TOTAL",
            status="APPLIED",
            after_json={"version_number": version.version_number, "totals": totals},
        )
    )
    await db.flush()
    return report


async def get_report(
    db: AsyncSession, project: BuyerProject, *, actor_id: uuid.UUID
) -> dict:
    report = (
        await db.execute(select(ProjectReport).where(ProjectReport.project_id == project.id))
    ).scalar_one_or_none()
    if report is None:
        report = await recalculate_report(db, project, actor_id=actor_id, source="INITIAL")
    return await report_detail(db, report)


async def report_detail(db: AsyncSession, report: ProjectReport) -> dict:
    await db.refresh(report)
    version = await db.get(ProjectReportVersion, report.current_version_id) if report.current_version_id else None
    columns = list(
        (
            await db.execute(
                select(ProjectReportColumn)
                .where(ProjectReportColumn.report_version_id == report.current_version_id)
                .order_by(ProjectReportColumn.sort_order)
            )
        ).scalars()
    ) if report.current_version_id else []
    rows = list(
        (
            await db.execute(
                select(ProjectReportRow)
                .where(ProjectReportRow.report_version_id == report.current_version_id)
                .order_by(ProjectReportRow.sort_order)
            )
        ).scalars()
    ) if report.current_version_id else []
    return {
        **_model_dict(report),
        "current_version": _model_dict(version) if version else None,
        "columns": [_model_dict(row) for row in columns],
        "rows": [_model_dict(row) for row in rows],
    }


async def list_report_versions(db: AsyncSession, report_id: uuid.UUID) -> list[dict]:
    rows = list(
        (
            await db.execute(
                select(ProjectReportVersion)
                .where(ProjectReportVersion.report_id == report_id)
                .order_by(ProjectReportVersion.version_number.desc())
            )
        ).scalars()
    )
    return [_model_dict(row) for row in rows]


async def freeze_report(
    db: AsyncSession, project: BuyerProject, *, actor_id: uuid.UUID
) -> ProjectReport:
    report = (
        await db.execute(select(ProjectReport).where(ProjectReport.project_id == project.id))
    ).scalar_one_or_none()
    if report is None or report.current_version_id is None:
        report = await recalculate_report(db, project, actor_id=actor_id, source="FREEZE_PREP")
    version = await db.get(ProjectReportVersion, report.current_version_id)
    if version is None:
        raise BuyerProjectError("Report version not found")
    version.status = "FROZEN"
    report.frozen_version_id = version.id
    db.add(
        ProjectReportChangeLog(
            project_id=project.id,
            report_id=report.id,
            version_id=version.id,
            actor_id=actor_id,
            change_type="FREEZE_REPORT",
            status="APPLIED",
            after_json={"status": "FROZEN"},
        )
    )
    await db.flush()
    return report


async def update_report_row(
    db: AsyncSession,
    project: BuyerProject,
    row_id: uuid.UUID,
    *,
    actor_id: uuid.UUID,
    fields: dict,
) -> ProjectReport:
    report = (
        await db.execute(select(ProjectReport).where(ProjectReport.project_id == project.id))
    ).scalar_one_or_none()
    if report is None or report.current_version_id is None:
        raise BuyerProjectError("Report not found")
    version = await db.get(ProjectReportVersion, report.current_version_id)
    if version is None or version.status in {"FROZEN", "PUBLISHED"}:
        raise BuyerProjectError("Frozen report cannot be edited")
    row = await db.get(ProjectReportRow, row_id)
    if row is None or row.project_id != project.id or row.report_version_id != version.id:
        raise BuyerProjectError("Report row not found")
    before = {key: getattr(row, key) for key in fields}
    for key, value in fields.items():
        if value is not None:
            setattr(row, key, value)
    db.add(
        ProjectReportChangeLog(
            project_id=project.id,
            report_id=report.id,
            version_id=version.id,
            actor_id=actor_id,
            change_type="EDIT_ROW",
            status="APPLIED",
            before_json=before,
            after_json={key: getattr(row, key) for key in fields},
        )
    )
    await db.flush()
    return report
