"""Shared Redis fixed-window rate limiting for public API cost and abuse control."""
from __future__ import annotations

import redis.asyncio as aioredis
from fastapi import HTTPException, Request, status

from app.core.config import settings


def request_subject(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "").split(",", 1)[0].strip()
    if forwarded_for:
        return forwarded_for
    return request.client.host if request.client else "unknown"


async def redis_fixed_window_limited(
    *,
    bucket: str,
    subject: str,
    limit: int,
    window_seconds: int,
) -> bool:
    client = aioredis.from_url(settings.REDIS_URL)
    try:
        key = f"rate:{bucket}:{subject}"
        count = await client.incr(key)
        if count == 1:
            await client.expire(key, window_seconds)
        return count > limit
    except Exception:  # noqa: BLE001 - public reads degrade safely if Redis is unavailable
        return False
    finally:
        await client.aclose()


async def enforce_public_rate_limit(
    request: Request,
    *,
    bucket: str,
    limit: int,
    window_seconds: int = 3600,
    subject_suffix: str | None = None,
) -> None:
    subject = request_subject(request)
    if subject_suffix:
        subject = f"{subject}:{subject_suffix.strip().lower()}"
    if await redis_fixed_window_limited(
        bucket=bucket,
        subject=subject,
        limit=limit,
        window_seconds=window_seconds,
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
        )
