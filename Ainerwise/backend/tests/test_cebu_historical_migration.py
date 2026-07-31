"""Historical Cebu imports are admin-only, idempotent and preserve ownership links."""
import asyncio
import uuid

from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from app.db.session import async_session_factory, engine
from app.main import app
from app.models.admin_config import AdminNote, NotificationTemplate, PlatformSetting
from app.models.audit import AuditLog
from app.models.backup import BackupJob, BackupSchedule
from app.models.commerce import (
    CommerceOrder,
    ProcurementRequest,
    RiskFlag,
    SupplierListing,
    SupplierOffer,
    TransactionReview,
    TrustProfile,
    TrustScoreEvent,
)
from app.models.commerce_geo import CompanyBranch, ServiceArea
from app.models.legacy_bridge import LegacyIdentityMapping
from app.models.legacy_migration import LegacyMigrationRecord, LegacyMigrationRun
from app.models.region import Region
from app.models.user import Company, User
from app.modules.buyer_project.models import (
    BuyerProject,
    ProjectMetricTemplate,
    ProjectMetricValue,
    ProjectLineItem,
    ProjectPriceSnapshot,
    ProjectReport,
    ProjectReportVersion,
    ProjectReportColumn,
    ProjectReportRow,
    ProjectReportChangeLog,
)
from app.modules.kyc.models import KYCAnalysisResult
from app.modules.cebu_trade.models import (
    CurrencyConfig,
    EscrowTransaction,
    FeeLineItem,
    FeeRule,
    FxQuote,
    OrderShipping,
    Payout,
    PaymentEvent,
    PaymentMethodConfig,
    PaymentQuote,
    ProviderPaymentIntent,
    RegionPaymentConfig,
    SettlementAdjustment,
    SettlementEvent,
)


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _bundle(batch_key: str) -> tuple[dict, dict]:
    ids = {key: str(uuid.uuid4()) for key in (
        "company", "supplier", "buyer", "category", "listing", "intent", "offer", "order",
        "wallet", "wallet_tx", "deposit", "address", "shipping_route", "shipping_rate",
        "order_shipping", "delivery", "campaign", "escrow", "payout", "dispute", "trust",
        "document", "verification", "notification", "message",
        "region", "project", "project_file", "project_ai_run", "project_message",
        "project_line_item", "transaction_review", "kyc_analysis", "risk_flag", "future",
        "admin_note", "notification_template", "platform_setting",
        "project_metric_template",
        "project_metric_value", "project_price_snapshot", "project_report",
        "project_report_version", "project_report_column", "project_report_row",
        "project_report_change_log", "trust_score_event",
        "branch", "service_area",
        "payment_event", "region_payment_config", "currency_config", "payment_method_config",
        "fee_rule", "fx_quote", "payment_quote", "fee_line_item", "payment_intent",
        "settlement_event", "settlement_adjustment",
        "audit_log", "backup_schedule", "backup_job",
    )}
    bundle = {
        "batch_key": batch_key,
        "source_system": "cebu",
        "portal_key": "cebu",
        "companies": [{
            "id": ids["company"],
            "owner_user_id": ids["supplier"],
            "name": "Legacy Supplier Company",
            "country": "Philippines",
            "status": "ACTIVE",
            "verification_level": "BUSINESS",
            "tax_id": "LEGACY-TAX-1",
        }],
        "users": [
            {
                "id": ids["supplier"],
                "email": f"legacy-supplier-{ids['supplier'][:8]}@example.com",
                "full_name": "Legacy Supplier",
                "role": "SUPPLIER_ADMIN",
                "status": "ACTIVE",
                "password_hash": "must-never-be-imported",
            },
            {
                "id": ids["buyer"],
                "email": f"legacy-buyer-{ids['buyer'][:8]}@example.com",
                "full_name": "Legacy Buyer",
                "role": "BUYER",
                "status": "ACTIVE",
                "password_hash": "must-never-be-imported",
            },
        ],
        "branches": [{
            "id": ids["branch"], "company_id": ids["company"], "name": "Legacy Cebu Branch",
            "country": "Philippines", "city": "Cebu", "radius_km": 35,
            "delivery_methods": ["DELIVERY", "INSTALLATION"], "status": "ACTIVE",
        }],
        "categories": [{
            "id": ids["category"], "name": "Smart Locks", "slug": f"smart-locks-{ids['category'][:8]}",
            "status": "ACTIVE", "schema_json": {"brand": {"type": "string"}},
        }],
        "catalog_items": [{
            "id": ids["listing"], "company_id": ids["company"], "category_id": ids["category"],
            "title": "Legacy Smart Lock", "price_minor": 1250000, "currency": "PHP",
            "stock_qty": 10, "status": "ACTIVE",
        }],
        "regions": [{
            "id": ids["region"], "name": "Metro Cebu", "slug": "metro-cebu",
            "country": "Philippines", "city": "Cebu", "status": "ACTIVE",
        }],
        "service_areas": [{
            "id": ids["service_area"], "name": "Legacy Metro Cebu Area",
            "region_id": ids["region"], "company_id": ids["company"], "coverage_type": "RADIUS",
            "center_lat": 10.3157, "center_lng": 123.8854, "radius_km": 40, "status": "ACTIVE",
        }],
        "buyer_projects": [{
            "id": ids["project"], "buyer_id": ids["buyer"], "title": "Legacy Villa Upgrade",
            "project_type": "RENOVATION", "status": "AI_ANALYZED", "country": "Philippines",
            "city": "Cebu", "currency": "PHP", "missing_questions_jsonb": ["Need floor plan?"],
            "acceptance_criteria_jsonb": ["All locks commissioned"],
        }],
        "project_files": [{
            "id": ids["project_file"], "project_id": ids["project"],
            "url": "https://example.com/floor-plan.pdf", "file_name": "floor-plan.pdf",
            "content_type": "application/pdf", "status": "EXTRACTED",
        }],
        "project_ai_runs": [{
            "id": ids["project_ai_run"], "project_id": ids["project"], "provider": "legacy-ai",
            "model": "legacy-model", "status": "SUCCESS", "structured_output_jsonb": {"rooms": 4},
        }],
        "project_messages": [{
            "id": ids["project_message"], "project_id": ids["project"], "role": "USER",
            "workflow_node": "intake_chat", "content": "Upgrade this villa",
        }],
        "project_metric_templates": [{
            "id": ids["project_metric_template"], "project_type": "RENOVATION",
            "key": "room_count", "label": "Room count", "data_type": "number",
            "required": True, "sort_order": 10, "active": True,
        }],
        "project_metric_values": [{
            "id": ids["project_metric_value"], "project_id": ids["project"],
            "template_id": ids["project_metric_template"], "key": "room_count",
            "label": "Room count", "value_jsonb": {"value": 4, "unit": "rooms"},
            "source": "AI", "confidence": 0.94,
        }],
        "intents": [{
            "id": ids["intent"], "buyer_id": ids["buyer"], "category_id": ids["category"],
            "title": "Need a smart lock", "qty": 2, "unit": "piece", "status": "ACTIVE",
            "budget_max_minor": 3000000, "currency": "PHP",
        }],
        "project_line_items": [{
            "id": ids["project_line_item"], "project_id": ids["project"],
            "ai_run_id": ids["project_ai_run"], "category_id": ids["category"],
            "intent_id": ids["intent"], "name": "Smart lock installation",
            "qty": 2, "unit": "pcs", "quality_tier": "MID_RANGE",
            "confidence": 0.91, "status": "SOURCING",
            "sourcing_notes": "Use Cebu certified installer", "category_hint": "smart-locks",
        }],
        "project_price_snapshots": [{
            "id": ids["project_price_snapshot"], "project_id": ids["project"],
            "line_item_id": ids["project_line_item"], "currency": "PHP",
            "sample_count": 3, "min_unit_price": 1100000, "avg_unit_price": 1250000,
            "median_unit_price": 1250000, "p20_unit_price": 1150000,
            "p80_unit_price": 1350000, "samples_jsonb": [{"price": 1250000}],
            "source_summary": "Legacy Cebu suppliers",
        }],
        "project_reports": [{
            "id": ids["project_report"], "project_id": ids["project"],
            "current_version_id": ids["project_report_version"],
            "frozen_version_id": ids["project_report_version"],
        }],
        "project_report_versions": [{
            "id": ids["project_report_version"], "report_id": ids["project_report"],
            "project_id": ids["project"], "version_number": 1, "status": "FROZEN",
            "source": "AI", "title": "Legacy Villa BOQ",
            "summary_jsonb": {"rooms": 4}, "totals_jsonb": {"PHP": 2500000},
            "created_by": ids["buyer"],
        }],
        "project_report_columns": [{
            "id": ids["project_report_column"],
            "report_version_id": ids["project_report_version"], "key": "name",
            "label": "Item", "data_type": "text", "sort_order": 1,
            "editable": True, "system": True,
        }],
        "project_report_rows": [{
            "id": ids["project_report_row"],
            "report_version_id": ids["project_report_version"], "project_id": ids["project"],
            "line_item_id": ids["project_line_item"], "category_id": ids["category"],
            "name": "Smart lock installation", "qty": 2, "unit": "pcs",
            "currency": "PHP", "quality_tier": "MID_RANGE", "selected_tier": "MID_RANGE",
            "include_in_total": True, "selected_for_purchase": True,
            "match_status": "MATCHED", "price_source": "SUPPLIER_SAMPLE",
        }],
        "project_report_change_logs": [{
            "id": ids["project_report_change_log"], "project_id": ids["project"],
            "report_id": ids["project_report"], "version_id": ids["project_report_version"],
            "actor_id": ids["buyer"], "change_type": "FREEZE", "status": "APPLIED",
            "user_message": "Freeze legacy BOQ", "patch_jsonb": {"status": "FROZEN"},
        }],
        "offers": [{
            "id": ids["offer"], "intent_id": ids["intent"], "company_id": ids["company"],
            "catalog_item_id": ids["listing"], "supplier_user_id": ids["supplier"],
            "unit_price_minor": 1250000, "qty_available": 2, "total_price_minor": 2500000,
            "currency": "PHP", "status": "AWARDED",
        }],
        "orders": [{
            "id": ids["order"], "offer_id": ids["offer"], "intent_id": ids["intent"],
            "buyer_id": ids["buyer"], "company_id": ids["company"],
            "total_amount_minor": 2500000, "currency": "PHP", "status": "ACCEPTED",
        }],
        "transaction_reviews": [{
            "id": ids["transaction_review"], "order_id": ids["order"], "reviewer_id": ids["buyer"],
            "reviewee_company_id": ids["company"], "target_type": "SELLER",
            "overall_rating": 5, "comment": "Legacy excellent delivery",
        }],
        "wallets": [{
            "id": ids["wallet"], "owner_user_id": ids["buyer"], "currency": "PHP",
            "available_balance_minor": 150000, "total_deposited_minor": 150000, "status": "ACTIVE",
        }],
        "wallet_transactions": [{
            "id": ids["wallet_tx"], "wallet_id": ids["wallet"], "owner_user_id": ids["buyer"],
            "tx_type": "DEPOSIT_VERIFIED", "amount_delta_minor": 150000,
            "available_balance_after_minor": 150000, "currency": "PHP",
        }],
        "wallet_deposits": [{
            "id": ids["deposit"], "wallet_id": ids["wallet"], "owner_user_id": ids["buyer"],
            "amount_minor": 150000, "currency": "PHP", "deposit_address": "legacy-bank",
            "status": "VERIFIED",
        }],
        "addresses": [{
            "id": ids["address"], "user_id": ids["buyer"], "address_type": "DELIVERY_TO",
            "label": "Legacy delivery", "contact_name": "Legacy Buyer", "contact_phone": "+63900",
            "country_code": "PH", "country_name": "Philippines", "city": "Cebu",
            "address_line1": "Legacy address", "status": "ACTIVE",
        }],
        "shipping_routes": [{
            "id": ids["shipping_route"], "origin_country": "PH", "dest_country": "PL",
            "shipping_method": "AIR_FREIGHT", "status": "ACTIVE",
        }],
        "shipping_rates": [{
            "id": ids["shipping_rate"], "route_id": ids["shipping_route"],
            "price_per_kg_minor": 2500, "currency": "PHP", "valid_from": "2026-01-01",
            "status": "ACTIVE",
        }],
        "order_shipping": [{
            "id": ids["order_shipping"], "order_id": ids["order"],
            "shipping_method": "AIR_FREIGHT", "dest_address_id": ids["address"],
            "shipping_cost_minor": 2500, "currency": "PHP", "status": "SHIPPED",
        }],
        "deliveries": [{
            "id": ids["delivery"], "order_id": ids["order"], "status": "DELIVERED",
            "carrier": "Legacy Carrier", "tracking_number": "LEGACY-TRACK-1",
            "proofs": [{"url": "https://example.com/proof.jpg"}], "actor_id": ids["supplier"],
        }],
        "ad_campaigns": [{
            "id": ids["campaign"], "company_id": ids["company"], "catalog_item_id": ids["listing"],
            "title": "Legacy Campaign", "placement": "FEED_TOP", "budget_minor": 100000,
            "bid_per_click_minor": 100, "currency": "PHP", "status": "ACTIVE",
        }],
        "escrow_transactions": [{
            "id": ids["escrow"], "order_id": ids["order"], "auth_amount_minor": 2500000,
            "captured_amount_minor": 2500000, "currency": "PHP", "status": "CAPTURED",
        }],
        "payouts": [{
            "id": ids["payout"], "company_id": ids["company"], "order_id": ids["order"],
            "escrow_id": ids["escrow"], "amount_minor": 2500000, "currency": "PHP", "status": "PAID",
        }],
        "disputes": [{
            "id": ids["dispute"], "order_id": ids["order"], "opened_by_user_id": ids["buyer"],
            "reason": "Legacy dispute", "status": "RESOLVED_REFUND", "refund_amount_minor": 100000,
        }],
        "trust_profiles": [{
            "id": ids["trust"], "entity_type": "COMPANY", "entity_id": ids["company"],
            "trust_score": 82, "successful_deals_count": 7, "dispute_rate": 2, "status": "ACTIVE",
        }],
        "trust_score_events": [{
            "id": ids["trust_score_event"], "trust_profile_id": ids["trust"],
            "event_type": "RECALCULATED", "score_delta": 7, "before_score": 75,
            "after_score": 82, "reason": "Legacy order completed",
            "related_entity_type": "ORDER", "related_entity_id": ids["order"],
            "created_by": ids["supplier"],
        }],
        "company_documents": [{
            "id": ids["document"], "company_id": ids["company"], "doc_type": "BUSINESS_REGISTRATION",
            "file_url": "https://example.com/legacy-registration.pdf", "status": "ACCEPTED",
        }],
        "kyc_analysis_results": [{
            "id": ids["kyc_analysis"], "company_id": ids["company"], "document_id": ids["document"],
            "analyzed_by": ids["supplier"], "authenticity": "AUTHENTIC", "confidence": 0.94,
            "overall_risk_score": 0.08, "recommended_action": "APPROVE",
        }],
        "verification_reviews": [{
            "id": ids["verification"], "company_id": ids["company"], "status": "APPROVED_BUSINESS",
            "decision": "APPROVE_BUSINESS", "decision_reason": "Legacy approved",
        }],
        "risk_flags": [{
            "id": ids["risk_flag"], "entity_type": "ORDER", "entity_id": ids["order"],
            "risk_type": "PAYMENT_MISMATCH", "risk_level": "HIGH", "status": "CLOSED",
            "description": "Resolved legacy mismatch",
        }],
        "payment_events": [{
            "id": ids["payment_event"], "provider": "LEGACY_PSP", "event_type": "PAYMENT_SUCCEEDED",
            "order_id": ids["order"], "escrow_id": ids["escrow"], "amount_minor": 2500000,
            "currency": "PHP", "status": "PROCESSED",
        }],
        "region_payment_configs": [{
            "id": ids["region_payment_config"], "country_code": "PH", "country_name": "Philippines",
            "local_currency": "PHP", "default_settlement_currency": "PHP",
            "default_transaction_mode": "LOCAL_ONLY", "enabled_currencies": ["PHP", "USD"],
            "enabled_payment_methods": ["PHP_MANUAL_BANK"], "cross_border_currencies": ["USD"],
        }],
        "currency_configs": [{
            "id": ids["currency_config"], "code": "PHP", "name": "Philippine Peso",
            "minor_unit": 2, "is_fiat": True, "is_enabled": True,
        }],
        "payment_method_configs": [{
            "id": ids["payment_method_config"], "country_code": "PH",
            "method_code": "PHP_MANUAL_BANK", "provider": "LEGACY_PSP",
            "currency": "PHP", "is_enabled": True,
        }],
        "fee_rules": [{
            "id": ids["fee_rule"], "name": "Legacy platform fee", "country_code": "PH",
            "fee_type": "PLATFORM_SERVICE_FEE", "currency": "PHP", "variable_bps": 100,
        }],
        "fx_quotes": [{
            "id": ids["fx_quote"], "source_currency": "PHP", "target_currency": "USD",
            "rate": "0.0172", "rate_source": "LEGACY_RATE_TABLE", "expires_at": "2027-01-01T00:00:00Z",
        }],
        "payment_quotes": [{
            "id": ids["payment_quote"], "buyer_country": "PH", "supplier_country": "PH",
            "mode": "LOCAL_ONLY", "payment_method": "PHP_MANUAL_BANK", "order_currency": "PHP",
            "payer_currency": "PHP", "settlement_currency": "PHP", "amount_minor": 2500000,
            "payer_total_minor": 2525000, "escrow_amount_minor": 2500000,
            "supplier_estimated_net_minor": 2475000, "platform_revenue_minor": 25000,
            "fx_quote_id": ids["fx_quote"], "expires_at": "2027-01-01T00:00:00Z", "status": "CONFIRMED",
        }],
        "payment_intents": [{
            "id": ids["payment_intent"], "quote_id": ids["payment_quote"], "order_id": ids["order"],
            "provider": "LEGACY_PSP", "provider_reference": "LEGACY-PAY-1",
            "payment_method": "PHP_MANUAL_BANK", "amount_minor": 2525000,
            "currency": "PHP", "status": "SUCCEEDED",
        }],
        "fee_line_items": [{
            "id": ids["fee_line_item"], "quote_id": ids["payment_quote"],
            "payment_intent_id": ids["payment_intent"], "fee_type": "PLATFORM_SERVICE_FEE",
            "label": "Legacy platform fee", "amount_minor": 25000, "currency": "PHP",
        }],
        "settlement_events": [{
            "id": ids["settlement_event"], "payment_intent_id": ids["payment_intent"],
            "provider": "LEGACY_PSP", "provider_reference": "LEGACY-SETTLE-1",
            "gross_amount_minor": 2525000, "fee_amount_minor": 25000,
            "net_amount_minor": 2500000, "currency": "PHP", "status": "MATCHED",
        }],
        "settlement_adjustments": [{
            "id": ids["settlement_adjustment"], "settlement_event_id": ids["settlement_event"],
            "adjustment_type": "ROUNDING", "amount_minor": -1, "currency": "PHP",
            "reason": "Legacy reconciliation adjustment",
        }],
        "notifications": [{
            "id": ids["notification"], "user_id": ids["buyer"], "channel": "IN_APP",
            "notification_type": "ORDER_ACCEPTED", "subject": "Legacy order accepted",
            "body": "The legacy order was accepted.", "status": "READ",
        }],
        "messages": [{
            "id": ids["message"], "thread_type": "ORDER", "thread_id": ids["order"],
            "sender_id": ids["buyer"], "body": "Legacy order message", "attachments": [],
        }],
        "admin_notes": [{
            "id": ids["admin_note"], "author_id": ids["supplier"], "entity_type": "ORDER",
            "entity_id": ids["order"], "visibility": "INTERNAL_ONLY",
            "note": "Legacy order reviewed by operations.",
        }],
        "notification_templates": [{
            "id": ids["notification_template"], "template_key": "legacy-order-awarded",
            "channel": "EMAIL", "language": "en", "subject": "Order awarded",
            "body": "Legacy order {{ order_id }} was awarded.", "active": True,
        }],
        "platform_settings": [{
            "id": ids["platform_setting"], "key": "commerce.quote_expiry",
            "value_json": {"days": 7}, "description": "Legacy quote expiry policy.",
        }],
        "audit_logs": [{
            "id": ids["audit_log"], "actor_id": ids["supplier"], "actor_role": "SUPPLIER_ADMIN",
            "action": "ORDER_STATUS_CHANGED", "entity_type": "ORDER", "entity_id": ids["order"],
            "before_json": {"status": "DELIVERED"}, "after_json": {"status": "ACCEPTED"},
            "ip_address": "127.0.0.1", "user_agent": "Legacy Cebu", "risk_level": "LOW",
        }],
        "backup_schedules": [{
            "id": ids["backup_schedule"], "name": "Legacy Cebu weekly",
            "frequency": "WEEKLY", "day_of_week": 1, "hour": 3, "minute": 30,
            "enabled": True, "retention_count": 8, "retention_days": 120,
            "created_by": ids["supplier"],
        }],
        "backup_jobs": [{
            "id": ids["backup_job"], "schedule_id": ids["backup_schedule"],
            "status": "SUCCESS", "archive_path": "/legacy/backups/cebu.zip",
            "archive_size_bytes": 123456, "created_by": ids["supplier"],
        }],
        "future_cebu_objects": [{
            "id": ids["future"], "name": "Preserve this future object",
            "password": "must-not-be-stored", "nested": {"secret": "also-remove", "value": 7},
        }],
    }
    return bundle, ids


