"""Workspace isolation for Cebu payment and fulfillment child records."""
import asyncio
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.commerce import CommerceOrder, ProcurementRequest
from app.models.portal_access import Workspace
from app.models.user import Company, User
from app.modules.cebu_trade.models import EscrowTransaction, OrderShipping, Payout, PaymentEvent, ProviderPaymentIntent
from app.modules.cebu_trade.service import CebuTradeError, create_escrow, create_payout, process_payout
from app.services.portal_access import ensure_membership, sync_role_portal_access


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _login(email: str, password: str) -> dict:
    async with _client() as client:
        response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def _seed_order_pair():
    suffix = uuid.uuid4().hex[:10]
    password = "cebu-workspace123"
    async with async_session_factory() as db:
        workspace_a = Workspace(name=f"Cebu pay A {suffix}", slug=f"cebu-pay-a-{suffix}")
        workspace_b = Workspace(name=f"Cebu pay B {suffix}", slug=f"cebu-pay-b-{suffix}")
        buyer_company = Company(name=f"Cebu pay buyer {suffix}", type="buyer")
        supplier_company = Company(name=f"Cebu pay supplier {suffix}", type="supplier")
        db.add_all([workspace_a, workspace_b, buyer_company, supplier_company])
        await db.flush()

        admin = User(
            email=f"cebu-pay-admin-{suffix}@example.com",
            password_hash=hash_password(password),
            full_name="Cebu Pay Admin",
            role="admin",
            is_active=True,
        )
        buyer = User(
            email=f"cebu-pay-buyer-{suffix}@example.com",
            password_hash=hash_password(password),
            full_name="Cebu Pay Buyer",
            role="buyer",
            company_id=buyer_company.id,
            is_active=True,
        )
        supplier = User(
            email=f"cebu-pay-supplier-{suffix}@example.com",
            password_hash=hash_password(password),
            full_name="Cebu Pay Supplier",
            role="vendor",
            company_id=supplier_company.id,
            is_active=True,
        )
        db.add_all([admin, buyer, supplier])
        await db.flush()

        await sync_role_portal_access(db, user_id=admin.id, role="admin", workspace_id=workspace_a.id)
        await ensure_membership(
            db,
            user_id=buyer.id,
            membership_type="customer_owner",
            workspace_id=workspace_a.id,
            company_id=buyer_company.id,
        )
        await ensure_membership(
            db,
            user_id=supplier.id,
            membership_type="supplier_owner",
            workspace_id=workspace_a.id,
            company_id=supplier_company.id,
        )

        request_a = ProcurementRequest(
            workspace_id=workspace_a.id,
            buyer_company_id=buyer_company.id,
            buyer_user_id=buyer.id,
            title="Cebu payment A",
            status="awarded",
        )
        request_b = ProcurementRequest(
            workspace_id=workspace_b.id,
            buyer_company_id=buyer_company.id,
            buyer_user_id=buyer.id,
            title="Cebu payment B",
            status="awarded",
        )
        db.add_all([request_a, request_b])
        await db.flush()
        order_a = CommerceOrder(
            workspace_id=workspace_a.id,
            procurement_request_id=request_a.id,
            buyer_company_id=buyer_company.id,
            supplier_company_id=supplier_company.id,
            status="funded",
            total_minor=100000,
            currency="PHP",
        )
        order_b = CommerceOrder(
            workspace_id=workspace_b.id,
            procurement_request_id=request_b.id,
            buyer_company_id=buyer_company.id,
            supplier_company_id=supplier_company.id,
            status="funded",
            total_minor=200000,
            currency="PHP",
        )
        db.add_all([order_a, order_b])
        await db.flush()
        result = {
            "password": password,
            "admin_email": admin.email,
            "workspace_a": workspace_a.id,
            "workspace_b": workspace_b.id,
            "order_a": order_a.id,
            "order_b": order_b.id,
            "supplier_company": supplier_company.id,
        }
        await db.commit()
        return result


