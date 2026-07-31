"""Workspace isolation for procurement and Commerce roots."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.commerce import (
    CommerceOrder,
    CommerceThread,
    OrderDelivery,
    ProcurementRequest,
    SupplierOffer,
)
from app.models.portal_access import Workspace
from app.models.user import Company, User
from app.services.commerce_trade import award_offer
from app.services.portal_access import ensure_membership
from tests.fixtures.procurement_e2e import ensure_portal_policy, seed_policies


def _headers(user: User, *, portal: str | None = None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {create_access_token(str(user.id), user.role)}"}
    if portal:
        headers[settings.PROCUREMENT_PORTAL_HEADER] = portal
    return headers


def test_same_company_commerce_isolated_by_workspace_and_supplier_party_preserved():
    async def _run():
        await engine.dispose()
        suffix = uuid.uuid4().hex[:10]
        async with async_session_factory() as db:
            workspace_a = Workspace(name=f"Commerce A {suffix}", slug=f"commerce-a-{suffix}")
            workspace_b = Workspace(name=f"Commerce B {suffix}", slug=f"commerce-b-{suffix}")
            buyer_company = Company(name=f"Commerce buyer {suffix}", type="buyer")
            supplier_company = Company(name=f"Commerce supplier {suffix}", type="supplier")
            db.add_all([workspace_a, workspace_b, buyer_company, supplier_company])
            await db.flush()
            buyer_a = User(
                email=f"commerce-a-{suffix}@example.com",
                password_hash=hash_password("test-password"),
                role="buyer",
                company_id=buyer_company.id,
            )
            buyer_b = User(
                email=f"commerce-b-{suffix}@example.com",
                password_hash=hash_password("test-password"),
                role="customer_user",
                company_id=buyer_company.id,
            )
            supplier = User(
                email=f"commerce-supplier-{suffix}@example.com",
                password_hash=hash_password("test-password"),
                role="vendor",
                company_id=supplier_company.id,
            )
            db.add_all([buyer_a, buyer_b, supplier])
            await db.flush()
            await ensure_membership(
                db,
                user_id=buyer_a.id,
                membership_type="customer_owner",
                workspace_id=workspace_a.id,
                company_id=buyer_company.id,
            )
            await ensure_membership(
                db,
                user_id=buyer_b.id,
                membership_type="customer_member",
                workspace_id=workspace_b.id,
                company_id=buyer_company.id,
            )
            request_a = ProcurementRequest(
                workspace_id=workspace_a.id,
                buyer_company_id=buyer_company.id,
                buyer_user_id=buyer_a.id,
                title="Workspace A request",
                status="published",
            )
            request_b = ProcurementRequest(
                workspace_id=workspace_b.id,
                buyer_company_id=buyer_company.id,
                buyer_user_id=buyer_b.id,
                title="Workspace B private request",
                status="published",
            )
            db.add_all([request_a, request_b])
            await db.flush()
            offer_a = SupplierOffer(
                workspace_id=workspace_a.id,
                procurement_request_id=request_a.id,
                supplier_company_id=supplier_company.id,
                price_minor=120000,
                currency="EUR",
                status="submitted",
            )
            order_b = CommerceOrder(
                workspace_id=workspace_b.id,
                procurement_request_id=request_b.id,
                buyer_company_id=buyer_company.id,
                supplier_company_id=supplier_company.id,
                status="in_delivery",
                total_minor=220000,
                currency="EUR",
            )
            db.add_all([offer_a, order_b])
            await db.flush()
            order_a = await award_offer(db, offer_a.id)
            assert order_a.workspace_id == workspace_a.id
            order_a.status = "in_delivery"
            delivery_a = OrderDelivery(
                workspace_id=workspace_a.id,
                commerce_order_id=order_a.id,
                status="delivered",
            )
            delivery_b = OrderDelivery(
                workspace_id=workspace_b.id,
                commerce_order_id=order_b.id,
                status="delivered",
            )
            db.add_all([delivery_a, delivery_b])
            thread_a = CommerceThread(
                workspace_id=workspace_a.id,
                procurement_request_id=request_a.id,
                commerce_order_id=order_a.id,
                buyer_company_id=buyer_company.id,
                supplier_company_id=supplier_company.id,
                subject="Workspace A thread",
            )
            thread_b = CommerceThread(
                workspace_id=workspace_b.id,
                procurement_request_id=request_b.id,
                commerce_order_id=order_b.id,
                buyer_company_id=buyer_company.id,
                supplier_company_id=supplier_company.id,
                subject="Workspace B private thread",
            )
            db.add_all([thread_a, thread_b])
            await db.commit()
            ids = {
                "workspace_a": str(workspace_a.id),
                "workspace_b": str(workspace_b.id),
                "request_a": str(request_a.id),
                "request_b": str(request_b.id),
                "order_a": str(order_a.id),
                "order_b": str(order_b.id),
                "delivery_a": str(delivery_a.id),
                "thread_a": str(thread_a.id),
                "thread_b": str(thread_b.id),
            }
            buyer_headers = _headers(buyer_a)
            supplier_headers = _headers(supplier)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            request_list = await client.get(
                "/api/v1/commerce/procurement-requests",
                headers=buyer_headers,
            )
            assert request_list.status_code == 200, request_list.text
            assert {item["id"] for item in request_list.json()["items"]} == {ids["request_a"]}
            denied_request = await client.get(
                f"/api/v1/commerce/procurement-requests/{ids['request_b']}",
                headers=buyer_headers,
            )
            assert denied_request.status_code == 403, denied_request.text

            denied_create = await client.post(
                "/api/v1/commerce/procurement-requests",
                headers=buyer_headers,
                json={"workspace_id": ids["workspace_b"], "title": "Cross Workspace write"},
            )
            assert denied_create.status_code == 403, denied_create.text
            created = await client.post(
                "/api/v1/commerce/procurement-requests",
                headers=buyer_headers,
                json={"workspace_id": ids["workspace_a"], "title": "Workspace A new request"},
            )
            assert created.status_code == 201, created.text
            assert created.json()["workspace_id"] == ids["workspace_a"]

            order_list = await client.get("/api/v1/commerce/orders", headers=buyer_headers)
            assert order_list.status_code == 200, order_list.text
            assert {item["id"] for item in order_list.json()["items"]} == {ids["order_a"]}
            denied_order = await client.get(
                f"/api/v1/commerce/orders/{ids['order_b']}",
                headers=buyer_headers,
            )
            assert denied_order.status_code == 403, denied_order.text

            approvals = await client.get(
                "/api/v1/customer/workspace/approvals",
                headers=buyer_headers,
            )
            assert approvals.status_code == 200, approvals.text
            assert {item["id"] for item in approvals.json()["deliveries"]} == {ids["delivery_a"]}

            supplier_order = await client.get(
                f"/api/v1/commerce/orders/{ids['order_b']}",
                headers=supplier_headers,
            )
            assert supplier_order.status_code == 200, supplier_order.text
            buyer_threads = await client.get("/api/v1/commerce/threads", headers=buyer_headers)
            assert buyer_threads.status_code == 200, buyer_threads.text
            assert ids["thread_a"] in {item["id"] for item in buyer_threads.json()["items"]}
            assert ids["thread_b"] not in {item["id"] for item in buyer_threads.json()["items"]}
            denied_messages = await client.get(
                f"/api/v1/commerce/threads/{ids['thread_b']}/messages",
                headers=buyer_headers,
            )
            assert denied_messages.status_code == 403, denied_messages.text
            denied_post = await client.post(
                f"/api/v1/commerce/threads/{ids['thread_b']}/messages",
                headers=buyer_headers,
                json={"body": "Cross Workspace probe"},
            )
            assert denied_post.status_code == 403, denied_post.text
            supplier_threads = await client.get(
                "/api/v1/commerce/threads", headers=supplier_headers
            )
            assert supplier_threads.status_code == 200, supplier_threads.text
            assert {ids["thread_a"], ids["thread_b"]} <= {
                item["id"] for item in supplier_threads.json()["items"]
            }

    asyncio.run(_run())


def test_procurement_project_requires_exact_workspace_when_memberships_are_ambiguous():
    async def _run():
        await engine.dispose()
        await seed_policies()
        await ensure_portal_policy("aislos", "managed")
        suffix = uuid.uuid4().hex[:10]
        async with async_session_factory() as db:
            workspace_a = Workspace(name=f"Procurement A {suffix}", slug=f"procurement-a-{suffix}")
            workspace_b = Workspace(name=f"Procurement B {suffix}", slug=f"procurement-b-{suffix}")
            outsider = Workspace(name=f"Procurement X {suffix}", slug=f"procurement-x-{suffix}")
            user = User(
                email=f"procurement-workspace-{suffix}@example.com",
                password_hash=hash_password("test-password"),
                role="buyer",
            )
            db.add_all([workspace_a, workspace_b, outsider, user])
            await db.flush()
            await ensure_membership(
                db,
                user_id=user.id,
                membership_type="customer_owner",
                workspace_id=workspace_a.id,
            )
            await ensure_membership(
                db,
                user_id=user.id,
                membership_type="customer_owner",
                workspace_id=workspace_b.id,
            )
            await db.commit()
            ids = {
                "workspace_b": str(workspace_b.id),
                "outsider": str(outsider.id),
            }
            headers = _headers(user, portal="aislos")

        payload = {
            "project_type": "villa_smart_home",
            "title": "Workspace-scoped procurement",
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            ambiguous = await client.post(
                "/api/v1/procurement/projects",
                headers=headers,
                json=payload,
            )
            assert ambiguous.status_code == 400, ambiguous.text
            denied = await client.post(
                "/api/v1/procurement/projects",
                headers=headers,
                json={**payload, "workspace_id": ids["outsider"]},
            )
            assert denied.status_code == 403, denied.text
            created = await client.post(
                "/api/v1/procurement/projects",
                headers=headers,
                json={**payload, "workspace_id": ids["workspace_b"]},
            )
            assert created.status_code == 201, created.text
            assert created.json()["workspace_id"] == ids["workspace_b"]

    asyncio.run(_run())
