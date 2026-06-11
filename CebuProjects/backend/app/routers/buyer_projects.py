"""Buyer Projects API router for AI Project Forge.

All endpoints are buyer-only, scoped to the current user's projects.
PC, H5, and Admin all use these same endpoints.
"""
import os
import uuid
from datetime import datetime, timedelta, timezone
from statistics import mean, median

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.buyer_project import (
    AIRunStatus,
    BuyerProject,
    LineItemSource,
    LineItemStatus,
    MetricValueSource,
    ProjectAIRun,
    ProjectFile,
    ProjectLineItem,
    ProjectMessage,
    ProjectMessageRole,
    ProjectMetricTemplate,
    ProjectMetricValue,
    ProjectPriceSnapshot,
    ProjectReport,
    ProjectReportChangeLog,
    ProjectReportColumn,
    ProjectReportPatchStatus,
    ProjectReportRow,
    ProjectReportVersion,
    ProjectReportVersionStatus,
    ProjectStatus,
    ProjectType,
    ProjectWorkflowNode,
)
from app.models.catalog import CatalogItem, CatalogItemStatus
from app.models.category import Category
from app.models.intent import Intent, IntentStatus
from app.models.offer import Offer
from app.models.user import User, UserRole
from app.schemas.buyer_project import (
    AIRunResponse,
    LineItemResponse,
    LineItemUpdate,
    ProjectCreate,
    ProjectDetailResponse,
    ProjectFileResponse,
    ProjectMessageCreate,
    ProjectMessageResponse,
    ProjectMetricsResponse,
    ProjectMetricsUpdate,
    ProjectMetricTemplateCreate,
    ProjectMetricTemplateResponse,
    ProjectMetricTemplateUpdate,
    ProjectReportCellsUpdate,
    ProjectReportChangeLogResponse,
    ProjectReportChatRequest,
    ProjectReportColumnCreate,
    ProjectReportResponse,
    ProjectReportRowCreate,
    ProjectReportVersionResponse,
    ProjectResponse,
    ProjectUpdate,
    PublishResult,
)
from app.services.audit_service import create_audit_log
from app.services.ai_service import _call_ai
from app.services.matching_service import find_matching_suppliers
from app.services.notification_service import notify_user
from app.services.project_ai_service import get_project_ai_config, run_project_analysis


router = APIRouter(prefix="/buyer/projects", tags=["Buyer Projects"])


