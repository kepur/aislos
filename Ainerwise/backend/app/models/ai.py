import uuid
from datetime import datetime
from decimal import Decimal

from pgvector.sqlalchemy import Vector
from sqlalchemy import Computed, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base, TimestampMixin, UUIDMixin

# Must match the embedding model in use; changing it requires re-embedding all chunks.
EMBEDDING_DIM = 1536


class KnowledgeDocument(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "knowledge_documents"
    __table_args__ = {"schema": "ai"}

    region_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("regions.id"))
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    lang: Mapped[str | None] = mapped_column(String(10))
    minio_key: Mapped[str | None] = mapped_column(String(500))
    checksum: Mapped[str | None] = mapped_column(String(64))
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), index=True
    )
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False, index=True)
    meta_json: Mapped[dict | None] = mapped_column(JSONB)


class DocumentChunk(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_document_chunks_doc_idx"),
        Index(
            "ix_ai_document_chunks_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index("ix_ai_document_chunks_tsv", "tsv", postgresql_using="gin"),
        {"schema": "ai"},
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai.knowledge_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM))
    tsv = mapped_column(TSVECTOR, Computed("to_tsvector('simple', content)", persisted=True))
    meta_json: Mapped[dict | None] = mapped_column(JSONB)


class Conversation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "conversations"
    __table_args__ = {"schema": "ai"}

    region_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("regions.id"))
    channel: Mapped[str] = mapped_column(String(50), default="web", nullable=False)
    visitor_id: Mapped[str | None] = mapped_column(String(100), index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    lead_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("leads.id"), index=True)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    lang: Mapped[str | None] = mapped_column(String(10))
    meta_json: Mapped[dict | None] = mapped_column(JSONB)


class ConversationMessage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "messages"
    __table_args__ = {"schema": "ai"}

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai.conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    tool_calls_json: Mapped[dict | None] = mapped_column(JSONB)
    tokens: Mapped[int | None] = mapped_column(Integer)


class AgentRun(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agent_runs"
    __table_args__ = {"schema": "ai"}

    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai.conversations.id")
    )
    # Stable identity is logged directly; workflow names are capabilities and
    # may be shared by more than one Agent.
    agent_slug: Mapped[str | None] = mapped_column(String(100), index=True)
    workflow: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    input_json: Mapped[dict | None] = mapped_column(JSONB)
    output_json: Mapped[dict | None] = mapped_column(JSONB)
    tool_trace_json: Mapped[dict | None] = mapped_column(JSONB)
    model_name: Mapped[str | None] = mapped_column(String(100))
    tokens_in: Mapped[int | None] = mapped_column(Integer)
    tokens_out: Mapped[int | None] = mapped_column(Integer)
    cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(50), default="running", nullable=False, index=True)
    error_message: Mapped[str | None] = mapped_column(Text)


class AIMemory(Base, UUIDMixin, TimestampMixin):
    """Long-lived facts about a subject (lead/company/contact/partner),
    extracted from conversations and injected into future prompts."""

    __tablename__ = "memories"
    __table_args__ = (
        Index("ix_ai_memories_subject", "subject_type", "subject_id"),
        {"schema": "ai"},
    )

    region_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("regions.id"))
    subject_type: Mapped[str] = mapped_column(String(50), nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    kind: Mapped[str] = mapped_column(String(50), nullable=False)  # preference|fact|constraint|plan
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai.conversations.id")
    )
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False, index=True)


class AIReview(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ai_reviews"
    __table_args__ = {"schema": "ai"}

    run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ai.agent_runs.id"))
    target_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    target_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    draft_json: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(50), default="preliminary", nullable=False, index=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_notes: Mapped[str | None] = mapped_column(Text)
