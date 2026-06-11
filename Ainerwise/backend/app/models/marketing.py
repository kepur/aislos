import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin


class MarketingCampaign(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "marketing_campaigns"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    objective: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)
    landing_path: Mapped[str | None] = mapped_column(String(500))
    utm_source: Mapped[str | None] = mapped_column(String(100))
    utm_medium: Mapped[str | None] = mapped_column(String(100))
    utm_campaign: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    audience_json: Mapped[dict | None] = mapped_column(JSONB)
    offer_json: Mapped[dict | None] = mapped_column(JSONB)
    content_json: Mapped[dict | None] = mapped_column(JSONB)
    budget: Mapped[float | None] = mapped_column(Float)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )


class MarketingContact(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "marketing_contacts"

    company_name: Mapped[str | None] = mapped_column(String(255))
    contact_name: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    phone: Mapped[str | None] = mapped_column(String(100))
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    segment: Mapped[str | None] = mapped_column(String(100), index=True)
    source: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), default="prospect", nullable=False, index=True)
    consent_status: Mapped[str] = mapped_column(
        String(50), default="unknown", nullable=False
    )
    tags_json: Mapped[list | None] = mapped_column(JSONB)
    notes: Mapped[str | None] = mapped_column(Text)
    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leads.id"), nullable=True
    )
    last_contacted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_follow_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class MarketingActivity(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "marketing_activities"

    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("marketing_campaigns.id"), nullable=True
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("marketing_contacts.id"), nullable=True
    )
    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leads.id"), nullable=True, index=True
    )
    inquiry_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inquiries.id"), nullable=True, index=True
    )
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    direction: Mapped[str] = mapped_column(String(20), default="outbound", nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="pending_approval", nullable=False, index=True
    )
    subject: Mapped[str | None] = mapped_column(String(500))
    content: Mapped[str | None] = mapped_column(Text)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    result_json: Mapped[dict | None] = mapped_column(JSONB)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )


class MarketingAsset(Base, UUIDMixin, TimestampMixin):
    """AI-generated marketing content. ai_generated flows through to publish
    metadata (EU AI Act transparency); everything passes ai_reviews first."""

    __tablename__ = "marketing_assets"
    __table_args__ = (
        UniqueConstraint(
            "integration_client_id",
            "external_asset_ref",
            name="uq_marketing_assets_client_external_ref",
        ),
    )

    region_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regions.id"), nullable=True
    )
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("marketing_campaigns.id"), nullable=True
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=True
    )
    case_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id"), nullable=True
    )
    brief_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("marketing_creative_brief_versions.id"), nullable=True, index=True
    )
    media_request_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("marketing_media_requests.id"), nullable=True, index=True
    )
    integration_client_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("marketing_integration_clients.id"), nullable=True, index=True
    )
    external_asset_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    variant_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(nullable=True)
    width: Mapped[int | None] = mapped_column(nullable=True)
    height: Mapped[int | None] = mapped_column(nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(nullable=True)
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    kind: Mapped[str] = mapped_column(String(50), nullable=False)  # post|article|image|video_script|email|landing_page
    channel: Mapped[str | None] = mapped_column(String(50))  # linkedin|facebook|instagram|tiktok|youtube|gbp|x|blog|email
    lang: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    title: Mapped[str | None] = mapped_column(String(500))
    content: Mapped[str | None] = mapped_column(Text)
    media_minio_key: Mapped[str | None] = mapped_column(String(500))
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    review_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai.ai_reviews.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False, index=True)
    meta_json: Mapped[dict | None] = mapped_column(JSONB)


class MarketingMediaUpload(Base, UUIDMixin, TimestampMixin):
    """Staging upload slot for external media integration (presigned PUT target)."""

    __tablename__ = "marketing_media_uploads"

    media_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("marketing_media_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    integration_client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("marketing_integration_clients.id"),
        nullable=False,
    )
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(nullable=False)
    sha256_expected: Mapped[str] = mapped_column(String(64), nullable=False)
    object_key: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    bucket: Mapped[str] = mapped_column(String(100), nullable=False, default="marketing-assets")
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


