import uuid
from datetime import datetime

from pydantic import EmailStr

from app.schemas.base import BaseSchema


class CategorySchemaCreate(BaseSchema):
    slug: str
    name: str
    definition: dict


class CategorySchemaRead(BaseSchema):
    id: uuid.UUID
    slug: str
    name: str
    version: int
    definition: dict
    status: str


class SupplierListingCreate(BaseSchema):
    # Accepted during the legacy migration window, but the API derives and
    # verifies supplier identity from the authenticated user.
    company_id: uuid.UUID | None = None
    region_id: uuid.UUID | None = None
    category_schema_id: uuid.UUID | None = None
    title: str
    attributes_json: dict | None = None
    price_minor: int | None = None
    currency: str = "EUR"
    legacy_catalog_item_id: str | None = None


class SupplierListingRead(SupplierListingCreate):
    id: uuid.UUID
    status: str
    created_at: datetime


class SupplierListingUpdate(BaseSchema):
    region_id: uuid.UUID | None = None
    category_schema_id: uuid.UUID | None = None
    title: str | None = None
    attributes_json: dict | None = None
    price_minor: int | None = None
    currency: str | None = None
    status: str | None = None


class BuyerWatchlistCreate(BaseSchema):
    supplier_listing_id: uuid.UUID
    target_price_minor: int | None = None
    currency: str = "EUR"


class BuyerWatchlistRead(BuyerWatchlistCreate):
    id: uuid.UUID
    buyer_user_id: uuid.UUID
    status: str
    listing: SupplierListingRead
    created_at: datetime


class BuyerAccountUpdate(BaseSchema):
    full_name: str | None = None
    phone: str | None = None
    language: str | None = None
    country: str | None = None
    company_name: str | None = None
    company_country: str | None = None
    company_city: str | None = None
    company_address: str | None = None
    company_description: str | None = None
    company_website: str | None = None


class SupplierTeamInvite(BaseSchema):
    email: EmailStr
    full_name: str | None = None
    phone: str | None = None


class SupplierTeamUpdate(BaseSchema):
    full_name: str | None = None
    phone: str | None = None
    is_active: bool | None = None


class ProcurementRequestCreate(BaseSchema):
    workspace_id: uuid.UUID | None = None
    title: str
    description: str | None = None
    category_schema_id: uuid.UUID | None = None
    region_id: uuid.UUID | None = None
    requirements_json: dict | None = None
    portal_key: str = "cebu"


class ProcurementRequestRead(ProcurementRequestCreate):
    id: uuid.UUID
    status: str
    lead_id: uuid.UUID | None = None
    attrs_json: dict | None = None
    published_at: datetime | None = None
    legacy_request_id: str | None = None
    created_at: datetime


class SupplierOfferCreate(BaseSchema):
    supplier_listing_id: uuid.UUID | None = None
    # Accepted during the legacy migration window; never trusted by the API.
    supplier_company_id: uuid.UUID | None = None
    price_minor: int
    currency: str = "EUR"
    terms_json: dict | None = None


class SupplierOfferRead(SupplierOfferCreate):
    id: uuid.UUID
    workspace_id: uuid.UUID | None
    procurement_request_id: uuid.UUID
    status: str
    created_at: datetime


class CommerceOrderRead(BaseSchema):
    id: uuid.UUID
    workspace_id: uuid.UUID | None
    procurement_request_id: uuid.UUID
    winning_offer_id: uuid.UUID | None
    buyer_company_id: uuid.UUID | None = None
    supplier_company_id: uuid.UUID | None = None
    status: str
    total_minor: int
    currency: str
    completed_at: datetime | None = None


class OrderDeliveryCreate(BaseSchema):
    carrier: str | None = None
    tracking_number: str | None = None
    ship_from_json: dict | None = None
    ship_to_json: dict | None = None
    estimated_at: datetime | None = None


class OrderDeliveryRead(OrderDeliveryCreate):
    id: uuid.UUID
    workspace_id: uuid.UUID | None
    commerce_order_id: uuid.UUID
    status: str
    shipped_at: datetime | None = None
    delivered_at: datetime | None = None
    accepted_at: datetime | None = None
    proof_json: dict | None = None


class DeliveryStatusUpdate(BaseSchema):
    status: str
    proof_json: dict | None = None


class OrderDisputeCreate(BaseSchema):
    reason_code: str
    description: str | None = None


