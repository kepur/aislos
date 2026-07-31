"""Backfill final PC/H5 portal access for existing users.

Revision ID: 042
Revises: 041
"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa

revision: str = "042"
down_revision: Union[str, None] = "041"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ROLE_ACCESS: dict[str, tuple[str, list[tuple[str, str]]]] = {
    "buyer": (
        "customer_owner",
        [
            ("customer", "portal.h5.customer"),
            ("customer_pc", "portal.pc.customer"),
            ("customer_h5", "portal.h5.customer"),
            ("cebu_buyer_pc", "portal.pc.cebu_buyer"),
            ("cebu_buyer_h5", "portal.h5.cebu_buyer"),
        ],
    ),
    "customer_user": (
        "customer_member",
        [
            ("customer", "portal.h5.customer"),
            ("customer_pc", "portal.pc.customer"),
            ("customer_h5", "portal.h5.customer"),
        ],
    ),
    "service_partner": (
        "partner_company_owner",
        [
            ("partner_company", "partner.rfq.read"),
            ("partner_company", "partner.work_package.read"),
            ("partner_company_pc", "partner.rfq.read"),
            ("partner_company_pc", "partner.work_package.read"),
            ("partner_company_h5", "partner.rfq.read"),
            ("partner_company_h5", "partner.work_package.read"),
        ],
    ),
    "partner_worker": (
        "field_worker",
        [
            ("field_worker", "field_task.read_assigned"),
            ("field_worker_h5", "field_task.read_assigned"),
        ],
    ),
    "maintenance_worker": (
        "field_worker",
        [
            ("field_worker", "field_task.read_assigned"),
            ("field_worker_h5", "field_task.read_assigned"),
            ("field_worker_h5", "field_task.maintenance"),
        ],
    ),
    "vendor": (
        "supplier_operator",
        [
            ("supplier", "supplier.rfq.read"),
            ("supplier", "supplier.catalog.read"),
            ("supplier_pc", "supplier.rfq.read"),
            ("supplier_pc", "supplier.catalog.read"),
            ("supplier_h5", "supplier.rfq.read"),
            ("supplier_h5", "supplier.catalog.read"),
        ],
    ),
    "project_manager": (
        "project_manager",
        [("admin_field_ops", "admin.field_ops.read"), ("admin_project", "admin.project.read")],
    ),
    "sales_manager": ("admin_operator", [("admin_crm", "admin.crm.read")]),
    "finance": ("admin_operator", [("admin_finance", "admin.finance.read")]),
    "admin": (
        "admin_operator",
        [
            ("admin_executive", "admin.executive.read"),
            ("admin_crm", "admin.crm.read"),
            ("admin_marketing", "admin.marketing.read"),
            ("marketing_pc", "admin.marketing.read"),
            ("marketing_h5", "admin.marketing.read"),
        ],
    ),
    "super_admin": (
        "admin_operator",
        [
            ("admin_executive", "admin.executive.read"),
            ("admin_crm", "admin.crm.read"),
            ("admin_ai_solution", "admin.ai_solution.read"),
            ("admin_procurement", "admin.procurement.read"),
            ("admin_supplier_ops", "admin.supplier_ops.read"),
            ("admin_partner", "admin.partner.read"),
            ("admin_field_ops", "admin.field_ops.read"),
            ("admin_project", "admin.project.read"),
            ("admin_asset", "admin.asset.read"),
            ("admin_commerce", "admin.commerce.read"),
            ("admin_marketing", "admin.marketing.read"),
            ("marketing_pc", "admin.marketing.read"),
            ("marketing_h5", "admin.marketing.read"),
            ("admin_ai_supervisor", "admin.ai_supervisor.read"),
            ("admin_knowledge", "admin.knowledge.read"),
            ("admin_finance", "admin.finance.read"),
            ("admin_audit", "admin.audit.read"),
        ],
    ),
    "developer": ("developer", [("developer", "portal.pc.developer")]),
}


def upgrade() -> None:
    conn = op.get_bind()
    workspace_id = conn.execute(
        sa.text("SELECT id FROM workspaces WHERE slug = 'default' AND status = 'active'")
    ).scalar_one_or_none()
    if workspace_id is None:
        return

    users = conn.execute(sa.text("SELECT id, role, company_id FROM users")).fetchall()
    for user_id, role, company_id in users:
        profile = ROLE_ACCESS.get(role)
        if profile is None:
            continue
        membership_type, grants = profile
        conn.execute(
            sa.text(
                """
                INSERT INTO workspace_memberships
                  (id, workspace_id, user_id, company_id, membership_type, status, valid_from)
                VALUES (:id, :workspace_id, :user_id, :company_id, :membership_type, 'active', now())
                ON CONFLICT ON CONSTRAINT uq_ws_membership
                DO UPDATE SET status = 'active', valid_until = NULL
                """
            ),
            {
                "id": uuid.uuid4(),
                "workspace_id": workspace_id,
                "user_id": user_id,
                "company_id": company_id,
                "membership_type": membership_type,
            },
        )
        for portal_key, grant_key in grants:
            conn.execute(
                sa.text(
                    """
                    INSERT INTO portal_grants
                      (id, user_id, workspace_id, portal_key, grant_key, granted, scope_json)
                    VALUES
                      (:id, :user_id, :workspace_id, :portal_key, :grant_key, true,
                       jsonb_build_object('source', 'role_sync', 'role', :role))
                    ON CONFLICT ON CONSTRAINT uq_portal_grant_scope
                    DO UPDATE SET granted = true, revoked_at = NULL, scope_json = EXCLUDED.scope_json
                    """
                ),
                {
                    "id": uuid.uuid4(),
                    "user_id": user_id,
                    "workspace_id": workspace_id,
                    "portal_key": portal_key,
                    "grant_key": grant_key,
                    "role": role,
                },
            )


def downgrade() -> None:
    # Role-synchronized grants are live authorization data and intentionally
    # survive a schema downgrade.
    pass
