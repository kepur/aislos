"""AI Project Analysis service.

Handles the async AI workflow for analyzing buyer projects:
1. File extraction (PDF/TXT/DOCX text, image vision summaries)
2. Information normalization
3. Gap check & missing questions
4. Material/component estimation
5. Quality tier & budget estimation
6. Category mapping to platform categories
7. Structured JSON output & schema validation

Uses the existing ai_service._call_ai for provider dispatch.
Saves audit records to project_ai_runs table.
"""
from __future__ import annotations

import asyncio
import io
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.buyer_project import (
    AIRunStatus,
    BuyerProject,
    LineItemSource,
    LineItemStatus,
    ProjectAIRun,
    ProjectFile,
    ProjectFileStatus,
    ProjectLineItem,
    ProjectReport,
    ProjectReportColumn,
    ProjectReportRow,
    ProjectReportVersion,
    ProjectReportVersionStatus,
    ProjectStatus,
    QualityTier,
)
from app.models.category import Category
from app.models.platform_setting import PlatformSetting
from app.services.ai_service import _call_ai, _extract_json, get_ai_config

logger = logging.getLogger(__name__)

PROMPT_VERSION = "v1"

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

PROJECT_ANALYSIS_PROMPT = """You are an expert procurement analyst for a B2B marketplace platform in the Philippines.

A buyer has a project and needs help generating a structured procurement / materials list.

Analyze the project info and any uploaded documents, then respond ONLY with a valid JSON object matching this schema:

{
  "project_summary": "1-3 sentence summary of the project",
  "project_type": "CONSTRUCTION|SOLAR|TECH_BUILD|RENOVATION|GENERAL",
  "quality_tier": "BUDGET|MID_RANGE|PREMIUM",
  "missing_questions": [
    {
      "key": "unique_key",
      "question": "What is ...?",
      "importance": "HIGH|MEDIUM|LOW"
    }
  ],
  "assumptions": ["assumption text ..."],
  "line_items": [
    {
      "name": "Item name",
      "category_hint": "Category name suggestion",
      "qty": 100,
      "unit": "kg|pcs|m|m2|m3|set|lot|rolls|bags|sheets|boxes",
      "quality_tier": "BUDGET|MID_RANGE|PREMIUM",
      "specs": {"key": "value"},
      "estimated_unit_price": 0,
      "estimated_total_price": 0,
      "price_tiers": {
        "BUDGET": {"unit_price": 0, "total_price": 0, "notes": "Economy brand / local alternative"},
        "MID_RANGE": {"unit_price": 0, "total_price": 0, "notes": "Standard brand"},
        "PREMIUM": {"unit_price": 0, "total_price": 0, "notes": "Premium / imported brand"}
      },
      "currency": "PHP",
      "confidence": 0.5,
      "sourcing_notes": "Note about this item"
    }
  ],
  "estimated_budget": {
    "min": 0,
    "max": 0,
    "currency": "PHP",
    "confidence": 0.5,
    "by_tier": {
      "BUDGET": {"min": 0, "max": 0},
      "MID_RANGE": {"min": 0, "max": 0},
      "PREMIUM": {"min": 0, "max": 0}
    }
  },
  "risk_notes": ["risk text ..."],
  "acceptance_criteria": ["criteria text ..."]
}

Rules:
- Generate realistic material/component lists based on the project type and scale.
- For CONSTRUCTION projects, include items like steel rebar, cement/concrete, aggregates, plumbing pipes (PVC), electrical wiring, fixtures, roofing, paint, etc.
- For SOLAR projects, include solar panels, inverters, cables, mounting brackets, batteries, etc.
- For TECH_BUILD projects, include development boards, sensors, power supplies, enclosures, connectors, etc.
- Estimate quantities based on area, scale, and typical industry standards for the region (Philippines).
- Use PHP as default currency with realistic Philippine market prices.
- IMPORTANT: For each line item, provide PRICE ESTIMATES for ALL THREE quality tiers (BUDGET, MID_RANGE, PREMIUM):
  - BUDGET: cheapest acceptable option, local brands
  - MID_RANGE: standard quality, mainstream brands
  - PREMIUM: best quality, imported/top brands
  - The estimated_unit_price and estimated_total_price should reflect the buyer's selected quality_tier.
- IMPORTANT: Also provide project-level "estimated_budget.by_tier" with total budget ranges for each tier.
- Set confidence between 0.0 and 1.0 based on how certain you are about each estimate.
- If information is missing, add it to missing_questions array rather than guessing wildly.
- Always include at least one assumption explaining your estimation basis.
- Keep line_items focused on materials/components the buyer needs to procure.
- Do NOT include labor costs — only materials and components.
- If the buyer only provided a description without documents, that is fine — estimate based on the description.
- Respond ONLY with valid JSON. No markdown, no explanation outside the JSON."""