async def _expire_stale_ai_runs(db: AsyncSession, project_id: uuid.UUID, minutes: int = 30) -> None:
    """Mark abandoned pending/running AI runs as failed so users can retry."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    result = await db.execute(
        select(ProjectAIRun).where(
            ProjectAIRun.project_id == project_id,
            ProjectAIRun.status.in_([AIRunStatus.PENDING, AIRunStatus.RUNNING]),
        )
    )
    for run in result.scalars().all():
        marker = run.started_at or run.created_at
        if marker and marker < cutoff:
            run.status = AIRunStatus.FAILED
            run.error_message = "Previous AI analysis was interrupted or timed out. Please start a new analysis."
            run.finished_at = datetime.now(timezone.utc)

# Allowed file types for project uploads
PROJECT_ALLOWED_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
PROJECT_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

DEFAULT_METRIC_TEMPLATES = {
    ProjectType.GENERAL: [
        ("use_case", "Use case", "text", True, "What are you trying to build or buy?"),
        ("location", "Location", "text", True, "Where will this project be delivered or installed?"),
        ("budget", "Budget", "number", False, "What budget range should the system optimize for?"),
        ("deadline", "Deadline", "date", False, "When do you need sourcing or delivery completed?"),
    ],
    ProjectType.CONSTRUCTION: [
        ("area", "Floor area", "number", True, "How many square meters is the project?"),
        ("floors", "Number of floors", "number", True, "How many floors or levels are planned?"),
        ("structure_type", "Structure type", "text", False, "Is it concrete, steel, mixed, or unknown?"),
        ("finish_level", "Finish level", "select", False, "Budget, mid-range, or premium finish?"),
    ],
    ProjectType.SOLAR: [
        ("roof_area", "Roof area", "number", True, "What roof or ground area is available?"),
        ("target_power_kw", "Target power", "number", True, "What kW capacity are you targeting?"),
        ("battery_required", "Battery required", "boolean", False, "Do you need battery storage?"),
        ("grid_type", "Grid type", "select", False, "On-grid, off-grid, or hybrid?"),
    ],
    ProjectType.TECH_BUILD: [
        ("prototype_goal", "Prototype goal", "text", True, "What should the device or build do?"),
        ("quantity", "Build quantity", "number", True, "How many units do you need?"),
        ("power_source", "Power source", "text", False, "Battery, wall power, solar, USB, or other?"),
        ("connectivity", "Connectivity", "text", False, "Wi-Fi, Bluetooth, LTE, LoRa, wired, or none?"),
    ],
    ProjectType.RENOVATION: [
        ("area", "Renovation area", "number", True, "How large is the renovation area?"),
        ("rooms", "Rooms or zones", "text", True, "Which rooms or zones are included?"),
        ("scope", "Scope", "text", True, "Painting, plumbing, electrical, flooring, fixtures, or other?"),
        ("finish_level", "Finish level", "select", False, "Budget, mid-range, or premium finish?"),
    ],
}

REPORT_BASE_COLUMNS = [
    ("category", "Category", "text", False, True),
    ("name", "Item", "text", True, True),
    ("specs", "Specs", "json", True, True),
    ("qty", "Qty", "number", True, True),
    ("unit", "Unit", "text", True, True),
    ("budget_price", "Budget Price", "money", True, True),
    ("mid_price", "Mid Price", "money", True, True),
    ("premium_price", "Premium Price", "money", True, True),
    ("selected_tier", "Selected Tier", "select", True, True),
    ("include_in_total", "Include Total", "boolean", True, True),
    ("selected_for_purchase", "Purchase", "boolean", True, True),
    ("match_status", "Match", "text", False, True),
    ("notes", "Notes", "text", True, True),
]

REPORT_ROW_FIELDS = {
    "name", "description", "specs_jsonb", "qty", "unit", "currency", "selected_tier",
    "include_in_total", "selected_for_purchase", "price_tiers_jsonb", "custom_values_jsonb",
    "notes", "match_status", "price_source",
}


# ─── Helper ────────────────────────────────────────────────────

async def _get_buyer_project(db: AsyncSession, project_id: str, user_id: uuid.UUID) -> BuyerProject:
    """Get a project owned by the current buyer or raise 404."""
    result = await db.execute(
        select(BuyerProject).where(BuyerProject.id == project_id, BuyerProject.buyer_id == user_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


async def _build_detail_response(db: AsyncSession, project: BuyerProject) -> dict:
    """Build full project detail with files, line items, and latest AI run."""
    files_result = await db.execute(
        select(ProjectFile).where(ProjectFile.project_id == project.id).order_by(ProjectFile.created_at)
    )
    files = files_result.scalars().all()

    items_result = await db.execute(
        select(ProjectLineItem).where(ProjectLineItem.project_id == project.id).order_by(ProjectLineItem.created_at)
    )
    items = items_result.scalars().all()

    run_result = await db.execute(
        select(ProjectAIRun)
        .where(ProjectAIRun.project_id == project.id)
        .order_by(ProjectAIRun.created_at.desc())
        .limit(1)
    )
    latest_run = run_result.scalar_one_or_none()

    return {
        **{c.key: getattr(project, c.key) for c in project.__table__.columns},
        "files": files,
        "line_items": items,
        "latest_ai_run": latest_run,
    }


def _project_type_templates(project_type: ProjectType) -> list[tuple[str, str, str, bool, str]]:
    return DEFAULT_METRIC_TEMPLATES.get(project_type) or DEFAULT_METRIC_TEMPLATES[ProjectType.GENERAL]


async def _load_metric_templates(db: AsyncSession, project_type: ProjectType) -> list[ProjectMetricTemplate]:
    result = await db.execute(
        select(ProjectMetricTemplate)
        .where(
            ProjectMetricTemplate.active == True,  # noqa: E712
            ProjectMetricTemplate.project_type.in_([project_type, ProjectType.GENERAL]),
        )
        .order_by(ProjectMetricTemplate.project_type, ProjectMetricTemplate.sort_order)
    )
    rows = result.scalars().all()
    if rows:
        return rows

    defaults = []
    now = datetime.now(timezone.utc)
    for order, (key, label, data_type, required, prompt) in enumerate(_project_type_templates(project_type)):
        defaults.append(ProjectMetricTemplate(
            id=uuid.uuid4(),
            project_type=project_type,
            key=key,
            label=label,
            data_type=data_type,
            required=required,
            sort_order=order,
            prompt=prompt,
            active=True,
            created_at=now,
            updated_at=now,
        ))
    return defaults


async def _upsert_metric_value(
    db: AsyncSession,
    project: BuyerProject,
    key: str,
    label: str | None,
    value,
    source: MetricValueSource,
    confidence: float | None = None,
) -> ProjectMetricValue:
    result = await db.execute(
        select(ProjectMetricValue).where(ProjectMetricValue.project_id == project.id, ProjectMetricValue.key == key)
    )
    metric = result.scalar_one_or_none()
    value_jsonb = value if isinstance(value, dict) else {"value": value}
    if metric:
        metric.label = label or metric.label
        metric.value_jsonb = value_jsonb
        metric.source = source
        metric.confidence = confidence
        metric.updated_at = datetime.now(timezone.utc)
    else:
        metric = ProjectMetricValue(
            project_id=project.id,
            key=key,
            label=label or key.replace("_", " ").title(),
            value_jsonb=value_jsonb,
            source=source,
            confidence=confidence,
        )
        db.add(metric)
    return metric


def _tier_total(row) -> float:
    tiers = row.price_tiers_jsonb or {}
    selected = row.selected_tier or "MID_RANGE"
    tier_data = tiers.get(selected) or tiers.get("MID_RANGE") or {}
    return float(tier_data.get("total_price") or 0)


def _calculate_report_totals(rows: list[ProjectReportRow]) -> dict:
    totals = {
        "BUDGET": 0.0,
        "MID_RANGE": 0.0,
        "PREMIUM": 0.0,
        "selected_total": 0.0,
        "excluded_total": 0.0,
        "unmatched_total": 0.0,
        "included_rows": 0,
        "excluded_rows": 0,
        "unmatched_rows": 0,
    }
    for row in rows:
        tiers = row.price_tiers_jsonb or {}
        selected_total = _tier_total(row)
        if row.include_in_total and row.selected_for_purchase:
            totals["included_rows"] += 1
            totals["selected_total"] += selected_total
            for tier in ("BUDGET", "MID_RANGE", "PREMIUM"):
                totals[tier] += float((tiers.get(tier) or {}).get("total_price") or 0)
            if row.match_status == "UNMATCHED":
                totals["unmatched_rows"] += 1
                totals["unmatched_total"] += selected_total
        else:
            totals["excluded_rows"] += 1
            totals["excluded_total"] += selected_total
    return {k: round(v, 2) if isinstance(v, float) else v for k, v in totals.items()}


def _line_item_to_report_row(project: BuyerProject, item: ProjectLineItem, sort_order: int = 0) -> dict:
    tiers = item.price_tiers_jsonb or {}
    selected_tier = item.quality_tier.value if item.quality_tier else "MID_RANGE"
    return {
        "project_id": project.id,
        "line_item_id": item.id,
        "category_id": item.category_id,
        "name": item.name,
        "description": item.description,
        "specs_jsonb": item.specs_jsonb,
        "qty": item.qty,
        "unit": item.unit,
        "currency": item.currency or project.currency,
        "quality_tier": item.quality_tier or QualityTier.MID_RANGE,
        "selected_tier": selected_tier,
        "include_in_total": getattr(item, "include_in_estimate", True),
        "selected_for_purchase": item.status != LineItemStatus.REMOVED,
        "price_tiers_jsonb": tiers,
        "custom_values_jsonb": {},
        "match_status": "MATCHED" if item.category_id else "UNMATCHED",
        "samples_jsonb": [],
        "price_source": "AI_ESTIMATE",
        "notes": item.sourcing_notes,
        "sort_order": sort_order,
    }


def _row_to_payload(row: ProjectReportRow) -> dict:
    return {
        "project_id": row.project_id,
        "line_item_id": row.line_item_id,
        "category_id": row.category_id,
        "name": row.name,
        "description": row.description,
        "specs_jsonb": row.specs_jsonb,
        "qty": row.qty,
        "unit": row.unit,
        "currency": row.currency,
        "quality_tier": row.quality_tier,
        "selected_tier": row.selected_tier,
        "include_in_total": row.include_in_total,
        "selected_for_purchase": row.selected_for_purchase,
        "price_tiers_jsonb": row.price_tiers_jsonb,
        "custom_values_jsonb": row.custom_values_jsonb or {},
        "match_status": row.match_status,
        "samples_jsonb": row.samples_jsonb,
        "price_source": row.price_source,
        "notes": row.notes,
        "sort_order": row.sort_order,
    }


def _column_to_payload(col: ProjectReportColumn) -> dict:
    return {
        "key": col.key,
        "label": col.label,
        "data_type": col.data_type,
        "sort_order": col.sort_order,
        "editable": col.editable,
        "system": col.system,
    }


async def _next_report_version_number(db: AsyncSession, report_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.coalesce(func.max(ProjectReportVersion.version_number), 0))
        .where(ProjectReportVersion.report_id == report_id)
    )
    return int(result.scalar() or 0) + 1


async def _create_report_version(
    db: AsyncSession,
    project: BuyerProject,
    report: ProjectReport,
    rows_payload: list[dict],
    columns_payload: list[dict] | None,
    *,
    actor_id: uuid.UUID | None,
    source: str,
    status: ProjectReportVersionStatus,
    title: str | None = None,
) -> ProjectReportVersion:
    version = ProjectReportVersion(
        report_id=report.id,
        project_id=project.id,
        version_number=await _next_report_version_number(db, report.id),
        status=status,
        source=source,
        title=title or f"{project.title} report",
        created_by=actor_id,
    )
    db.add(version)
    await db.flush()

    columns = columns_payload or [
        {"key": key, "label": label, "data_type": data_type, "sort_order": idx, "editable": editable, "system": system}
        for idx, (key, label, data_type, editable, system) in enumerate(REPORT_BASE_COLUMNS)
    ]
    for col in columns:
        db.add(ProjectReportColumn(report_version_id=version.id, **col))

    rows: list[ProjectReportRow] = []
    for idx, payload in enumerate(rows_payload):
        payload = {**payload}
        payload.setdefault("sort_order", idx)
        row = ProjectReportRow(report_version_id=version.id, **payload)
        rows.append(row)
        db.add(row)
    await db.flush()
    version.totals_jsonb = _calculate_report_totals(rows)
    report.current_version_id = version.id
    report.updated_at = datetime.now(timezone.utc)
    return version


async def _ensure_project_report(
    db: AsyncSession,
    project: BuyerProject,
    actor_id: uuid.UUID | None = None,
) -> ProjectReport:
    result = await db.execute(
        select(ProjectReport)
        .where(ProjectReport.project_id == project.id)
        .order_by(ProjectReport.updated_at.desc(), ProjectReport.created_at.desc())
    )
    reports = result.scalars().all()
    report = next((item for item in reports if item.current_version_id or item.frozen_version_id), None)
    if not report and reports:
        report = reports[0]
    if not report:
        report = ProjectReport(project_id=project.id)
        db.add(report)
        await db.flush()
    if not report.current_version_id:
        items_result = await db.execute(
            select(ProjectLineItem)
            .where(ProjectLineItem.project_id == project.id, ProjectLineItem.status != LineItemStatus.REMOVED)
            .order_by(ProjectLineItem.created_at)
        )
        rows = [_line_item_to_report_row(project, item, idx) for idx, item in enumerate(items_result.scalars().all())]
        await _create_report_version(
            db, project, report, rows, None,
            actor_id=actor_id, source="LINE_ITEMS", status=ProjectReportVersionStatus.DRAFT,
        )
        await db.commit()
        await db.refresh(report)
    return report


async def _load_report_detail(db: AsyncSession, report: ProjectReport, version_id: uuid.UUID | None = None) -> dict:
    target_version_id = version_id or report.current_version_id
    version = None
    columns = []
    rows = []
    if target_version_id:
        result = await db.execute(select(ProjectReportVersion).where(ProjectReportVersion.id == target_version_id))
        version = result.scalar_one_or_none()
        if version:
            columns = (await db.execute(
                select(ProjectReportColumn)
                .where(ProjectReportColumn.report_version_id == version.id)
                .order_by(ProjectReportColumn.sort_order)
            )).scalars().all()
            rows = (await db.execute(
                select(ProjectReportRow)
                .where(ProjectReportRow.report_version_id == version.id)
                .order_by(ProjectReportRow.sort_order)
            )).scalars().all()
    return {
        **{c.key: getattr(report, c.key) for c in report.__table__.columns},
        "current_version": version,
        "columns": columns,
        "rows": rows,
    }


async def _current_report_parts(db: AsyncSession, project: BuyerProject, actor_id: uuid.UUID | None):
    report = await _ensure_project_report(db, project, actor_id)
    version = (await db.execute(select(ProjectReportVersion).where(ProjectReportVersion.id == report.current_version_id))).scalar_one()
    columns = (await db.execute(
        select(ProjectReportColumn).where(ProjectReportColumn.report_version_id == version.id).order_by(ProjectReportColumn.sort_order)
    )).scalars().all()
    rows = (await db.execute(
        select(ProjectReportRow).where(ProjectReportRow.report_version_id == version.id).order_by(ProjectReportRow.sort_order)
    )).scalars().all()
    return report, version, columns, rows


def _set_report_row_field(payload: dict, field: str, value):
    if field in {"qty"}:
        payload[field] = float(value or 0)
    elif field in {"include_in_total", "selected_for_purchase"}:
        payload[field] = bool(value)
    elif field in {"selected_tier"}:
        payload[field] = str(value or "MID_RANGE").upper()
    elif field in REPORT_ROW_FIELDS:
        payload[field] = value
    else:
        custom = payload.get("custom_values_jsonb") or {}
        custom[field] = value
        payload["custom_values_jsonb"] = custom


def _find_row_for_text(rows: list[ProjectReportRow], text: str) -> ProjectReportRow | None:
    lowered = text.lower()
    for row in rows:
        if row.name and row.name.lower() in lowered:
            return row
    for row in rows:
        for token in row.name.lower().split():
            if len(token) > 2 and token in lowered:
                return row
    return rows[0] if rows else None


def _build_chat_patch(message: str, rows: list[ProjectReportRow]) -> dict:
    import re
    lower = message.lower()
    ops = []
    if "新增一列" in message or "增加一列" in message or "add column" in lower:
        label = message.split("列", 1)[-1].strip(" ：:，,。") or "自定义列"
        key = re.sub(r"[^a-z0-9_]+", "_", label.lower()).strip("_") or f"custom_{len(message)}"
        ops.append({"type": "ADD_COLUMN", "key": key[:60], "label": label[:80], "data_type": "text"})
    elif "不计入" in message or "不要参与" in message or "不参与总价" in message or "exclude" in lower:
        row = _find_row_for_text(rows, message)
        if row:
            ops.append({"type": "TOGGLE_INCLUDE_IN_TOTAL", "row_id": str(row.id), "include_in_total": False})
    elif "改成" in message or "改为" in message or "change" in lower:
        row = _find_row_for_text(rows, message)
        num = re.search(r"(\d+(?:\.\d+)?)", message)
        if row and ("数量" in message or "qty" in lower) and num:
            ops.append({"type": "UPDATE_CELL", "row_id": str(row.id), "field": "qty", "value": float(num.group(1))})
        elif row and ("高端" in message or "premium" in lower):
            ops.append({"type": "SET_SELECTED_TIER", "row_id": str(row.id), "selected_tier": "PREMIUM"})
        elif row and ("中端" in message or "mid" in lower):
            ops.append({"type": "SET_SELECTED_TIER", "row_id": str(row.id), "selected_tier": "MID_RANGE"})
        elif row and ("平价" in message or "budget" in lower):
            ops.append({"type": "SET_SELECTED_TIER", "row_id": str(row.id), "selected_tier": "BUDGET"})
    if not ops:
        ops.append({"type": "RECALCULATE_TOTAL"})
    return {"ops": ops, "message": message}


async def _apply_report_patch(
    db: AsyncSession,
    project: BuyerProject,
    report: ProjectReport,
    columns: list[ProjectReportColumn],
    rows: list[ProjectReportRow],
    patch: dict,
    actor_id: uuid.UUID,
    source: str,
) -> ProjectReportVersion:
    columns_payload = [_column_to_payload(c) for c in columns]
    rows_payload = [_row_to_payload(r) for r in rows]
    row_index = {str(r.id): idx for idx, r in enumerate(rows)}
    for op in patch.get("ops", []):
        op_type = op.get("type")
        if op_type == "ADD_COLUMN":
            key = op.get("key") or f"custom_{len(columns_payload) + 1}"
            columns_payload.append({
                "key": key,
                "label": op.get("label") or key.replace("_", " ").title(),
                "data_type": op.get("data_type") or "text",
                "sort_order": len(columns_payload),
                "editable": True,
                "system": False,
            })
            for payload in rows_payload:
                custom = payload.get("custom_values_jsonb") or {}
                custom.setdefault(key, None)
                payload["custom_values_jsonb"] = custom
        elif op_type == "ADD_ROW":
            rows_payload.append({
                "project_id": project.id,
                "line_item_id": None,
                "category_id": None,
                "name": op.get("name") or "New item",
                "description": op.get("description"),
                "specs_jsonb": op.get("specs_jsonb") or {},
                "qty": float(op.get("qty") or 1),
                "unit": op.get("unit") or "pcs",
                "currency": project.currency,
                "quality_tier": QualityTier.MID_RANGE,
                "selected_tier": op.get("selected_tier") or "MID_RANGE",
                "include_in_total": op.get("include_in_total", True),
                "selected_for_purchase": op.get("selected_for_purchase", True),
                "price_tiers_jsonb": op.get("price_tiers_jsonb") or {},
                "custom_values_jsonb": op.get("custom_values_jsonb") or {},
                "match_status": "UNMATCHED",
                "samples_jsonb": [],
                "price_source": "MANUAL",
                "notes": op.get("notes"),
                "sort_order": len(rows_payload),
            })
        elif op_type in {"UPDATE_ROW", "UPDATE_CELL"}:
            idx = row_index.get(str(op.get("row_id")))
            if idx is not None:
                _set_report_row_field(rows_payload[idx], op.get("field") or "notes", op.get("value"))
        elif op_type == "TOGGLE_INCLUDE_IN_TOTAL":
            idx = row_index.get(str(op.get("row_id")))
            if idx is not None:
                rows_payload[idx]["include_in_total"] = bool(op.get("include_in_total"))
        elif op_type == "SET_SELECTED_TIER":
            idx = row_index.get(str(op.get("row_id")))
            if idx is not None:
                rows_payload[idx]["selected_tier"] = op.get("selected_tier") or "MID_RANGE"
        elif op_type == "DELETE_ROW":
            idx = row_index.get(str(op.get("row_id")))
            if idx is not None:
                rows_payload.pop(idx)
                row_index = {str(rows[i].id): i for i in range(min(len(rows), len(rows_payload)))}

    version = await _create_report_version(
        db, project, report, rows_payload, columns_payload,
        actor_id=actor_id, source=source, status=ProjectReportVersionStatus.USER_REVIEWED,
    )
    return version


async def _extract_basic_metrics_from_message(db: AsyncSession, project: BuyerProject, content: str) -> dict:
    """Lightweight deterministic extraction for chat turns.

    This does not replace the configured AI provider. It keeps the project form useful
    even before the async AI analysis run finishes.
    """
    lowered = content.lower()
    extracted: dict = {}
    if any(token in lowered for token in ["villa", "house", "别墅", "厂房", "factory", "warehouse"]):
        extracted["use_case"] = content[:500]
    elif content.strip() and len(content.strip()) >= 12:
        extracted["use_case"] = content[:500]
    if any(token in lowered for token in ["sqm", "平米", "平方米", "m2"]):
        import re
        match = re.search(r"(\d+(?:\.\d+)?)\s*(sqm|m2|平米|平方米)", lowered)
        if match:
            extracted["area"] = {"value": float(match.group(1)), "unit": "sqm"}
            project.area_value = float(match.group(1))
            project.area_unit = "sqm"
    if any(token in lowered for token in ["budget", "预算", "php", "₱"]):
        extracted["budget_note"] = content[:500]
    if any(token in lowered for token in ["cebu", "mandaue", "lapu-lapu", "manila", "宿务"]):
        extracted["location"] = content[:500]
        if "cebu" in lowered or "宿务" in lowered:
            project.city = project.city or "Cebu"
            project.country = project.country or "PH"

    for key, value in extracted.items():
        await _upsert_metric_value(db, project, key, key.replace("_", " ").title(), value, MetricValueSource.USER, 0.7)
    return extracted


async def _build_metrics_response(db: AsyncSession, project: BuyerProject) -> dict:
    templates = await _load_metric_templates(db, project.project_type)
    values_result = await db.execute(
        select(ProjectMetricValue).where(ProjectMetricValue.project_id == project.id).order_by(ProjectMetricValue.key)
    )
    values = values_result.scalars().all()
    value_keys = {v.key for v in values if v.value_jsonb is not None}
    missing = [
        {
            "key": t.key,
            "label": t.label,
            "prompt": t.prompt,
            "required": t.required,
        }
        for t in templates
        if t.required and t.key not in value_keys
    ]
    return {
        "project_id": project.id,
        "project_type": project.project_type,
        "templates": templates,
        "values": values,
        "missing_required": missing,
    }


def _enum_value(value) -> str:
    return getattr(value, "value", value) or ""


def _clip(value: str | None, limit: int = 600) -> str:
    if not value:
        return ""
    value = str(value).strip()
    return value if len(value) <= limit else f"{value[:limit]}..."


async def _build_project_chat_context(db: AsyncSession, project: BuyerProject, metrics: dict) -> str:
    """Build a compact internal context snapshot for Project Forge chat AI."""
    files_result = await db.execute(
        select(ProjectFile).where(ProjectFile.project_id == project.id).order_by(ProjectFile.created_at.desc()).limit(10)
    )
    files = files_result.scalars().all()

    categories_result = await db.execute(select(Category).order_by(Category.sort_order).limit(12))
    categories = categories_result.scalars().all()

    catalog_result = await db.execute(
        select(CatalogItem)
        .where(CatalogItem.status == CatalogItemStatus.ACTIVE)
        .order_by(CatalogItem.updated_at.desc())
        .limit(10)
    )
    catalog_items = catalog_result.scalars().all()

    metric_lines = []
    for metric in metrics.get("values") or []:
        metric_lines.append(f"- {metric.key}: {metric.value_jsonb}")
    missing_lines = [
        f"- {item.get('label') or item.get('key')}: {item.get('prompt') or ''}"
        for item in metrics.get("missing_required") or []
    ]
    file_lines = [
        (
            f"- {pf.file_name} ({pf.content_type}, {pf.status.value}): "
            f"{_clip(pf.extracted_text or pf.vision_summary, 140) or 'uploaded; no extracted text yet'}"
        )
        for pf in files
    ]
    category_lines = [
        f"- {cat.name}" + (f" / {cat.name_zh}" if cat.name_zh else "")
        for cat in categories
    ]
    catalog_lines = [
        (
            f"- {item.title}: {round((item.price_minor or 0) / 100, 2)} "
            f"{item.currency}/{item.unit}, mode={_enum_value(item.market_mode)}, stock={item.stock_qty}"
        )
        for item in catalog_items
    ]

    return "\n".join([
        "ProcurePing Project Forge internal context snapshot:",
        f"Project id: {project.id}",
        f"Title: {project.title}",
        f"Type: {_enum_value(project.project_type)}",
        f"Status: {_enum_value(project.status)}",
        f"Location: {', '.join([x for x in [project.city, project.country] if x]) or 'unknown'}",
        f"Area: {project.area_value or 'unknown'} {project.area_unit or ''}".strip(),
        f"Budget: {project.budget_min or 'unknown'} - {project.budget_max or 'unknown'} {project.currency}",
        f"Quality preference: {_enum_value(project.quality_preference)}",
        f"Description: {_clip(project.description, 1200) or 'not provided'}",
        "",
        "Collected indicators:",
        "\n".join(metric_lines) or "- none yet",
        "",
        "Missing required indicators:",
        "\n".join(missing_lines) or "- none",
        "",
        "Uploaded/supporting files:",
        "\n".join(file_lines) or "- none",
        "",
        "Available marketplace categories sample:",
        "\n".join(category_lines) or "- none",
        "",
        "Recent active catalog/marketplace sample data:",
        "\n".join(catalog_lines) or "- none",
    ])


def _fallback_project_chat_reply(metrics: dict, file_ids: list | None, multimodal_enabled: bool) -> tuple[str, ProjectWorkflowNode]:
    missing = metrics["missing_required"]
    file_note = ""
    if file_ids and not multimodal_enabled:
        file_note = " Images/files are saved, but multimodal image analysis is disabled in Admin; add a short text description for image-only details."
    if missing:
        next_questions = "; ".join(m["prompt"] or m["label"] for m in missing[:3])
        return f"I captured your project details. Next I still need: {next_questions}.{file_note}", ProjectWorkflowNode.GAP_QUESTION
    return (
        "I have enough core indicators to continue. You can add optional files or details, or click Proceed / AI Analyze to generate the editable demand form.",
        ProjectWorkflowNode.METRIC_EXTRACT,
    )


async def _generate_project_chat_reply(
    db: AsyncSession,
    project: BuyerProject,
    metrics: dict,
    cfg: dict,
    file_ids: list | None,
) -> tuple[str, ProjectWorkflowNode, dict]:
    """Generate the assistant's next chat turn with Admin-configured AI provider, falling back locally."""
    fallback_text, fallback_node = _fallback_project_chat_reply(metrics, file_ids, bool(cfg.get("multimodal_enabled")))
    if not cfg.get("enabled") or not cfg.get("project_estimation_enabled") or not cfg.get("api_key"):
        return fallback_text, fallback_node, {"source": "FALLBACK", "reason": "AI provider disabled or not configured"}

    recent_result = await db.execute(
        select(ProjectMessage)
        .where(ProjectMessage.project_id == project.id, ProjectMessage.role != ProjectMessageRole.SYSTEM)
        .order_by(ProjectMessage.created_at.desc())
        .limit(8)
    )
    recent_messages = list(reversed(recent_result.scalars().all()))
    context = await _build_project_chat_context(db, project, metrics)
    system_prompt = (
        "You are ProcurePing AI Project Forge, a procurement planning assistant inside a marketplace. "
        "Collect project information step by step, use the provided internal marketplace snapshot, and help the buyer turn messy ideas into an editable demand form. "
        "You cannot call live tools directly in this chat; the backend has already supplied project, metric, file, category, and catalog context below. "
        "Ask at most 3 concise follow-up questions. Tell the buyer they can proceed early if they want AI to estimate with assumptions. "
        "If marketplace sample data is relevant, mention it carefully as a sample, not guaranteed stock. "
        "Respond in the same language the buyer used, unless the buyer asks otherwise.\n\n"
        f"{context}"
    )
    ai_messages = [{"role": "system", "content": system_prompt}]
    for msg in recent_messages:
        role = "assistant" if msg.role == ProjectMessageRole.ASSISTANT else "user"
        ai_messages.append({"role": role, "content": _clip(msg.content, 1200)})

    try:
        assistant_text = (await _call_ai(cfg, ai_messages, max_tokens=1400, json_mode=False)).strip()
        if not assistant_text:
            return fallback_text, fallback_node, {"source": "FALLBACK", "reason": "empty AI response"}
        node = ProjectWorkflowNode.GAP_QUESTION if metrics.get("missing_required") else ProjectWorkflowNode.METRIC_EXTRACT
        return assistant_text, node, {
            "source": "AI_PROVIDER",
            "provider": cfg.get("provider"),
            "model": cfg.get("model"),
            "base_url": cfg.get("base_url"),
        }
    except Exception as exc:
        return (
            f"{fallback_text}\n\nAI provider note: {str(exc)[:260]}",
            fallback_node,
            {"source": "FALLBACK", "ai_error": str(exc)[:500]},
        )


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * pct
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


