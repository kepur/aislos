"""Seed the default AISLOS / Cebu portal policies (idempotent).

Usage (inside the backend container or with backend deps installed):

    python -m scripts.seed_portal_policies
"""
import asyncio

from app.db.session import async_session_factory, engine
from app.services.portal_policy import ensure_default_policies


async def main() -> None:
    async with async_session_factory() as db:
        policies = await ensure_default_policies(db)
        await db.commit()
        for portal_key, policy in policies.items():
            print(
                f"portal={portal_key} version={policy.version} status={policy.status} "
                f"mode={policy.default_procurement_mode}"
            )
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
