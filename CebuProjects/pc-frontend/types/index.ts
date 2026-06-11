export type UserRole =
  | "BUYER"
  | "SUPPLIER_ADMIN"
  | "SUPPLIER_AGENT"
  | "ADMIN"
  | "SUPER_ADMIN"
  | "OPS_MANAGER"
  | "VERIFICATION_OFFICER"
  | "DISPUTE_AGENT"
  | "FINANCE_OFFICER"
  | "RISK_ANALYST"
  | "SUPPORT_AGENT"
  | "AUDITOR";

export type UserStatus = "ACTIVE" | "INACTIVE" | "SUSPENDED" | "PENDING_VERIFICATION" | "RESTRICTED" | "BANNED";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  status: UserStatus;
  account_type?: "PERSONAL" | "BUSINESS";
  phone?: string;
  avatar_url?: string;
  telegram_chat_id?: string | null;
  two_fa_enabled: boolean;
  last_login_at?: string;
  created_at: string;
}

export interface Company {
  id: string;
  owner_user_id: string;
  name: string;
  tax_id?: string | null;
  country: string;
  city?: string | null;
  address?: string | null;
  verification_level: "NONE" | "BASIC" | "BUSINESS";
  status: "ACTIVE" | "INACTIVE" | "SUSPENDED" | "PENDING_REVIEW";
  created_at: string;
}

export interface Branch {
  id: string;
  company_id: string;
  name: string;
  country: string;
  city: string;
  address: string;
  lat: number;
  lng: number;
  radius_km: number;
  delivery_methods: string[];
}

export type IntentStatus =
  | "DRAFT"
  | "ACTIVE"
  | "AWARDED"
  | "CLOSED"
  | "CANCELED"
  | "EXPIRED";

export interface Intent {
  id: string;
  buyer_id: string;
  category_id: string;
  title: string;
  notes?: string;
  qty: number;
  unit: string;
  budget_min_minor?: number;
  budget_max_minor?: number;
  currency: string;
  country?: string;
  city?: string;
  lat?: number;
  lng?: number;
  radius_km?: number;
  delivery_window_start?: string;
  delivery_window_end?: string;
  attrs_jsonb?: Record<string, unknown>;
  status: IntentStatus;
  expires_at?: string;
  created_at: string;
  attachments?: string[];
  offer_count?: number;
}

export type OfferStatus =
  | "DRAFT"
  | "SUBMITTED"
  | "VIEWED"
  | "SHORTLISTED"
  | "AWARDED"
  | "REJECTED"
  | "WITHDRAWN"
  | "EXPIRED";
export type OfferTier = "GOOD" | "BETTER" | "BEST" | "CUSTOM";
export type StockConfidence = "FIRM" | "BACKORDER" | "UNKNOWN";

export interface Offer {
  id: string;
  intent_id: string;
  company_id: string;
  branch_id?: string;
  catalog_item_id?: string;
  supplier_user_id: string;
  unit_price_minor: number;
  qty_available: number;
  delivery_fee_minor: number;
  total_price_minor: number;
  currency: string;
  eta_date?: string;
  warranty?: string;
  tier?: OfferTier;
  stock_confidence?: StockConfidence;
  message?: string;
  status: OfferStatus;
  expires_at?: string;
  created_at: string;
  company_name?: string;
}

export type OrderStatus =
  | "CREATED"
  | "AWAITING_PAYMENT"
  | "PAID_IN_ESCROW"
  | "IN_PROGRESS"
  | "DELIVERED"
  | "ACCEPTED"
  | "PAYOUT_RELEASED"
  | "DISPUTED"
  | "CANCELED"
  | "REFUNDED";

export interface Order {
  id: string;
  intent_id: string;
  offer_id: string;
  buyer_id: string;
  company_id: string;
  company_name?: string;
  branch_id?: string;
  total_amount_minor: number;
  currency: string;
  status: OrderStatus;
  notes?: string;
  created_at: string;
  updated_at?: string;
  escrow?: Escrow;
  delivery?: Delivery;
}