async def _price_samples_for_item(db: AsyncSession, item: ProjectLineItem) -> list[dict]:
    samples: list[dict] = []
    if item.category_id:
        catalog_result = await db.execute(
            select(CatalogItem)
            .where(
                CatalogItem.category_id == item.category_id,
                CatalogItem.status == CatalogItemStatus.ACTIVE,
                CatalogItem.currency == item.currency,
            )
            .order_by(CatalogItem.updated_at.desc())
            .limit(50)
        )
        for catalog_item in catalog_result.scalars().all():
            samples.append({
                "source": "CATALOG",
                "catalog_item_id": str(catalog_item.id),
                "title": catalog_item.title,
                "unit_price": round((catalog_item.price_minor or 0) / 100, 2),
                "currency": catalog_item.currency,
                "unit": catalog_item.unit,
                "company_id": str(catalog_item.company_id),
            })

    if item.intent_id:
        offer_result = await db.execute(select(Offer).where(Offer.intent_id == item.intent_id, Offer.currency == item.currency))
        for offer in offer_result.scalars().all():
            samples.append({
                "source": "OFFER",
                "offer_id": str(offer.id),
                "catalog_item_id": str(offer.catalog_item_id) if offer.catalog_item_id else None,
                "unit_price": round((offer.unit_price_minor or 0) / 100, 2),
                "currency": offer.currency,
                "company_id": str(offer.company_id),
            })
    return [s for s in samples if s.get("unit_price", 0) > 0]


