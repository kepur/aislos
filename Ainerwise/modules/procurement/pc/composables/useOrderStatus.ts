// Customer-facing labels for the legacy order-status enums.
// Enum values are backend contract (cebu-compat) and must not change here;
// records-first wording only (AISLOS never holds funds).
const ORDER_STATUS_LABELS: Record<string, string> = {
  CREATED: 'Created',
  AWAITING_PAYMENT: 'Awaiting Payment',
  PAID_IN_ESCROW: 'Payment Recorded',
  IN_PROGRESS: 'In Progress',
  DELIVERED: 'Delivered',
  ACCEPTED: 'Completed',
  PAYOUT_RELEASED: 'Settled',
  DISPUTED: 'Disputed',
  CANCELED: 'Canceled',
  CANCELLED: 'Canceled',
  REFUNDED: 'Refunded',
}

export function orderStatusLabel(status: string | null | undefined): string {
  const normalized = String(status || '').toUpperCase()
  return ORDER_STATUS_LABELS[normalized] || normalized || '—'
}
