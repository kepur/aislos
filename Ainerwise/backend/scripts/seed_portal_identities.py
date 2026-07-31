"""PF10: Seed local test portal identities. Run: python -m scripts.seed_portal_identities"""
import asyncio
import sys

sys.path.insert(0, "/app")

from app.db.session import async_session_factory
from app.services.demo_bootstrap import PORTAL_IDENTITIES, ensure_portal_identities


async def main() -> None:
    async with async_session_factory() as db:
        created = await ensure_portal_identities(db)
        await db.commit()
        print(f"Seeded {len(PORTAL_IDENTITIES)} portal test identities ({created} new)")


if __name__ == "__main__":
    asyncio.run(main())