BRIEF_STATUSES = ("draft", "in_review", "approved", "rejected", "retired")
MEDIA_REQUEST_STATUSES = (
    "available",
    "claimed",
    "in_progress",
    "submitted",
    "completed",
    "failed",
    "cancelled",
)
DELIVERABLE_MEDIA_TYPES = ("image", "video", "audio", "document", "other")
MARKETING_ASSETS_BUCKET = "marketing-assets"
UPLOAD_EXPIRE_MINUTES = 15
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
ALLOWED_UPLOAD_MIMES = frozenset({
    "image/png",
    "image/jpeg",
    "image/webp",
    "video/mp4",
    "audio/mpeg",
    "application/pdf",
})
ALLOWED_UPLOAD_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".webp", ".mp4", ".mp3", ".pdf"})


class MarketingCreativeBrief(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "marketing_creative_briefs"

    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("marketing_campaigns.id"), nullable=True, index=True
    )
    region_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regions.id"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    objective: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False, index=True)
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("marketing_creative_brief_versions.id", use_alter=True, name="fk_brief_current_version"),
        nullable=True,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MarketingCreativeBriefVersion(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "marketing_creative_brief_versions"
    __table_args__ = (
        UniqueConstraint("brief_id", "version", name="uq_marketing_brief_versions_brief_version"),
    )

    brief_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("marketing_creative_briefs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False, index=True)
    copy_json: Mapped[dict | None] = mapped_column(JSONB)
    audience_json: Mapped[dict | None] = mapped_column(JSONB)
    brand_constraints_json: Mapped[dict | None] = mapped_column(JSONB)
    channel_specs_json: Mapped[dict | None] = mapped_column(JSONB)
    deliverables_json: Mapped[list | None] = mapped_column(JSONB)
    source_refs_json: Mapped[dict | None] = mapped_column(JSONB)
    compliance_json: Mapped[dict | None] = mapped_column(JSONB)
    content_hash: Mapped[str | None] = mapped_column(String(64))
    review_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai.ai_reviews.id"), nullable=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )


INTEGRATION_CLIENT_STATUSES = ("active", "suspended", "revoked")
INTEGRATION_SCOPES = (
    "briefs:read",
    "briefs:claim",
    "briefs:progress",
    "assets:upload",
    "assets:submit",
)
CLAIM_LEASE_MINUTES = 30


class MarketingIntegrationClient(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "marketing_integration_clients"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    secret_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False, index=True)
    scopes_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    allowed_region_ids_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )


class MarketingIntegrationIdempotency(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "marketing_integration_idempotency"
    __table_args__ = (
        UniqueConstraint(
            "client_id",
            "operation",
            "idempotency_key",
            name="uq_marketing_integration_idempotency",
        ),
    )

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("marketing_integration_clients.id", ondelete="CASCADE"),
        nullable=False,
    )
    operation: Mapped[str] = mapped_column(String(50), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(200), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    response_status: Mapped[int] = mapped_column(nullable=False)
    response_json: Mapped[dict] = mapped_column(JSONB, nullable=False)


class MarketingMediaRequest(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "marketing_media_requests"
    __table_args__ = (
        UniqueConstraint(
            "brief_version_id",
            "deliverable_key",
            name="uq_marketing_media_requests_version_deliverable",
        ),
    )

    brief_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("marketing_creative_brief_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    deliverable_key: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="available", nullable=False, index=True)
    claimed_by_client_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("marketing_integration_clients.id"),
        nullable=True,
    )
    claim_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    external_job_ref: Mapped[str | None] = mapped_column(String(255))
    progress_percent: Mapped[int | None] = mapped_column(nullable=True)
    progress_message: Mapped[str | None] = mapped_column(Text)
    failure_code: Mapped[str | None] = mapped_column(String(100))
    failure_message: Mapped[str | None] = mapped_column(Text)
    submitted_asset_count: Mapped[int] = mapped_column(default=0, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RegionMarketingProfile(Base, UUIDMixin, TimestampMixin):
    """Per-country messaging: tone, selling points, compliance phrasing."""

    __tablename__ = "region_marketing_profiles"

    region_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regions.id"), nullable=False, unique=True
    )
    tone_json: Mapped[dict | None] = mapped_column(JSONB)
    emphasis_json: Mapped[list | None] = mapped_column(JSONB)
    compliance_notes: Mapped[str | None] = mapped_column(Text)
