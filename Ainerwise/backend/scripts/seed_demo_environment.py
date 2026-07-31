"""Bootstrap demo mode, test accounts, and sample data.

Run inside backend container:
    python -m scripts.seed_demo_environment
"""
import asyncio
import sys

sys.path.insert(0, "/app")

from app.db.session import async_session_factory
from app.services.demo_bootstrap import bootstrap_demo_environment


async def main() -> None:
    async with async_session_factory() as db:
        results = await bootstrap_demo_environment(db)
    print("Demo environment ready:", results)


if __name__ == "__main__":
    asyncio.run(main())
