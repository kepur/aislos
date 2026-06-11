from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class NormalizedMessage:
    external_thread_id: str
    external_message_id: str | None
    content: str | None
    contact_name: str | None
    raw_payload: dict


@dataclass(frozen=True)
class SendResult:
    external_message_id: str | None
    raw_payload: dict


class ChannelAdapter(ABC):
    @abstractmethod
    async def receive(self, payload: dict) -> NormalizedMessage | None:
        """Receive and normalize a provider webhook."""

    @abstractmethod
    async def send(self, external_thread_id: str, content: str) -> SendResult:
        """Send a message through the provider."""

    @abstractmethod
    def normalize(self, payload: dict) -> NormalizedMessage | None:
        """Map provider payload to the shared message contract."""
