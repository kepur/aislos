"""Transaction reviews

Revision ID: 0008
Revises: 0007
Create Date: 2026-05-07
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0008"
down_revision: str = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text(
        "DO $$ BEGIN CREATE TYPE transaction_channel AS ENUM ('ONLINE','OFFLINE'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))
    conn.execute(sa.text(
        "DO $$ BEGIN CREATE TYPE review_target_type AS ENUM ('BUYER','SELLER'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))

    op.create_table(
        "transaction_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewee_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewee_company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("target_type", postgresql.ENUM("BUYER", "SELLER", name="review_target_type", create_type=False), nullable=False),
        sa.Column("transaction_channel", postgresql.ENUM("ONLINE", "OFFLINE", name="transaction_channel", create_type=False), nullable=False, server_default="ONLINE"),
        sa.Column("product_quality_rating", sa.Integer(), nullable=True),
        sa.Column("logistics_rating", sa.Integer(), nullable=True),
        sa.Column("communication_rating", sa.Integer(), nullable=True),
        sa.Column("buyer_rating", sa.Integer(), nullable=True),
        sa.Column("overall_rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("order_id", "reviewer_id", "target_type", name="uq_transaction_review_once"),
    )
    op.create_index("ix_transaction_reviews_order_id", "transaction_reviews", ["order_id"])
    op.create_index("ix_transaction_reviews_reviewer_id", "transaction_reviews", ["reviewer_id"])
    op.create_index("ix_transaction_reviews_reviewee_user_id", "transaction_reviews", ["reviewee_user_id"])
    op.create_index("ix_transaction_reviews_reviewee_company_id", "transaction_reviews", ["reviewee_company_id"])
    op.create_index("ix_transaction_reviews_target_type", "transaction_reviews", ["target_type"])


def downgrade() -> None:
    op.drop_index("ix_transaction_reviews_target_type", table_name="transaction_reviews")
    op.drop_index("ix_transaction_reviews_reviewee_company_id", table_name="transaction_reviews")
    op.drop_index("ix_transaction_reviews_reviewee_user_id", table_name="transaction_reviews")
    op.drop_index("ix_transaction_reviews_reviewer_id", table_name="transaction_reviews")
    op.drop_index("ix_transaction_reviews_order_id", table_name="transaction_reviews")
    op.drop_table("transaction_reviews")
    conn = op.get_bind()
    conn.execute(sa.text("DROP TYPE IF EXISTS review_target_type"))
    conn.execute(sa.text("DROP TYPE IF EXISTS transaction_channel"))
