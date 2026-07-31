"""Bind Lead child and Experience Center resources to a Workspace.

Revision ID: 072
Revises: 071
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "072"
down_revision: Union[str, None] = "071"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = (
    "site_surveys",
    "stores",
    "kiosk_devices",
    "showroom_sessions",
    "showroom_orders",
)


def _add(table: str, *, schema: str | None = None) -> None:
    op.add_column(
        table,
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema=schema,
    )
    op.create_foreign_key(
        f"fk_{table}_workspace_id",
        table,
        "workspaces",
        ["workspace_id"],
        ["id"],
        source_schema=schema,
    )
    index_name = f"ix_{schema}_{table}_workspace_id" if schema else f"ix_{table}_workspace_id"
    op.create_index(index_name, table, ["workspace_id"], schema=schema)


def _default(conn, table: str) -> None:
    conn.execute(
        sa.text(
            f"""
            UPDATE {table}
            SET workspace_id = (
                SELECT id FROM workspaces
                WHERE slug = 'default' AND status = 'active'
                LIMIT 1
            )
            WHERE workspace_id IS NULL
            """
        )
    )


def _assert_links_agree(conn, query: str, message: str) -> None:
    if conn.execute(sa.text(query)).first():
        raise RuntimeError(message)


def upgrade() -> None:
    for table in TABLES:
        _add(table)
    _add("conversations", schema="ai")
    conn = op.get_bind()

    conn.execute(sa.text("UPDATE site_surveys AS s SET workspace_id = l.workspace_id FROM leads l WHERE l.id = s.lead_id AND l.workspace_id IS NOT NULL"))
    _default(conn, "site_surveys")

    _default(conn, "stores")
    conn.execute(sa.text("UPDATE kiosk_devices AS d SET workspace_id = s.workspace_id FROM stores s WHERE s.id = d.store_id AND s.workspace_id IS NOT NULL"))
    _default(conn, "kiosk_devices")

    conn.execute(sa.text("UPDATE showroom_sessions AS s SET workspace_id = d.workspace_id FROM kiosk_devices d WHERE d.id = s.device_id AND d.workspace_id IS NOT NULL"))
    _assert_links_agree(
        conn,
        "SELECT s.id FROM showroom_sessions s JOIN leads l ON l.id = s.lead_id WHERE s.workspace_id IS NOT NULL AND l.workspace_id IS NOT NULL AND s.workspace_id <> l.workspace_id LIMIT 1",
        "Cannot bind showroom_sessions: Device and Lead use different Workspaces.",
    )
    _default(conn, "showroom_sessions")

    conn.execute(sa.text("UPDATE showroom_orders AS o SET workspace_id = s.workspace_id FROM showroom_sessions s WHERE s.id = o.session_id AND s.workspace_id IS NOT NULL"))
    conn.execute(sa.text("UPDATE showroom_orders AS o SET workspace_id = s.workspace_id FROM stores s WHERE s.id = o.store_id AND o.workspace_id IS NULL AND s.workspace_id IS NOT NULL"))
    _assert_links_agree(
        conn,
        "SELECT o.id FROM showroom_orders o JOIN showroom_sessions session ON session.id = o.session_id JOIN stores store ON store.id = o.store_id WHERE session.workspace_id IS NOT NULL AND store.workspace_id IS NOT NULL AND session.workspace_id <> store.workspace_id LIMIT 1",
        "Cannot bind showroom_orders: Session and Store use different Workspaces.",
    )
    _default(conn, "showroom_orders")

    conn.execute(sa.text("UPDATE ai.conversations AS c SET workspace_id = l.workspace_id FROM leads l WHERE l.id = c.lead_id AND l.workspace_id IS NOT NULL"))
    conn.execute(sa.text("UPDATE ai.conversations AS c SET workspace_id = s.workspace_id FROM showroom_sessions s WHERE s.conversation_id = c.id AND c.workspace_id IS NULL AND s.workspace_id IS NOT NULL"))
    _assert_links_agree(
        conn,
        "SELECT c.id FROM ai.conversations c JOIN showroom_sessions s ON s.conversation_id = c.id WHERE c.workspace_id IS NOT NULL AND s.workspace_id IS NOT NULL AND c.workspace_id <> s.workspace_id LIMIT 1",
        "Cannot bind conversations: linked Showroom Session uses a different Workspace.",
    )
    _default(conn, "ai.conversations")


def downgrade() -> None:
    op.drop_index("ix_ai_conversations_workspace_id", table_name="conversations", schema="ai")
    op.drop_constraint(
        "fk_conversations_workspace_id", "conversations", schema="ai", type_="foreignkey"
    )
    op.drop_column("conversations", "workspace_id", schema="ai")
    for table in reversed(TABLES):
        op.drop_index(f"ix_{table}_workspace_id", table_name=table)
        op.drop_constraint(f"fk_{table}_workspace_id", table, type_="foreignkey")
        op.drop_column(table, "workspace_id")
