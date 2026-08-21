"""Growth module — provider-adapter STANDARD (底层标准).

This file is the single source of truth for the capability contracts that every
concrete integration must satisfy: sourcing (闲鱼/淘宝/1688), text translation,
image translation, copy/image/video generation, auto-pricing, and publishing to
social channels (Instagram/Facebook/…).

Design goals
------------
* One capability = one Protocol. A provider declares which capabilities it
  implements and is registered once; nothing else in the system special-cases a
  vendor by name. Swapping ByteDance for OpenAI, or 1688 for Xianyu, is a new
  adapter file — no call-site changes.
* Everything is expressed as small, JSON-serialisable pydantic v2 DTOs, so the
  same method surface can be exposed to an LLM/agent as a tool (see
  ``tool_signatures``) and driven automatically.
* Async work reuses the platform's existing claim-queue lifecycle
  (``MarketingMediaRequest``): a ``ProviderJob`` is *available → claimed →
  running → completed | failed*, so an external worker OR an in-process adapter
  can fulfil it identically.

Nothing here touches the database or performs I/O — it is pure contract, safe to
import and unit-test in isolation. Concrete adapters live in ``adapters/`` and
the ORM/service/API wiring in the sibling modules.
"""
from __future__ import annotations

import enum
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Capability taxonomy
# --------------------------------------------------------------------------- #
class Capability(str, enum.Enum):
    """The standard set of things a provider can do. Admin config, the provider
    registry and the LLM tool surface are all keyed off these values."""

    SOURCE = "source"                 # pull a listing from an external marketplace
    TRANSLATE_TEXT = "translate_text"  # localise title/description/attributes
    TRANSLATE_IMAGE = "translate_image"  # re-render in-image text in the target language
    GEN_COPY = "gen_copy"             # promo caption / article / landing copy
    GEN_IMAGE = "gen_image"           # text-to-image / product beauty shot
    GEN_VIDEO = "gen_video"           # short promo / product video
    PRICE = "price"                   # cost + freight + fx + margin + fee -> sell price
    PUBLISH = "publish"               # post / schedule to a social channel


class JobStatus(str, enum.Enum):
    """Lifecycle shared by every asynchronous provider job. Mirrors the existing
    ``MarketingMediaRequest`` states so the claim queue stays uniform."""

    AVAILABLE = "available"
    CLAIMED = "claimed"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# --------------------------------------------------------------------------- #
# Shared value objects
# --------------------------------------------------------------------------- #
class Money(BaseModel):
    """Amounts are always integer minor units + ISO currency, matching the rest
    of the platform (``*_minor`` columns)."""

    minor: int
    currency: str = "EUR"


class MediaAsset(BaseModel):
    """A produced image/video, normalised to what ``MarketingAsset`` stores."""

    kind: str  # image | video | video_script
    object_key: str | None = None      # MinIO/S3 key when the file lives with us
    url: str | None = None             # or an external URL
    external_ref: str | None = None    # provider job / asset id, for idempotency
    mime_type: str | None = None
    width: int | None = None
    height: int | None = None
    duration_seconds: int | None = None
    sha256: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


# --------------------------------------------------------------------------- #
# SOURCE — normalised item pulled from an external marketplace
# --------------------------------------------------------------------------- #
class SourcedItem(BaseModel):
    """Whatever a marketplace returns is normalised into this shape before it
    touches the rest of the pipeline. `source` + `external_id` is the natural key
    used for dedupe and idempotent re-imports."""

    source: str                      # xianyu | taobao | 1688 | …
    external_id: str
    url: str | None = None
    title: str = ""
    description: str = ""
    images: list[str] = Field(default_factory=list)
    price: Money | None = None       # the source listing price (e.g. CNY)
    attributes: dict[str, Any] = Field(default_factory=dict)  # specs, brand, moq…
    seller_ref: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)  # kept for audit, never rendered


class SourceQuery(BaseModel):
    q: str
    page: int = 1
    page_size: int = 20
    filters: dict[str, Any] = Field(default_factory=dict)


# --------------------------------------------------------------------------- #
# TRANSLATE
# --------------------------------------------------------------------------- #
class TranslateRequest(BaseModel):
    texts: list[str]
    target_lang: str                 # en | sr | pl | …
    source_lang: str | None = None   # None = auto-detect
    glossary: dict[str, str] = Field(default_factory=dict)  # brand/term overrides
    context: str | None = None       # e.g. "smart-home product listing"


class TranslateResult(BaseModel):
    texts: list[str]
    detected_source_lang: str | None = None
    provider_ref: str | None = None


class ImageTranslateRequest(BaseModel):
    image_url: str | None = None
    object_key: str | None = None
    target_lang: str
    source_lang: str | None = None
    keep_layout: bool = True         # re-render text in place vs. clean plate + caption


