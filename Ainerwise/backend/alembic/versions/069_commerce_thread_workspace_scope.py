"""Bind Commerce Threads to their Request or Order Workspace.

Revision ID: 069
Revises: 068
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "069"
down_revision: Union[str, None] = "068"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "commerce_threads",
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_commerce_threads_workspace_id",
        "commerce_threads",
        "workspaces",
        ["workspace_id"],
        ["id"],
    )
    op.create_index("ix_commerce_threads_workspace_id", "commerce_threads", ["workspace_id"])
    conn = op.get_bind()
    mismatch = conn.execute(
        sa.text(
            """
            SELECT thread.id
            FROM commerce_threads AS thread
            JOIN procurement_requests AS request ON request.id = thread.procurement_request_id
            JOIN commerce_orders AS commerce_order ON commerce_order.id = thread.commerce_order_id
            WHERE request.workspace_id IS NOT NULL
              AND commerce_order.workspace_id IS NOT NULL
              AND request.workspace_id <> commerce_order.workspace_id
            LIMIT 1
            """
        )
    ).first()
    if mismatch:
        raise RuntimeError("Cannot bind commerce_threads: Request and Order use different Workspaces.")
    conn.execute(
        sa.text(
            """
            UPDATE commerce_threads AS thread
            SET workspace_id = request.workspace_id
            FROM procurement_requests AS request
            WHERE request.id = thread.procurement_request_id
              AND request.workspace_id IS NOT NULL
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE commerce_threads AS thread
            SET workspace_id = commerce_order.workspace_id
            FROM commerce_orders AS commerce_order
            WHERE commerce_order.id = thread.commerce_order_id
              AND thread.workspace_id IS NULL
              AND commerce_order.workspace_id IS NOT NULL
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE commerce_threads
            SET workspace_id = (
                SELECT id FROM workspaces
                WHERE slug = 'default' AND status = 'active'
                LIMIT 1
            )
            WHERE workspace_id IS NULL
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_commerce_threads_workspace_id", table_name="commerce_threads")
    op.drop_constraint("fk_commerce_threads_workspace_id", "commerce_threads", type_="foreignkey")
    op.drop_column("commerce_threads", "workspace_id")

