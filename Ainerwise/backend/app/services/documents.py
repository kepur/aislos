"""Document Center: template rendering ({{variable}} substitution), optional
AI draft via orchestrator, simple PDF output to MinIO. AI-generated documents
go through ai_reviews before they can be finalized."""
from __future__ import annotations

import io
import re
import uuid

from app.core.config import settings
from app.services.knowledge import get_minio_client

DOCUMENTS_BUCKET = "documents"
_VAR_RE = re.compile(r"\{\{\s*([\w.]+)\s*\}\}")


def render_template(body_md: str, variables: dict) -> tuple[str, list[str]]:
    """Substitute {{var}} placeholders; returns (rendered, missing_vars)."""
    missing: list[str] = []

    def _sub(match: re.Match) -> str:
        key = match.group(1)
        value = variables.get(key)
        if value is None:
            missing.append(key)
            return f"[{key}]"
        return str(value)

    return _VAR_RE.sub(_sub, body_md), missing


def markdown_to_pdf_bytes(title: str, body_md: str) -> bytes:
    """Minimal markdown-ish PDF (headings + paragraphs) via reportlab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm, bottomMargin=18 * mm,
        title=title,
    )
    styles = getSampleStyleSheet()
    story = [Paragraph(title, styles["Title"]), Spacer(1, 6 * mm)]
    for raw_line in body_md.split("\n"):
        line = raw_line.strip()
        if not line:
            story.append(Spacer(1, 3 * mm))
        elif line.startswith("## "):
            story.append(Paragraph(line[3:], styles["Heading2"]))
        elif line.startswith("# "):
            story.append(Paragraph(line[2:], styles["Heading1"]))
        elif line.startswith(("- ", "* ")):
            story.append(Paragraph(f"• {line[2:]}", styles["Normal"]))
        else:
            story.append(Paragraph(line, styles["Normal"]))
    doc.build(story)
    return buffer.getvalue()


def store_pdf(title: str, body_md: str) -> str:
    client = get_minio_client()
    if not client.bucket_exists(DOCUMENTS_BUCKET):
        client.make_bucket(DOCUMENTS_BUCKET)
    data = markdown_to_pdf_bytes(title, body_md)
    object_name = f"generated/{uuid.uuid4()}.pdf"
    client.put_object(DOCUMENTS_BUCKET, object_name, io.BytesIO(data), len(data), content_type="application/pdf")
    return object_name


def pdf_download_url(object_name: str) -> str:
    from datetime import timedelta

    client = get_minio_client()
    return client.presigned_get_object(DOCUMENTS_BUCKET, object_name, expires=timedelta(hours=1))