def test_cebu_payment_children_inherit_and_reject_mismatched_workspace():
    async def _run():
        await engine.dispose()
        scope = await _seed_order_pair()
        async with async_session_factory() as db:
            escrow = await create_escrow(
                db,
                order_id=scope["order_a"],
                auth_amount_minor=100000,
                currency="PHP",
            )
            assert escrow.workspace_id == scope["workspace_a"]
            escrow.status = "AUTH_HELD"

            payout = await create_payout(
                db,
                company_id=scope["supplier_company"],
                order_id=scope["order_a"],
                escrow_id=escrow.id,
                amount_minor=100000,
                currency="PHP",
            )
            assert payout.workspace_id == scope["workspace_a"]

            shipping = OrderShipping(
                workspace_id=scope["workspace_a"],
                order_id=scope["order_a"],
                shipping_method="LOCAL_DELIVERY",
                currency="PHP",
            )
            intent = ProviderPaymentIntent(
                workspace_id=scope["workspace_a"],
                order_id=scope["order_a"],
                payment_method="PHP_MANUAL_BANK",
                amount_minor=100000,
                currency="PHP",
            )
            event = PaymentEvent(
                workspace_id=scope["workspace_a"],
                provider="TEST",
                event_type="PAYMENT_SUCCEEDED",
                order_id=scope["order_a"],
                escrow_id=escrow.id,
                amount_minor=100000,
                currency="PHP",
            )
            db.add_all([shipping, intent, event])
            await db.flush()
            assert {
                shipping.workspace_id,
                intent.workspace_id,
                event.workspace_id,
            } == {scope["workspace_a"]}

            payout.workspace_id = scope["workspace_b"]
            with pytest.raises(CebuTradeError, match="different Workspaces"):
                await process_payout(db, payout.id, new_status="PAID")

    asyncio.run(_run())


def test_cebu_trade_admin_payment_actions_are_workspace_scoped():
    async def _run():
        await engine.dispose()
        scope = await _seed_order_pair()
        async with async_session_factory() as db:
            escrow_a = EscrowTransaction(
                workspace_id=scope["workspace_a"],
                order_id=scope["order_a"],
                auth_amount_minor=100000,
                captured_amount_minor=100000,
                currency="PHP",
                status="CAPTURED",
            )
            escrow_b = EscrowTransaction(
                workspace_id=scope["workspace_b"],
                order_id=scope["order_b"],
                auth_amount_minor=200000,
                captured_amount_minor=200000,
                currency="PHP",
                status="CAPTURED",
            )
            payout_a = Payout(
                workspace_id=scope["workspace_a"],
                company_id=scope["supplier_company"],
                order_id=scope["order_a"],
                amount_minor=100000,
                currency="PHP",
                status="PENDING",
            )
            payout_b = Payout(
                workspace_id=scope["workspace_b"],
                company_id=scope["supplier_company"],
                order_id=scope["order_b"],
                amount_minor=200000,
                currency="PHP",
                status="PENDING",
            )
            db.add_all([escrow_a, escrow_b, payout_a, payout_b])
            await db.flush()
            ids = {
                "escrow_a": escrow_a.id,
                "escrow_b": escrow_b.id,
                "payout_a": payout_a.id,
                "payout_b": payout_b.id,
            }
            await db.commit()

        admin = await _login(scope["admin_email"], scope["password"])
        async with _client() as client:
            ok_refund = await client.post(
                f"/api/v1/admin/cebu-trade/escrow/{ids['escrow_a']}/refund",
                headers=admin,
                json={"amount_minor": 10000, "reason": "workspace A refund"},
            )
            assert ok_refund.status_code == 200, ok_refund.text
            assert ok_refund.json()["workspace_id"] == str(scope["workspace_a"])

            denied_refund = await client.post(
                f"/api/v1/admin/cebu-trade/escrow/{ids['escrow_b']}/refund",
                headers=admin,
                json={"amount_minor": 10000, "reason": "workspace B refund"},
            )
            assert denied_refund.status_code == 403

            payouts = await client.get("/api/v1/admin/cebu-trade/payouts", headers=admin)
            assert payouts.status_code == 200, payouts.text
            payout_ids = {item["id"] for item in payouts.json()["items"]}
            assert str(ids["payout_a"]) in payout_ids
            assert str(ids["payout_b"]) not in payout_ids

    asyncio.run(_run())
