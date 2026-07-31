"""2Hands second-hand domain: condition/provenance detail + controlled
pickup-address disclosure audit trail.

Revision ID: 079
Revises: 078
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "079"
down_revision: Union[str, None] = "078"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "secondhand_listings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=True),
        sa.Column(
            "supplier_listing_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("supplier_listings.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        # condition & provenance
        sa.Column("condition_grade", sa.String(2), server_default="B", nullable=False),
        sa.Column("purchase_year", sa.Integer(), nullable=True),
        sa.Column("usage_note", sa.String(255), nullable=True),
        sa.Column("serial_type", sa.String(16), server_default="NONE", nullable=False),
        sa.Column("serial_no", sa.String(120), nullable=True),
        sa.Column("warranty_left_months", sa.Integer(), nullable=True),
        sa.Column("original_packaging", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("defects_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("inspection_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # fulfilment — pickup_address/pickup_note/contact_phone are RESTRICTED
        sa.Column("fulfillment_mode", sa.String(32), server_default="SELLER_PICKUP", nullable=False),
        sa.Column("pickup_country", sa.String(2), nullable=True),
        sa.Column("pickup_city", sa.String(120), nullable=True),
        sa.Column("pickup_area", sa.String(120), nullable=True),
        sa.Column("pickup_address", sa.Text(), nullable=True),
        sa.Column("pickup_note", sa.Text(), nullable=True),
        sa.Column("contact_phone", sa.String(60), nullable=True),
        sa.Column("quantity", sa.Integer(), server_default="1", nullable=False),
        sa.Column("sold_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_secondhand_listings_workspace_id", "secondhand_listings", ["workspace_id"])
    op.create_index("ix_secondhand_listings_supplier_listing_id", "secondhand_listings", ["supplier_listing_id"])
    op.create_index("ix_secondhand_listings_condition_grade", "secondhand_listings", ["condition_grade"])
    op.create_index("ix_secondhand_listings_serial_no", "secondhand_listings", ["serial_no"])
    op.create_index("ix_secondhand_listings_fulfillment_mode", "secondhand_listings", ["fulfillment_mode"])
    op.create_index("ix_secondhand_listings_pickup_country", "secondhand_listings", ["pickup_country"])
    op.create_index("ix_secondhand_listings_pickup_city", "secondhand_listings", ["pickup_city"])

    op.create_table(
        "secondhand_address_disclosures",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=True),
        sa.Column(
            "secondhand_listing_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("secondhand_listings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "buyer_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("granted_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column(
            "commerce_order_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("commerce_orders.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(24), server_default="granted", nullable=False),
        sa.Column("disclosed_fields_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.String(255), nullable=True),
        sa.UniqueConstraint("secondhand_listing_id", "buyer_user_id", name="uq_secondhand_disclosure_buyer"),
    )
    op.create_index(
        "ix_secondhand_disclosures_workspace_id", "secondhand_address_disclosures", ["workspace_id"]
    )
    op.create_index(
        "ix_secondhand_disclosures_listing_id", "secondhand_address_disclosures", ["secondhand_listing_id"]
    )
    op.create_index(
        "ix_secondhand_disclosures_buyer_user_id", "secondhand_address_disclosures", ["buyer_user_id"]
    )
    op.create_index(
        "ix_secondhand_disclosures_order_id", "secondhand_address_disclosures", ["commerce_order_id"]
    )
    op.create_index("ix_secondhand_disclosures_status", "secondhand_address_disclosures", ["status"])


def downgrade() -> None:
    op.drop_table("secondhand_address_disclosures")
    op.drop_table("secondhand_listings")
