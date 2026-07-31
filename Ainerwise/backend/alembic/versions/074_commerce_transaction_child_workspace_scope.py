"""Bind Commerce transaction child resources to a Workspace.

Revision ID: 074
Revises: 073
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "074"
down_revision: Union[str, None] = "073"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = (
    "supplier_offers",
    "order_deliveries",
    "order_disputes",
    "transaction_reviews",
    "commerce_payment_intents",
    "commerce_messages",
    "commerce_settlements",
)


def _add(table: str) -> None:
    op.add_column(
        table,
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        f"fk_{table}_workspace_id",
        table,
        "workspaces",
        ["workspace_id"],
        ["id"],
    )
    op.create_index(f"ix_{table}_workspace_id", table, ["workspace_id"])


def _assert_none(conn, query: str, message: str) -> None:
    if conn.execute(sa.text(query)).first():
        raise RuntimeError(message)


def _backfill_roots(conn) -> None:
    conn.execute(
        sa.text(
            """
            UPDATE procurement_requests AS request
            SET workspace_id = (
                SELECT min(membership.workspace_id::text)::uuid
                FROM workspace_memberships AS membership
                JOIN workspaces AS workspace ON workspace.id = membership.workspace_id
                WHERE membership.user_id = request.buyer_user_id
                  AND membership.status = 'active'
                  AND workspace.status = 'active'
                HAVING count(DISTINCT membership.workspace_id) = 1
            )
            WHERE request.workspace_id IS NULL
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE procurement_requests
            SET workspace_id = (
                SELECT id FROM workspaces
                WHERE slug = 'default' AND status = 'active'
                LIMIT 1
            )
            WHERE workspace_id IS NULL
            """
        )
    )
    _assert_none(
        conn,
        """
        SELECT commerce_order.id
        FROM commerce_orders AS commerce_order
        JOIN procurement_requests AS request ON request.id = commerce_order.procurement_request_id
        WHERE commerce_order.workspace_id IS NOT NULL
          AND request.workspace_id IS NOT NULL
          AND commerce_order.workspace_id <> request.workspace_id
        LIMIT 1
        """,
        "Cannot bind Commerce children: Order and Request use different Workspaces.",
    )
    conn.execute(
        sa.text(
            """
            UPDATE commerce_orders AS commerce_order
            SET workspace_id = request.workspace_id
            FROM procurement_requests AS request
            WHERE request.id = commerce_order.procurement_request_id
              AND commerce_order.workspace_id IS NULL
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE commerce_orders
            SET workspace_id = (
                SELECT id FROM workspaces
                WHERE slug = 'default' AND status = 'active'
                LIMIT 1
            )
            WHERE workspace_id IS NULL
            """
        )
    )
    _assert_none(
        conn,
        """
        SELECT thread.id
        FROM commerce_threads AS thread
        JOIN procurement_requests AS request ON request.id = thread.procurement_request_id
        JOIN commerce_orders AS commerce_order ON commerce_order.id = thread.commerce_order_id
        WHERE request.workspace_id <> commerce_order.workspace_id
        LIMIT 1
        """,
        "Cannot bind Commerce messages: Thread Request and Order use different Workspaces.",
    )
    conn.execute(
        sa.text(
            """
            UPDATE commerce_threads AS thread
            SET workspace_id = request.workspace_id
            FROM procurement_requests AS request
            WHERE request.id = thread.procurement_request_id
              AND thread.workspace_id IS NULL
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


def _bind(conn, *, table: str, parent: str, fk: str) -> None:
    _assert_none(
        conn,
        f"SELECT child.id FROM {table} AS child JOIN {parent} AS parent ON parent.id = child.{fk} WHERE parent.workspace_id IS NULL LIMIT 1",
        f"Cannot bind {table}: parent resource has no Workspace.",
    )
    conn.execute(
        sa.text(
            f"UPDATE {table} AS child SET workspace_id = parent.workspace_id FROM {parent} AS parent WHERE parent.id = child.{fk}"
        )
    )


def upgrade() -> None:
    for table in TABLES:
        _add(table)
    conn = op.get_bind()
    _backfill_roots(conn)

    _bind(
        conn,
        table="supplier_offers",
        parent="procurement_requests",
        fk="procurement_request_id",
    )
    for table in (
        "order_deliveries",
        "order_disputes",
        "transaction_reviews",
        "commerce_payment_intents",
        "commerce_settlements",
    ):
        _bind(conn, table=table, parent="commerce_orders", fk="commerce_order_id")
    _bind(conn, table="commerce_messages", parent="commerce_threads", fk="thread_id")

    _assert_none(
        conn,
        """
        SELECT settlement.id
        FROM commerce_settlements AS settlement
        JOIN commerce_payment_intents AS intent ON intent.id = settlement.payment_intent_id
        WHERE intent.commerce_order_id <> settlement.commerce_order_id
           OR intent.workspace_id <> settlement.workspace_id
        LIMIT 1
        """,
        "Cannot bind commerce_settlements: Payment Intent and Settlement disagree.",
    )


def downgrade() -> None:
    for table in reversed(TABLES):
        op.drop_index(f"ix_{table}_workspace_id", table_name=table)
        op.drop_constraint(f"fk_{table}_workspace_id", table, type_="foreignkey")
        op.drop_column(table, "workspace_id")