export type EscrowStatus = "PENDING" | "AUTHORIZED" | "CAPTURED" | "RELEASED" | "REFUNDED" | "DISPUTED" | "FAILED";

export interface Escrow {
  id: string;
  order_id: string;
  provider: string;
  amount_minor?: number;
  auth_amount_minor?: number;
  captured_amount_minor?: number;
  released_amount_minor?: number;
  refunded_amount_minor?: number;
  currency: string;
  status: EscrowStatus;
  created_at: string;
  updated_at?: string;
}

export type DeliveryStatus =
  | "PENDING"
  | "READY_FOR_PICKUP"
  | "DISPATCHED"
  | "DELIVERED"
  | "ACCEPTED"
  | "FAILED";

export interface Delivery {
  id: string;
  order_id: string;
  status: DeliveryStatus;
  tracking_number?: string;
  carrier?: string;
  notes?: string;
  proofs?: string[];
  actor_id: string;
  created_at: string;
  updated_at?: string;
}

export type DisputeStatus =
  | "OPENED"
  | "WAITING_BUYER_EVIDENCE"
  | "WAITING_SUPPLIER_EVIDENCE"
  | "UNDER_REVIEW"
  | "RESOLVED_REFUND"
  | "RESOLVED_RELEASE"
  | "RESOLVED_PARTIAL_REFUND"
  | "ESCALATED"
  | "CANCELED";

export interface Dispute {
  id: string;
  order_id: string;
  opened_by_user_id: string;
  reason: string;
  evidence_json?: Record<string, unknown>[];
  admin_notes?: string;
  status: DisputeStatus;
  resolution?: string;
  refund_amount_minor?: number;
  created_at: string;
  updated_at?: string;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  description?: string;
  schema_json?: Record<string, unknown>;
  status: "ACTIVE" | "INACTIVE";
}

export interface CatalogItem {
  id: string;
  company_id: string;
  branch_id?: string;
  category_id: string;
  title: string;
  description?: string;
  attrs_jsonb?: Record<string, unknown>;
  price_minor: number;
  currency: string;
  stock_qty?: number;
  unit: string;
  tags?: string[];
  status: "ACTIVE" | "INACTIVE" | "OUT_OF_STOCK";
  created_at: string;
}

export interface Notification {
  id: string;
  user_id: string;
  channel: "IN_APP" | "EMAIL" | "TELEGRAM";
  notification_type: string;
  subject?: string;
  body: string;
  status: "PENDING" | "SENT" | "FAILED" | "READ" | "UNREAD";
  read_at?: string;
  created_at: string;
  // convenience alias — backend returns status, frontend historically used is_read
  is_read?: boolean;
}

export interface Message {
  id: string;
  thread_type: string;
  thread_id: string;
  sender_id: string;
  body: string;
  attachments?: string[];
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface ApiError {
  detail: string | { msg: string; type: string }[];
}

export type TrustTier = "BRONZE" | "SILVER" | "GOLD" | "PLATINUM" | "DIAMOND";
export type TrustProfileStatus = "ACTIVE" | "FROZEN" | "HIDDEN";

export interface TrustProfile {
  id: string;
  entity_type: "USER" | "COMPANY";
  entity_id: string;
  trust_score: number;
  trust_tier: TrustTier;
  profile_completion_rate: number;
  deal_completion_rate: number;
  deposit_amount_minor: number;
  deposit_currency: string;
  verified_deposit_minor: number;
  successful_deals_count: number;
  canceled_deals_count: number;
  dispute_rate: number;
  refund_rate: number;
  late_delivery_rate: number;
  late_payment_rate: number;
  score_breakdown_json?: Record<string, unknown>;
  status: TrustProfileStatus;
  last_calculated_at?: string;
  created_at: string;
  updated_at: string;
}

export interface TrustMe {
  user: TrustProfile;
  company?: TrustProfile | null;
}