async def get_project_ai_config(db: AsyncSession) -> dict[str, Any]:
    """Load AI project analysis config from Admin-managed platform_settings.

    Environment values are accepted only as a local development fallback, never
    as the product configuration path shown to buyers.
    """
    from app.core.config import settings as app_settings

    keys = [
        "ai_enabled",
        "ai_provider",
        "ai_api_key",
        "ai_model",
        "ai_base_url",
        "ai_project_estimation_enabled",
        "ai_project_model",
        "ai_multimodal_enabled",
        "ai_multimodal_model",
        "ai_project_prompt_version",
        "ai_project_max_files",
        "ai_project_max_file_size_mb",
    ]
    result = await db.execute(select(PlatformSetting).where(PlatformSetting.key.in_(keys)))
    settings = {s.key: s.value for s in result.scalars().all()}

    allow_dev_env_fallback = (app_settings.APP_ENV or "development").lower() != "production"

    # Resolve API key: Admin platform_settings first; env only for local development fallback.
    api_key = settings.get("ai_api_key", "")
    if allow_dev_env_fallback and (not api_key or api_key.startswith("sk-test")):
        api_key = app_settings.OPENAI_API_KEY or ""

    provider = settings.get("ai_provider") or (app_settings.AI_PROVIDER if allow_dev_env_fallback else "") or "openai"
    base_url = (settings.get("ai_base_url", "") or "").strip()
    if "api.deepseek.com" in base_url:
        provider = "deepseek"
    elif provider == "deepseek" and not base_url:
        base_url = "https://api.deepseek.com"
    base_url = base_url.rstrip("/")
    model = (
        settings.get("ai_project_model")
        or settings.get("ai_model")
        or (app_settings.AI_MODEL if allow_dev_env_fallback else "")
        or "gpt-4o-mini"
    )
    if provider == "deepseek" and (not model or model == "gpt-4o-mini"):
        model = "deepseek-v4-pro"

    base_cfg = {
        "enabled": settings.get("ai_enabled") == "true",
        "provider": provider,
        "api_key": api_key,
        "model": model,
        "base_url": base_url,
    }
    return {
        **base_cfg,
        "project_estimation_enabled": settings.get("ai_project_estimation_enabled") == "true",
        "multimodal_enabled": settings.get("ai_multimodal_enabled") == "true",
        "multimodal_model": settings.get("ai_multimodal_model", ""),
        "prompt_version": settings.get("ai_project_prompt_version", PROMPT_VERSION),
        "max_files": int(settings.get("ai_project_max_files") or 10),
        "max_file_size_mb": int(settings.get("ai_project_max_file_size_mb") or 10),
    }


