"""Default repricer — the standard auto-markup maths as a Repricer adapter."""
from __future__ import annotations

from ..contracts import PriceInputs, PriceQuote, compute_sell_price


class DefaultRepricer:
    key = "default"

    def price(self, inputs: PriceInputs) -> PriceQuote:
        return compute_sell_price(inputs)