def test_cebu_historical_migration_is_admin_only_idempotent_and_linked():
    async def _run():
        from tests.test_cebu_trade_security import _create_identity, _login

        await engine.dispose()
        admin_email, password, _ = await _create_identity(role="admin", with_company=False)
        buyer_email, buyer_password, _ = await _create_identity(role="buyer")
        admin = await _login(admin_email, password)
        buyer = await _login(buyer_email, buyer_password)
        bundle, ids = _bundle(f"migration-test-{uuid.uuid4()}")

        async with _client() as client:
            denied_read = await client.get("/api/v1/admin/cebu/migrations", headers=buyer)
            denied_write = await client.post(
                "/api/v1/admin/cebu/migrations/import", headers=buyer, json=bundle
            )
            assert denied_read.status_code == 403
            assert denied_write.status_code == 403

            imported = await client.post(
                "/api/v1/admin/cebu/migrations/import", headers=admin, json=bundle
            )
            assert imported.status_code == 200, imported.text
            result = imported.json()
            assert result["status"] == "COMPLETED"
            assert result["total_records"] == 63
            assert result["succeeded_records"] == 63
            assert result["failed_records"] == 0
            assert result["reused"] is False

            rerun = await client.post(
                "/api/v1/admin/cebu/migrations/import", headers=admin, json=bundle
            )
            assert rerun.status_code == 200, rerun.text
            assert rerun.json()["id"] == result["id"]
            assert rerun.json()["reused"] is True

            changed = {**bundle, "companies": [{**bundle["companies"][0], "name": "Changed"}]}
            conflict = await client.post(
                "/api/v1/admin/cebu/migrations/import", headers=admin, json=changed
            )
            assert conflict.status_code == 409

            detail = await client.get(
                f"/api/v1/admin/cebu/migrations/{result['id']}", headers=admin
            )
            assert detail.status_code == 200, detail.text
            assert len(detail.json()["records"]) == 63
            assert all(row["status"] == "SUCCESS" for row in detail.json()["records"])

            legacy_login = await client.post(
                "/api/v1/auth/login",
                json={"email": bundle["users"][0]["email"], "password": "must-never-be-imported"},
            )
            assert legacy_login.status_code == 401

        async with async_session_factory() as db:
            run_count = int(
                (await db.execute(
                    select(func.count()).select_from(LegacyMigrationRun).where(
                        LegacyMigrationRun.batch_key == bundle["batch_key"]
                    )
                )).scalar_one()
            )
            assert run_count == 1
            record_count = int(
                (await db.execute(
                    select(func.count()).select_from(LegacyMigrationRecord).where(
                        LegacyMigrationRecord.run_id == uuid.UUID(result["id"])
                    )
                )).scalar_one()
            )
            assert record_count == 63

            archived = (
                await db.execute(
                    select(LegacyMigrationRecord).where(
                        LegacyMigrationRecord.entity_type == "future_cebu_objects",
                        LegacyMigrationRecord.legacy_id == ids["future"],
                    )
                )
            ).scalar_one()
            assert archived.operation == "archived"
            assert "password" not in archived.source_payload_json
            assert "secret" not in archived.source_payload_json["nested"]
            assert archived.source_payload_json["nested"]["value"] == 7

            imported_user_record = (
                await db.execute(
                    select(LegacyMigrationRecord).where(
                        LegacyMigrationRecord.entity_type == "users",
                        LegacyMigrationRecord.legacy_id == ids["supplier"],
                    )
                )
            ).scalar_one()
            assert "password_hash" not in imported_user_record.source_payload_json

            company_id = (
                await db.execute(
                    select(LegacyMigrationRecord.core_entity_id).where(
                        LegacyMigrationRecord.entity_type == "companies",
                        LegacyMigrationRecord.legacy_id == ids["company"],
                    )
                )
            ).scalar_one()
            supplier_id = (
                await db.execute(
                    select(LegacyMigrationRecord.core_entity_id).where(
                        LegacyMigrationRecord.entity_type == "users",
                        LegacyMigrationRecord.legacy_id == ids["supplier"],
                    )
                )
            ).scalar_one()
            listing_id = (
                await db.execute(
                    select(LegacyMigrationRecord.core_entity_id).where(
                        LegacyMigrationRecord.entity_type == "catalog_items",
                        LegacyMigrationRecord.legacy_id == ids["listing"],
                    )
                )
            ).scalar_one()
            intent_id = (
                await db.execute(
                    select(LegacyMigrationRecord.core_entity_id).where(
                        LegacyMigrationRecord.entity_type == "intents",
                        LegacyMigrationRecord.legacy_id == ids["intent"],
                    )
                )
            ).scalar_one()
            offer_id = (
                await db.execute(
                    select(LegacyMigrationRecord.core_entity_id).where(
                        LegacyMigrationRecord.entity_type == "offers",
                        LegacyMigrationRecord.legacy_id == ids["offer"],
                    )
                )
            ).scalar_one()
            order_id = (
                await db.execute(
                    select(LegacyMigrationRecord.core_entity_id).where(
                        LegacyMigrationRecord.entity_type == "orders",
                        LegacyMigrationRecord.legacy_id == ids["order"],
                    )
                )
            ).scalar_one()

            company = await db.get(Company, company_id)
            supplier = await db.get(User, supplier_id)
            listing = await db.get(SupplierListing, listing_id)
            intent = await db.get(ProcurementRequest, intent_id)
            offer = await db.get(SupplierOffer, offer_id)
            order = await db.get(CommerceOrder, order_id)
            assert company and company.verification_status == "verified"
            assert supplier and supplier.company_id == company_id and supplier.role == "vendor"
            assert listing and listing.company_id == company_id
            assert intent and intent.buyer_user_id is not None
            assert offer and offer.procurement_request_id == intent_id and offer.supplier_company_id == company_id
            assert order and order.winning_offer_id == offer_id and order.supplier_company_id == company_id

            assert await db.get(Region, (
                await db.execute(select(LegacyMigrationRecord.core_entity_id).where(
                    LegacyMigrationRecord.entity_type == "regions",
                    LegacyMigrationRecord.legacy_id == ids["region"],
                ))
            ).scalar_one())
            imported_project = await db.get(BuyerProject, (
                await db.execute(select(LegacyMigrationRecord.core_entity_id).where(
                    LegacyMigrationRecord.entity_type == "buyer_projects",
                    LegacyMigrationRecord.legacy_id == ids["project"],
                ))
            ).scalar_one())
            assert imported_project and imported_project.acceptance_criteria_json == ["All locks commissioned"]
            imported_project_line_item = await db.get(ProjectLineItem, (
                await db.execute(select(LegacyMigrationRecord.core_entity_id).where(
                    LegacyMigrationRecord.entity_type == "project_line_items",
                    LegacyMigrationRecord.legacy_id == ids["project_line_item"],
                ))
            ).scalar_one())
            assert imported_project_line_item and imported_project_line_item.category_hint == "smart-locks"
            assert imported_project_line_item.sourcing_notes == "Use Cebu certified installer"
            assert await db.get(KYCAnalysisResult, (
                await db.execute(select(LegacyMigrationRecord.core_entity_id).where(
                    LegacyMigrationRecord.entity_type == "kyc_analysis_results",
                    LegacyMigrationRecord.legacy_id == ids["kyc_analysis"],
                ))
            ).scalar_one())
            assert await db.get(TransactionReview, (
                await db.execute(select(LegacyMigrationRecord.core_entity_id).where(
                    LegacyMigrationRecord.entity_type == "transaction_reviews",
                    LegacyMigrationRecord.legacy_id == ids["transaction_review"],
                ))
            ).scalar_one())
            assert await db.get(RiskFlag, (
                await db.execute(select(LegacyMigrationRecord.core_entity_id).where(
                    LegacyMigrationRecord.entity_type == "risk_flags",
                    LegacyMigrationRecord.legacy_id == ids["risk_flag"],
                ))
            ).scalar_one())
            assert await db.get(AdminNote, (
                await db.execute(select(LegacyMigrationRecord.core_entity_id).where(
                    LegacyMigrationRecord.entity_type == "admin_notes",
                    LegacyMigrationRecord.legacy_id == ids["admin_note"],
                ))
            ).scalar_one())
            assert await db.get(NotificationTemplate, (
                await db.execute(select(LegacyMigrationRecord.core_entity_id).where(
                    LegacyMigrationRecord.entity_type == "notification_templates",
                    LegacyMigrationRecord.legacy_id == ids["notification_template"],
                ))
            ).scalar_one())
            assert await db.get(PlatformSetting, (
                await db.execute(select(LegacyMigrationRecord.core_entity_id).where(
                    LegacyMigrationRecord.entity_type == "platform_settings",
                    LegacyMigrationRecord.legacy_id == ids["platform_setting"],
                ))
            ).scalar_one())
            assert await db.get(ProjectMetricTemplate, (
                await db.execute(select(LegacyMigrationRecord.core_entity_id).where(
                    LegacyMigrationRecord.entity_type == "project_metric_templates",
                    LegacyMigrationRecord.legacy_id == ids["project_metric_template"],
                ))
            ).scalar_one())
            project_metric_value = await db.get(ProjectMetricValue, (
                await db.execute(select(LegacyMigrationRecord.core_entity_id).where(
                    LegacyMigrationRecord.entity_type == "project_metric_values",
                    LegacyMigrationRecord.legacy_id == ids["project_metric_value"],
                ))
            ).scalar_one())
            project_price_snapshot = await db.get(ProjectPriceSnapshot, (
                await db.execute(select(LegacyMigrationRecord.core_entity_id).where(
                    LegacyMigrationRecord.entity_type == "project_price_snapshots",
                    LegacyMigrationRecord.legacy_id == ids["project_price_snapshot"],
                ))
            ).scalar_one())
            report = await db.get(ProjectReport, (
                await db.execute(select(LegacyMigrationRecord.core_entity_id).where(
                    LegacyMigrationRecord.entity_type == "project_reports",
                    LegacyMigrationRecord.legacy_id == ids["project_report"],
                ))
            ).scalar_one())
            report_version = await db.get(ProjectReportVersion, (
                await db.execute(select(LegacyMigrationRecord.core_entity_id).where(
                    LegacyMigrationRecord.entity_type == "project_report_versions",
                    LegacyMigrationRecord.legacy_id == ids["project_report_version"],
                ))
            ).scalar_one())
            report_column = await db.get(ProjectReportColumn, (
                await db.execute(select(LegacyMigrationRecord.core_entity_id).where(
                    LegacyMigrationRecord.entity_type == "project_report_columns",
                    LegacyMigrationRecord.legacy_id == ids["project_report_column"],
                ))
            ).scalar_one())
            report_row = await db.get(ProjectReportRow, (
                await db.execute(select(LegacyMigrationRecord.core_entity_id).where(
                    LegacyMigrationRecord.entity_type == "project_report_rows",
                    LegacyMigrationRecord.legacy_id == ids["project_report_row"],
                ))
            ).scalar_one())
            report_change = await db.get(ProjectReportChangeLog, (
                await db.execute(select(LegacyMigrationRecord.core_entity_id).where(
                    LegacyMigrationRecord.entity_type == "project_report_change_logs",
                    LegacyMigrationRecord.legacy_id == ids["project_report_change_log"],
                ))
            ).scalar_one())
            assert project_metric_value and project_metric_value.template_id is not None
            assert project_price_snapshot and project_price_snapshot.line_item_id is not None
            assert report and report.current_version_id == report.frozen_version_id
            assert report_version and report.current_version_id == report_version.id
            assert report_column and report_column.report_version_id == report_version.id
            assert report_row and report_row.report_version_id == report_version.id
            assert report_change and report_change.version_id == report_version.id
            trust_event = await db.get(TrustScoreEvent, (
                await db.execute(select(LegacyMigrationRecord.core_entity_id).where(
                    LegacyMigrationRecord.entity_type == "trust_score_events",
                    LegacyMigrationRecord.legacy_id == ids["trust_score_event"],
                ))
            ).scalar_one())
            trust_profile = await db.get(TrustProfile, trust_event.trust_profile_id if trust_event else None)
            assert trust_event and trust_profile and trust_event.related_entity_id == order_id
            typed_platform_models = {
                "audit_logs": AuditLog,
                "backup_schedules": BackupSchedule,
                "backup_jobs": BackupJob,
            }
            typed_platform_rows = {}
            for entity_type, model in typed_platform_models.items():
                core_id = (
                    await db.execute(select(LegacyMigrationRecord.core_entity_id).where(
                        LegacyMigrationRecord.entity_type == entity_type,
                        LegacyMigrationRecord.legacy_id == ids[entity_type[:-1]],
                    ))
                ).scalar_one()
                typed_platform_rows[entity_type] = await db.get(model, core_id)
                assert typed_platform_rows[entity_type]
            assert typed_platform_rows["backup_jobs"].schedule_id == typed_platform_rows["backup_schedules"].id
            assert typed_platform_rows["audit_logs"].actor_user_id == supplier_id
            assert await db.get(CompanyBranch, (
                await db.execute(select(LegacyMigrationRecord.core_entity_id).where(
                    LegacyMigrationRecord.entity_type == "branches",
                    LegacyMigrationRecord.legacy_id == ids["branch"],
                ))
            ).scalar_one())
            assert await db.get(ServiceArea, (
                await db.execute(select(LegacyMigrationRecord.core_entity_id).where(
                    LegacyMigrationRecord.entity_type == "service_areas",
                    LegacyMigrationRecord.legacy_id == ids["service_area"],
                ))
            ).scalar_one())
            typed_payment_models = {
                "payment_events": PaymentEvent,
                "region_payment_configs": RegionPaymentConfig,
                "currency_configs": CurrencyConfig,
                "payment_method_configs": PaymentMethodConfig,
                "fee_rules": FeeRule,
                "fx_quotes": FxQuote,
                "payment_quotes": PaymentQuote,
                "fee_line_items": FeeLineItem,
                "payment_intents": ProviderPaymentIntent,
                "settlement_events": SettlementEvent,
                "settlement_adjustments": SettlementAdjustment,
            }
            for entity_type, model in typed_payment_models.items():
                core_id = (
                    await db.execute(select(LegacyMigrationRecord.core_entity_id).where(
                        LegacyMigrationRecord.entity_type == entity_type,
                        LegacyMigrationRecord.legacy_id == ids[entity_type[:-1] if entity_type.endswith("s") else entity_type],
                    ))
                ).scalar_one()
                assert await db.get(model, core_id)

            workspace_bound_payment_rows = {
                "order_shipping": (OrderShipping, ids["order_shipping"]),
                "escrow_transactions": (EscrowTransaction, ids["escrow"]),
                "payouts": (Payout, ids["payout"]),
                "payment_events": (PaymentEvent, ids["payment_event"]),
                "payment_intents": (ProviderPaymentIntent, ids["payment_intent"]),
            }
            for entity_type, (model, legacy_id) in workspace_bound_payment_rows.items():
                core_id = (
                    await db.execute(
                        select(LegacyMigrationRecord.core_entity_id).where(
                            LegacyMigrationRecord.entity_type == entity_type,
                            LegacyMigrationRecord.legacy_id == legacy_id,
                        )
                    )
                ).scalar_one()
                row = await db.get(model, core_id)
                assert row and row.workspace_id == order.workspace_id

            identity = (
                await db.execute(
                    select(LegacyIdentityMapping).where(
                        LegacyIdentityMapping.legacy_system == "cebu",
                        LegacyIdentityMapping.legacy_user_id == ids["supplier"],
                    )
                )
            ).scalar_one()
            assert identity.core_user_id == supplier_id
            assert identity.metadata_json["password_reset_required"] is True

    asyncio.run(_run())
