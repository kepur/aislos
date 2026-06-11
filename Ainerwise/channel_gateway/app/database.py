from __future__ import annotations

import json
import uuid

import asyncpg


class ChannelDatabase:
    """The gateway's deliberately narrow write surface: channels schema only."""

    def __init__(self, dsn: str):
        self.dsn = dsn
        self.pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        self.pool = await asyncpg.create_pool(self.dsn, min_size=1, max_size=5)

    async def close(self) -> None:
        if self.pool:
            await self.pool.close()

    def _require_pool(self) -> asyncpg.Pool:
        if self.pool is None:
            raise RuntimeError("Database pool is not initialized")
        return self.pool

    async def _account_id(self, conn: asyncpg.Connection, channel: str, name: str) -> uuid.UUID:
        account_id = await conn.fetchval(
            """
            SELECT id FROM channels.channel_accounts
            WHERE channel = $1 AND name = $2 AND status = 'active'
            ORDER BY created_at LIMIT 1
            """,
            channel,
            name,
        )
        if account_id:
            return account_id
        account_id = uuid.uuid4()
        await conn.execute(
            """
            INSERT INTO channels.channel_accounts
                (id, channel, name, status, meta_json)
            VALUES ($1, $2, $3, 'active', $4::jsonb)
            """,
            account_id,
            channel,
            name,
            json.dumps({"managed_by": "channel-gateway"}),
        )
        return account_id

    async def _thread_id(
        self,
        conn: asyncpg.Connection,
        account_id: uuid.UUID,
        external_thread_id: str,
        contact_name: str | None = None,
    ) -> uuid.UUID:
        thread_id = await conn.fetchval(
            """
            SELECT id FROM channels.channel_threads
            WHERE account_id = $1 AND external_thread_id = $2
            """,
            account_id,
            external_thread_id,
        )
        if thread_id:
            if contact_name:
                await conn.execute(
                    """
                    UPDATE channels.channel_threads
                    SET contact_name = COALESCE(contact_name, $2), updated_at = now()
                    WHERE id = $1
                    """,
                    thread_id,
                    contact_name,
                )
            return thread_id
        thread_id = uuid.uuid4()
        await conn.execute(
            """
            INSERT INTO channels.channel_threads
                (id, account_id, external_thread_id, contact_name)
            VALUES ($1, $2, $3, $4)
            """,
            thread_id,
            account_id,
            external_thread_id,
            contact_name,
        )
        return thread_id

    async def prepare_outbound(
        self,
        *,
        message_id: uuid.UUID,
        channel: str,
        account_name: str,
        external_thread_id: str,
        content: str,
        metadata: dict,
    ) -> dict:
        pool = self._require_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                existing = await conn.fetchrow(
                    """
                    SELECT id, status, external_message_id
                    FROM channels.channel_messages WHERE id = $1
                    """,
                    message_id,
                )
                if existing:
                    return {**dict(existing), "duplicate": True}
                account_id = await self._account_id(conn, channel, account_name)
                thread_id = await self._thread_id(conn, account_id, external_thread_id)
                await conn.execute(
                    """
                    INSERT INTO channels.channel_messages
                        (id, thread_id, direction, content, payload_json, status)
                    VALUES ($1, $2, 'out', $3, $4::jsonb, 'queued')
                    """,
                    message_id,
                    thread_id,
                    content,
                    json.dumps(metadata),
                )
                await conn.execute(
                    """
                    INSERT INTO channels.delivery_log
                        (id, message_id, attempt, status)
                    VALUES ($1, $2, 1, 'queued')
                    """,
                    uuid.uuid4(),
                    message_id,
                )
                return {
                    "id": message_id,
                    "status": "queued",
                    "external_message_id": None,
                    "duplicate": False,
                }

    async def finish_outbound(
        self,
        message_id: uuid.UUID,
        *,
        status: str,
        external_message_id: str | None = None,
        error_message: str | None = None,
    ) -> None:
        pool = self._require_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    """
                    UPDATE channels.channel_messages
                    SET status = $2, external_message_id = COALESCE($3, external_message_id), updated_at = now()
                    WHERE id = $1
                    """,
                    message_id,
                    status,
                    external_message_id,
                )
                await conn.execute(
                    """
                    UPDATE channels.delivery_log
                    SET status = $2, error_message = $3, updated_at = now()
                    WHERE message_id = $1 AND attempt = 1
                    """,
                    message_id,
                    status,
                    error_message,
                )

    async def store_inbound(
        self,
        *,
        channel: str,
        account_name: str,
        external_thread_id: str,
        external_message_id: str | None,
        content: str | None,
        contact_name: str | None,
        raw_payload: dict,
    ) -> uuid.UUID:
        pool = self._require_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                account_id = await self._account_id(conn, channel, account_name)
                thread_id = await self._thread_id(conn, account_id, external_thread_id, contact_name)
                if external_message_id:
                    existing = await conn.fetchval(
                        """
                        SELECT id FROM channels.channel_messages
                        WHERE thread_id = $1 AND external_message_id = $2
                        """,
                        thread_id,
                        external_message_id,
                    )
                    if existing:
                        return existing
                message_id = uuid.uuid4()
                await conn.execute(
                    """
                    INSERT INTO channels.channel_messages
                        (id, thread_id, direction, external_message_id, content, payload_json, status)
                    VALUES ($1, $2, 'in', $3, $4, $5::jsonb, 'received')
                    """,
                    message_id,
                    thread_id,
                    external_message_id,
                    content,
                    json.dumps(raw_payload),
                )
                return message_id
