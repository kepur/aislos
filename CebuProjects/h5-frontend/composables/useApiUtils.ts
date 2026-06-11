export function useApiUtils() {
  return {
    formatPrice,
    formatDate,
    formatRelativeTime,
    getOrderStatusLabel,
    getOrderStatusColor,
    getIntentStatusLabel,
    getOfferStatusLabel,
    truncateText,
  };
}