# --------------------------------------------------------------------------- #
# GENERATE (copy / image / video)
# --------------------------------------------------------------------------- #
class CopyRequest(BaseModel):
    channel: str                     # instagram | facebook | linkedin | email | landing
    lang: str
    product_ref: str | None = None
    brief: str                       # creative brief / key points
    tone: str | None = None
    max_chars: int | None = None
    hashtags: bool = True


class CopyResult(BaseModel):
    channel: str
    lang: str
    title: str | None = None
    body: str
    hashtags: list[str] = Field(default_factory=list)
    provider_ref: str | None = None


class ImageGenRequest(BaseModel):
    prompt: str
    lang: str | None = None
    size: str = "1024x1024"
    reference_images: list[str] = Field(default_factory=list)
    product_ref: str | None = None
    n: int = 1


class VideoGenRequest(BaseModel):
    brief: str
    lang: str
    duration_seconds: int = 15
    aspect_ratio: str = "9:16"
    reference_images: list[str] = Field(default_factory=list)
    voiceover: bool = False
    product_ref: str | None = None


# --------------------------------------------------------------------------- #
# PRICE — the auto-markup / arbitrage pricing standard
# --------------------------------------------------------------------------- #
class PriceInputs(BaseModel):
    """All figures needed to turn a source cost into a sell price. Mirrors the
    existing ``ProductCost`` (freight_pct/freight_fixed/landed) + ``ExchangeRate``
    + ``platform_fee_rules`` primitives, unified into one call."""

    purchase_cost: Money             # in the source currency (e.g. CNY)
    fx_rate: Decimal = Decimal(1)    # source currency -> target currency
    sell_currency: str | None = None # target/sell currency; defaults to EUR (or freight_fixed's currency)
    freight_pct: Decimal = Decimal(0)     # % of purchase cost
    freight_fixed: Money | None = None    # flat freight, in target currency
    duties_pct: Decimal = Decimal(0)      # customs/VAT on landed, %
    target_margin_pct: Decimal = Decimal("0.30")   # gross margin you want to keep
    platform_fee_pct: Decimal = Decimal(0)         # platform take, grossed-up
    min_price: Money | None = None
    max_price: Money | None = None
    round_to_minor: int = 0          # 0 = no rounding; 9900 = round to x.99 in minor


class PriceQuote(BaseModel):
    sell: Money
    landed: Money                    # cost delivered to us, target currency
    margin_pct: Decimal              # realised margin after rounding & clamps
    breakdown: dict[str, int] = Field(default_factory=dict)  # every component, minor units


class PublishRequest(BaseModel):
    """Maps 1:1 onto the existing ``PublishJob`` row."""

    asset_id: str                    # MarketingAsset id
    platform: str                    # instagram | facebook | tiktok | …
    account_ref: str | None = None   # which connected account
    scheduled_at: str | None = None  # ISO-8601; None = publish now
    idempotency_key: str | None = None


class PublishResult(BaseModel):
    status: JobStatus
    external_post_id: str | None = None
    scheduled_at: str | None = None
    error: str | None = None


# --------------------------------------------------------------------------- #
# Async job envelope (claim queue) — one shape for every long-running capability
# --------------------------------------------------------------------------- #
class ProviderJob(BaseModel):
    id: str
    capability: Capability
    status: JobStatus = JobStatus.AVAILABLE
    provider_key: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)   # a *Request DTO dumped
    result: dict[str, Any] | None = None                    # a *Result DTO dumped
    external_ref: str | None = None
    progress_percent: int | None = None
    failure_code: str | None = None
    failure_message: str | None = None


# --------------------------------------------------------------------------- #
# Capability Protocols — what an adapter must implement
# --------------------------------------------------------------------------- #
@runtime_checkable
class SourceAdapter(Protocol):
    key: str
    async def search(self, query: SourceQuery) -> list[SourcedItem]: ...
    async def fetch(self, url_or_id: str) -> SourcedItem: ...


@runtime_checkable
class TextTranslator(Protocol):
    key: str
    async def translate(self, req: TranslateRequest) -> TranslateResult: ...


@runtime_checkable
class ImageTranslator(Protocol):
    key: str
    async def translate_image(self, req: ImageTranslateRequest) -> MediaAsset: ...


@runtime_checkable
class CopyGenerator(Protocol):
    key: str
    async def generate_copy(self, req: CopyRequest) -> CopyResult: ...


@runtime_checkable
class ImageGenerator(Protocol):
    key: str
    async def generate_image(self, req: ImageGenRequest) -> list[MediaAsset]: ...


@runtime_checkable
class VideoGenerator(Protocol):
    key: str
    async def generate_video(self, req: VideoGenRequest) -> MediaAsset: ...


@runtime_checkable
class Repricer(Protocol):
    key: str
    def price(self, inputs: PriceInputs) -> PriceQuote: ...


@runtime_checkable
class Publisher(Protocol):
    key: str
    async def publish(self, req: PublishRequest) -> PublishResult: ...


