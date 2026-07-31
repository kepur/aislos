"""Security boundary tests for Cebu zero-loss migration: wallet, address, ads, escrow, payout."""
import asyncio
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import hash_password
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.user import Company, User
from app.modules.cebu_trade.models import Wallet, WalletDeposit, EscrowTransaction


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _create_identity(*, role: str, with_company: bool = True) -> tuple[str, str, uuid.UUID | None]:
    suffix = uuid.uuid4().hex[:10]
    email = f"cebu-{role}-{suffix}@example.com"
    password = "cebutest123"
    async with async_session_factory() as db:
        company_id = None
        if with_company:
            company = Company(
                name=f"Cebu {role} {suffix}",
                type="supplier" if role == "vendor" else "buyer",
                verification_status="verified",
            )
            db.add(company)
            await db.flush()
            company_id = company.id
        db.add(
            User(
                email=email,
                password_hash=hash_password(password),
                full_name=f"Cebu {role}",
                role=role,
                company_id=company_id,
                is_active=True,
            )
        )
        await db.commit()
    return email, password, company_id


async def _login(email: str, password: str) -> dict:
    async with _client() as client:
        response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


# ── Wallet ownership isolation ──────────────────────────────────────


def test_wallet_is_isolated_per_user():
    async def _run():
        await engine.dispose()
        user_a_email, password, _ = await _create_identity(role="buyer")
        user_b_email, _, _ = await _create_identity(role="buyer")
        user_a = await _login(user_a_email, password)
        user_b = await _login(user_b_email, password)

        async with _client() as client:
            wallet_a = await client.get("/api/v1/cebu-trade/wallet", headers=user_a)
            assert wallet_a.status_code == 200, wallet_a.text
            wallet_a_id = wallet_a.json()["id"]

            wallet_b = await client.get("/api/v1/cebu-trade/wallet", headers=user_b)
            assert wallet_b.status_code == 200, wallet_b.text
            wallet_b_id = wallet_b.json()["id"]

            assert wallet_a_id != wallet_b_id

            txs_cross = await client.get(
                f"/api/v1/cebu-trade/wallet/{wallet_a_id}/transactions", headers=user_b
            )
            assert txs_cross.status_code == 404

            txs_own = await client.get(
                f"/api/v1/cebu-trade/wallet/{wallet_a_id}/transactions", headers=user_a
            )
            assert txs_own.status_code == 200

    asyncio.run(_run())


# ── Address ownership isolation ─────────────────────────────────────


def test_address_crud_is_scoped_to_owner():
    async def _run():
        await engine.dispose()
        owner_email, password, _ = await _create_identity(role="buyer")
        stranger_email, _, _ = await _create_identity(role="buyer")
        owner = await _login(owner_email, password)
        stranger = await _login(stranger_email, password)

        async with _client() as client:
            addr = await client.post(
                "/api/v1/cebu-trade/addresses",
                headers=owner,
                json={
                    "label": "Home",
                    "contact_name": "Test User",
                    "contact_phone": "+639001234567",
                    "country_code": "PH",
                    "country_name": "Philippines",
                    "city": "Cebu City",
                    "address_line1": "123 Test Street",
                },
            )
            assert addr.status_code == 201, addr.text
            addr_id = addr.json()["id"]

            stranger_list = await client.get("/api/v1/cebu-trade/addresses", headers=stranger)
            assert stranger_list.status_code == 200
            stranger_ids = {a["id"] for a in stranger_list.json()["items"]}
            assert addr_id not in stranger_ids

            stranger_update = await client.patch(
                f"/api/v1/cebu-trade/addresses/{addr_id}",
                headers=stranger,
                json={"label": "Stolen"},
            )
            assert stranger_update.status_code == 404

            stranger_delete = await client.delete(
                f"/api/v1/cebu-trade/addresses/{addr_id}", headers=stranger
            )
            assert stranger_delete.status_code == 404

            owner_update = await client.patch(
                f"/api/v1/cebu-trade/addresses/{addr_id}",
                headers=owner,
                json={"label": "Updated Home"},
            )
            assert owner_update.status_code == 200

    asyncio.run(_run())


# ── Ad campaign company isolation ───────────────────────────────────


def test_ad_campaigns_are_scoped_to_company():
    async def _run():
        await engine.dispose()
        vendor_a_email, password, company_a = await _create_identity(role="vendor")
        vendor_b_email, _, company_b = await _create_identity(role="vendor")
        vendor_a = await _login(vendor_a_email, password)
        vendor_b = await _login(vendor_b_email, password)

        async with _client() as client:
            campaign = await client.post(
                "/api/v1/cebu-trade/ads/campaigns",
                headers=vendor_a,
                json={
                    "title": "Company A Campaign",
                    "budget_minor": 500000,
                    "bid_per_click_minor": 100,
                },
            )
            assert campaign.status_code == 201, campaign.text
            campaign_id = campaign.json()["id"]

            vendor_b_list = await client.get(
                "/api/v1/cebu-trade/ads/campaigns", headers=vendor_b
            )
            assert vendor_b_list.status_code == 200
            vendor_b_ids = {c["id"] for c in vendor_b_list.json()["items"]}
            assert campaign_id not in vendor_b_ids

    asyncio.run(_run())


