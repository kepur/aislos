"""Phase 2: trust profiles, reviews, risk flags, payment intents.

Revision ID: 038
Revises: 037
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "038"
down_revision: Union[str, None] = "037"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "trust_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("portal_key", sa.String(64), nullable=False, server_default="cebu"),
        sa.Column("completed_orders", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("dispute_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("review_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_rating", sa.Numeric(4, 2), nullable=True),
        sa.Column("trust_score", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("metrics_json", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("company_id", "portal_key", name="uq_trust_profile_company_portal"),
    )
    op.create_index("ix_trust_profiles_company", "trust_profiles", ["company_id"])

    op.create_table(
        "transaction_reviews",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("commerce_order_id", UUID(as_uuid=True), sa.ForeignKey("commerce_orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewer_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("supplier_company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="published"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("commerce_order_id", "reviewer_user_id", name="uq_review_per_buyer_order"),
    )
    op.create_index("ix_transaction_reviews_order", "transaction_reviews", ["commerce_order_id"])

    op.create_table(
        "risk_flags",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("subject_type", sa.String(64), nullable=False),
        sa.Column("subject_id", UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("reason_code", sa.String(64), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(32), nullable=False, server_default="open"),
        sa.Column("source_event", sa.String(120), nullable=True),
        sa.Column("details_json", JSONB, nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_risk_flags_status", "risk_flags", ["status"])
    op.create_index("ix_risk_flags_subject", "risk_flags", ["subject_type", "subject_id"])

    op.create_table(
        "commerce_payment_intents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("commerce_order_id", UUID(as_uuid=True), sa.ForeignKey("commerce_orders.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("payment_plan_id", UUID(as_uuid=True), sa.ForeignKey("payment_plans.id"), nullable=True),
        sa.Column("psp_provider", sa.String(32), nullable=False, server_default="stripe"),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("amount_minor", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="EUR"),
        sa.Column("quote_currency", sa.String(3), nullable=True),
        sa.Column("fx_rate", sa.Numeric(18, 8), nullable=True),
        sa.Column("quote_amount_minor", sa.BigInteger(), nullable=True),
        sa.Column("external_ref", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_commerce_payment_intents_status", "commerce_payment_intents", ["status"])


def downgrade() -> None:
    op.drop_table("commerce_payment_intents")
    op.drop_table("risk_flags")
    op.drop_table("transaction_reviews")
    op.drop_table("trust_profiles")
