"""Cebu payment policy and reconciliation workbench is admin-only and audited."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.db.session import async_session_factory, engine
from app.main import app
from app.models.audit import AuditLog
from app.modules.cebu_trade.models import PaymentEvent, RegionPaymentConfig, SettlementEvent


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def test_cebu_payment_policy_and_reconciliation_are_real_and_admin_only():
    async def _run():
        from tests.test_cebu_trade_security import _create_identity, _login

        await engine.dispose()
        admin_email, password, _ = await _create_identity(role="admin", with_company=False)
        buyer_email, buyer_password, _ = await _create_identity(role="buyer")
        admin = await _login(admin_email, password)
        buyer = await _login(buyer_email, buyer_password)

        async with _client() as client:
            denied = await client.put(
                "/api/v1/admin/cebu/payment-region-configs/PH",
                headers=buyer,
                json={
                    "country_code": "PH", "country_name": "Philippines",
                    "local_currency": "PHP", "default_settlement_currency": "PHP",
                },
            )
            assert denied.status_code == 403
            saved = await client.put(
                "/api/v1/admin/cebu/payment-region-configs/PH",
                headers=admin,
                json={
                    "country_code": "PH", "country_name": "Philippines",
                    "local_currency": "PHP", "default_settlement_currency": "PHP",
                    "enabled_currencies": ["PHP", "USD"],
                    "enabled_payment_methods": ["PHP_MANUAL_BANK"],
                    "cross_border_currencies": ["USD"],
                },
            )
            assert saved.status_code == 200, saved.text
            configs = await client.get("/api/v1/admin/cebu/payment-configs", headers=admin)
            assert configs.status_code == 200, configs.text
            assert any(row["country_code"] == "PH" for row in configs.json()["regions"]["items"])

        async with async_session_factory() as db:
            db.add(PaymentEvent(provider="TEST", event_type="PAYMENT_SUCCEEDED", status="RECEIVED"))
            db.add(SettlementEvent(provider="TEST", gross_amount_minor=1000, net_amount_minor=950, fee_amount_minor=50, currency="PHP", status="MATCHED"))
            await db.commit()

        async with _client() as client:
            reconciliation = await client.get(
                "/api/v1/admin/cebu/reconciliation/payment-events", headers=admin
            )
            assert reconciliation.status_code == 200, reconciliation.text
            assert reconciliation.json()["summary"]["payment_event_count"] >= 1
            assert reconciliation.json()["summary"]["settlement_event_count"] >= 1

        async with async_session_factory() as db:
            assert (
                await db.execute(
                    select(RegionPaymentConfig).where(RegionPaymentConfig.country_code == "PH")
                )
            ).scalar_one()
            actions = set(
                (
                    await db.execute(
                        select(AuditLog.action).where(AuditLog.portal_key == "admin_cebu")
                    )
                ).scalars()
            )
            assert actions & {
                "cebu.admin.payment_region_config_created",
                "cebu.admin.payment_region_config_updated",
            }

    asyncio.run(_run())


def test_cebu_payment_region_fallback_supports_serbia_and_poland():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            await db.execute(
                delete(RegionPaymentConfig).where(
                    RegionPaymentConfig.country_code.in_(["RS", "PL"])
                )
            )
            await db.commit()

        async with _client() as client:
            serbia = await client.get("/api/v1/cebu-compat/payments/region-config?country=RS")
            assert serbia.status_code == 200, serbia.text
            rs_policy = serbia.json()
            assert rs_policy["country_code"] == "RS"
            assert rs_policy["country_name"] == "Serbia"
            assert rs_policy["local_currency"] == "RSD"
            assert rs_policy["local_currency_alias"] == "DIN"
            assert rs_policy["default_settlement_currency"] == "EUR"
            assert rs_policy["settlement_currencies"] == ["EUR", "RSD"]
            assert "USD" not in rs_policy["settlement_currencies"]
            assert rs_policy["reference_rates"]["EUR:RSD"]

            poland = await client.get("/api/v1/cebu-compat/payments/region-config?country=PL")
            assert poland.status_code == 200, poland.text
            pl_policy = poland.json()
            assert pl_policy["country_code"] == "PL"
            assert pl_policy["local_currency"] == "PLN"
            assert pl_policy["default_settlement_currency"] == "PLN"
            assert pl_policy["settlement_currencies"] == ["PLN", "EUR"]

    asyncio.run(_run())
