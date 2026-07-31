"""PF02: workspaces, memberships and portal grants.

Revision ID: 034
Revises: 033
"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "034"
down_revision: Union[str, None] = "033"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_WORKSPACE_ID = "00000000-0000-4000-8000-000000000001"

ROLE_MEMBERSHIP = {
    "buyer": "customer_owner",
    "customer_user": "customer_member",
    "service_partner": "partner_company_owner",
    "partner_worker": "field_worker",
    "maintenance_worker": "field_worker",
    "vendor": "supplier_operator",
    "project_manager": "project_manager",
    "sales_manager": "admin_operator",
    "finance": "admin_operator",
    "admin": "admin_operator",
    "super_admin": "admin_operator",
    "developer": "developer",
}

ROLE_GRANTS: dict[str, list[str]] = {
    "buyer": ["portal.h5.customer"],
    "customer_user": ["portal.h5.customer"],
    "service_partner": ["partner.rfq.read", "partner.work_package.read", "portal.h5.partner"],
    "partner_worker": ["field_task.read_assigned"],
    "maintenance_worker": ["field_task.read_assigned", "field_task.maintenance"],
    "vendor": ["supplier.rfq.read", "supplier.catalog.read", "portal.h5.supplier"],
    "project_manager": ["admin.field_ops.read", "admin.project.read"],
    "sales_manager": ["admin.crm.read"],
    "finance": ["admin.finance.read"],
    "admin": ["admin.executive.read", "admin.crm.read", "admin.marketing.read"],
    "super_admin": [
        "admin.executive.read", "admin.crm.read", "admin.procurement.read",
        "admin.field_ops.read", "admin.project.read", "admin.marketing.read",
        "admin.ai_supervisor.read", "admin.audit.read",
    ],
    "developer": ["portal.pc.developer"],
}


def upgrade() -> None:
    op.create_table(
        "workspaces",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(64), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("region_id", UUID(as_uuid=True), sa.ForeignKey("regions.id"), nullable=True),
        sa.Column("metadata_json", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_workspaces_slug", "workspaces", ["slug"], unique=True)

    op.create_table(
        "workspace_memberships",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("membership_type", sa.String(64), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("workspace_id", "user_id", "membership_type", name="uq_ws_membership"),
    )
    op.create_index("ix_workspace_memberships_user_id", "workspace_memberships", ["user_id"])

    op.create_table(
        "portal_grants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True),
        sa.Column("portal_key", sa.String(64), nullable=True),
        sa.Column("grant_key", sa.String(128), nullable=False),
        sa.Column("granted", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("granted_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scope_json", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", "grant_key", "workspace_id", name="uq_portal_grant"),
    )
    op.create_index("ix_portal_grants_user_id", "portal_grants", ["user_id"])
    op.create_index("ix_portal_grants_grant_key", "portal_grants", ["grant_key"])

    conn = op.get_bind()
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

    users = conn.execute(sa.text("SELECT id, role, company_id FROM users")).fetchall()
    for row in users:
        user_id, role, company_id = str(row[0]), row[1], row[2]
        membership_type = ROLE_MEMBERSHIP.get(role)
        if not membership_type:
            continue
        mem_id = str(uuid.uuid4())
        conn.execute(
            sa.text(
                """
                INSERT INTO workspace_memberships
                  (id, workspace_id, user_id, company_id, membership_type, status)
                VALUES (:id, :ws, :uid, :cid, :mtype, 'active')
                ON CONFLICT ON CONSTRAINT uq_ws_membership DO NOTHING
                """
            ),
            {
                "id": mem_id,
                "ws": DEFAULT_WORKSPACE_ID,
                "uid": user_id,
                "cid": str(company_id) if company_id else None,
                "mtype": membership_type,
            },
        )
        for grant_key in ROLE_GRANTS.get(role, []):
            grant_id = str(uuid.uuid4())
            conn.execute(
                sa.text(
                    """
                    INSERT INTO portal_grants
                      (id, user_id, workspace_id, grant_key, granted)
                    VALUES (:id, :uid, :ws, :gkey, true)
                    ON CONFLICT ON CONSTRAINT uq_portal_grant DO NOTHING
                    """
                ),
                {"id": grant_id, "uid": user_id, "ws": DEFAULT_WORKSPACE_ID, "gkey": grant_key},
            )


def downgrade() -> None:
    op.drop_table("portal_grants")
    op.drop_table("workspace_memberships")
    op.drop_table("workspaces")
