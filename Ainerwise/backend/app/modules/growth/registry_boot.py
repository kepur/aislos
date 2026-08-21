"""Register the P1 provider specs in the shared registry.

The registry is a *discovery catalog* (the admin UI lists what's installed and
which IntegrationSetting row holds each provider's keys). Concrete instances
are built per-request in ``service`` (some need a DB session), so here we only
register specs. Import this module once at app startup.
"""
from __future__ import annotations

from .contracts import Capability, ProviderSpec, registry

_BOOTED = False


def boot() -> None:
    global _BOOTED
    if _BOOTED:
        return
    registry.register(
        ProviderSpec(
            key="manual",
            label="Manual / fixture source",
            capabilities={Capability.SOURCE},
            settings_category="source",
        ),
        impl=None,
    )
    registry.register(
        ProviderSpec(
            key="llm",
            label="LLM translator (platform AI)",
            capabilities={Capability.TRANSLATE_TEXT, Capability.GEN_COPY},
            settings_category="ai",
        ),
        impl=None,
    )
    registry.register(
        ProviderSpec(
            key="default",
            label="Default repricer (standard markup)",
            capabilities={Capability.PRICE},
            settings_category="pricing",
        ),
        impl=None,
    )
    _BOOTED = True


boot()