class OrderDisputeRead(OrderDisputeCreate):
    id: uuid.UUID
    workspace_id: uuid.UUID | None
    commerce_order_id: uuid.UUID
    opened_by_role: str
    status: str
    resolution_json: dict | None = None
    resolved_at: datetime | None = None
    created_at: datetime


class DisputeResolveRequest(BaseSchema):
    resolution: str
    resolution_json: dict | None = None


class TrustProfileRead(BaseSchema):
    id: uuid.UUID
    company_id: uuid.UUID
    portal_key: str
    completed_orders: int
    dispute_count: int
    review_count: int
    avg_rating: float | None = None
    trust_score: int
    metrics_json: dict | None = None


class TransactionReviewCreate(BaseSchema):
    rating: int
    comment: str | None = None


class TransactionReviewRead(TransactionReviewCreate):
    id: uuid.UUID
    workspace_id: uuid.UUID | None
    commerce_order_id: uuid.UUID
    supplier_company_id: uuid.UUID | None = None
    status: str
    created_at: datetime


class RiskFlagRead(BaseSchema):
    id: uuid.UUID
    subject_type: str
    subject_id: uuid.UUID
    company_id: uuid.UUID | None = None
    reason_code: str
    severity: str
    status: str
    source_event: str | None = None
    details_json: dict | None = None
    resolved_at: datetime | None = None
    created_at: datetime


class RiskFlagResolveRequest(BaseSchema):
    resolution: str


class PaymentIntentCreate(BaseSchema):
    quote_currency: str | None = None
    psp_provider: str = "stripe"


class PaymentIntentRead(BaseSchema):
    id: uuid.UUID
    workspace_id: uuid.UUID | None
    commerce_order_id: uuid.UUID
    payment_plan_id: uuid.UUID | None = None
    psp_provider: str
    status: str
    amount_minor: int
    currency: str
    quote_currency: str | None = None
    fx_rate: float | None = None
    quote_amount_minor: int | None = None
    external_ref: str | None = None
    created_at: datetime


class FxQuoteRead(BaseSchema):
    order_id: str
    base_currency: str
    quote_currency: str
    base_amount_minor: int
    quote_amount_minor: int
    fx_rate: str


class PortalNotificationRead(BaseSchema):
    id: uuid.UUID
    portal_key: str
    domain: str
    event_type: str
    title: str
    body: str | None = None
    link_path: str | None = None
    aggregate_type: str | None = None
    aggregate_id: uuid.UUID | None = None
    status: str
    read_at: datetime | None = None
    created_at: datetime


class CommerceMessageCreate(BaseSchema):
    body: str
    attachments_json: dict | None = None


class CommerceMessageRead(CommerceMessageCreate):
    id: uuid.UUID
    workspace_id: uuid.UUID | None
    thread_id: uuid.UUID
    sender_user_id: uuid.UUID | None = None
    sender_role: str
    read_at: datetime | None = None
    created_at: datetime


class CheckoutSessionRead(BaseSchema):
    checkout_url: str | None = None
    configured: bool
    detail: str | None = None


class ConfirmFundingRequest(BaseSchema):
    external_ref: str
    source_account: str = "bank:offline"


class SettlementSettleRequest(BaseSchema):
    psp_settlement_ref: str
    platform_fee_minor: int = 0


class CommerceSettlementRead(BaseSchema):
    id: uuid.UUID
    workspace_id: uuid.UUID | None
    commerce_order_id: uuid.UUID
    payment_intent_id: uuid.UUID | None = None
    status: str
    amount_minor: int
    currency: str
    platform_fee_minor: int
    psp_provider: str
    external_ref: str | None = None
    psp_settlement_ref: str | None = None
    funded_at: datetime | None = None
    settled_at: datetime | None = None
    reconciled_at: datetime | None = None
    created_at: datetime


class ReconciliationRunCreate(BaseSchema):
    period_start: datetime
    period_end: datetime


class ReconciliationRunRead(ReconciliationRunCreate):
    id: uuid.UUID
    status: str
    matched_count: int
    mismatch_count: int
    pending_count: int
    summary_json: dict | None = None
    created_at: datetime


class CommerceThreadRead(BaseSchema):
    id: uuid.UUID
    workspace_id: uuid.UUID | None = None
    portal_key: str
    procurement_request_id: uuid.UUID | None = None
    commerce_order_id: uuid.UUID | None = None
    buyer_company_id: uuid.UUID | None = None
    supplier_company_id: uuid.UUID | None = None
    subject: str
    status: str
    created_at: datetime
