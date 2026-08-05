import type { Intent, Notification, Offer, Order, User } from "~/types";

export const demoBuyerUser: User = {
  id: "00000000-0000-4000-8000-000000000101",
  email: "buyer@demo.ainerwise.com",
  full_name: "Demo Buyer",
  role: "BUYER",
  status: "ACTIVE",
  phone: "+381 60 000 0001",
  avatar_url: "",
  two_fa_enabled: false,
  created_at: "2026-05-14T00:00:00.000Z",
};

export const demoSupplierUser: User = {
  id: "00000000-0000-4000-8000-000000000201",
  email: "supplier@demo.ainerwise.com",
  full_name: "Demo Supplier",
  role: "SUPPLIER_ADMIN",
  status: "ACTIVE",
  phone: "+381 60 000 0002",
  avatar_url: "",
  two_fa_enabled: false,
  created_at: "2026-05-14T00:00:00.000Z",
};

export function isDemoEmail(email: string) {
  return email.trim().toLowerCase().endsWith("@demo.ainerwise.com");
}

export function isDemoToken(token?: string | null) {
  return !!token && token.startsWith("demo-");
}

export function demoUserForEmail(email: string): User | null {
  const normalized = email.trim().toLowerCase();
  if (normalized === demoBuyerUser.email) return demoBuyerUser;
  if (normalized === demoSupplierUser.email) return demoSupplierUser;
  return null;
}

export function demoUserForToken(token?: string | null): User | null {
  if (token === "demo-buyer-token") return demoBuyerUser;
  if (token === "demo-supplier-token") return demoSupplierUser;
  return null;
}

export const demoMarketplaceItems = [
  {
    id: "demo-market-n95-mask",
    title: "KNX Smart Switch Panel",
    description: "Glass wall switch panel for smart villas, boutique hotels, and office upgrades.",
    price_minor: 55000,
    currency: "EUR",
    unit: "pcs",
    stock_qty: 1200,
    images: ["https://images.unsplash.com/photo-1584634731339-252c581abfc5?auto=format&fit=crop&w=900&q=80"],
    tags: ["knx", "smart-home", "switch"],
    market_mode: "B2B",
    min_order_qty: 20,
    weight_kg: 8,
    origin_country: "RS",
    view_count: 230,
    order_count: 82,
    category_id: "demo-cat-smart-living",
    category_name: "Smart Living",
    company_id: "demo-company-belgrade-supply",
    company_name: "AinerWise Building Supply",
    company_trust_score: 86,
    is_sponsored: false,
  },
  {
    id: "demo-market-gloves",
    title: "DIN Rail Energy Meter",
    description: "Three-phase energy meter for solar, HVAC, and smart building dashboards.",
    price_minor: 45000,
    currency: "EUR",
    unit: "pcs",
    stock_qty: 800,
    images: ["https://images.unsplash.com/photo-1583947215259-38e31be8751f?auto=format&fit=crop&w=900&q=80"],
    tags: ["energy", "meter", "dashboard"],
    market_mode: "B2B",
    min_order_qty: 10,
    weight_kg: 5,
    origin_country: "RS",
    view_count: 148,
    order_count: 64,
    category_id: "demo-cat-energy",
    category_name: "Energy / Solar",
    company_id: "demo-company-belgrade-supply",
    company_name: "AinerWise Building Supply",
    company_trust_score: 84,
    is_sponsored: true,
  },
  {
    id: "demo-market-keyboard",
    title: "Logitech MX Keys Business Keyboard",
    description: "Wireless productivity keyboard for office procurement and IT rollout.",
    price_minor: 699900,
    currency: "EUR",
    unit: "pcs",
    stock_qty: 75,
    images: ["https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=900&q=80"],
    tags: ["keyboard", "electronics", "office"],
    market_mode: "B2C",
    min_order_qty: 1,
    weight_kg: 1,
    origin_country: "RS",
    view_count: 512,
    order_count: 67,
    category_id: "demo-cat-electronics",
    category_name: "Electronics & Components",
    company_id: "demo-company-tech",
    company_name: "TechWholesale Inc",
    company_trust_score: 91,
    is_sponsored: false,
  },
  {
    id: "demo-market-cement",
    title: "Smart Hotel Upgrade Materials Kit",
    description: "Starter materials package for small hotel lighting, access, network, and room-control upgrades.",
    price_minor: 49500,
    currency: "EUR",
    unit: "set",
    stock_qty: 3000,
    images: ["https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=900&q=80"],
    tags: ["cement", "construction"],
    market_mode: "B2B",
    min_order_qty: 50,
    weight_kg: 40,
    origin_country: "RS",
    view_count: 333,
    order_count: 115,
    category_id: "demo-cat-construction",
    category_name: "Construction Materials",
    company_id: "demo-company-belgrade-supply",
    company_name: "AinerWise Building Supply",
    company_trust_score: 88,
    is_sponsored: false,
  },
];

