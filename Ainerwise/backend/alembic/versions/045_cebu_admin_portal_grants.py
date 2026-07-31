"""Grant existing administrators the Cebu administration workbench.

Revision ID: 045
Revises: 044
"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa

revision: str = "045"
down_revision: Union[str, None] = "044"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    workspace_id = conn.execute(
        sa.text("SELECT id FROM workspaces WHERE slug = 'default' AND status = 'active'")
    ).scalar_one_or_none()
    if workspace_id is None:
        return
    users = conn.execute(
        sa.text("SELECT id, role FROM users WHERE role IN ('admin', 'super_admin')")
    ).fetchall()
    for user_id, role in users:
        conn.execute(
            sa.text(
                """
                INSERT INTO portal_grants
                  (id, user_id, workspace_id, portal_key, grant_key, granted, scope_json)
                VALUES
                  (:id, :user_id, :workspace_id, 'admin_cebu', 'admin.cebu.read', true,
                   jsonb_build_object('source', 'role_sync', 'role', :role))
                ON CONFLICT ON CONSTRAINT uq_portal_grant_scope
                DO UPDATE SET granted = true, revoked_at = NULL, scope_json = EXCLUDED.scope_json
                """
            ),
            {"id": uuid.uuid4(), "user_id": user_id, "workspace_id": workspace_id, "role": role},
        )


def downgrade() -> None:
    pass
