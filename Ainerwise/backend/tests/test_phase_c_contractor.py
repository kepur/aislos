"""Phase C tests: pricing engine, RFQ bidding, partner score, payment ledger,
case embedding. Service-level against the live DB with cleanup."""
import asyncio
import uuid
from datetime import date
from decimal import Decimal

from app.db.session import async_session_factory, engine
from app.main import app
from app.models import (
    CaseStudy,
    ExchangeRate,
    Lead,
    PaymentMilestone,
    PaymentPlan,
    PriceList,
    ProductCost,
    Quote,
    Region,
    RFQ,
    ServicePartner,
)
from app.models.ai import KnowledgeDocument
from app.services.payments import create_plan_from_quote, mark_milestone_funded, release_milestone
from app.services.pricing import compute_landed_cost, quote_price
from app.services.rfq import award_bid, evaluate_bids, invite_partners, match_partners, record_bid
from app.tasks.celery_app import celery_app


def test_phase_c_routes_registered():
    paths = {r.path for r in app.routes}
    for p in (
        "/api/v1/admin/costing/product-costs",
        "/api/v1/admin/costing/price-lists",
        "/api/v1/admin/costing/quote-price",
        "/api/v1/admin/rfqs",
        "/api/v1/admin/rfqs/{id}/invite",
        "/api/v1/admin/rfqs/{id}/evaluate",
        "/api/v1/admin/rfqs/{id}/award",
        "/api/v1/admin/payments/plans",
        "/api/v1/admin/payments/milestones/{id}/fund",
        "/api/v1/admin/sites",
        "/api/v1/admin/assets",
        "/api/v1/admin/cases",
        "/api/v1/cases",
        "/api/v1/admin/marketing/generate",
        "/api/v1/admin/leads/{lead_id}/quote-draft",
        "/api/v1/admin/memories",
    ):
        assert p in paths, p


def test_phase_c_celery_wiring():
    routes = celery_app.conf.task_routes
    assert routes["consume_domain_events"]["queue"] == "automation"
    assert routes["recompute_partner_metrics"]["queue"] == "automation"
    assert routes["release_due_retentions"]["queue"] == "automation"
    beat = celery_app.conf.beat_schedule
    assert "consume-domain-events" in beat
    assert "recompute-partner-metrics-daily" in beat
    assert "release-due-retentions-daily" in beat


def test_landed_cost_computation():
    cost = ProductCost(
        region_id=uuid.uuid4(), product_id=uuid.uuid4(),
        purchase_cost=Decimal("1000"), currency="EUR",
        freight_pct=Decimal("10"), customs_pct=Decimal("5"),
        warehousing_pct=Decimal("2"), labor_estimate=Decimal("200"),
        valid_from=date(2026, 1, 1),
    )
    # 1000 + 100 + 50 + 20 + 200 = 1370
    assert compute_landed_cost(cost) == Decimal("1370.00")
    cost.freight_fixed = Decimal("100")  # fixed overrides pct
    cost.freight_pct = Decimal("99")
    assert compute_landed_cost(cost) == Decimal("1370.00")


def test_pricing_engine_quote_price():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            from sqlalchemy import select

            from app.models.product import Product

            region = Region(code=f"T{uuid.uuid4().hex[:6]}", name=f"Testland-{uuid.uuid4().hex[:6]}",
                            currency_code="EUR",
                            tax_rules_json={"vat_default": 20, "overrides": []})
            db.add(region)
            product = (await db.execute(select(Product).limit(1))).scalars().first()
            assert product is not None, "seeded products required"
            await db.flush()

            db.add(ProductCost(region_id=region.id, product_id=product.id,
                               purchase_cost=Decimal("1000"), currency="EUR",
                               freight_pct=Decimal("10"), customs_pct=Decimal("5"),
                               warehousing_pct=Decimal("2"), labor_estimate=Decimal("200"),
                               landed_cost=None, valid_from=date(2026, 1, 1)))
            db.add(PriceList(region_id=region.id, product_id=product.id,
                             list_price=Decimal("2200"), currency="EUR",
                             partner_price=Decimal("1900"), valid_from=date(2026, 1, 1)))
            await db.flush()

            result = await quote_price(db, region.id, product.id, qty=2)
            assert result["unit_price"] == 2200.0
            assert result["unit_landed_cost"] == 1370.0
            assert result["unit_margin"] == 830.0
            assert result["vat_pct"] == 20.0
            assert result["total_net"] == 4400.0
            assert result["total_gross"] == 5280.0

            partner_result = await quote_price(db, region.id, product.id, tier="partner")
            assert partner_result["unit_price"] == 1900.0

            await db.rollback()

    asyncio.run(_run())


def test_exchange_rate_conversion():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            from app.services.pricing import convert_amount

            db.add(ExchangeRate(base="EUR", quote="RSD", rate=Decimal("117.2"), as_of=date(2026, 6, 1)))
            await db.flush()
            converted = await convert_amount(db, Decimal("100"), "EUR", "RSD")
            assert converted == Decimal("11720.00")
            await db.rollback()

    asyncio.run(_run())