# ─── File text extraction ──────────────────────────────────────

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            pages = []
            for page in pdf.pages[:50]:  # limit pages
                text = page.extract_text()
                if text:
                    pages.append(text)
            return "\n\n".join(pages)[:20000]
    except ImportError:
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            pages = []
            for page in reader.pages[:50]:
                text = page.extract_text()
                if text:
                    pages.append(text)
            return "\n\n".join(pages)[:20000]
        except ImportError:
            return "[PDF extraction unavailable — install pdfplumber or PyPDF2]"
    except Exception as e:
        return f"[PDF extraction error: {e}]"


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from a DOCX file."""
    try:
        from docx import Document
        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)[:20000]
    except ImportError:
        return "[DOCX extraction unavailable — install python-docx]"
    except Exception as e:
        return f"[DOCX extraction error: {e}]"


def extract_text_from_txt(file_path: str) -> str:
    """Read plain text file."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()[:20000]
    except Exception as e:
        return f"[TXT read error: {e}]"


async def extract_file_text(file_url: str, content_type: str, upload_dir: str) -> tuple[str, str | None]:
    """Extract text from an uploaded file. Returns (text, error_or_none)."""
    # Derive local path from URL
    filename = file_url.rsplit("/", 1)[-1]
    file_path = os.path.join(upload_dir, filename)

    if not os.path.exists(file_path):
        return "", f"File not found on server: {filename}"

    try:
        if content_type == "application/pdf":
            text = extract_text_from_pdf(file_path)
        elif content_type in ("text/plain",):
            text = extract_text_from_txt(file_path)
        elif content_type in (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        ):
            text = extract_text_from_docx(file_path)
        elif content_type.startswith("image/"):
            # Images handled separately via vision — return empty text
            return "", None
        else:
            return "", f"Unsupported content type for extraction: {content_type}"

        if text and not text.startswith("["):
            return text, None
        return text, text if text.startswith("[") else None
    except Exception as e:
        return "", str(e)


# ─── AI Analysis orchestration ─────────────────────────────────

def _build_analysis_prompt(project: BuyerProject, files_text: list[dict]) -> str:
    """Build the user message combining project info and extracted file content."""
    parts = [
        f"Project Title: {project.title}",
        f"Project Type: {project.project_type.value if project.project_type else 'GENERAL'}",
        f"Location: {project.city or ''}, {project.country or ''}",
    ]
    if project.area_value:
        parts.append(f"Area/Scale: {project.area_value} {project.area_unit or 'sqm'}")
    if project.budget_min or project.budget_max:
        parts.append(f"Budget Range: {project.budget_min or 0} - {project.budget_max or 0} {project.currency}")
    if project.quality_preference:
        parts.append(f"Quality Preference: {project.quality_preference.value}")
    if project.description:
        parts.append(f"Description: {project.description}")

    user_msg = "\n".join(parts)

    if files_text:
        user_msg += "\n\n--- UPLOADED DOCUMENTS ---\n"
        for ft in files_text:
            user_msg += f"\n[File: {ft['name']} ({ft['type']})]\n{ft['text'][:5000]}\n"

    return user_msg


def _validate_ai_output(data: dict) -> tuple[bool, str]:
    """Validate AI structured output has required fields."""
    required = ["project_summary", "line_items"]
    for key in required:
        if key not in data:
            return False, f"Missing required field: {key}"
    if not isinstance(data.get("line_items"), list):
        return False, "line_items must be a list"
    if len(data["line_items"]) == 0:
        return False, "line_items is empty"
    for i, item in enumerate(data["line_items"]):
        if not item.get("name"):
            return False, f"line_items[{i}].name is required"
    return True, ""


def _report_totals(rows: list[ProjectReportRow]) -> dict:
    totals = {"BUDGET": 0.0, "MID_RANGE": 0.0, "PREMIUM": 0.0, "selected_total": 0.0, "included_rows": 0}
    for row in rows:
        if not row.include_in_total or not row.selected_for_purchase:
            continue
        totals["included_rows"] += 1
        tiers = row.price_tiers_jsonb or {}
        for tier in ("BUDGET", "MID_RANGE", "PREMIUM"):
            totals[tier] += float((tiers.get(tier) or {}).get("total_price") or 0)
        selected = tiers.get(row.selected_tier or "MID_RANGE") or {}
        totals["selected_total"] += float(selected.get("total_price") or 0)
    return {k: round(v, 2) if isinstance(v, float) else v for k, v in totals.items()}


