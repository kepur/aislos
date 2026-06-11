"""Phase D content modules: SEO pages, document center, publish jobs,
design revisions. Everything AI-generated passes ai_reviews before going out."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin

SEO_PAGE_STATUSES = ("draft", "in_review", "approved", "published", "archived")
DOCUMENT_KINDS = ("contract", "proposal", "acceptance_report", "maintenance_report", "installation_report")
PUBLISH_JOB_STATUSES = ("scheduled", "publishing", "published", "failed", "manual_required", "cancelled")


class SeoPage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "seo_pages"
    __table_args__ = (UniqueConstraint("slug", name="uq_seo_pages_slug"),)

    region_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("regions.id"))
    lang: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    target_keyword: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    meta_description: Mapped[str | None] = mapped_column(String(500))
    content_md: Mapped[str | None] = mapped_column(Text)
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    review_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ai.ai_reviews.id"))
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DocumentTemplate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "document_templates"

    region_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("regions.id"))
    kind: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    lang: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    body_md: Mapped[str] = mapped_column(Text, nullable=False)  # {{variable}} placeholders
    variables_json: Mapped[list | None] = mapped_column(JSONB)  # documented variable names
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class GeneratedDocument(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "generated_documents"
    __table_args__ = (
        Index("ix_generated_documents_subject", "subject_type", "subject_id"),
    )

    template_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("document_templates.id"))
    kind: Mapped[str] = mapped_column(String(50), nullable=False)
    subject_type: Mapped[str | None] = mapped_column(String(50))  # lead|quote|project|ticket
    subject_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body_md: Mapped[str | None] = mapped_column(Text)
    pdf_minio_key: Mapped[str | None] = mapped_column(String(500))
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    review_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ai.ai_reviews.id"))
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False, index=True)


class PublishJob(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "publish_jobs"

    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("marketing_assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    account_ref: Mapped[str | None] = mapped_column(String(255))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    external_post_id: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="scheduled", nullable=False, index=True)
    error_message: Mapped[str | None] = mapped_column(Text)


class DesignRevision(Base, UUIDMixin, TimestampMixin):
    """Design Center: CAD/floor-plan archive per site/project, versioned."""

    __tablename__ = "design_revisions"

    site_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sites.id"), index=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    file_minio_key: Mapped[str] = mapped_column(String(500), nullable=False)
    file_kind: Mapped[str | None] = mapped_column(String(50))  # cad|pdf|image|other
    notes: Mapped[str | None] = mapped_column(Text)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))


SIGNATURE_STATUSES = ("sent", "viewed", "signed", "cancelled", "expired")


class DocumentSignature(Base, UUIDMixin, TimestampMixin):
    """eIDAS simple-electronic-signature audit record: who signed what, when,
    from where, against which exact document hash. Append-only by convention."""

    __tablename__ = "document_signatures"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("generated_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    signer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    signer_email: Mapped[str | None] = mapped_column(String(255))
    token: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(50), default="sent", nullable=False, index=True)
    document_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    signature_minio_key: Mapped[str | None] = mapped_column(String(500))
    signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    signer_ip: Mapped[str | None] = mapped_column(String(64))
    signer_user_agent: Mapped[str | None] = mapped_column(String(500))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