export const demoSupplierCandidates = [
  {
    supplier_id: demoSupplierUser.id,
    company_id: "demo-company-tech",
    company_name: "TechWholesale Inc",
    catalog_item_id: "demo-market-keyboard",
    catalog_item_title: "Logitech MX Keys Business Keyboard",
    unit_price_minor: 699900,
    currency: "EUR",
    unit: "pcs",
    market_mode: "B2C",
    origin_country: "RS",
    ranking_score: 96.4,
    why_recommended: "selected catalog item · 4.8km away · 92% deal rate · in stock",
    score_breakdown: {
      category_match: 98,
      trust_score: 910,
      trust_tier: "GOLD",
      deal_completion_rate: 0.92,
      distance_km: 4.8,
      has_stock: true,
      stock_qty: 75,
      verification_level: "TRUSTED",
      price_minor: 699900,
      bound_catalog_item: false,
      bound_supplier: false,
    },
  },
  {
    supplier_id: demoSupplierUser.id,
    company_id: "demo-company-belgrade-supply",
    company_name: "AinerWise Building Supply",
    catalog_item_id: "demo-market-n95-mask",
    catalog_item_title: "KNX Smart Switch Panel",
    unit_price_minor: 55000,
    currency: "EUR",
    unit: "pcs",
    market_mode: "B2B",
    origin_country: "RS",
    ranking_score: 92.1,
    why_recommended: "3.2km away · 89% deal rate · in stock · verified business",
    score_breakdown: {
      category_match: 95,
      trust_score: 880,
      trust_tier: "SILVER",
      deal_completion_rate: 0.89,
      distance_km: 3.2,
      has_stock: true,
      stock_qty: 1200,
      verification_level: "BUSINESS",
      price_minor: 55000,
      bound_catalog_item: false,
      bound_supplier: false,
    },
  },
  {
    supplier_id: "00000000-0000-4000-8000-000000000202",
    company_id: "demo-company-medtrade",
    company_name: "Energy Systems Partner",
    catalog_item_id: "demo-market-gloves",
    catalog_item_title: "DIN Rail Energy Meter",
    unit_price_minor: 45000,
    currency: "EUR",
    unit: "pcs",
    market_mode: "B2B",
    origin_country: "RS",
    ranking_score: 84.7,
    why_recommended: "lower cost · 8.5km away · in stock",
    score_breakdown: {
      category_match: 88,
      trust_score: 760,
      trust_tier: "BRONZE",
      deal_completion_rate: 0.78,
      distance_km: 8.5,
      has_stock: true,
      stock_qty: 800,
      verification_level: "BASIC",
      price_minor: 45000,
      bound_catalog_item: false,
      bound_supplier: false,
    },
  },
];

export const demoIntents: Intent[] = [
  {
    id: "demo-intent-n95",
    buyer_id: demoBuyerUser.id,
    category_id: "demo-cat-smart-living",
    title: "Quote Request: KNX Smart Switch Panel",
    notes: "Need smart switch panels for a Belgrade smart living upgrade. Compare by landed cost and delivery speed.",
    qty: 20,
    unit: "pcs",
    budget_min_minor: 0,
    budget_max_minor: 1500000,
    currency: "EUR",
    country: "RS",
    city: "Belgrade",
    radius_km: 25,
    status: "ACTIVE",
    created_at: "2026-05-14T01:00:00.000Z",
    offer_count: 3,
  },
  {
    id: "demo-intent-keyboard",
    buyer_id: demoBuyerUser.id,
    category_id: "demo-cat-electronics",
    title: "B2C Direct Order: Logitech MX Keys Business Keyboard",
    notes: "Single unit business keyboard purchase.",
    qty: 1,
    unit: "pcs",
    currency: "EUR",
    country: "RS",
    city: "Belgrade",
    radius_km: 15,
    status: "AWARDED",
    created_at: "2026-05-14T02:00:00.000Z",
    offer_count: 1,
  },
];