async def _sync_report_from_line_items(db: AsyncSession, project: BuyerProject, ai_run_id: uuid.UUID | None) -> None:
    report_result = await db.execute(
        select(ProjectReport)
        .where(ProjectReport.project_id == project.id)
        .order_by(ProjectReport.updated_at.desc(), ProjectReport.created_at.desc())
    )
    reports = report_result.scalars().all()
    report = next((item for item in reports if item.current_version_id or item.frozen_version_id), None)
    if not report and reports:
        report = reports[0]
    if not report:
        report = ProjectReport(project_id=project.id)
        db.add(report)
        await db.flush()
    max_version = (await db.execute(
        select(func.coalesce(func.max(ProjectReportVersion.version_number), 0))
        .where(ProjectReportVersion.report_id == report.id)
    )).scalar() or 0
    version = ProjectReportVersion(
        report_id=report.id,
        project_id=project.id,
        version_number=int(max_version) + 1,
        status=ProjectReportVersionStatus.ESTIMATED,
        source="AI_ANALYSIS",
        title=f"{project.title} report",
        summary_jsonb={"ai_run_id": str(ai_run_id) if ai_run_id else None, "summary": project.ai_summary},
    )
    db.add(version)
    await db.flush()
    for idx, (key, label, data_type, editable, system) in enumerate(REPORT_BASE_COLUMNS):
        db.add(ProjectReportColumn(
            report_version_id=version.id,
            key=key,
            label=label,
            data_type=data_type,
            sort_order=idx,
            editable=editable,
            system=system,
        ))
    items = (await db.execute(
        select(ProjectLineItem)
        .where(ProjectLineItem.project_id == project.id, ProjectLineItem.status != LineItemStatus.REMOVED)
        .order_by(ProjectLineItem.created_at)
    )).scalars().all()
    rows = []
    for idx, item in enumerate(items):
        selected_tier = item.quality_tier.value if item.quality_tier else "MID_RANGE"
        row = ProjectReportRow(
            report_version_id=version.id,
            project_id=project.id,
            line_item_id=item.id,
            category_id=item.category_id,
            name=item.name,
            description=item.description,
            specs_jsonb=item.specs_jsonb,
            qty=item.qty,
            unit=item.unit,
            currency=item.currency or project.currency,
            quality_tier=item.quality_tier or QualityTier.MID_RANGE,
            selected_tier=selected_tier,
            include_in_total=item.include_in_estimate,
            selected_for_purchase=True,
            price_tiers_jsonb=item.price_tiers_jsonb,
            custom_values_jsonb={},
            match_status="MATCHED" if item.category_id else "UNMATCHED",
            samples_jsonb=[],
            price_source="AI_ESTIMATE",
            notes=item.sourcing_notes,
            sort_order=idx,
        )
        rows.append(row)
        db.add(row)
    await db.flush()
    version.totals_jsonb = _report_totals(rows)
    report.current_version_id = version.id
    report.updated_at = datetime.now(timezone.utc)


async def _map_category_hint(db: AsyncSession, hint: str) -> uuid.UUID | None:
    """Try to map a category_hint to an existing platform category."""
    if not hint:
        return None
    hint_lower = hint.lower()
    result = await db.execute(select(Category))
    categories = result.scalars().all()
    for cat in categories:
        if cat.name.lower() in hint_lower or hint_lower in cat.name.lower():
            return cat.id
    # Fuzzy: check if any word from hint matches category name
    hint_words = set(hint_lower.split())
    for cat in categories:
        cat_words = set(cat.name.lower().split())
        if hint_words & cat_words:
            return cat.id
    return None


