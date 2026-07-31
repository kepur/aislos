"""Cebu Admin operational actions are real, admin-only and audited."""
import asyncio
import uuid
from datetime import date

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.db.session import async_session_factory, engine
from app.main import app
from app.models.audit import AuditLog
from app.models.commerce import CommerceOrder, OrderDispute, ProcurementRequest, TrustProfile, TrustScoreEvent
from app.models.user import User
from app.modules.cebu_trade.models import AdCampaign, EscrowTransaction, Payout, Wallet, WalletDeposit
from app.modules.kyc.models import CompanyDocument, VerificationReview


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def test_cebu_admin_operational_actions_are_admin_only_and_audited():
    async def _run():
        from tests.test_cebu_trade_security import _create_identity, _login

        await engine.dispose()
        admin_email, password, _ = await _create_identity(role="admin", with_company=False)
        buyer_email, buyer_password, buyer_company = await _create_identity(role="buyer")
        supplier_email, _, supplier_company = await _create_identity(role="vendor")
        admin = await _login(admin_email, password)
        buyer = await _login(buyer_email, buyer_password)

        async with async_session_factory() as db:
            buyer_user = (await db.execute(select(User).where(User.email == buyer_email))).scalar_one()
            request = ProcurementRequest(
                buyer_company_id=buyer_company,
                buyer_user_id=buyer_user.id,
                portal_key="cebu",
                title="Admin actions request",
                status="awarded",
            )
            db.add(request)
            await db.flush()
            order = CommerceOrder(
                procurement_request_id=request.id,
                buyer_company_id=buyer_company,
                supplier_company_id=supplier_company,
                status="disputed",
                total_minor=50000,
                currency="PHP",
            )
            db.add(order)
            wallet = Wallet(owner_user_id=buyer_user.id, currency="PHP")
            db.add(wallet)
            await db.flush()
            deposit = WalletDeposit(
                wallet_id=wallet.id,
                owner_user_id=buyer_user.id,
                amount_minor=10000,
                currency="PHP",
                deposit_address="bank-reference",
                status="SUBMITTED",
            )
            campaign = AdCampaign(
                company_id=supplier_company,
                title="Admin review campaign",
                placement="FEED_TOP",
                budget_minor=10000,
                bid_per_click_minor=10,
                currency="PHP",
                status="PENDING_REVIEW",
            )
            db.add_all([deposit, campaign])
            await db.flush()
            dispute = OrderDispute(
                workspace_id=order.workspace_id,
                commerce_order_id=order.id,
                opened_by_user_id=buyer_user.id,
                opened_by_role="buyer",
                reason_code="non_delivery",
                status="open",
            )
            escrow = EscrowTransaction(
                order_id=order.id,
                auth_amount_minor=50000,
                captured_amount_minor=50000,
                currency="PHP",
                status="CAPTURED",
            )
            payout = Payout(
                company_id=supplier_company,
                order_id=order.id,
                amount_minor=50000,
                currency="PHP",
                status="PENDING",
            )
            review = VerificationReview(company_id=supplier_company, status="SUBMITTED")
            document = CompanyDocument(
                company_id=supplier_company,
                doc_type="BUSINESS_REGISTRATION",
                file_url="https://example.com/kyc.pdf",
                status="PENDING",
            )
            trust = TrustProfile(company_id=supplier_company, portal_key="cebu", trust_score=50)
            db.add_all([dispute, escrow, payout, review, document, trust])
            await db.commit()
            ids = {
                "deposit": deposit.id, "campaign": campaign.id, "dispute": dispute.id,
                "escrow": escrow.id, "payout": payout.id, "review": review.id,
                "document": document.id, "trust": trust.id, "order": order.id,
            }

        async with _client() as client:
            denied = await client.post(
                f"/api/v1/admin/cebu-trade/deposits/{ids['deposit']}/verify",
                headers=buyer,
                json={"admin_note": "not allowed"},
            )
            assert denied.status_code == 403

            deposit = await client.post(
                f"/api/v1/admin/cebu-trade/deposits/{ids['deposit']}/verify",
                headers=admin,
                json={"admin_note": "bank transfer confirmed"},
            )
            assert deposit.status_code == 200, deposit.text
            assert deposit.json()["status"] == "VERIFIED"

            campaign = await client.patch(
                f"/api/v1/admin/cebu-trade/ads/campaigns/{ids['campaign']}/status",
                headers=admin,
                json={"status": "ACTIVE"},
            )
            assert campaign.status_code == 200, campaign.text

            route = await client.post(
                "/api/v1/admin/cebu-trade/shipping/routes",
                headers=admin,
                json={"origin_country": "PH", "dest_country": "PL", "shipping_method": "AIR"},
            )
            assert route.status_code == 201, route.text
            route_id = route.json()["id"]
            updated_route = await client.patch(
                f"/api/v1/admin/cebu-trade/shipping/routes/{route_id}",
                headers=admin,
                json={"description": "Audited route"},
            )
            assert updated_route.status_code == 200, updated_route.text
            rate = await client.post(
                "/api/v1/admin/cebu-trade/shipping/rates",
                headers=admin,
                json={
                    "route_id": route_id,
                    "price_per_kg_minor": 2500,
                    "currency": "PHP",
                    "valid_from": date.today().isoformat(),
                },
            )
            assert rate.status_code == 201, rate.text
            disabled_rate = await client.delete(
                f"/api/v1/admin/cebu-trade/shipping/rates/{rate.json()['id']}", headers=admin
            )
            assert disabled_rate.status_code == 204, disabled_rate.text

            document = await client.post(
                f"/api/v1/admin/kyc/documents/{ids['document']}/review",
                headers=admin,
                json={"status": "ACCEPTED", "reviewer_note": "document checked"},
            )
            assert document.status_code == 200, document.text
            review = await client.post(
                f"/api/v1/admin/kyc/verification/{ids['review']}/decide",
                headers=admin,
                json={"decision": "APPROVE_BUSINESS", "decision_reason": "documents accepted"},
            )
            assert review.status_code == 200, review.text
            assert review.json()["status"] == "APPROVED_BUSINESS"

            dispute = await client.post(
                f"/api/v1/admin/cebu/disputes/{ids['dispute']}/resolve",
                headers=admin,
                json={"resolution": "resolved_buyer", "reason": "delivery evidence absent"},
            )
            assert dispute.status_code == 200, dispute.text

            refund = await client.post(
                f"/api/v1/admin/cebu-trade/escrow/{ids['escrow']}/refund",
                headers=admin,
                json={"amount_minor": 10000, "reason": "partial dispute refund"},
            )
            assert refund.status_code == 200, refund.text
            assert refund.json()["refunded_amount_minor"] == 10000

            payout = await client.post(
                f"/api/v1/admin/cebu-trade/payouts/{ids['payout']}/process",
                headers=admin,
                params={"new_status": "PAID", "provider_reference": "provider-123"},
            )
            assert payout.status_code == 200, payout.text
            assert payout.json()["status"] == "PAID"

            trust = await client.post(
                f"/api/v1/admin/cebu/trust-profiles/{ids['trust']}/adjust",
                headers=admin,
                json={"delta": 5, "reason": "verified successful delivery"},
            )
            assert trust.status_code == 200, trust.text
            assert trust.json()["trust_score"] == 55
            trust_events = await client.get(
                f"/api/v1/admin/cebu/trust-profiles/{ids['trust']}/events", headers=admin
            )
            assert trust_events.status_code == 200, trust_events.text
            assert trust_events.json()["items"][0]["event_type"] == "ADMIN_ADJUSTED"
            denied_trust_events = await client.get(
                f"/api/v1/admin/cebu/trust-profiles/{ids['trust']}/events", headers=buyer
            )
            assert denied_trust_events.status_code == 403

            notification = await client.post(
                "/api/v1/admin/cebu/notifications/test",
                headers=admin,
                json={"title": "Operational test"},
            )
            assert notification.status_code == 201, notification.text

            held = await client.post(
                f"/api/v1/admin/cebu/orders/{ids['order']}/hold",
                headers=admin,
                json={"reason": "Risk review required"},
            )
            assert held.status_code == 200, held.text
            assert held.json()["admin_hold"] is True
            released = await client.post(
                f"/api/v1/admin/cebu/orders/{ids['order']}/release-hold",
                headers=admin,
                json={"reason": "Risk review completed"},
            )
            assert released.status_code == 200, released.text
            assert released.json()["admin_hold"] is False

            risk = await client.post(
                "/api/v1/admin/cebu/risk-flags",
                headers=admin,
                json={
                    "subject_type": "commerce_order",
                    "subject_id": str(ids["order"]),
                    "company_id": str(buyer_company),
                    "reason_code": "manual_review",
                    "severity": "high",
                },
            )
            assert risk.status_code == 201, risk.text
            acted = await client.post(
                f"/api/v1/admin/cebu/risk-flags/{risk.json()['id']}/action",
                headers=admin,
                json={"status": "resolved", "action_taken": "Identity and payment evidence checked"},
            )
            assert acted.status_code == 200, acted.text
            assert acted.json()["status"] == "resolved"

        async with async_session_factory() as db:
            actions = set(
                (
                    await db.execute(
                        select(AuditLog.action).where(AuditLog.portal_key == "admin_cebu")
                    )
                ).scalars()
            )
            assert {
                "cebu.admin.deposit_verified",
                "cebu.admin.ad_campaign_status_changed",
                "cebu.admin.shipping_route_created",
                "cebu.admin.shipping_rate_deactivated",
                "cebu.admin.kyc_document_reviewed",
                "cebu.admin.kyc_verification_decided",
                "cebu.admin.dispute_resolved",
                "cebu.admin.escrow_refunded",
                "cebu.admin.payout_processed",
                "cebu.admin.trust_score_adjusted",
                "cebu.admin.notification_tested",
                "cebu.admin.order_held",
                "cebu.admin.order_hold_released",
                "cebu.admin.risk_flag_created",
                "cebu.admin.risk_action_taken",
            }.issubset(actions)
            trust_events = list(
                (
                    await db.execute(
                        select(TrustScoreEvent).where(TrustScoreEvent.trust_profile_id == ids["trust"])
                    )
                ).scalars()
            )
            assert trust_events and trust_events[-1].after_score == 55

    asyncio.run(_run())
