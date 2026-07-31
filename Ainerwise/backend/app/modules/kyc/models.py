"""KYC & company verification models — document upload, AI analysis, admin review."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin


class CompanyDocument(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "company_documents"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    doc_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    file_url: Mapped[str] = mapped_column(String(512), nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False, index=True)
    reviewer_note: Mapped[str | None] = mapped_column(Text)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class KYCAnalysisResult(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "kyc_analysis_results"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    analyzed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    ai_provider: Mapped[str] = mapped_column(String(50), default="openai", nullable=False)
    ai_model: Mapped[str] = mapped_column(String(100), default="gpt-4o-mini", nullable=False)
    authenticity: Mapped[str] = mapped_column(String(32), default="SUSPICIOUS", nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    overall_risk_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    recommended_action: Mapped[str] = mapped_column(String(32), default="MANUAL_REVIEW", nullable=False)
    tamper_suspected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    photoshop_suspected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    text_photo_consistency: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    extracted_fields: Mapped[dict | None] = mapped_column(JSONB)
    detected_issues: Mapped[list | None] = mapped_column(JSONB)
    concerns: Mapped[list | None] = mapped_column(JSONB)
    raw_result_json: Mapped[dict | None] = mapped_column(JSONB)


class VerificationReview(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "verification_reviews"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(32), default="SUBMITTED", nullable=False, index=True)
    assigned_reviewer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    decision: Mapped[str | None] = mapped_column(String(32))
    decision_reason: Mapped[str | None] = mapped_column(String(500))
    internal_note: Mapped[str | None] = mapped_column(Text)
    user_facing_note: Mapped[str | None] = mapped_column(Text)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decided_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
