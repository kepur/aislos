from __future__ import annotations

import httpx

from app.config import Settings


class BackendClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def _headers(self) -> dict[str, str]:
        return {"X-Service-Token": self.settings.SERVICE_TOKEN}

    async def channel_config(self, channel: str) -> dict:
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(
                f"{self.settings.BACKEND_INTERNAL_URL.rstrip('/')}/channel-config/{channel}",
                headers=self._headers,
            )
            response.raise_for_status()
            return response.json()

    async def forward_inbound(self, message: dict) -> None:
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.post(
                f"{self.settings.BACKEND_INTERNAL_URL.rstrip('/')}/channels/inbound",
                headers=self._headers,
                json=message,
            )
            response.raise_for_status()