def test_rfq_full_flow():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            partner_a = ServicePartner(partner_type="electrician", country="Serbia", city="Belgrade",
                                       skills_json=["knx", "electrical"], rating_internal=4.5,
                                       availability_status="available")
            partner_b = ServicePartner(partner_type="electrician", country="Serbia", city="Novi Sad",
                                       skills_json=["knx"], rating_internal=3.0,
                                       availability_status="available")
            lead = Lead(contact_name="RFQ Test", contact_email="rfq@test.local", status="new")
            db.add_all([partner_a, partner_b, lead])
            await db.flush()

            rfq = RFQ(title="Villa KNX install", trade="knx",
                      scope_json={"country": "Serbia", "city": "Belgrade", "summary": "280sqm villa"},
                      currency="EUR", status="draft", lead_id=lead.id)
            db.add(rfq)
            await db.flush()

            candidates = await match_partners(db, rfq)
            candidate_ids = {c["partner_id"] for c in candidates}
            assert str(partner_a.id) in candidate_ids and str(partner_b.id) in candidate_ids

            await invite_partners(db, rfq, [partner_a.id, partner_b.id])
            assert rfq.status == "bidding"

            await record_bid(db, rfq, partner_id=partner_a.id, amount=3000,
                             currency="EUR", lead_time_days=14, notes=None)
            await record_bid(db, rfq, partner_id=partner_b.id, amount=2800,
                             currency="EUR", lead_time_days=30, notes=None)

            review = await evaluate_bids(db, rfq)
            assert rfq.status == "evaluating"
            ranking = review.draft_json["ranking"]
            assert len(ranking) == 2
            assert all(r["score"] > 0 for r in ranking)
            assert {"price_score", "partner_score", "lead_time_score"} <= set(ranking[0]["breakdown"])

            winner_bid_id = uuid.UUID(ranking[0]["bid_id"])
            winner = await award_bid(db, rfq, winner_bid_id, None)
            assert rfq.status == "awarded"
            assert winner.status == "awarded"
            assert rfq.project_id is not None  # auto-created from lead

            await db.rollback()

    asyncio.run(_run())


def test_payment_plan_lifecycle_and_ledger():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            from sqlalchemy import select

            from app.models.payment import LedgerEntry

            quote = Quote(total=10000.0, currency="EUR", status="accepted")
            db.add(quote)
            await db.flush()

            plan = await create_plan_from_quote(db, quote, retention_pct=Decimal("5"))
            milestones = (
                await db.execute(
                    select(PaymentMilestone).where(PaymentMilestone.plan_id == plan.id).order_by(PaymentMilestone.seq)
                )
            ).scalars().all()
            assert [m.label for m in milestones] == ["deposit", "midterm", "acceptance", "retention"]
            assert sum(Decimal(m.amount) for m in milestones) == Decimal("10000.00")
            retention = milestones[-1]
            assert Decimal(retention.amount) == Decimal("500.00")

            deposit = milestones[0]
            await mark_milestone_funded(db, deposit)
            assert deposit.status == "funded"
            entries = (
                await db.execute(select(LedgerEntry).where(LedgerEntry.milestone_id == deposit.id))
            ).scalars().all()
            assert len(entries) == 2
            debits = sum(Decimal(e.amount) for e in entries if e.direction == "debit")
            credits = sum(Decimal(e.amount) for e in entries if e.direction == "credit")
            assert debits == credits == Decimal(deposit.amount)

            await release_milestone(db, deposit)
            assert deposit.status == "released"

            # retention gets a release_due_at when funded
            await mark_milestone_funded(db, retention)
            assert retention.release_due_at is not None

            # invalid transitions guarded
            try:
                await mark_milestone_funded(db, deposit)
                raise AssertionError("funding a released milestone must fail")
            except ValueError:
                pass

            await db.rollback()

    asyncio.run(_run())


def test_case_embed_creates_knowledge_document():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            from app.services.cases import build_case_summary, embed_case

            case = CaseStudy(
                title="Warsaw 200sqm villa", country="Poland", city="Warsaw",
                property_type="villa", area_sqm=200, budget=Decimal("50000"),
                gross_margin_pct=Decimal("25"),
                summary="Full KNX + solar + security delivery.",
            )
            db.add(case)
            await db.flush()
            doc = await embed_case(db, case)
            assert case.embedding_document_id == doc.id
            assert doc.source_type == "case_study"
            text = doc.meta_json["inline_text"]
            assert "Warsaw" in text and "50000" in text
            assert "25" not in build_case_summary(case) or "margin" not in text.lower()  # margin never embedded
            await db.rollback()

    asyncio.run(_run())


def test_partner_score_recompute():
    async def _run():
        await engine.dispose()
        async with async_session_factory() as db:
            from sqlalchemy import select

            from app.models.rfq import PartnerMetric
            from app.services.partner_score import recompute_partner_metrics

            partner = ServicePartner(partner_type="installer", rating_internal=4.0,
                                     availability_status="available")
            db.add(partner)
            await db.commit()
            partner_id = partner.id

            await recompute_partner_metrics(db)
            metric = (
                await db.execute(select(PartnerMetric).where(PartnerMetric.partner_id == partner_id))
            ).scalar_one_or_none()
            assert metric is not None
            # cold start: only rating factor -> 4.0 * 20 = 80
            assert float(metric.composite_score) == 80.0
            assert "rating" in metric.breakdown_json["factors"]

            # append-only history snapshot written for the future risk engine
            from app.models.rfq import PartnerMetricSnapshot

            snapshots = (
                await db.execute(
                    select(PartnerMetricSnapshot).where(PartnerMetricSnapshot.partner_id == partner_id)
                )
            ).scalars().all()
            assert len(snapshots) == 1
            assert float(snapshots[0].composite_score) == 80.0

            # cleanup
            for snapshot in snapshots:
                await db.delete(snapshot)
            await db.delete(metric)
            refreshed = await db.get(ServicePartner, partner_id)
            await db.delete(refreshed)
            await db.commit()

    asyncio.run(_run())
