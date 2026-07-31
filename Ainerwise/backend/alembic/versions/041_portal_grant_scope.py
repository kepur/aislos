"""Scope portal grants by logical portal.

Revision ID: 041
Revises: 74ba695300ac
"""
from typing import Sequence, Union

from alembic import op

revision: str = "041"
down_revision: Union[str, None] = "74ba695300ac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("uq_portal_grant", "portal_grants", type_="unique")
    op.create_unique_constraint(
        "uq_portal_grant_scope",
        "portal_grants",
        ["user_id", "grant_key", "workspace_id", "portal_key"],
        postgresql_nulls_not_distinct=True,
    )


def downgrade() -> None:
    op.drop_constraint("uq_portal_grant_scope", "portal_grants", type_="unique")
    op.create_unique_constraint(
        "uq_portal_grant",
        "portal_grants",
        ["user_id", "grant_key", "workspace_id"],
    )
