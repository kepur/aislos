import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


def run_db_task(fn: Callable[[AsyncSession], Awaitable[Any]]) -> Any:
    """Run an async DB function from a sync Celery task.

    Each call gets a NullPool engine inside its own event loop: asyncpg
    connections are bound to the loop that created them, so reusing the
    module-level pool across successive asyncio.run() calls in a worker
    child fails with "attached to a different loop".
    """

    async def _run() -> Any:
        task_engine = create_async_engine(settings.DATABASE_URL, echo=False, poolclass=NullPool)
        factory = async_sessionmaker(task_engine, class_=AsyncSession, expire_on_commit=False)
        try:
            async with factory() as session:
                return await fn(session)
        finally:
            await task_engine.dispose()

    return asyncio.run(_run())