def test_companyless_user_cannot_create_campaign():
    async def _run():
        await engine.dispose()
        email, password, _ = await _create_identity(role="buyer", with_company=False)
        headers = await _login(email, password)

        async with _client() as client:
            resp = await client.post(
                "/api/v1/cebu-trade/ads/campaigns",
                headers=headers,
                json={
                    "title": "Should fail",
                    "budget_minor": 100000,
                    "bid_per_click_minor": 50,
                },
            )
            assert resp.status_code == 403

    asyncio.run(_run())


# ── Deposit admin-only verification ─────────────────────────────────


def test_regular_user_cannot_verify_or_reject_deposits():
    async def _run():
        await engine.dispose()
        buyer_email, password, _ = await _create_identity(role="buyer")
        buyer = await _login(buyer_email, password)

        async with _client() as client:
            deposit = await client.post(
                "/api/v1/cebu-trade/wallet/deposits",
                headers=buyer,
                json={
                    "amount_minor": 100000,
                    "deposit_address": "TRC20_TEST_ADDR",
                },
            )
            assert deposit.status_code == 201, deposit.text
            deposit_id = deposit.json()["id"]

            verify = await client.post(
                f"/api/v1/admin/cebu-trade/deposits/{deposit_id}/verify",
                headers=buyer,
                json={},
            )
            assert verify.status_code == 403

            reject = await client.post(
                f"/api/v1/admin/cebu-trade/deposits/{deposit_id}/reject",
                headers=buyer,
                json={},
            )
            assert reject.status_code == 403

    asyncio.run(_run())


# ── Escrow requires order party ─────────────────────────────────────


def test_escrow_view_requires_order_party():
    async def _run():
        await engine.dispose()
        stranger_email, password, _ = await _create_identity(role="buyer")
        stranger = await _login(stranger_email, password)
        fake_order_id = str(uuid.uuid4())

        async with _client() as client:
            resp = await client.get(
                f"/api/v1/cebu-trade/orders/{fake_order_id}/escrow", headers=stranger
            )
            assert resp.status_code == 404

    asyncio.run(_run())


# ── Payout admin-only processing ────────────────────────────────────


def test_regular_user_cannot_list_admin_payouts():
    async def _run():
        await engine.dispose()
        buyer_email, password, _ = await _create_identity(role="buyer")
        buyer = await _login(buyer_email, password)

        async with _client() as client:
            resp = await client.get("/api/v1/admin/cebu-trade/payouts", headers=buyer)
            assert resp.status_code == 403

    asyncio.run(_run())


# ── Unauthenticated access blocked ──────────────────────────────────


def test_unauthenticated_cannot_access_cebu_trade():
    async def _run():
        await engine.dispose()
        async with _client() as client:
            for path in (
                "/api/v1/cebu-trade/wallet",
                "/api/v1/cebu-trade/wallet/balances",
                "/api/v1/cebu-trade/addresses",
                "/api/v1/cebu-trade/ads/campaigns",
                "/api/v1/cebu-trade/payouts",
                "/api/v1/cebu-trade/shipping/routes",
            ):
                resp = await client.get(path)
                assert resp.status_code == 401, f"{path} returned {resp.status_code}"

    asyncio.run(_run())


# ── Admin campaign status only by admin ─────────────────────────────


def test_user_campaign_status_limited_to_allowed_statuses():
    async def _run():
        await engine.dispose()
        vendor_email, password, _ = await _create_identity(role="vendor")
        vendor = await _login(vendor_email, password)

        async with _client() as client:
            campaign = await client.post(
                "/api/v1/cebu-trade/ads/campaigns",
                headers=vendor,
                json={
                    "title": "Status test campaign",
                    "budget_minor": 100000,
                    "bid_per_click_minor": 50,
                },
            )
            assert campaign.status_code == 201
            campaign_id = campaign.json()["id"]

            forbidden_status = await client.patch(
                f"/api/v1/cebu-trade/ads/campaigns/{campaign_id}/status",
                headers=vendor,
                json={"status": "ACTIVE"},
            )
            assert forbidden_status.status_code == 403

            allowed_status = await client.patch(
                f"/api/v1/cebu-trade/ads/campaigns/{campaign_id}/status",
                headers=vendor,
                json={"status": "PAUSED"},
            )
            assert allowed_status.status_code == 200

    asyncio.run(_run())


# ── Wallet deposit cross-user isolation ─────────────────────────────


def test_deposit_list_scoped_to_owner():
    async def _run():
        await engine.dispose()
        user_a_email, password, _ = await _create_identity(role="buyer")
        user_b_email, _, _ = await _create_identity(role="buyer")
        user_a = await _login(user_a_email, password)
        user_b = await _login(user_b_email, password)

        async with _client() as client:
            dep = await client.post(
                "/api/v1/cebu-trade/wallet/deposits",
                headers=user_a,
                json={
                    "amount_minor": 50000,
                    "deposit_address": "ADDR_A",
                },
            )
            assert dep.status_code == 201
            dep_id = dep.json()["id"]

            user_b_deposits = await client.get(
                "/api/v1/cebu-trade/wallet/deposits", headers=user_b
            )
            assert user_b_deposits.status_code == 200
            user_b_ids = {d["id"] for d in user_b_deposits.json()["items"]}
            assert dep_id not in user_b_ids

    asyncio.run(_run())
