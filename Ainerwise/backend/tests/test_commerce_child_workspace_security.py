"""Workspace inheritance and mismatch rejection for Commerce transaction children."""
import asyncio
import uuid

import pytest

from app.core.security import hash_password
from app.db.session import async_session_factory, engine
from app.models.commerce import CommerceMessage, ProcurementRequest
from app.models.portal_access import Workspace
from app.models.user import Company, User
from app.services.commerce_messaging import (
    get_or_create_thread_for_order,
    list_thread_messages,
    post_thread_message,
)
from app.services.commerce_settlement import confirm_order_funding
from app.services.commerce_trade import (
    CommerceTradeError,
    advance_delivery,
    award_offer,
    create_delivery,
    open_dispute,
    submit_offer,
)
from app.services.commerce_trust import create_payment_intent, submit_transaction_review
from app.services.portal_access import ensure_membership


def test_commerce_transaction_children_inherit_and_enforce_parent_workspace():
    async def _run():
        await engine.dispose()
        suffix = uuid.uuid4().hex[:10]
        async with async_session_factory() as db:
            workspace_a = Workspace(name=f"Commerce child A {suffix}", slug=f"cc-a-{suffix}")
            workspace_b = Workspace(name=f"Commerce child B {suffix}", slug=f"cc-b-{suffix}")
            buyer_company = Company(name=f"Commerce child buyer {suffix}", type="buyer")
            supplier_company = Company(name=f"Commerce child supplier {suffix}", type="supplier")
            db.add_all([workspace_a, workspace_b, buyer_company, supplier_company])
            await db.flush()
            buyer = User(
                email=f"commerce-child-buyer-{suffix}@example.com",
                password_hash=hash_password("test-password"),
                role="buyer",
                company_id=buyer_company.id,
            )
            supplier = User(
                email=f"commerce-child-supplier-{suffix}@example.com",
                password_hash=hash_password("test-password"),
                role="vendor",
                company_id=supplier_company.id,
            )
            db.add_all([buyer, supplier])
            await db.flush()
            await ensure_membership(
                db,
                user_id=buyer.id,
                membership_type="customer_owner",
                workspace_id=workspace_a.id,
                company_id=buyer_company.id,
            )
            request = ProcurementRequest(
                workspace_id=workspace_a.id,
                buyer_company_id=buyer_company.id,
                buyer_user_id=buyer.id,
                title="Workspace-scoped request",
                status="published",
            )
            db.add(request)
            await db.flush()

            offer = await submit_offer(
                db,
                procurement_request_id=request.id,
                supplier_company_id=supplier_company.id,
                price_minor=125000,
                currency="EUR",
            )
            assert offer.workspace_id == workspace_a.id

            order = await award_offer(db, offer.id)
            assert order.workspace_id == workspace_a.id

            delivery = await create_delivery(db, order.id, carrier="Scoped Carrier")
            assert delivery.workspace_id == workspace_a.id

            thread = await get_or_create_thread_for_order(db, order)
            message = await post_thread_message(
                db,
                thread_id=thread.id,
                user=buyer,
                body="Workspace-scoped message",
            )
            assert message.workspace_id == workspace_a.id

            forged_message = CommerceMessage(
                workspace_id=workspace_b.id,
                thread_id=thread.id,
                sender_user_id=buyer.id,
                sender_role="buyer",
                body="Forged cross-Workspace message",
            )
            db.add(forged_message)
            await db.flush()
            visible_messages = await list_thread_messages(db, thread)
            assert {row.id for row in visible_messages} == {message.id}

            dispute = await open_dispute(
                db,
                order_id=order.id,
                user=buyer,
                reason_code="non_delivery",
                description="Test dispute",
            )
            assert dispute.workspace_id == workspace_a.id

            order.status = "completed"
            review = await submit_transaction_review(
                db,
                order_id=order.id,
                user=buyer,
                rating=5,
                comment="Scoped review",
            )
            assert review.workspace_id == workspace_a.id

            intent = await create_payment_intent(db, order_id=order.id)
            assert intent.workspace_id == workspace_a.id
            settlement = await confirm_order_funding(
                db,
                order_id=order.id,
                external_ref=f"funding-{suffix}",
            )
            assert settlement.workspace_id == workspace_a.id

            delivery.workspace_id = workspace_b.id
            with pytest.raises(CommerceTradeError, match="different Workspaces"):
                await advance_delivery(db, delivery.id, new_status="shipped")

    asyncio.run(_run())