async def _create_price_snapshot(db: AsyncSession, project: BuyerProject, item: ProjectLineItem) -> ProjectPriceSnapshot:
    samples = await _price_samples_for_item(db, item)
    prices = [float(s["unit_price"]) for s in samples]
    qty = max(float(item.qty or 1), 1)
    ai_tiers = item.price_tiers_jsonb or {}

    if prices:
        p20 = _percentile(prices, 0.2)
        med = median(prices)
        p80 = _percentile(prices, 0.8)
        tiers = {
            "BUDGET": {
                "unit_price": round(p20, 2),
                "total_price": round(p20 * qty, 2),
                "source": "REAL_MARKET",
                "notes": f"Low-market estimate from {len(prices)} catalog/offer samples",
            },
            "MID_RANGE": {
                "unit_price": round(med, 2),
                "total_price": round(med * qty, 2),
                "source": "REAL_MARKET",
                "notes": "Median market sample",
            },
            "PREMIUM": {
                "unit_price": round(p80, 2),
                "total_price": round(p80 * qty, 2),
                "source": "REAL_MARKET",
                "notes": "High-market estimate from real samples",
            },
        }
        source_summary = f"{len(prices)} real marketplace price samples"
        item.confidence = max(item.confidence or 0, 0.78)
    else:
        fallback_unit = float(item.estimated_unit_price or 0)
        fallback_total = float(item.estimated_total_price or (fallback_unit * qty))
        tiers = ai_tiers or {
            "BUDGET": {"unit_price": round(fallback_unit * 0.75, 2), "total_price": round(fallback_total * 0.75, 2), "source": "AI_ESTIMATE", "notes": "Real quotes unavailable; AI fallback"},
            "MID_RANGE": {"unit_price": round(fallback_unit or 0, 2), "total_price": round(fallback_total or 0, 2), "source": "AI_ESTIMATE", "notes": "Real quotes unavailable; AI fallback"},
            "PREMIUM": {"unit_price": round(fallback_unit * 1.35, 2), "total_price": round(fallback_total * 1.35, 2), "source": "AI_ESTIMATE", "notes": "Real quotes unavailable; AI fallback"},
        }
        for tier in tiers.values():
            tier.setdefault("source", "AI_ESTIMATE")
            tier.setdefault("notes", "真实报价不足，使用 AI 估算兜底")
        source_summary = "No real marketplace samples; AI fallback estimate"
        item.confidence = min(item.confidence or 0.45, 0.55)

    selected = tiers.get(item.quality_tier.value) or tiers.get("MID_RANGE") or {}
    if selected.get("unit_price"):
        item.estimated_unit_price = selected["unit_price"]
        item.estimated_total_price = selected.get("total_price", selected["unit_price"] * qty)
    item.price_tiers_jsonb = tiers

    snapshot = ProjectPriceSnapshot(
        project_id=project.id,
        line_item_id=item.id,
        currency=item.currency,
        sample_count=len(samples),
        min_unit_price=round(min(prices), 2) if prices else None,
        avg_unit_price=round(mean(prices), 2) if prices else None,
        median_unit_price=round(median(prices), 2) if prices else None,
        p20_unit_price=round(_percentile(prices, 0.2), 2) if prices else None,
        p80_unit_price=round(_percentile(prices, 0.8), 2) if prices else None,
        price_tiers_jsonb=tiers,
        samples_jsonb=samples[:20],
        source_summary=source_summary,
    )
    db.add(snapshot)
    return snapshot


# ─── Project CRUD ──────────────────────────────────────────────