# --------------------------------------------------------------------------- #
# The standard pricing function (default Repricer maths)
# --------------------------------------------------------------------------- #
def compute_sell_price(inputs: PriceInputs) -> PriceQuote:
    """Reference implementation of the auto-markup formula. A custom Repricer may
    override it, but this is the contract every rule engine is measured against::

        landed  = purchase*fx*(1 + freight_pct) + freight_fixed
        landed += landed * duties_pct
        pre_fee = landed / (1 - target_margin_pct)     # keep the margin
        sell    = pre_fee / (1 - platform_fee_pct)      # gross up for platform take
        sell    = round / clamp(min,max)

    All money is target-currency minor units. Margin/fee/duty are fractions
    (0.30 = 30%). ``round_to_minor`` snaps to a psychological price (e.g. 9900 ->
    x900 endings) after the gross-up.
    """
    # Amounts below are already fx-converted into the target currency, so label
    # them with the sell currency — never the source (purchase) currency.
    cur = inputs.sell_currency or (inputs.freight_fixed.currency if inputs.freight_fixed else "EUR")
    D = Decimal

    purchase = D(inputs.purchase_cost.minor) * inputs.fx_rate
    freight = purchase * inputs.freight_pct + D(inputs.freight_fixed.minor if inputs.freight_fixed else 0)
    landed_base = purchase + freight
    duties = landed_base * inputs.duties_pct
    landed = landed_base + duties

    margin = inputs.target_margin_pct
    fee = inputs.platform_fee_pct
    pre_fee = landed / (D(1) - margin) if margin < 1 else landed
    sell = pre_fee / (D(1) - fee) if fee < 1 else pre_fee

    if inputs.round_to_minor and inputs.round_to_minor > 0:
        step = D(inputs.round_to_minor)
        sell = (sell / step).to_integral_value(rounding=ROUND_HALF_UP) * step

    sell_minor = int(sell.to_integral_value(rounding=ROUND_HALF_UP))
    if inputs.min_price and sell_minor < inputs.min_price.minor:
        sell_minor = inputs.min_price.minor
    if inputs.max_price and sell_minor > inputs.max_price.minor:
        sell_minor = inputs.max_price.minor

    landed_minor = int(landed.to_integral_value(rounding=ROUND_HALF_UP))
    net_after_fee = D(sell_minor) * (D(1) - fee)
    realised_margin = (net_after_fee - D(landed_minor)) / net_after_fee if net_after_fee > 0 else D(0)

    return PriceQuote(
        sell=Money(minor=sell_minor, currency=cur),
        landed=Money(minor=landed_minor, currency=cur),
        margin_pct=realised_margin.quantize(D("0.0001")),
        breakdown={
            "purchase_converted": int(purchase),
            "freight": int(freight),
            "duties": int(duties),
            "landed": landed_minor,
            "platform_fee": int(D(sell_minor) * fee),
            "sell": sell_minor,
        },
    )


# --------------------------------------------------------------------------- #
# Provider registry — every adapter registers here, keyed by (key, capability)
# --------------------------------------------------------------------------- #
class ProviderSpec(BaseModel):
    key: str                          # "ayrshare", "openai", "xianyu-open", …
    label: str
    capabilities: set[Capability]
    settings_category: str            # which IntegrationSetting row holds its keys
    model_config = {"arbitrary_types_allowed": True}


class ProviderRegistry:
    """In-memory registry populated at import time by each adapter module. The
    admin UI reads it to show what's installed; the service layer resolves the
    enabled provider for a capability from ``IntegrationSetting``."""

    def __init__(self) -> None:
        self._specs: dict[str, ProviderSpec] = {}
        self._impls: dict[str, Any] = {}

    def register(self, spec: ProviderSpec, impl: Any) -> None:
        self._specs[spec.key] = spec
        self._impls[spec.key] = impl

    def spec(self, key: str) -> ProviderSpec | None:
        return self._specs.get(key)

    def impl(self, key: str) -> Any | None:
        return self._impls.get(key)

    def for_capability(self, cap: Capability) -> list[ProviderSpec]:
        return [s for s in self._specs.values() if cap in s.capabilities]

    def all(self) -> list[ProviderSpec]:
        return list(self._specs.values())


registry = ProviderRegistry()


# --------------------------------------------------------------------------- #
# LLM tool surface — each capability method is exposed to the agent team as a
# JSON-schema tool. The runtime builds these from the *Request DTOs; this list is
# the canonical name↔capability map an agent is allowed to call.
# --------------------------------------------------------------------------- #
TOOL_SIGNATURES: dict[str, Capability] = {
    "source.search": Capability.SOURCE,
    "source.fetch": Capability.SOURCE,
    "translate.text": Capability.TRANSLATE_TEXT,
    "translate.image": Capability.TRANSLATE_IMAGE,
    "generate.copy": Capability.GEN_COPY,
    "generate.image": Capability.GEN_IMAGE,
    "generate.video": Capability.GEN_VIDEO,
    "price.quote": Capability.PRICE,
    "publish.post": Capability.PUBLISH,
}
