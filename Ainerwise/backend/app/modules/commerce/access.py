"""Object-level authorization rules for the Commerce domain."""
from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commerce import CommerceOrder, ProcurementRequest, SupplierListing
from app.models.portal_access import Workspace
from app.models.user import User
from app.services.portal_access import (
    get_default_workspace,
    list_memberships,
    resolve_workspace_scope,
)

PLATFORM_ADMIN_ROLES = frozenset({"admin", "super_admin"})
SUPPLIER_ROLES = frozenset({"vendor"})
FINANCE_ROLES = frozenset({"admin", "super_admin", "finance"})


class CommerceAccessDenied(PermissionError):
    pass


class CommerceResourceNotFound(LookupError):
    pass


def is_platform_admin(user: User) -> bool:
    return user.role in PLATFORM_ADMIN_ROLES


async def customer_commerce_workspace_ids(db: AsyncSession, user: User) -> set[uuid.UUID]:
    return {
        membership.workspace_id
        for membership in await list_memberships(db, user.id)
        if user.company_id is not None and membership.company_id == user.company_id
    }


async def resolve_commerce_workspace(
    db: AsyncSession,
    *,
    user: User,
    requested_workspace_id: uuid.UUID | None,
) -> uuid.UUID:
    if is_platform_admin(user):
        workspace = (
            await db.get(Workspace, requested_workspace_id)
            if requested_workspace_id is not None
            else await get_default_workspace(db)
        )
        if workspace is None or workspace.status != "active":
            raise CommerceAccessDenied("An active workspace_id is required")
        return workspace.id
    try:
        workspace_id = await resolve_workspace_scope(
            db,
            user_id=user.id,
            requested_workspace_id=requested_workspace_id,
        )
    except (PermissionError, ValueError) as exc:
        raise CommerceAccessDenied(str(exc)) from None
    if workspace_id is not None:
        return workspace_id
    workspace = await get_default_workspace(db)
    if workspace is None or workspace.status != "active":
        raise CommerceAccessDenied("No active default Workspace is available")
    return workspace.id


async def user_owns_procurement_request(
    db: AsyncSession,
    user: User,
    request: ProcurementRequest,
) -> bool:
    if is_platform_admin(user):
        return True
    if request.buyer_user_id == user.id:
        return True
    if not (
        request.buyer_company_id
        and user.company_id
        and request.buyer_company_id == user.company_id
    ):
        return False
    if request.workspace_id is None:
        return True
    return request.workspace_id in await customer_commerce_workspace_ids(db, user)


async def require_procurement_request_owner(
    db: AsyncSession,
    *,
    user: User,
    request_id: uuid.UUID,
) -> ProcurementRequest:
    request = await db.get(ProcurementRequest, request_id)
    if request is None:
        raise CommerceResourceNotFound("Procurement request not found")
    if not await user_owns_procurement_request(db, user, request):
        raise CommerceAccessDenied("Not allowed to manage this procurement request")
    return request


def require_supplier_company(
    user: User,
    *,
    requested_company_id: uuid.UUID | None,
) -> uuid.UUID:
    if user.role not in SUPPLIER_ROLES:
        raise CommerceAccessDenied("Supplier account required")
    if user.company_id is None:
        raise CommerceAccessDenied("Supplier company required")
    if requested_company_id is not None and requested_company_id != user.company_id:
        raise CommerceAccessDenied("Cannot act for another supplier company")
    return user.company_id


async def require_supplier_listing_owner(
    db: AsyncSession,
    *,
    supplier_company_id: uuid.UUID,
    listing_id: uuid.UUID,
) -> SupplierListing:
    listing = await db.get(SupplierListing, listing_id)
    if listing is None:
        raise CommerceResourceNotFound("Supplier listing not found")
    if listing.company_id != supplier_company_id:
        raise CommerceAccessDenied("Cannot use another supplier company's listing")
    return listing


async def user_is_order_party(
    db: AsyncSession,
    user: User,
    order: CommerceOrder,
) -> str | None:
    if is_platform_admin(user):
        return "admin"
    if order.supplier_company_id and user.company_id and order.supplier_company_id == user.company_id:
        return "supplier"
    if order.buyer_company_id and user.company_id and order.buyer_company_id == user.company_id:
        request = await db.get(ProcurementRequest, order.procurement_request_id)
        if request and await user_owns_procurement_request(db, user, request):
            return "buyer"
    return None


async def require_order_party(
    db: AsyncSession,
    *,
    user: User,
    order_id: uuid.UUID,
    allowed_parties: frozenset[str] | None = None,
) -> tuple[CommerceOrder, str]:
    order = await db.get(CommerceOrder, order_id)
    if order is None:
        raise CommerceResourceNotFound("Order not found")
    party = await user_is_order_party(db, user, order)
    if party is None:
        raise CommerceAccessDenied("Not a party to this order")
    if allowed_parties and party not in allowed_parties:
        raise CommerceAccessDenied(f"Operation requires {' or '.join(allowed_parties)} role")
    return order, party


async def require_workspace_membership(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
) -> bool:
    from app.models.portal_access import WorkspaceMembership
    from sqlalchemy import select

    result = await db.execute(
        select(WorkspaceMembership.id).where(
            WorkspaceMembership.user_id == user_id,
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.status == "active",
        ).limit(1)
    )
    if result.scalar_one_or_none() is None:
        raise CommerceAccessDenied("No active membership in workspace")
    return True
