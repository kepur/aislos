"""Promote one existing supplier operator per company to supplier owner.

Revision ID: 056
Revises: 055
"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa

revision: str = "056"
down_revision: Union[str, None] = "055"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            """
            SELECT workspace_id, user_id, company_id
            FROM (
                SELECT
                    wm.workspace_id,
                    wm.user_id,
                    wm.company_id,
                    row_number() OVER (
                        PARTITION BY wm.workspace_id, wm.company_id
                        ORDER BY u.created_at ASC, wm.created_at ASC
                    ) AS owner_rank
                FROM workspace_memberships wm
                JOIN users u ON u.id = wm.user_id
                WHERE wm.membership_type = 'supplier_operator'
                  AND wm.company_id IS NOT NULL
                  AND u.role = 'vendor'
                  AND NOT EXISTS (
                      SELECT 1
                      FROM workspace_memberships owner
                      WHERE owner.workspace_id = wm.workspace_id
                        AND owner.company_id = wm.company_id
                        AND owner.membership_type = 'supplier_owner'
                  )
            ) ranked
            WHERE owner_rank = 1
            """
        )
    ).fetchall()
    for workspace_id, user_id, company_id in rows:
        conn.execute(
            sa.text(
                """
                INSERT INTO workspace_memberships
                    (id, workspace_id, user_id, company_id, membership_type, status, valid_from)
                VALUES
                    (:id, :workspace_id, :user_id, :company_id, 'supplier_owner', 'active', now())
                ON CONFLICT ON CONSTRAINT uq_ws_membership
                DO UPDATE SET status = 'active', valid_until = NULL, company_id = EXCLUDED.company_id
                """
            ),
            {
                "id": uuid.uuid4(),
                "workspace_id": workspace_id,
                "user_id": user_id,
                "company_id": company_id,
            },
        )


def downgrade() -> None:
    # Owner designation is live authorization data and is intentionally retained.
    pass
