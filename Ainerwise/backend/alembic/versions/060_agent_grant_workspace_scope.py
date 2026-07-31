"""Scope Agent capability and object grants to a Workspace.

Revision ID: 060
Revises: 059
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "060"
down_revision: Union[str, None] = "059"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for table in ("agent_grants", "agent_object_grants"):
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
            ondelete="CASCADE",
        )
        op.create_index(f"ix_{table}_workspace_id", table, ["workspace_id"])

    op.drop_constraint("uq_agent_grants_agent_scope", "agent_grants", type_="unique")
    op.create_unique_constraint(
        "uq_agent_grants_agent_scope_workspace",
        "agent_grants",
        ["agent_id", "scope", "workspace_id"],
        postgresql_nulls_not_distinct=True,
    )
    op.drop_constraint(
        "uq_agent_object_grants_target_scope",
        "agent_object_grants",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_agent_object_grants_target_scope",
        "agent_object_grants",
        ["agent_id", "object_type", "object_id", "scope", "workspace_id"],
        postgresql_nulls_not_distinct=True,
    )


def downgrade() -> None:
    conn = op.get_bind()
    duplicate_grant = conn.execute(
        sa.text(
            """
            SELECT agent_id, scope
            FROM agent_grants
            GROUP BY agent_id, scope
            HAVING count(*) > 1
            LIMIT 1
            """
        )
    ).first()
    duplicate_object_grant = conn.execute(
        sa.text(
            """
            SELECT agent_id, object_type, object_id, scope
            FROM agent_object_grants
            GROUP BY agent_id, object_type, object_id, scope
            HAVING count(*) > 1
            LIMIT 1
            """
        )
    ).first()
    if duplicate_grant or duplicate_object_grant:
        raise RuntimeError(
            "Cannot downgrade migration 060: Workspace-scoped Agent grants cannot "
            "be represented by the previous global-only uniqueness rules."
        )

    op.drop_constraint(
        "uq_agent_object_grants_target_scope",
        "agent_object_grants",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_agent_object_grants_target_scope",
        "agent_object_grants",
        ["agent_id", "object_type", "object_id", "scope"],
    )
    op.drop_constraint(
        "uq_agent_grants_agent_scope_workspace",
        "agent_grants",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_agent_grants_agent_scope",
        "agent_grants",
        ["agent_id", "scope"],
    )
    for table in ("agent_object_grants", "agent_grants"):
        op.drop_index(f"ix_{table}_workspace_id", table_name=table)
        op.drop_constraint(f"fk_{table}_workspace_id", table, type_="foreignkey")
        op.drop_column(table, "workspace_id")
