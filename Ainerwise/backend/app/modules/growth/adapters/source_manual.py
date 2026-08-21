"""Manual / fixture source adapter — the compliance-safe default.

It does **no scraping**. It normalises an operator-supplied payload (pasted in
the admin UI, uploaded as a fixture, or handed over by a licensed data feed)
into the standard ``SourcedItem``. When a real source is chosen (official open
API or a licensed third-party feed), it drops in as another adapter with the
same Protocol — nothing downstream changes. See standard §9 (compliance).
"""
from __future__ import annotations

from typing import Any

from ..contracts import Money, SourcedItem, SourceQuery


class ManualSourceAdapter:
    key = "manual"

    async def search(self, query: SourceQuery) -> list[SourcedItem]:
        # A manual source has nothing to crawl; items arrive via ``fetch``/normalise.
        return []

    async def fetch(self, url_or_id: str) -> SourcedItem:
        # Nothing to fetch remotely — the caller must supply the payload and use
        # ``normalize``. Kept to satisfy the SourceAdapter Protocol.
        raise NotImplementedError(
            "ManualSourceAdapter does not fetch remotely; use normalize(payload)."
        )

    @staticmethod
    def normalize(payload: dict[str, Any], *, source: str = "manual") -> SourcedItem:
        """Turn a loose operator/feed payload into a validated ``SourcedItem``.

        Accepts either flat keys (title/description/price_minor/price_currency…)
        or an already-shaped ``SourcedItem`` dict. The natural key is
        ``(source, external_id)``.
        """
        src = str(payload.get("source") or source)
        external_id = str(payload.get("external_id") or payload.get("id") or "").strip()
        if not external_id:
            raise ValueError("external_id is required to normalise a sourced item")

        price: Money | None = None
        price_minor = payload.get("price_minor")
        if price_minor is None and isinstance(payload.get("price"), dict):
            p = payload["price"]
            price_minor, price_cur = p.get("minor"), p.get("currency", "CNY")
        else:
            price_cur = payload.get("price_currency", "CNY")
        if price_minor is not None:
            price = Money(minor=int(price_minor), currency=str(price_cur or "CNY"))

        images = payload.get("images") or []
        if isinstance(images, str):
            images = [images]

        return SourcedItem(
            source=src,
            external_id=external_id,
            url=payload.get("url"),
            title=str(payload.get("title") or ""),
            description=str(payload.get("description") or ""),
            images=[str(i) for i in images],
            price=price,
            attributes=payload.get("attributes") or {},
            seller_ref=payload.get("seller_ref"),
            raw=payload.get("raw") or {},
        )