async def run_project_analysis(project_id: uuid.UUID) -> None:
    """Background task: Run AI analysis on a buyer project.

    This function creates its own DB session since it runs as a background task.
    """
    async with async_session() as db:
        try:
            # Load project
            result = await db.execute(select(BuyerProject).where(BuyerProject.id == project_id))
            project = result.scalar_one_or_none()
            if not project:
                logger.error(f"Project {project_id} not found for analysis")
                return

            # Load AI config
            cfg = await get_project_ai_config(db)

            # Find the pending AI run first, so we can record errors on it
            run_result = await db.execute(
                select(ProjectAIRun)
                .where(ProjectAIRun.project_id == project_id, ProjectAIRun.status == AIRunStatus.PENDING)
                .order_by(ProjectAIRun.created_at.desc())
                .limit(1)
            )
            ai_run = run_result.scalar_one_or_none()
            if not ai_run:
                logger.error(f"No pending AI run found for project {project_id}")
                return

            if not cfg["enabled"] or not cfg["project_estimation_enabled"]:
                ai_run.status = AIRunStatus.FAILED
                ai_run.error_message = "AI Project Forge is disabled. Please enable it in Admin → Integrations → AI Provider."
                ai_run.finished_at = datetime.now(timezone.utc)
                await db.commit()
                return
            if not cfg["api_key"]:
                ai_run.status = AIRunStatus.FAILED
                ai_run.error_message = "AI provider is not configured. Please configure Admin → Integrations → AI Provider and enable AI Project Forge."
                ai_run.finished_at = datetime.now(timezone.utc)
                await db.commit()
                return

            # Mark as running
            ai_run.status = AIRunStatus.RUNNING
            ai_run.started_at = datetime.now(timezone.utc)
            ai_run.provider = cfg["provider"]
            ai_run.model = cfg["model"]
            ai_run.prompt_version = cfg.get("prompt_version", PROMPT_VERSION)
            project.status = ProjectStatus.ANALYZING
            await db.commit()

            # Load and extract files
            files_result = await db.execute(
                select(ProjectFile).where(ProjectFile.project_id == project_id)
            )
            files = files_result.scalars().all()

            from app.core.config import settings
            files_text = []
            for pf in files:
                if pf.content_type.startswith("image/"):
                    continue  # Skip images for P0, handled by multimodal in P1
                text, error = await extract_file_text(pf.url, pf.content_type, settings.UPLOAD_DIR)
                if text:
                    pf.extracted_text = text
                    pf.status = ProjectFileStatus.EXTRACTED
                    files_text.append({"name": pf.file_name, "type": pf.content_type, "text": text})
                elif error:
                    pf.error_message = error
                    pf.status = ProjectFileStatus.FAILED
                else:
                    pf.status = ProjectFileStatus.EXTRACTED  # Empty but no error (e.g. image)
            await db.commit()

            # Build prompt
            user_message = _build_analysis_prompt(project, files_text)

            # Save input snapshot
            ai_run.input_snapshot_jsonb = {
                "title": project.title,
                "project_type": project.project_type.value if project.project_type else "GENERAL",
                "country": project.country,
                "city": project.city,
                "area_value": project.area_value,
                "area_unit": project.area_unit,
                "budget_min": project.budget_min,
                "budget_max": project.budget_max,
                "currency": project.currency,
                "quality_preference": project.quality_preference.value if project.quality_preference else "NOT_SURE",
                "description": project.description,
                "files_count": len(files),
                "files_text_count": len(files_text),
            }
            await db.commit()

            # Call AI
            ai_cfg = {
                "provider": cfg["provider"],
                "api_key": cfg["api_key"],
                "model": cfg["model"],
                "base_url": cfg.get("base_url", ""),
            }
            raw_output = await _call_ai(
                ai_cfg,
                [
                    {"role": "system", "content": PROJECT_ANALYSIS_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=4000,
                json_mode=True,
            )

            ai_run.raw_output = raw_output

            # Parse output
            parsed = _extract_json(raw_output)
            if not parsed:
                ai_run.status = AIRunStatus.FAILED
                ai_run.error_message = "AI returned non-JSON output"
                ai_run.finished_at = datetime.now(timezone.utc)
                await db.commit()
                return

            # Validate output
            valid, error = _validate_ai_output(parsed)
            if not valid:
                ai_run.status = AIRunStatus.FAILED
                ai_run.error_message = f"AI output validation failed: {error}"
                ai_run.structured_output_jsonb = parsed
                ai_run.finished_at = datetime.now(timezone.utc)
                await db.commit()
                return

            # Save structured output
            ai_run.structured_output_jsonb = parsed
            ai_run.status = AIRunStatus.SUCCESS
            ai_run.finished_at = datetime.now(timezone.utc)

            # Update project with AI results
            project.ai_summary = parsed.get("project_summary", "")
            project.missing_questions_jsonb = parsed.get("missing_questions", [])
            project.assumptions_jsonb = parsed.get("assumptions", [])
            project.risk_notes_jsonb = parsed.get("risk_notes", [])
            project.acceptance_criteria_jsonb = parsed.get("acceptance_criteria", [])
            project.estimated_budget_jsonb = parsed.get("estimated_budget")
            project.status = ProjectStatus.AI_ANALYZED

            # Create line items from AI output
            for item_data in parsed.get("line_items", []):
                category_id = await _map_category_hint(db, item_data.get("category_hint", ""))
                quality_str = item_data.get("quality_tier", "MID_RANGE")
                try:
                    quality = QualityTier(quality_str)
                except ValueError:
                    quality = QualityTier.MID_RANGE

                line_item = ProjectLineItem(
                    project_id=project_id,
                    ai_run_id=ai_run.id,
                    category_id=category_id,
                    name=item_data.get("name", "Unknown Item"),
                    description=item_data.get("sourcing_notes", ""),
                    specs_jsonb=item_data.get("specs"),
                    qty=float(item_data.get("qty", 1)),
                    unit=item_data.get("unit", "pcs"),
                    quality_tier=quality,
                    estimated_unit_price=item_data.get("estimated_unit_price"),
                    estimated_total_price=item_data.get("estimated_total_price"),
                    price_tiers_jsonb=item_data.get("price_tiers"),
                    currency=item_data.get("currency", project.currency),
                    confidence=item_data.get("confidence"),
                    sourcing_notes=item_data.get("sourcing_notes"),
                    category_hint=item_data.get("category_hint"),
                    source=LineItemSource.AI,
                    status=LineItemStatus.DRAFT,
                )
                db.add(line_item)

            await db.flush()
            await _sync_report_from_line_items(db, project, ai_run.id)
            await db.commit()
            logger.info(f"AI analysis completed for project {project_id}, {len(parsed.get('line_items', []))} line items created")

        except Exception as e:
            logger.exception(f"AI analysis failed for project {project_id}: {e}")
            # Try to update the run status
            try:
                async with async_session() as err_db:
                    run_result = await err_db.execute(
                        select(ProjectAIRun)
                        .where(ProjectAIRun.project_id == project_id, ProjectAIRun.status == AIRunStatus.RUNNING)
                        .order_by(ProjectAIRun.created_at.desc())
                        .limit(1)
                    )
                    ai_run = run_result.scalar_one_or_none()
                    if ai_run:
                        ai_run.status = AIRunStatus.FAILED
                        ai_run.error_message = str(e)[:2000]
                        ai_run.finished_at = datetime.now(timezone.utc)
                        await err_db.commit()

                    proj_result = await err_db.execute(select(BuyerProject).where(BuyerProject.id == project_id))
                    proj = proj_result.scalar_one_or_none()
                    if proj and proj.status == ProjectStatus.ANALYZING:
                        proj.status = ProjectStatus.COLLECTING_INFO
                        await err_db.commit()
            except Exception:
                logger.exception("Failed to update error status")
