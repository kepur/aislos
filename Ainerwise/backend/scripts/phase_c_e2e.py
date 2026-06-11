"""Phase C end-to-end demo of the general-contractor main loop (run inside
the backend container). Exercises real HTTP APIs + the live event bus.
Leaves demo data in place (region pricing, RFQ, plan, site, case) — it doubles
as seed content; rerunning is idempotent-ish (creates new RFQ/plan rows).
"""
import json
import time

import httpx

BASE = "http://localhost:8000/api/v1"


def main() -> None:
    token = httpx.post(
        f"{BASE}/auth/login",
        json={"email": "admin@ainerwise.com", "password": "admin123456"},
        timeout=15,
    ).json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    # ── 1. Pricing: cost -> price -> margin ────────────────────
    regions_resp = httpx.get(f"{BASE}/regions", headers=h, timeout=15).json()
    region_items = regions_resp["items"] if isinstance(regions_resp, dict) else regions_resp
    region = next((r for r in region_items if r.get("code") == "RS"), region_items[0] if region_items else None)
    assert region, "need at least one region (seed first)"
    region_id = region["id"]
    print(f"[1] region: {region.get('code')} {region_id[:8]}")

    import asyncio

    from sqlalchemy import select

    from app.db.session import async_session_factory, engine
    from app.models.product import Product

    async def _first_product():
        await engine.dispose()
        async with async_session_factory() as db:
            row = (await db.execute(select(Product).limit(1))).scalars().first()
            return (str(row.id), row.name) if row else (None, None)

    product_id, product_name = asyncio.run(_first_product())
    assert product_id, "no products in DB — run seed first"
    print(f"[1] product: {product_name[:50]}")

    cost = httpx.post(
        f"{BASE}/admin/costing/product-costs", headers=h, timeout=15,
        json={"region_id": region_id, "product_id": product_id, "purchase_cost": 1000,
              "freight_pct": 10, "customs_pct": 5, "warehousing_pct": 2,
              "labor_estimate": 200, "valid_from": "2026-01-01"},
    ).json()
    print(f"[1] landed_cost: {cost['landed_cost']}")

    httpx.post(
        f"{BASE}/admin/costing/price-lists", headers=h, timeout=15,
        json={"region_id": region_id, "product_id": product_id,
              "list_price": 2200, "valid_from": "2026-01-01"},
    )
    qp = httpx.get(
        f"{BASE}/admin/costing/quote-price", headers=h, timeout=15,
        params={"region_id": region_id, "product_id": product_id, "qty": 2},
    ).json()
    print(f"[1] quote-price: unit={qp['unit_price']} cost={qp['unit_landed_cost']} "
          f"margin={qp['unit_margin']} ({qp['margin_pct']}%) gross={qp['total_gross']}")

    # ── 2. AI chat creates a lead (public endpoint, event bus) ─
    chat = httpx.post(
        f"{BASE}/ai/chat", timeout=60,
        json={"message": "I have a 280 sqm villa in Belgrade, need KNX + solar. "
                         "Quote please: villa-e2e@test.rs", "visitor_id": "phase-c-e2e"},
    ).json()
    print(f"[2] chat lead_created: {chat['lead_created']}")

    leads = httpx.get(f"{BASE}/leads", headers=h, params={"limit": 5}, timeout=15).json()
    lead = next(l for l in leads["items"] if l.get("contact_email") == "villa-e2e@test.rs")
    lead_id = lead["id"]
    print(f"[2] lead: {lead_id[:8]} status={lead['status']}")

    # ── 3. RFQ: create -> partner -> invite -> bids -> score -> award ─
    partner_a = httpx.post(
        f"{BASE}/service-partners", headers=h, timeout=15,
        json={"partner_type": "knx_installer", "country": "Serbia", "city": "Belgrade",
              "skills_json": ["knx", "electrical"], "rating_internal": 4.5},
    ).json()
    partner_b = httpx.post(
        f"{BASE}/service-partners", headers=h, timeout=15,
        json={"partner_type": "electrician", "country": "Serbia", "city": "Novi Sad",
              "skills_json": ["knx"], "rating_internal": 3.5},
    ).json()
    print(f"[3] partners: {partner_a['id'][:8]}, {partner_b['id'][:8]}")

    httpx.post(f"{BASE}/admin/rfqs/partner-metrics/recompute", headers=h, timeout=30)

    rfq = httpx.post(
        f"{BASE}/admin/rfqs", headers=h, timeout=15,
        json={"title": "Belgrade villa — KNX package", "trade": "knx", "lead_id": lead_id,
              "region_id": region_id,
              "scope_json": {"country": "Serbia", "city": "Belgrade", "summary": "280sqm villa KNX backbone"}},
    ).json()
    rfq_id = rfq["id"]
    candidates = httpx.get(f"{BASE}/admin/rfqs/{rfq_id}/match-partners", headers=h, timeout=15).json()["candidates"]
    print(f"[3] rfq {rfq_id[:8]}, candidates: {len(candidates)}")

    httpx.post(f"{BASE}/admin/rfqs/{rfq_id}/invite", headers=h, timeout=15,
               json={"partner_ids": [partner_a["id"], partner_b["id"]]})
    httpx.post(f"{BASE}/admin/rfqs/{rfq_id}/bids", headers=h, timeout=15,
               json={"partner_id": partner_a["id"], "amount": 3000, "lead_time_days": 14})
    httpx.post(f"{BASE}/admin/rfqs/{rfq_id}/bids", headers=h, timeout=15,
               json={"partner_id": partner_b["id"], "amount": 2800, "lead_time_days": 30})
    evaluation = httpx.post(f"{BASE}/admin/rfqs/{rfq_id}/evaluate", headers=h, timeout=15).json()
    ranking = evaluation["draft"]["ranking"]
    print(f"[3] AI ranking: " + " | ".join(f"{r['amount']}€ score={r['score']}" for r in ranking))

    award = httpx.post(f"{BASE}/admin/rfqs/{rfq_id}/award", headers=h, timeout=15,
                       json={"bid_id": evaluation["draft"]["recommended_bid_id"]}).json()
    print(f"[3] awarded, auto project: {str(award['project_id'])[:8]}")

    # ── 4. Quote -> payment plan -> fund deposit -> ledger ─────
    quote = httpx.post(
        f"{BASE}/quotes", headers=h, timeout=15,
        json={"lead_id": lead_id, "project_id": award["project_id"], "total": 10000, "currency": "EUR"},
    ).json()
    plan = httpx.post(f"{BASE}/admin/payments/plans", headers=h, timeout=15,
                      json={"quote_id": quote["id"], "retention_pct": 5}).json()
    detail = httpx.get(f"{BASE}/admin/payments/plans/{plan['id']}", headers=h, timeout=15).json()
    print(f"[4] plan milestones: " + " | ".join(f"{m['label']}={m['amount']}" for m in detail["milestones"]))

    deposit = detail["milestones"][0]
    httpx.post(f"{BASE}/admin/payments/milestones/{deposit['id']}/fund", headers=h, timeout=15,
               json={"memo": "offline bank transfer received"})
    detail = httpx.get(f"{BASE}/admin/payments/plans/{plan['id']}", headers=h, timeout=15).json()
    print(f"[4] deposit status: {detail['milestones'][0]['status']}, ledger entries: {len(detail['ledger'])}")

    # ── 5. Site + asset registry ───────────────────────────────
    site = httpx.post(f"{BASE}/admin/sites", headers=h, timeout=15,
                      json={"name": "Belgrade villa (e2e)", "city": "Belgrade", "country": "Serbia",
                            "region_id": region_id}).json()
    asset = httpx.post(f"{BASE}/admin/assets", headers=h, timeout=15,
                       json={"site_id": site["id"], "name": "KNX gateway", "floor": "1",
                             "room": "utility", "project_id": award["project_id"]}).json()
    print(f"[5] site {site['id'][:8]} asset {asset['id'][:8]} ({asset['floor']}/{asset['room']})")

    # ── 6. Case library -> knowledge base -> AI cites it ───────
    case = httpx.post(
        f"{BASE}/admin/cases", headers=h, timeout=30,
        json={"title": "Belgrade 280sqm villa — KNX + solar delivery", "country": "Serbia",
              "city": "Belgrade", "property_type": "villa", "area_sqm": 280, "budget": 30000,
              "duration_days": 21, "gross_margin_pct": 26,
              "summary": "Delivered full KNX backbone, 10kW solar with storage, security cameras "
                         "and EV charger for a 280 sqm villa in Belgrade within 3 weeks.",
              "public_visible": True},
    ).json()
    print(f"[6] case {case['id'][:8]} embedded -> waiting for ingestion...")
    time.sleep(8)
    chat2 = httpx.post(
        f"{BASE}/ai/chat", timeout=60,
        json={"message": "Do you have experience with villa KNX and solar projects in Belgrade?",
              "visitor_id": "phase-c-e2e-2"},
    ).json()
    cited = [s["title"] for s in chat2.get("sources", [])]
    print(f"[6] AI cited sources: {cited}")

    # ── 7. Event-driven lead scoring (consumer runs every 30s) ─
    print("[7] waiting for consume_domain_events beat cycle (~35s)...")
    time.sleep(35)
    lead_after = httpx.get(f"{BASE}/leads/{lead_id}", headers=h, timeout=15).json()
    analyzed = bool(lead_after.get("ai_analysis_json"))
    print(f"[7] lead auto-analyzed via event bus: {analyzed} "
          f"(score={lead_after.get('lead_score')}, status={lead_after.get('status')})")

    print("\nE2E COMPLETE")


if __name__ == "__main__":
    main()
