import asyncio
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.main import app

# Integration tests run against the configured (shared/dev) DB via ASGITransport.
# They create commerce chains (category -> listing -> request -> offer -> order)
# with fixed names. Without cleanup these accumulate across runs and flood the
# public marketplace. This pattern matches the names those tests use.
_TEST_CATEGORY_FILTER = (
    "name ILIKE 'Delivery Test%' "
    "OR name ILIKE 'Cebu E2E%' "
    "OR name ILIKE '%E2E Category%' "
    "OR name ILIKE 'Parity Cat%'"
)

# 2Hands listings are created under the production "2hands" category, so they
# are identified by their test title prefix instead.
_TEST_LISTING_FILTER = "title ILIKE '2Hands Test%'"

# Child-first deletion order. Cascade FKs (order_deliveries/disputes/reviews/
# settlements/escrow/shipping/payment_intents) are removed automatically with
# their commerce_orders; the no-action FKs below are deleted explicitly first.
_CLEANUP_STATEMENTS = [
    f"DELETE FROM commerce_threads WHERE procurement_request_id IN (SELECT id FROM procurement_requests WHERE category_schema_id IN (SELECT id FROM trade_category_schemas WHERE {_TEST_CATEGORY_FILTER}))",
    f"DELETE FROM payment_events WHERE order_id IN (SELECT id FROM commerce_orders WHERE procurement_request_id IN (SELECT id FROM procurement_requests WHERE category_schema_id IN (SELECT id FROM trade_category_schemas WHERE {_TEST_CATEGORY_FILTER})))",
    f"DELETE FROM provider_payment_intents WHERE order_id IN (SELECT id FROM commerce_orders WHERE procurement_request_id IN (SELECT id FROM procurement_requests WHERE category_schema_id IN (SELECT id FROM trade_category_schemas WHERE {_TEST_CATEGORY_FILTER})))",
    f"DELETE FROM payouts WHERE order_id IN (SELECT id FROM commerce_orders WHERE procurement_request_id IN (SELECT id FROM procurement_requests WHERE category_schema_id IN (SELECT id FROM trade_category_schemas WHERE {_TEST_CATEGORY_FILTER})))",
    f"DELETE FROM commerce_orders WHERE procurement_request_id IN (SELECT id FROM procurement_requests WHERE category_schema_id IN (SELECT id FROM trade_category_schemas WHERE {_TEST_CATEGORY_FILTER}))",
    f"DELETE FROM supplier_offers WHERE procurement_request_id IN (SELECT id FROM procurement_requests WHERE category_schema_id IN (SELECT id FROM trade_category_schemas WHERE {_TEST_CATEGORY_FILTER})) OR supplier_listing_id IN (SELECT id FROM supplier_listings WHERE category_schema_id IN (SELECT id FROM trade_category_schemas WHERE {_TEST_CATEGORY_FILTER}))",
    f"DELETE FROM ad_campaigns WHERE listing_id IN (SELECT id FROM supplier_listings WHERE category_schema_id IN (SELECT id FROM trade_category_schemas WHERE {_TEST_CATEGORY_FILTER}))",
    f"DELETE FROM procurement_requests WHERE category_schema_id IN (SELECT id FROM trade_category_schemas WHERE {_TEST_CATEGORY_FILTER})",
    f"DELETE FROM supplier_listings WHERE category_schema_id IN (SELECT id FROM trade_category_schemas WHERE {_TEST_CATEGORY_FILTER})",
    f"DELETE FROM trade_category_schemas WHERE {_TEST_CATEGORY_FILTER}",
    # 2Hands tests list against the real "2hands" category, so they are matched
    # by listing title instead. Children first, then the parent listing.
    # Analytics is append-only, so tests clean up by their own markers.
    "DELETE FROM analytics.events WHERE source_app = 'test-suite' OR portal_key LIKE 'test-portal-%'",
    f"DELETE FROM analytics.events WHERE listing_id IN (SELECT id FROM supplier_listings WHERE {_TEST_LISTING_FILTER})",
    "DELETE FROM analytics.creatives WHERE variant_label LIKE 'good-%' OR variant_label LIKE 'poor-%'",
    f"DELETE FROM analytics.creatives WHERE listing_id IN (SELECT id FROM supplier_listings WHERE {_TEST_LISTING_FILTER})",
    f"DELETE FROM channels.channel_listings WHERE supplier_listing_id IN (SELECT id FROM supplier_listings WHERE {_TEST_LISTING_FILTER})",
    "DELETE FROM channels.channel_category_maps WHERE account_id IN (SELECT id FROM channels.channel_accounts WHERE channel IN ('testfeed','testassisted'))",
    "DELETE FROM channels.channel_accounts WHERE channel IN ('testfeed','testassisted')",
    f"DELETE FROM secondhand_deals WHERE supplier_listing_id IN (SELECT id FROM supplier_listings WHERE {_TEST_LISTING_FILTER})",
    f"DELETE FROM secondhand_address_disclosures WHERE secondhand_listing_id IN (SELECT id FROM secondhand_listings WHERE supplier_listing_id IN (SELECT id FROM supplier_listings WHERE {_TEST_LISTING_FILTER}))",
    f"DELETE FROM secondhand_listings WHERE supplier_listing_id IN (SELECT id FROM supplier_listings WHERE {_TEST_LISTING_FILTER})",
    f"DELETE FROM supplier_listings WHERE {_TEST_LISTING_FILTER}",
]


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _dedup_duplicate_categories(session) -> None:
    """Merge same-name active categories left behind by tests that create real
    category names with random slugs (e.g. historical-migration's Smart Locks).
    Keeps the most-referenced (earliest on ties), migrates FKs, deletes the rest."""
    pairs = (await session.execute(text(
        """
        WITH ranked AS (
            SELECT c.id, c.name,
                   row_number() OVER (
                       PARTITION BY c.name
                       ORDER BY (SELECT count(*) FROM supplier_listings l WHERE l.category_schema_id = c.id) DESC,
                                c.created_at ASC
                   ) AS rn
            FROM trade_category_schemas c
            WHERE c.status = 'active'
              AND c.name IN (
                  SELECT name FROM trade_category_schemas
                  WHERE status = 'active' GROUP BY name HAVING count(*) > 1
              )
        )
        SELECT dup.id, keep.id
        FROM ranked dup JOIN ranked keep ON keep.name = dup.name AND keep.rn = 1
        WHERE dup.rn > 1
        """
    ))).fetchall()
    for dup_id, keep_id in pairs:
        await session.execute(
            text("UPDATE supplier_listings SET category_schema_id = :k WHERE category_schema_id = :d"),
            {"k": keep_id, "d": dup_id},
        )
        await session.execute(
            text("UPDATE procurement_requests SET category_schema_id = :k WHERE category_schema_id = :d"),
            {"k": keep_id, "d": dup_id},
        )
        await session.execute(text("DELETE FROM trade_category_schemas WHERE id = :d"), {"d": dup_id})


async def _purge_commerce_test_data() -> None:
    # Fresh NullPool engine on a fresh loop, independent of any test-session
    # engine/loop state (avoids async-fixture finalizer conflicts).
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )
    from sqlalchemy.pool import NullPool

    from app.core.config import settings

    eng = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    factory = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)
    try:
        async with factory() as session:
            for stmt in _CLEANUP_STATEMENTS:
                await session.execute(text(stmt))
            await _dedup_duplicate_categories(session)
            await session.commit()
    finally:
        await eng.dispose()


def pytest_sessionfinish(session, exitstatus):  # noqa: ARG001
    """Remove fixed-name commerce test chains after the whole suite so the shared
    DB (and the public marketplace) does not accumulate test junk across runs."""
    try:
        asyncio.run(_purge_commerce_test_data())
    except Exception:  # noqa: BLE001 - teardown must never fail the suite
        pass
