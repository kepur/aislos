import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class KYCAuthenticity(str, enum.Enum):
    AUTHENTIC = "AUTHENTIC"
    SUSPICIOUS = "SUSPICIOUS"
    FAKE = "FAKE"


class KYCRecommendedAction(str, enum.Enum):
    APPROVE = "APPROVE"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    REJECT = "REJECT"


class KYCAnalysisResult(Base):
    __tablename__ = "kyc_analysis_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    analyzed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    ai_provider: Mapped[str] = mapped_column(String(50), default="openai")
    ai_model: Mapped[str] = mapped_column(String(100), default="gpt-4o-mini")
    authenticity: Mapped[KYCAuthenticity] = mapped_column(
        Enum(KYCAuthenticity, name="kyc_authenticity", create_type=False),
        default=KYCAuthenticity.SUSPICIOUS,
    )
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    overall_risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    recommended_action: Mapped[KYCRecommendedAction] = mapped_column(
        Enum(KYCRecommendedAction, name="kyc_recommended_action", create_type=False),
        default=KYCRecommendedAction.MANUAL_REVIEW,
    )
    tamper_suspected: Mapped[bool] = mapped_column(default=False)
    photoshop_suspected: Mapped[bool] = mapped_column(default=False)
    text_photo_consistency: Mapped[bool] = mapped_column(default=False)
    extracted_fields: Mapped[dict | None] = mapped_column(JSONB)
    detected_issues: Mapped[list | None] = mapped_column(JSONB)
    concerns: Mapped[list | None] = mapped_column(JSONB)
    raw_result_json: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
