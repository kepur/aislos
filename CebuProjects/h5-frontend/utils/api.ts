import type { $Fetch } from "ofetch";
import { isDemoToken } from "~/utils/demoData";

let _apiFetch: $Fetch | null = null;

export function useApiFetch() {
  const config = useRuntimeConfig();
  const authStore = useAuthStore();

  if (!_apiFetch) {
    _apiFetch = $fetch.create({
      baseURL: config.public.apiBase,
      onRequest({ options }) {
        const token = authStore.accessToken;
        if (token) {
          options.headers = {
            ...(options.headers as Record<string, string>),
            Authorization: `Bearer ${token}`,
          };
        }
      },
      async onResponseError({ response }) {
        if (response.status === 401 && (!authStore.isDemoMode || !isDemoToken(authStore.accessToken))) {
          await authStore.logout();
          navigateTo("/auth/login");
        }
      },
    });
  }

  return _apiFetch;
}

export function formatPrice(minor: number, currency = "PHP"): string {
  const amount = minor / 100;
  if (currency === "USDT") {
    return `${amount.toLocaleString("en-PH", { minimumFractionDigits: 0, maximumFractionDigits: 2 })} USDT`;
  }
  try {
    return new Intl.NumberFormat("en-PH", {
      style: "currency",
      currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    }).format(amount);
  } catch {
    return `${amount.toLocaleString("en-PH", { minimumFractionDigits: 0, maximumFractionDigits: 2 })} ${currency}`;
  }
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-PH", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatRelativeTime(dateStr: string): string {
  const now = new Date();
  const date = new Date(dateStr);
  const diff = now.getTime() - date.getTime();
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 7) return formatDate(dateStr);
  if (days > 0) return `${days}d ago`;
  if (hours > 0) return `${hours}h ago`;
  if (minutes > 0) return `${minutes}m ago`;
  return "just now";
}

export function getOrderStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    CREATED: "Created",
    AWAITING_PAYMENT: "Awaiting Payment",
    PAID_IN_ESCROW: "Paid in Escrow",
    IN_PROGRESS: "In Progress",
    DELIVERED: "Delivered",
    ACCEPTED: "Completed",
    DISPUTED: "Disputed",
    REFUNDED: "Refunded",
    PAYOUT_RELEASED: "Payout Released",
    CANCELED: "Cancelled",
  };
  return labels[status] || status;
}

export function getOrderStatusColor(status: string): string {
  const colors: Record<string, string> = {
    CREATED: "gray",
    AWAITING_PAYMENT: "warning",
    PAID_IN_ESCROW: "warning",
    IN_PROGRESS: "primary",
    DELIVERED: "success",
    ACCEPTED: "success",
    DISPUTED: "danger",
    REFUNDED: "warning",
    PAYOUT_RELEASED: "success",
    CANCELED: "default",
  };
  return colors[status] || "default";
}

export function getIntentStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    DRAFT: "Draft",
    ACTIVE: "Active",
    AWARDED: "Awarded",
    CLOSED: "Closed",
    CANCELED: "Cancelled",
    EXPIRED: "Expired",
  };
  return labels[status] || status;
}

export function getOfferStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    DRAFT: "Draft",
    SUBMITTED: "Submitted",
    VIEWED: "Viewed",
    SHORTLISTED: "Shortlisted",
    AWARDED: "Awarded",
    REJECTED: "Rejected",
    WITHDRAWN: "Withdrawn",
    EXPIRED: "Expired",
  };
  return labels[status] || status;
}

export function truncateText(text: string, maxLen = 80): string {
  if (text.length <= maxLen) return text;
  return text.slice(0, maxLen) + "…";
}