export const demoOffers: Offer[] = [
  {
    id: "demo-offer-mask-a",
    intent_id: "demo-intent-n95",
    company_id: "demo-company-belgrade-supply",
    branch_id: "demo-branch-belgrade",
    supplier_user_id: demoSupplierUser.id,
    unit_price_minor: 55000,
    qty_available: 500,
    delivery_fee_minor: 35000,
    total_price_minor: 1135000,
    currency: "EUR",
    eta_date: "2026-05-16",
    warranty: "7-day replacement for damaged boxes",
    tier: "BEST",
    stock_confidence: "FIRM",
    message: "In stock in Belgrade. Same week delivery available.",
    status: "SUBMITTED",
    created_at: "2026-05-14T03:00:00.000Z",
    company_name: "AinerWise Building Supply",
  },
  {
    id: "demo-offer-mask-b",
    intent_id: "demo-intent-n95",
    company_id: "demo-company-medtrade",
    supplier_user_id: "00000000-0000-4000-8000-000000000202",
    unit_price_minor: 52000,
    qty_available: 300,
    delivery_fee_minor: 65000,
    total_price_minor: 1105000,
    currency: "EUR",
    eta_date: "2026-05-18",
    tier: "GOOD",
    stock_confidence: "FIRM",
    message: "Lower unit price, delivery from partner warehouse.",
    status: "SUBMITTED",
    created_at: "2026-05-14T03:15:00.000Z",
    company_name: "Energy Systems Partner",
  },
  {
    id: "demo-offer-mask-c",
    intent_id: "demo-intent-n95",
    company_id: "demo-company-quickppe",
    supplier_user_id: "00000000-0000-4000-8000-000000000203",
    unit_price_minor: 59000,
    qty_available: 1000,
    delivery_fee_minor: 0,
    total_price_minor: 1180000,
    currency: "EUR",
    eta_date: "2026-05-15",
    tier: "CUSTOM",
    stock_confidence: "FIRM",
    message: "Fastest delivery. Free delivery inside Belgrade.",
    status: "SUBMITTED",
    created_at: "2026-05-14T03:30:00.000Z",
    company_name: "QuickPPE Supply",
  },
];

export const demoOrders: Order[] = [
  {
    id: "demo-order-keyboard",
    intent_id: "demo-intent-keyboard",
    offer_id: "demo-offer-keyboard",
    buyer_id: demoBuyerUser.id,
    company_id: "demo-company-tech",
    total_amount_minor: 699900,
    currency: "EUR",
    status: "AWAITING_PAYMENT",
    created_at: "2026-05-14T04:00:00.000Z",
  },
];

export const demoNotifications: Notification[] = [
  {
    id: "demo-notif-offer",
    user_id: demoBuyerUser.id,
    channel: "IN_APP",
    notification_type: "OFFER_RECEIVED",
    subject: "New offer received",
    body: "AinerWise Building Supply submitted an offer for your smart switch panel request.",
    status: "SENT",
    created_at: "2026-05-14T03:05:00.000Z",
    is_read: false,
  },
];

export function demoOffersForIntent(intentId: string) {
  return demoOffers.filter((offer) => offer.intent_id === intentId);
}

export function demoMarketplaceItemById(id: string) {
  return demoMarketplaceItems.find((item) => item.id === id) ?? null;
}

export function demoSupplierCandidatesForIntent(intentId: string) {
  const intent = demoIntents.find((row) => row.id === intentId);
  if (!intent) return [];
  const rows = demoSupplierCandidates.filter((candidate) => {
    if (intent.category_id === "demo-cat-electronics") {
      return candidate.catalog_item_id === "demo-market-keyboard";
    }
    if (intent.category_id === "demo-cat-medical") {
      return ["demo-market-n95-mask", "demo-market-gloves"].includes(candidate.catalog_item_id);
    }
    return true;
  });
  return rows.map((row) => ({ ...row, score_breakdown: { ...row.score_breakdown } }));
}
