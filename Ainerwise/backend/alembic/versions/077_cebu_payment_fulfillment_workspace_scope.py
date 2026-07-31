"""Bind Cebu payment and fulfillment children to a Workspace.

Revision ID: 077
Revises: 076
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "077"
down_revision: Union[str, None] = "076"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_WORKSPACE_ID = "00000000-0000-4000-8000-000000000001"

TABLES = (
    "order_shipping",
    "escrow_transactions",
    "payouts",
    "provider_payment_intents",
    "payment_events",
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


def _ensure_default_workspace(conn) -> None:
    conn.execute(
        sa.text(
            """
            INSERT INTO workspaces (id, name, slug, status)
            VALUES (:id, 'Default Workspace', 'default', 'active')
            ON CONFLICT (slug) DO NOTHING
            """
        ),
        {"id": DEFAULT_WORKSPACE_ID},
    )


def _backfill_order_roots(conn) -> None:
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
        "Cannot bind Cebu payment children: Order and Procurement Request use different Workspaces.",
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


def _bind_from_order(conn, table: str) -> None:
    _assert_none(
        conn,
        f"""
        SELECT child.id
        FROM {table} AS child
        JOIN commerce_orders AS commerce_order ON commerce_order.id = child.order_id
        WHERE commerce_order.workspace_id IS NULL
        LIMIT 1
        """,
        f"Cannot bind {table}: parent order has no Workspace.",
    )
    conn.execute(
        sa.text(
            f"""
            UPDATE {table} AS child
            SET workspace_id = commerce_order.workspace_id
            FROM commerce_orders AS commerce_order
            WHERE commerce_order.id = child.order_id
              AND child.order_id IS NOT NULL
            """
        )
    )


def upgrade() -> None:
    for table in TABLES:
        _add(table)

    conn = op.get_bind()
    _ensure_default_workspace(conn)
    _backfill_order_roots(conn)

    for table in ("order_shipping", "escrow_transactions", "payouts", "provider_payment_intents"):
        _bind_from_order(conn, table)

    conn.execute(
        sa.text(
            """
            UPDATE payment_events AS event
            SET workspace_id = commerce_order.workspace_id
            FROM commerce_orders AS commerce_order
            WHERE commerce_order.id = event.order_id
              AND event.order_id IS NOT NULL
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE payment_events AS event
            SET workspace_id = escrow.workspace_id
            FROM escrow_transactions AS escrow
            WHERE escrow.id = event.escrow_id
              AND event.workspace_id IS NULL
              AND escrow.workspace_id IS NOT NULL
            """
        )
    )

    _assert_none(
        conn,
        """
        SELECT payout.id
        FROM payouts AS payout
        JOIN escrow_transactions AS escrow ON escrow.id = payout.escrow_id
        WHERE payout.workspace_id IS NOT NULL
          AND escrow.workspace_id IS NOT NULL
          AND payout.workspace_id <> escrow.workspace_id
        LIMIT 1
        """,
        "Cannot bind payouts: Payout escrow and order use different Workspaces.",
    )
    _assert_none(
        conn,
        """
        SELECT event.id
        FROM payment_events AS event
        JOIN commerce_orders AS commerce_order ON commerce_order.id = event.order_id
        WHERE event.workspace_id IS NOT NULL
          AND commerce_order.workspace_id IS NOT NULL
          AND event.workspace_id <> commerce_order.workspace_id
        LIMIT 1
        """,
        "Cannot bind payment_events: Payment event and order use different Workspaces.",
    )
    _assert_none(
        conn,
        """
        SELECT event.id
        FROM payment_events AS event
        JOIN escrow_transactions AS escrow ON escrow.id = event.escrow_id
        WHERE event.workspace_id IS NOT NULL
          AND escrow.workspace_id IS NOT NULL
          AND event.workspace_id <> escrow.workspace_id
        LIMIT 1
        """,
        "Cannot bind payment_events: Payment event and escrow use different Workspaces.",
    )


def downgrade() -> None:
    for table in reversed(TABLES):
        op.drop_index(f"ix_{table}_workspace_id", table_name=table)
        op.drop_constraint(f"fk_{table}_workspace_id", table, type_="foreignkey")
        op.drop_column(table, "workspace_id")