@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    req: ProjectCreate,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    """Create a new buyer project."""
    project = BuyerProject(buyer_id=user.id, **req.model_dump())
    db.add(project)
    await db.flush()

    await create_audit_log(
        db, action="PROJECT_CREATED", entity_type="BuyerProject", entity_id=project.id,
        actor_id=user.id, actor_role=user.role.value,
    )
    await db.commit()
    await db.refresh(project)
    return project


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    status: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    """List the current buyer's projects."""
    q = select(BuyerProject).where(BuyerProject.buyer_id == user.id)
    if status:
        try:
            q = q.where(BuyerProject.status == ProjectStatus(status))
        except ValueError:
            pass
    q = q.order_by(BuyerProject.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: str,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    """Get full project detail including files, line items, and latest AI run."""
    project = await _get_buyer_project(db, project_id, user.id)
    detail = await _build_detail_response(db, project)
    return detail


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    req: ProjectUpdate,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    """Update project basic info. Only allowed in editable statuses."""
    project = await _get_buyer_project(db, project_id, user.id)
    editable = {ProjectStatus.DRAFT, ProjectStatus.COLLECTING_INFO, ProjectStatus.AI_ANALYZED, ProjectStatus.READY_FOR_SOURCING}
    if project.status not in editable:
        raise HTTPException(status_code=400, detail=f"Cannot update project in {project.status.value} status")

    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(project, field, value)

    await db.commit()
    await db.refresh(project)
    return project


@router.get("/{project_id}/messages", response_model=list[ProjectMessageResponse])
async def list_project_messages(
    project_id: str,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    """Read the LangGraph-style conversation history for a project."""
    project = await _get_buyer_project(db, project_id, user.id)
    result = await db.execute(
        select(ProjectMessage).where(ProjectMessage.project_id == project.id).order_by(ProjectMessage.created_at)
    )
    return result.scalars().all()


@router.post("/{project_id}/messages", response_model=list[ProjectMessageResponse], status_code=201)
async def create_project_message(
    project_id: str,
    req: ProjectMessageCreate,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    """Append a user message and return the assistant's next collection prompt."""
    project = await _get_buyer_project(db, project_id, user.id)

    if req.file_ids:
        file_result = await db.execute(
            select(ProjectFile).where(ProjectFile.project_id == project.id, ProjectFile.id.in_(req.file_ids))
        )
        found = {f.id for f in file_result.scalars().all()}
        missing = [str(fid) for fid in req.file_ids if fid not in found]
        if missing:
            raise HTTPException(status_code=400, detail=f"Files do not belong to project: {', '.join(missing)}")

    extracted = await _extract_basic_metrics_from_message(db, project, req.content)
    if project.status == ProjectStatus.DRAFT:
        project.status = ProjectStatus.COLLECTING_INFO
    if not project.description:
        project.description = req.content[:2000]

    user_msg = ProjectMessage(
        project_id=project.id,
        role=ProjectMessageRole.USER,
        workflow_node=ProjectWorkflowNode.INTAKE_CHAT,
        content=req.content,
        file_ids_jsonb=[str(fid) for fid in req.file_ids],
        structured_delta_jsonb={"extracted_metrics": extracted} if extracted else None,
    )
    db.add(user_msg)
    await db.flush()

    metrics = await _build_metrics_response(db, project)
    cfg = await get_project_ai_config(db)
    assistant_text, node, reply_meta = await _generate_project_chat_reply(db, project, metrics, cfg, req.file_ids)

    assistant_msg = ProjectMessage(
        project_id=project.id,
        role=ProjectMessageRole.ASSISTANT,
        workflow_node=node,
        content=assistant_text,
        structured_delta_jsonb={
            "missing_required": metrics["missing_required"],
            "workflow_next": "ai_analyze" if not metrics["missing_required"] else "collect_more",
            "reply_meta": reply_meta,
        },
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(user_msg)
    await db.refresh(assistant_msg)
    return [user_msg, assistant_msg]


@router.get("/{project_id}/metrics", response_model=ProjectMetricsResponse)
async def get_project_metrics(
    project_id: str,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_buyer_project(db, project_id, user.id)
    return await _build_metrics_response(db, project)


@router.patch("/{project_id}/metrics", response_model=ProjectMetricsResponse)
async def update_project_metrics(
    project_id: str,
    req: ProjectMetricsUpdate,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_buyer_project(db, project_id, user.id)
    if project.status in {ProjectStatus.SOURCING, ProjectStatus.ORDERING, ProjectStatus.COMPLETED, ProjectStatus.CANCELED}:
        raise HTTPException(status_code=400, detail=f"Cannot edit metrics in {project.status.value} status")

    for metric in req.metrics:
        await _upsert_metric_value(db, project, metric.key, metric.label, metric.value, metric.source, metric.confidence)

    if project.status == ProjectStatus.DRAFT:
        project.status = ProjectStatus.COLLECTING_INFO
    await db.commit()
    return await _build_metrics_response(db, project)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    """Cancel / soft-delete a project. Sets status to CANCELED."""
    project = await _get_buyer_project(db, project_id, user.id)
    # Don't allow deleting projects that have published intents
    if project.status in (ProjectStatus.SOURCING, ProjectStatus.ORDERING):
        raise HTTPException(status_code=400, detail="Cannot cancel a project with active sourcing or orders")
    if project.status == ProjectStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Cannot cancel a completed project")

    project.status = ProjectStatus.CANCELED
    await create_audit_log(
        db, action="PROJECT_CANCELED", entity_type="BuyerProject", entity_id=project.id,
        actor_id=user.id, actor_role=user.role.value,
    )
    await db.commit()
    return None


# ─── File Upload ───────────────────────────────────────────────

@router.post("/{project_id}/files", response_model=ProjectFileResponse, status_code=201)
async def upload_project_file(
    project_id: str,
    file: UploadFile,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    """Upload a file (image/PDF/TXT/DOCX) and bind it to a project."""
    project = await _get_buyer_project(db, project_id, user.id)

    # Check AI config for max files
    cfg = await get_project_ai_config(db)
    max_files = cfg.get("max_files", 10)

    # Count existing files
    count_result = await db.execute(
        select(func.count()).select_from(ProjectFile).where(ProjectFile.project_id == project.id)
    )
    current_count = count_result.scalar() or 0
    if current_count >= max_files:
        raise HTTPException(status_code=400, detail=f"Maximum {max_files} files per project")

    if file.content_type not in PROJECT_ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed: {file.content_type}. Allowed: image/jpeg, image/png, image/webp, application/pdf, text/plain, application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    content = await file.read()
    max_size = cfg.get("max_file_size_mb", 10) * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail=f"File too large (max {cfg.get('max_file_size_mb', 10)}MB)")

    # Save to disk
    ext = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "bin"
    filename = f"{uuid.uuid4().hex}.{ext}"
    dest = os.path.join(settings.UPLOAD_DIR, filename)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    with open(dest, "wb") as f:
        f.write(content)

    url = f"{settings.PUBLIC_FILE_BASE_URL}/{filename}"

    # Create project file record
    pf = ProjectFile(
        project_id=project.id,
        url=url,
        file_name=file.filename or filename,
        content_type=file.content_type,
        file_size=len(content),
    )
    db.add(pf)

    # Move project to COLLECTING_INFO if still DRAFT
    if project.status == ProjectStatus.DRAFT:
        project.status = ProjectStatus.COLLECTING_INFO

    await db.commit()
    await db.refresh(pf)
    return pf


@router.delete("/{project_id}/files/{file_id}", status_code=204)
async def delete_project_file(
    project_id: str,
    file_id: str,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    """Remove a file from a project."""
    project = await _get_buyer_project(db, project_id, user.id)
    result = await db.execute(
        select(ProjectFile).where(ProjectFile.id == file_id, ProjectFile.project_id == project.id)
    )
    pf = result.scalar_one_or_none()
    if not pf:
        raise HTTPException(status_code=404, detail="File not found")
    await db.delete(pf)
    await db.commit()
    return None


# ─── AI Analysis ───────────────────────────────────────────────

@router.post("/{project_id}/ai/analyze", response_model=AIRunResponse, status_code=202)
async def start_ai_analysis(
    project_id: str,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    """Start async AI analysis for the project. Returns the AI run record immediately."""
    project = await _get_buyer_project(db, project_id, user.id)

    # Check if AI project analysis is enabled
    cfg = await get_project_ai_config(db)
    if not cfg.get("enabled") or not cfg.get("project_estimation_enabled"):
        raise HTTPException(status_code=403, detail="AI project analysis is disabled by administrator")

    await _expire_stale_ai_runs(db, project.id)

    # Don't allow re-analysis if one is already running
    running_result = await db.execute(
        select(ProjectAIRun).where(
            ProjectAIRun.project_id == project.id,
            ProjectAIRun.status.in_([AIRunStatus.PENDING, AIRunStatus.RUNNING]),
        )
    )
    if running_result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="An analysis is already in progress for this project")

    # Create AI run record
    ai_run = ProjectAIRun(
        project_id=project.id,
        status=AIRunStatus.PENDING,
        prompt_version=cfg.get("prompt_version", "v1"),
    )
    db.add(ai_run)
    await db.flush()

    await create_audit_log(
        db, action="PROJECT_AI_ANALYSIS_STARTED", entity_type="ProjectAIRun", entity_id=ai_run.id,
        actor_id=user.id, actor_role=user.role.value,
    )

    await db.commit()
    await db.refresh(ai_run)

    # Schedule background task
    background_tasks.add_task(run_project_analysis, project.id)

    return ai_run


@router.get("/{project_id}/ai-runs/{run_id}", response_model=AIRunResponse)
async def get_ai_run(
    project_id: str,
    run_id: str,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    """Get AI run status and results."""
    project = await _get_buyer_project(db, project_id, user.id)
    result = await db.execute(
        select(ProjectAIRun).where(ProjectAIRun.id == run_id, ProjectAIRun.project_id == project.id)
    )
    ai_run = result.scalar_one_or_none()
    if not ai_run:
        raise HTTPException(status_code=404, detail="AI run not found")
    return ai_run


@router.post("/{project_id}/ai-runs/{run_id}/retry", response_model=AIRunResponse, status_code=202)
async def retry_ai_analysis(
    project_id: str,
    run_id: str,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    """Retry a failed AI analysis. Creates a new AI run and starts background analysis."""
    project = await _get_buyer_project(db, project_id, user.id)
    result = await db.execute(
        select(ProjectAIRun).where(ProjectAIRun.id == run_id, ProjectAIRun.project_id == project.id)
    )
    old_run = result.scalar_one_or_none()
    if not old_run:
        raise HTTPException(status_code=404, detail="AI run not found")

    await _expire_stale_ai_runs(db, project.id)

    if old_run.status not in (AIRunStatus.FAILED,):
        raise HTTPException(status_code=400, detail="Can only retry failed analysis runs")

    # Check no run is currently active
    running_result = await db.execute(
        select(ProjectAIRun).where(
            ProjectAIRun.project_id == project.id,
            ProjectAIRun.status.in_([AIRunStatus.PENDING, AIRunStatus.RUNNING]),
        )
    )
    if running_result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="An analysis is already in progress")

    cfg = await get_project_ai_config(db)
    if not cfg.get("enabled") or not cfg.get("project_estimation_enabled"):
        raise HTTPException(status_code=403, detail="AI project analysis is disabled by administrator")

    ai_run = ProjectAIRun(
        project_id=project.id,
        status=AIRunStatus.PENDING,
        prompt_version=cfg.get("prompt_version", "v1"),
    )
    db.add(ai_run)
    await db.flush()

    await create_audit_log(
        db, action="PROJECT_AI_ANALYSIS_RETRIED", entity_type="ProjectAIRun", entity_id=ai_run.id,
        actor_id=user.id, actor_role=user.role.value,
        before_json={"failed_run_id": str(old_run.id)},
    )
    await db.commit()
    await db.refresh(ai_run)

    background_tasks.add_task(run_project_analysis, project.id)
    return ai_run


@router.get("/{project_id}/matches")
async def get_project_matches(
    project_id: str,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated supplier matches for all published line items in this project."""
    project = await _get_buyer_project(db, project_id, user.id)

    # Get line items that have been published (have intent_id)
    items_result = await db.execute(
        select(ProjectLineItem).where(
            ProjectLineItem.project_id == project.id,
            ProjectLineItem.intent_id.isnot(None),
        )
    )
    items = items_result.scalars().all()

    matches_by_item = []
    for item in items:
        # Load the intent
        intent_result = await db.execute(select(Intent).where(Intent.id == item.intent_id))
        intent = intent_result.scalar_one_or_none()
        if not intent:
            continue

        # Get supplier matches
        try:
            suppliers = await find_matching_suppliers(db, intent)
        except Exception:
            suppliers = []

        matches_by_item.append({
            "line_item_id": str(item.id),
            "line_item_name": item.name,
            "intent_id": str(item.intent_id),
            "intent_status": intent.status.value if intent.status else None,
            "matched_suppliers": len(suppliers),
            "top_suppliers": suppliers[:5],
        })

    return {
        "project_id": str(project.id),
        "total_published": len(items),
        "items": matches_by_item,
    }


# ─── Versioned Report Sheet ────────────────────────────────────

@router.get("/{project_id}/report", response_model=ProjectReportResponse)
async def get_project_report(
    project_id: str,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_buyer_project(db, project_id, user.id)
    report = await _ensure_project_report(db, project, user.id)
    return await _load_report_detail(db, report)


@router.get("/{project_id}/report/versions", response_model=list[ProjectReportVersionResponse])
async def list_project_report_versions(
    project_id: str,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_buyer_project(db, project_id, user.id)
    report = await _ensure_project_report(db, project, user.id)
    result = await db.execute(
        select(ProjectReportVersion)
        .where(ProjectReportVersion.report_id == report.id)
        .order_by(ProjectReportVersion.version_number.desc())
    )
    return result.scalars().all()


@router.get("/{project_id}/report/versions/{version_id}", response_model=ProjectReportResponse)
async def get_project_report_version(
    project_id: str,
    version_id: str,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_buyer_project(db, project_id, user.id)
    report = await _ensure_project_report(db, project, user.id)
    return await _load_report_detail(db, report, uuid.UUID(version_id))


@router.post("/{project_id}/report/versions/{version_id}/restore", response_model=ProjectReportResponse)
async def restore_project_report_version(
    project_id: str,
    version_id: str,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_buyer_project(db, project_id, user.id)
    report = await _ensure_project_report(db, project, user.id)
    result = await db.execute(
        select(ProjectReportVersion).where(
            ProjectReportVersion.id == version_id,
            ProjectReportVersion.report_id == report.id,
        )
    )
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Report version not found")
    report.current_version_id = version.id
    report.updated_at = datetime.now(timezone.utc)
    db.add(ProjectReportChangeLog(
        project_id=project.id,
        report_id=report.id,
        version_id=version.id,
        actor_id=user.id,
        change_type="RESTORE_VERSION",
        status=ProjectReportPatchStatus.APPLIED,
        patch_jsonb={"restore_version_id": str(version.id)},
        applied_at=datetime.now(timezone.utc),
    ))
    await db.commit()
    await db.refresh(report)
    return await _load_report_detail(db, report)


@router.post("/{project_id}/report/versions/{version_id}/diff")
async def diff_project_report_version(
    project_id: str,
    version_id: str,
    compare_to: str | None = Query(default=None),
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_buyer_project(db, project_id, user.id)
    report = await _ensure_project_report(db, project, user.id)
    base_id = uuid.UUID(version_id)
    target_id = uuid.UUID(compare_to) if compare_to else report.current_version_id
    base_rows = (await db.execute(select(ProjectReportRow).where(ProjectReportRow.report_version_id == base_id))).scalars().all()
    target_rows = (await db.execute(select(ProjectReportRow).where(ProjectReportRow.report_version_id == target_id))).scalars().all()

    def key(row: ProjectReportRow) -> str:
        return str(row.line_item_id or row.name.lower())

    base_map = {key(r): r for r in base_rows}
    target_map = {key(r): r for r in target_rows}
    added = [r.name for k, r in target_map.items() if k not in base_map]
    removed = [r.name for k, r in base_map.items() if k not in target_map]
    changed = []
    for k, row in target_map.items():
        old = base_map.get(k)
        if old and (
            old.qty != row.qty or old.unit != row.unit or old.selected_tier != row.selected_tier
            or old.include_in_total != row.include_in_total or old.selected_for_purchase != row.selected_for_purchase
            or old.price_tiers_jsonb != row.price_tiers_jsonb
        ):
            changed.append(row.name)
    return {"added": added, "removed": removed, "changed": changed, "counts": {"added": len(added), "removed": len(removed), "changed": len(changed)}}


@router.patch("/{project_id}/report/cells", response_model=ProjectReportResponse)
async def update_project_report_cells(
    project_id: str,
    req: ProjectReportCellsUpdate,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_buyer_project(db, project_id, user.id)
    report, version, columns, rows = await _current_report_parts(db, project, user.id)
    row_index = {str(r.id): r for r in rows}
    patch = {"ops": []}
    for change in req.changes:
        if str(change.row_id) not in row_index:
            raise HTTPException(status_code=404, detail=f"Report row not found: {change.row_id}")
        patch["ops"].append({"type": "UPDATE_CELL", "row_id": str(change.row_id), "field": change.field, "value": change.value})
    new_version = await _apply_report_patch(db, project, report, columns, rows, patch, user.id, "CELL_EDIT")
    db.add(ProjectReportChangeLog(
        project_id=project.id,
        report_id=report.id,
        version_id=new_version.id,
        actor_id=user.id,
        change_type="CELL_EDIT",
        status=ProjectReportPatchStatus.APPLIED,
        user_message=req.message,
        patch_jsonb=patch,
        before_jsonb={"version_id": str(version.id)},
        after_jsonb={"version_id": str(new_version.id)},
        applied_at=datetime.now(timezone.utc),
    ))
    await db.commit()
    await db.refresh(report)
    return await _load_report_detail(db, report)


@router.post("/{project_id}/report/columns", response_model=ProjectReportResponse)
async def add_project_report_column(
    project_id: str,
    req: ProjectReportColumnCreate,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_buyer_project(db, project_id, user.id)
    report, version, columns, rows = await _current_report_parts(db, project, user.id)
    patch = {"ops": [{"type": "ADD_COLUMN", "key": req.key, "label": req.label, "data_type": req.data_type}]}
    new_version = await _apply_report_patch(db, project, report, columns, rows, patch, user.id, "ADD_COLUMN")
    db.add(ProjectReportChangeLog(
        project_id=project.id, report_id=report.id, version_id=new_version.id, actor_id=user.id,
        change_type="ADD_COLUMN", status=ProjectReportPatchStatus.APPLIED,
        patch_jsonb=patch, before_jsonb={"version_id": str(version.id)}, after_jsonb={"version_id": str(new_version.id)},
        applied_at=datetime.now(timezone.utc),
    ))
    await db.commit()
    await db.refresh(report)
    return await _load_report_detail(db, report)


@router.post("/{project_id}/report/rows", response_model=ProjectReportResponse)
async def add_project_report_row(
    project_id: str,
    req: ProjectReportRowCreate,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_buyer_project(db, project_id, user.id)
    report, version, columns, rows = await _current_report_parts(db, project, user.id)
    patch = {"ops": [{"type": "ADD_ROW", **req.model_dump()}]}
    new_version = await _apply_report_patch(db, project, report, columns, rows, patch, user.id, "ADD_ROW")
    db.add(ProjectReportChangeLog(
        project_id=project.id, report_id=report.id, version_id=new_version.id, actor_id=user.id,
        change_type="ADD_ROW", status=ProjectReportPatchStatus.APPLIED,
        patch_jsonb=patch, before_jsonb={"version_id": str(version.id)}, after_jsonb={"version_id": str(new_version.id)},
        applied_at=datetime.now(timezone.utc),
    ))
    await db.commit()
    await db.refresh(report)
    return await _load_report_detail(db, report)


@router.delete("/{project_id}/report/rows/{row_id}", response_model=ProjectReportResponse)
async def delete_project_report_row(
    project_id: str,
    row_id: str,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_buyer_project(db, project_id, user.id)
    report, version, columns, rows = await _current_report_parts(db, project, user.id)
    if not any(str(r.id) == row_id for r in rows):
        raise HTTPException(status_code=404, detail="Report row not found")
    patch = {"ops": [{"type": "DELETE_ROW", "row_id": row_id}]}
    new_version = await _apply_report_patch(db, project, report, columns, rows, patch, user.id, "DELETE_ROW")
    db.add(ProjectReportChangeLog(
        project_id=project.id, report_id=report.id, version_id=new_version.id, actor_id=user.id,
        change_type="DELETE_ROW", status=ProjectReportPatchStatus.APPLIED,
        patch_jsonb=patch, before_jsonb={"version_id": str(version.id)}, after_jsonb={"version_id": str(new_version.id)},
        applied_at=datetime.now(timezone.utc),
    ))
    await db.commit()
    await db.refresh(report)
    return await _load_report_detail(db, report)


@router.post("/{project_id}/report/recalculate", response_model=ProjectReportResponse)
async def recalculate_project_report(
    project_id: str,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_buyer_project(db, project_id, user.id)
    report, version, columns, rows = await _current_report_parts(db, project, user.id)
    rows_payload = [_row_to_payload(r) for r in rows]
    line_items = {
        str(item.id): item for item in (await db.execute(
            select(ProjectLineItem).where(ProjectLineItem.project_id == project.id)
        )).scalars().all()
    }
    for payload in rows_payload:
        item = line_items.get(str(payload.get("line_item_id")))
        if item:
            snapshot = await _create_price_snapshot(db, project, item)
            payload["price_tiers_jsonb"] = snapshot.price_tiers_jsonb
            payload["samples_jsonb"] = snapshot.samples_jsonb
            payload["match_status"] = "MATCHED" if snapshot.sample_count else payload.get("match_status") or "UNMATCHED"
            payload["price_source"] = "MARKET_SAMPLE" if snapshot.sample_count else "AI_ESTIMATE"
    new_version = await _create_report_version(
        db, project, report, rows_payload, [_column_to_payload(c) for c in columns],
        actor_id=user.id, source="RECALCULATE", status=ProjectReportVersionStatus.ESTIMATED,
    )
    db.add(ProjectReportChangeLog(
        project_id=project.id, report_id=report.id, version_id=new_version.id, actor_id=user.id,
        change_type="RECALCULATE_TOTAL", status=ProjectReportPatchStatus.APPLIED,
        before_jsonb={"version_id": str(version.id)}, after_jsonb={"version_id": str(new_version.id)},
        applied_at=datetime.now(timezone.utc),
    ))
    await db.commit()
    await db.refresh(report)
    return await _load_report_detail(db, report)


@router.post("/{project_id}/report/freeze", response_model=ProjectReportResponse)
async def freeze_project_report(
    project_id: str,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_buyer_project(db, project_id, user.id)
    report, version, columns, rows = await _current_report_parts(db, project, user.id)
    version.status = ProjectReportVersionStatus.FROZEN
    version.totals_jsonb = _calculate_report_totals(rows)
    report.frozen_version_id = version.id
    report.updated_at = datetime.now(timezone.utc)
    project.status = ProjectStatus.READY_FOR_SOURCING
    db.add(ProjectReportChangeLog(
        project_id=project.id, report_id=report.id, version_id=version.id, actor_id=user.id,
        change_type="FREEZE_REPORT", status=ProjectReportPatchStatus.APPLIED,
        after_jsonb={"frozen_version_id": str(version.id)}, applied_at=datetime.now(timezone.utc),
    ))
    await db.commit()
    await db.refresh(report)
    return await _load_report_detail(db, report)


@router.post("/{project_id}/report/chat", response_model=ProjectReportChangeLogResponse)
async def chat_project_report_patch(
    project_id: str,
    req: ProjectReportChatRequest,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_buyer_project(db, project_id, user.id)
    report, version, columns, rows = await _current_report_parts(db, project, user.id)
    patch = _build_chat_patch(req.message, rows)
    log = ProjectReportChangeLog(
        project_id=project.id,
        report_id=report.id,
        version_id=version.id,
        actor_id=user.id,
        change_type="CHAT_PATCH",
        status=ProjectReportPatchStatus.PENDING,
        user_message=req.message,
        patch_jsonb=patch,
        before_jsonb={"version_id": str(version.id)},
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


@router.post("/{project_id}/report/patches/{patch_id}/apply", response_model=ProjectReportResponse)
async def apply_project_report_patch(
    project_id: str,
    patch_id: str,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_buyer_project(db, project_id, user.id)
    report, version, columns, rows = await _current_report_parts(db, project, user.id)
    log = (await db.execute(
        select(ProjectReportChangeLog).where(
            ProjectReportChangeLog.id == patch_id,
            ProjectReportChangeLog.project_id == project.id,
            ProjectReportChangeLog.status == ProjectReportPatchStatus.PENDING,
        )
    )).scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="Pending patch not found")
    try:
        new_version = await _apply_report_patch(db, project, report, columns, rows, log.patch_jsonb or {}, user.id, "CHAT_PATCH")
        log.status = ProjectReportPatchStatus.APPLIED
        log.version_id = new_version.id
        log.after_jsonb = {"version_id": str(new_version.id)}
        log.applied_at = datetime.now(timezone.utc)
    except Exception as e:
        log.status = ProjectReportPatchStatus.FAILED
        log.error_message = str(e)[:1000]
        await db.commit()
        raise
    await db.commit()
    await db.refresh(report)
    return await _load_report_detail(db, report)


@router.post("/{project_id}/report/patches/{patch_id}/reject", response_model=ProjectReportChangeLogResponse)
async def reject_project_report_patch(
    project_id: str,
    patch_id: str,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_buyer_project(db, project_id, user.id)
    log = (await db.execute(
        select(ProjectReportChangeLog).where(
            ProjectReportChangeLog.id == patch_id,
            ProjectReportChangeLog.project_id == project.id,
            ProjectReportChangeLog.status == ProjectReportPatchStatus.PENDING,
        )
    )).scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="Pending patch not found")
    log.status = ProjectReportPatchStatus.REJECTED
    await db.commit()
    await db.refresh(log)
    return log


@router.post("/{project_id}/freeze-form", response_model=ProjectDetailResponse)
async def freeze_project_form(
    project_id: str,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    """Freeze current AI results/metrics into a sourcing-ready demand form."""
    project = await _get_buyer_project(db, project_id, user.id)
    if project.status in {ProjectStatus.SOURCING, ProjectStatus.ORDERING, ProjectStatus.COMPLETED, ProjectStatus.CANCELED}:
        raise HTTPException(status_code=400, detail=f"Cannot freeze project in {project.status.value} status")

    items_count = (await db.execute(
        select(func.count()).select_from(ProjectLineItem).where(
            ProjectLineItem.project_id == project.id,
            ProjectLineItem.status != LineItemStatus.REMOVED,
        )
    )).scalar() or 0
    if items_count == 0:
        raise HTTPException(status_code=400, detail="Cannot freeze form before AI creates line items")

    project.status = ProjectStatus.READY_FOR_SOURCING
    msg = ProjectMessage(
        project_id=project.id,
        role=ProjectMessageRole.SYSTEM,
        workflow_node=ProjectWorkflowNode.FORM_FREEZE,
        content="Project demand form frozen for sourcing. Buyer can confirm line items and publish procurement requests.",
    )
    db.add(msg)
    await create_audit_log(
        db, action="PROJECT_FORM_FROZEN", entity_type="BuyerProject", entity_id=project.id,
        actor_id=user.id, actor_role=user.role.value,
    )
    await db.commit()
    await db.refresh(project)
    return await _build_detail_response(db, project)


@router.post("/{project_id}/price-estimate")
async def estimate_project_prices(
    project_id: str,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    """Recalculate BUDGET/MID_RANGE/PREMIUM tiers using real catalog/offer samples first."""
    project = await _get_buyer_project(db, project_id, user.id)
    result = await db.execute(
        select(ProjectLineItem).where(
            ProjectLineItem.project_id == project.id,
            ProjectLineItem.status != LineItemStatus.REMOVED,
        )
    )
    items = result.scalars().all()
    snapshots = []
    for item in items:
        snapshots.append(await _create_price_snapshot(db, project, item))

    if snapshots:
        by_tier = {"BUDGET": 0.0, "MID_RANGE": 0.0, "PREMIUM": 0.0}
        for item in items:
            if not getattr(item, "include_in_estimate", True):
                continue
            tiers = item.price_tiers_jsonb or {}
            for tier in by_tier:
                by_tier[tier] += float((tiers.get(tier) or {}).get("total_price") or 0)
        project.estimated_budget_jsonb = {
            "min": round(min(by_tier.values()), 2),
            "max": round(max(by_tier.values()), 2),
            "currency": project.currency,
            "confidence": 0.78 if any(s.sample_count for s in snapshots) else 0.5,
            "by_tier": {tier: {"min": round(total, 2), "max": round(total, 2)} for tier, total in by_tier.items()},
            "source": "REAL_MARKET_WITH_AI_FALLBACK",
        }

    msg = ProjectMessage(
        project_id=project.id,
        role=ProjectMessageRole.SYSTEM,
        workflow_node=ProjectWorkflowNode.PRICE_TIER_ESTIMATE,
        content=f"Price tiers recalculated for {len(snapshots)} line items using real marketplace data first.",
        structured_delta_jsonb={"snapshots": len(snapshots)},
    )
    db.add(msg)
    await db.commit()
    return {
        "project_id": str(project.id),
        "snapshots_created": len(snapshots),
        "items": [
            {
                "line_item_id": str(s.line_item_id),
                "sample_count": s.sample_count,
                "source_summary": s.source_summary,
                "price_tiers": s.price_tiers_jsonb,
            }
            for s in snapshots
        ],
        "estimated_budget": project.estimated_budget_jsonb,
    }


@router.get("/{project_id}/comparison")
async def get_project_comparison(
    project_id: str,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    """Return line item comparison data: price tiers, latest snapshots, and supplier matches."""
    project = await _get_buyer_project(db, project_id, user.id)
    items_result = await db.execute(
        select(ProjectLineItem).where(
            ProjectLineItem.project_id == project.id,
            ProjectLineItem.status != LineItemStatus.REMOVED,
        ).order_by(ProjectLineItem.created_at)
    )
    items = items_result.scalars().all()
    comparison = []
    for item in items:
        snapshot_result = await db.execute(
            select(ProjectPriceSnapshot)
            .where(ProjectPriceSnapshot.line_item_id == item.id)
            .order_by(ProjectPriceSnapshot.created_at.desc())
            .limit(1)
        )
        snapshot = snapshot_result.scalar_one_or_none()
        suppliers = []
        if item.intent_id:
            intent_result = await db.execute(select(Intent).where(Intent.id == item.intent_id))
            intent = intent_result.scalar_one_or_none()
            if intent:
                try:
                    suppliers = (await find_matching_suppliers(db, intent))[:5]
                except Exception:
                    suppliers = []
        comparison.append({
            "line_item": {
                "id": str(item.id),
                "name": item.name,
                "qty": item.qty,
                "unit": item.unit,
                "category_id": str(item.category_id) if item.category_id else None,
                "quality_tier": item.quality_tier.value if item.quality_tier else None,
                "price_tiers": item.price_tiers_jsonb,
                "include_in_estimate": getattr(item, "include_in_estimate", True),
                "intent_id": str(item.intent_id) if item.intent_id else None,
            },
            "price_snapshot": {
                "sample_count": snapshot.sample_count if snapshot else 0,
                "min_unit_price": snapshot.min_unit_price if snapshot else None,
                "avg_unit_price": snapshot.avg_unit_price if snapshot else None,
                "median_unit_price": snapshot.median_unit_price if snapshot else None,
                "p20_unit_price": snapshot.p20_unit_price if snapshot else None,
                "p80_unit_price": snapshot.p80_unit_price if snapshot else None,
                "source_summary": snapshot.source_summary if snapshot else "No price snapshot yet",
                "samples": snapshot.samples_jsonb if snapshot else [],
            },
            "suppliers": suppliers,
        })
    return {"project_id": str(project.id), "items": comparison}


# ─── Line Items ────────────────────────────────────────────────

@router.patch("/{project_id}/line-items/{line_item_id}", response_model=LineItemResponse)
async def update_line_item(
    project_id: str,
    line_item_id: str,
    req: LineItemUpdate,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    """Edit an AI-generated or user-created line item."""
    project = await _get_buyer_project(db, project_id, user.id)
    result = await db.execute(
        select(ProjectLineItem).where(
            ProjectLineItem.id == line_item_id,
            ProjectLineItem.project_id == project.id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Line item not found")

    # Only DRAFT items can be fully edited; CONFIRMED items can be set back to DRAFT
    if item.status not in (LineItemStatus.DRAFT, LineItemStatus.CONFIRMED):
        raise HTTPException(status_code=400, detail=f"Cannot edit line item in {item.status.value} status")

    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(item, field, value)

    # If user explicitly edits, mark as user-modified
    if item.source == LineItemSource.AI:
        # Keep source as AI but it's been user-edited — tracked by updated_at
        pass

    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/{project_id}/line-items/{line_item_id}", status_code=204)
async def remove_line_item(
    project_id: str,
    line_item_id: str,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    """Mark a line item as REMOVED."""
    project = await _get_buyer_project(db, project_id, user.id)
    result = await db.execute(
        select(ProjectLineItem).where(
            ProjectLineItem.id == line_item_id,
            ProjectLineItem.project_id == project.id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Line item not found")
    item.status = LineItemStatus.REMOVED
    await db.commit()
    return None


# ─── Publish ───────────────────────────────────────────────────

@router.post("/{project_id}/publish", response_model=PublishResult)
async def publish_project(
    project_id: str,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    """Publish confirmed line items as Intent records.

    Each CONFIRMED line item generates one Intent reusing the existing
    Intent → Offer → Order → Payment chain.
    """
    project = await _get_buyer_project(db, project_id, user.id)

    allowed = {ProjectStatus.AI_ANALYZED, ProjectStatus.READY_FOR_SOURCING}
    if project.status not in allowed:
        raise HTTPException(status_code=400, detail=f"Cannot publish from {project.status.value} status")

    # Prefer frozen report rows; fallback to legacy confirmed line items.
    items: list[ProjectLineItem] = []
    frozen_version = None
    report = (await db.execute(select(ProjectReport).where(ProjectReport.project_id == project.id))).scalar_one_or_none()
    if report and report.frozen_version_id:
        frozen_version = (await db.execute(
            select(ProjectReportVersion).where(ProjectReportVersion.id == report.frozen_version_id)
        )).scalar_one_or_none()
        rows = (await db.execute(
            select(ProjectReportRow).where(
                ProjectReportRow.report_version_id == report.frozen_version_id,
                ProjectReportRow.include_in_total == True,  # noqa: E712
                ProjectReportRow.selected_for_purchase == True,  # noqa: E712
            ).order_by(ProjectReportRow.sort_order)
        )).scalars().all()
        ids = [row.line_item_id for row in rows if row.line_item_id]
        existing = {}
        if ids:
            existing = {
                item.id: item for item in (await db.execute(
                    select(ProjectLineItem).where(ProjectLineItem.id.in_(ids))
                )).scalars().all()
            }
        for row in rows:
            selected_tier = row.selected_tier if row.selected_tier in {"BUDGET", "MID_RANGE", "PREMIUM"} else "MID_RANGE"
            selected_price = (row.price_tiers_jsonb or {}).get(selected_tier) or {}
            item = existing.get(row.line_item_id)
            if not item:
                item = ProjectLineItem(
                    project_id=project.id,
                    category_id=row.category_id,
                    name=row.name,
                    description=row.description,
                    specs_jsonb=row.specs_jsonb,
                    qty=row.qty,
                    unit=row.unit,
                    quality_tier=QualityTier(selected_tier),
                    estimated_unit_price=selected_price.get("unit_price"),
                    estimated_total_price=selected_price.get("total_price"),
                    currency=row.currency,
                    price_tiers_jsonb=row.price_tiers_jsonb,
                    include_in_estimate=True,
                    sourcing_notes=row.notes,
                    source=LineItemSource.USER,
                    status=LineItemStatus.CONFIRMED,
                )
                db.add(item)
                await db.flush()
                row.line_item_id = item.id
            else:
                item.category_id = row.category_id
                item.name = row.name
                item.description = row.description
                item.specs_jsonb = row.specs_jsonb
                item.qty = row.qty
                item.unit = row.unit
                item.quality_tier = QualityTier(selected_tier)
                item.estimated_unit_price = selected_price.get("unit_price")
                item.estimated_total_price = selected_price.get("total_price")
                item.currency = row.currency
                item.price_tiers_jsonb = row.price_tiers_jsonb
                item.include_in_estimate = True
                item.sourcing_notes = row.notes
                item.status = LineItemStatus.CONFIRMED
            items.append(item)
    else:
        items_result = await db.execute(
            select(ProjectLineItem).where(
                ProjectLineItem.project_id == project.id,
                ProjectLineItem.status == LineItemStatus.CONFIRMED,
                ProjectLineItem.include_in_estimate == True,  # noqa: E712
            )
        )
        items = items_result.scalars().all()

    if not items:
        raise HTTPException(status_code=400, detail="No confirmed line items to publish. Please confirm at least one line item first.")

    intents_created = []
    skipped = 0

    for item in items:
        # Need a category_id to create an Intent
        if not item.category_id:
            skipped += 1
            continue

        # Verify category exists
        cat_result = await db.execute(select(Category).where(Category.id == item.category_id))
        if not cat_result.scalar_one_or_none():
            skipped += 1
            continue

        # Create Intent from line item
        intent = Intent(
            buyer_id=user.id,
            category_id=item.category_id,
            title=f"[Project] {item.name}",
            attrs_jsonb={
                "from_project": True,
                "project_title": project.title,
                "specs": item.specs_jsonb,
                "quality_tier": item.quality_tier.value if item.quality_tier else None,
                "sourcing_notes": item.sourcing_notes,
            },
            qty=int(item.qty),
            unit=item.unit,
            budget_min_minor=int(item.estimated_unit_price * 100) if item.estimated_unit_price else None,
            budget_max_minor=int(item.estimated_total_price * 100) if item.estimated_total_price else None,
            currency=item.currency,
            country=project.country,
            city=project.city,
            lat=project.lat,
            lng=project.lng,
            radius_km=30,
            notes=item.sourcing_notes or item.description,
            status=IntentStatus.ACTIVE,
            project_id=project.id,
            project_line_item_id=item.id,
        )
        db.add(intent)
        await db.flush()

        # Link line item to intent
        item.intent_id = intent.id
        item.status = LineItemStatus.SOURCING

        intents_created.append(intent.id)

        # Trigger supplier matching & notification
        try:
            matches = await find_matching_suppliers(db, intent)
            for m in matches:
                await notify_user(
                    db, user_id=m["owner_user_id"],
                    notification_type="NEW_INTENT_FOR_SUPPLIER",
                    body=f"New project purchase request: {intent.title}",
                )
        except Exception:
            pass  # Non-critical

    # Update project status
    if intents_created:
        project.status = ProjectStatus.SOURCING
        if frozen_version:
            frozen_version.status = ProjectReportVersionStatus.PUBLISHED

    await create_audit_log(
        db, action="PROJECT_PUBLISHED", entity_type="BuyerProject", entity_id=project.id,
        actor_id=user.id, actor_role=user.role.value,
        after_json={"intents_created": [str(i) for i in intents_created], "skipped": skipped},
    )

    await db.commit()
    return PublishResult(
        project_id=project.id,
        published_count=len(intents_created),
        intents_created=intents_created,
        skipped_count=skipped,
    )
