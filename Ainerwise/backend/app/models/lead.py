import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import Base, TimestampMixin, UUIDMixin


LEAD_STATUSES = (
    "new", "ai_analyzing", "need_more_info", "matched",
    "quotation_drafting", "quotation_sent", "negotiating",
    "won", "lost", "converted",
)

SURVEY_TYPES = ("quick", "detailed", "professional")


class Lead(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "leads"

    buyer_company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    buyer_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    contact_name: Mapped[str | None] = mapped_column(String(255))
    contact_email: Mapped[str | None] = mapped_column(String(255))
    contact_phone: Mapped[str | None] = mapped_column(String(50))
    project_type: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    city: Mapped[str | None] = mapped_column(String(100))
    site_info_json: Mapped[dict | None] = mapped_column(JSONB)
    budget_range: Mapped[str | None] = mapped_column(String(100))
    systems_needed_json: Mapped[list | None] = mapped_column(JSONB)
    description: Mapped[str | None] = mapped_column(Text)
    uploaded_files_json: Mapped[list | None] = mapped_column(JSONB)
    ai_analysis_json: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(50), default="new", nullable=False)
    assigned_admin_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    solution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("solutions.id"), nullable=True
    )
    telegram_chat_id: Mapped[str | None] = mapped_column(String(100))
    language: Mapped[str] = mapped_column(String(10), default="en")
    notes: Mapped[str | None] = mapped_column(Text)
    lead_score: Mapped[int | None] = mapped_column(Integer)
    lead_stage: Mapped[str | None] = mapped_column(String(50))  # cold|warm|qualified|phase1_ready|negotiation|contract_pending|won|lost
    desired_intelligence_level: Mapped[int | None] = mapped_column(Integer)  # 1-6
    conversation_json: Mapped[list | None] = mapped_column(JSONB)  # AI Forge chat transcript
    proposal_tiers_json: Mapped[dict | None] = mapped_column(JSONB)  # {budget:{},standard:{},premium:{},future:{}}

    # Acquisition attribution. These fields preserve the first-touch context
    # that brought a visitor into the B2B intake workflow.
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("marketing_campaigns.id"), nullable=True
    )
    source_channel: Mapped[str | None] = mapped_column(String(100))
    source_detail: Mapped[str | None] = mapped_column(String(255))
    utm_source: Mapped[str | None] = mapped_column(String(100))
    utm_medium: Mapped[str | None] = mapped_column(String(100))
    utm_campaign: Mapped[str | None] = mapped_column(String(150))
    utm_content: Mapped[str | None] = mapped_column(String(150))
    landing_page: Mapped[str | None] = mapped_column(String(500))
    referrer: Mapped[str | None] = mapped_column(Text)

    # FI.2.3 — recurring-revenue qualification (LTV CRM). Populated by the
    # recurring-revenue scoring service (FI.6.1) during AI analysis.
    solution_line: Mapped[str | None] = mapped_column(String(50))  # see constants.SOLUTION_LINES
    recurring_revenue_score: Mapped[int | None] = mapped_column(Integer)
    compliance_risk_level: Mapped[str | None] = mapped_column(String(50))  # none|low|medium|high
    consumable_potential: Mapped[str | None] = mapped_column(String(50))  # low|medium|high
    amc_potential: Mapped[str | None] = mapped_column(String(50))  # low|medium|high
    estimated_arr: Mapped[float | None] = mapped_column(Float)
    estimated_ltv: Mapped[float | None] = mapped_column(Float)
    is_multi_site: Mapped[bool] = mapped_column(Boolean, default=False)
    monitoring_points_count: Mapped[int | None] = mapped_column(Integer)

    site_surveys: Mapped[list["SiteSurvey"]] = relationship("SiteSurvey", back_populates="lead")


class SiteSurvey(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "site_surveys"

    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False
    )
    survey_type: Mapped[str] = mapped_column(String(50), default="quick", nullable=False)
    survey_json: Mapped[dict | None] = mapped_column(JSONB)
    uploaded_files_json: Mapped[list | None] = mapped_column(JSONB)
    completeness_score: Mapped[float | None] = mapped_column()
    risk_score: Mapped[float | None] = mapped_column()
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    lead: Mapped[Lead] = relationship("Lead", back_populates="site_surveys")
