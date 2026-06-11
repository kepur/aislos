"""Phase A foundation: ai/channels schemas, pgvector, outbox columns

Revision ID: 011
Revises: 010
Create Date: 2026-06-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = 1536


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE SCHEMA IF NOT EXISTS ai")
    op.execute("CREATE SCHEMA IF NOT EXISTS channels")

    # ── ai schema ──────────────────────────────────────────────
    op.create_table(
        "knowledge_documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("region_id", UUID(as_uuid=True), nullable=True),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("lang", sa.String(10), nullable=True),
        sa.Column("minio_key", sa.String(500), nullable=True),
        sa.Column("checksum", sa.String(64), nullable=True),
        sa.Column("product_id", UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("meta_json", JSONB, nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["region_id"], ["public.regions.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["public.products.id"]),
        schema="ai",
    )
    op.create_index("ix_ai_knowledge_documents_status", "knowledge_documents", ["status"], schema="ai")
    op.create_index("ix_ai_knowledge_documents_product_id", "knowledge_documents", ["product_id"], schema="ai")

    op.create_table(
        "document_chunks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=True),
        sa.Column("tsv", TSVECTOR, sa.Computed("to_tsvector('simple', content)", persisted=True), nullable=True),
        sa.Column("meta_json", JSONB, nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["document_id"], ["ai.knowledge_documents.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_document_chunks_doc_idx"),
        schema="ai",
    )
    op.create_index("ix_ai_document_chunks_document_id", "document_chunks", ["document_id"], schema="ai")
    op.execute(
        "CREATE INDEX ix_ai_document_chunks_embedding ON ai.document_chunks "
        "USING hnsw (embedding vector_cosine_ops)"
    )
    op.execute("CREATE INDEX ix_ai_document_chunks_tsv ON ai.document_chunks USING gin (tsv)")

    op.create_table(
        "conversations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("region_id", UUID(as_uuid=True), nullable=True),
        sa.Column("channel", sa.String(50), nullable=False, server_default="web"),
        sa.Column("visitor_id", sa.String(100), nullable=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=True),
        sa.Column("lead_id", UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("lang", sa.String(10), nullable=True),
        sa.Column("meta_json", JSONB, nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["region_id"], ["public.regions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["public.users.id"]),
        sa.ForeignKeyConstraint(["lead_id"], ["public.leads.id"]),
        schema="ai",
    )
    op.create_index("ix_ai_conversations_visitor_id", "conversations", ["visitor_id"], schema="ai")
    op.create_index("ix_ai_conversations_lead_id", "conversations", ["lead_id"], schema="ai")

    op.create_table(
        "messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("conversation_id", UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=True),
        sa.Column("tool_calls_json", JSONB, nullable=True),
        sa.Column("tokens", sa.Integer, nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["conversation_id"], ["ai.conversations.id"], ondelete="CASCADE"),
        schema="ai",
    )
    op.create_index("ix_ai_messages_conversation_id", "messages", ["conversation_id"], schema="ai")

    op.create_table(
        "agent_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("conversation_id", UUID(as_uuid=True), nullable=True),
        sa.Column("workflow", sa.String(100), nullable=False),
        sa.Column("input_json", JSONB, nullable=True),
        sa.Column("output_json", JSONB, nullable=True),
        sa.Column("tool_trace_json", JSONB, nullable=True),
        sa.Column("model_name", sa.String(100), nullable=True),
        sa.Column("tokens_in", sa.Integer, nullable=True),
        sa.Column("tokens_out", sa.Integer, nullable=True),
        sa.Column("cost_usd", sa.Numeric(10, 4), nullable=True),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="running"),
        sa.Column("error_message", sa.Text, nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["conversation_id"], ["ai.conversations.id"]),
        schema="ai",
    )
    op.create_index("ix_ai_agent_runs_workflow", "agent_runs", ["workflow"], schema="ai")
    op.create_index("ix_ai_agent_runs_status", "agent_runs", ["status"], schema="ai")

    op.create_table(
        "ai_reviews",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", UUID(as_uuid=True), nullable=True),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("target_id", UUID(as_uuid=True), nullable=True),
        sa.Column("draft_json", JSONB, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="preliminary"),
        sa.Column("reviewed_by", UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_notes", sa.Text, nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["run_id"], ["ai.agent_runs.id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["public.users.id"]),
        schema="ai",
    )
    op.create_index("ix_ai_ai_reviews_target_type", "ai_reviews", ["target_type"], schema="ai")
    op.create_index("ix_ai_ai_reviews_status", "ai_reviews", ["status"], schema="ai")

    # ── channels schema ────────────────────────────────────────
    op.create_table(
        "channel_accounts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("region_id", UUID(as_uuid=True), nullable=True),
        sa.Column("channel", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("credentials_json", JSONB, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("meta_json", JSONB, nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["region_id"], ["public.regions.id"]),
        schema="channels",
    )
    op.create_index("ix_channels_channel_accounts_channel", "channel_accounts", ["channel"], schema="channels")

    op.create_table(
        "channel_threads",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("account_id", UUID(as_uuid=True), nullable=False),
        sa.Column("external_thread_id", sa.String(255), nullable=False),
        sa.Column("conversation_id", UUID(as_uuid=True), nullable=True),
        sa.Column("contact_name", sa.String(255), nullable=True),
        sa.Column("meta_json", JSONB, nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["account_id"], ["channels.channel_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["conversation_id"], ["ai.conversations.id"]),
        sa.UniqueConstraint("account_id", "external_thread_id", name="uq_channel_threads_account_external"),
        schema="channels",
    )
    op.create_index("ix_channels_channel_threads_account_id", "channel_threads", ["account_id"], schema="channels")

    op.create_table(
        "channel_messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("thread_id", UUID(as_uuid=True), nullable=False),
        sa.Column("direction", sa.String(10), nullable=False),
        sa.Column("external_message_id", sa.String(255), nullable=True),
        sa.Column("content", sa.Text, nullable=True),
        sa.Column("payload_json", JSONB, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="received"),
        *_timestamps(),
        sa.ForeignKeyConstraint(["thread_id"], ["channels.channel_threads.id"], ondelete="CASCADE"),
        schema="channels",
    )
    op.create_index("ix_channels_channel_messages_thread_id", "channel_messages", ["thread_id"], schema="channels")
    op.create_index("ix_channels_channel_messages_status", "channel_messages", ["status"], schema="channels")
    # Inbound idempotency: a provider message id may appear only once per thread.
    op.create_index(
        "uq_channels_channel_messages_thread_external",
        "channel_messages",
        ["thread_id", "external_message_id"],
        unique=True,
        schema="channels",
        postgresql_where=sa.text("external_message_id IS NOT NULL"),
    )

    op.create_table(
        "delivery_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("message_id", UUID(as_uuid=True), nullable=False),
        sa.Column("attempt", sa.Integer, nullable=False, server_default="1"),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("error_message", sa.Text, nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["message_id"], ["channels.channel_messages.id"], ondelete="CASCADE"),
        schema="channels",
    )
    op.create_index("ix_channels_delivery_log_message_id", "delivery_log", ["message_id"], schema="channels")

    # ── outbox columns on integration_events ──────────────────
    op.add_column("integration_events", sa.Column("aggregate_type", sa.String(50), nullable=True))
    op.add_column("integration_events", sa.Column("aggregate_id", UUID(as_uuid=True), nullable=True))
    op.add_column("integration_events", sa.Column("published_at", sa.DateTime(timezone=True), nullable=True))
    # Pre-existing rows are history, not a backlog — never replay them onto the stream.
    op.execute("UPDATE integration_events SET published_at = now() WHERE published_at IS NULL")
    op.create_index(
        "ix_integration_events_unpublished",
        "integration_events",
        ["created_at"],
        postgresql_where=sa.text("published_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_integration_events_unpublished", table_name="integration_events")
    op.drop_column("integration_events", "published_at")
    op.drop_column("integration_events", "aggregate_id")
    op.drop_column("integration_events", "aggregate_type")
    op.execute("DROP SCHEMA IF EXISTS channels CASCADE")
    op.execute("DROP SCHEMA IF EXISTS ai CASCADE")
