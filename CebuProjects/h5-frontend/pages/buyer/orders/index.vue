<template>
  <div>
    <div class="bg-white border-b border-slate-100 px-4 h-14 flex items-center sticky top-0 z-40 pt-safe">
      <h1 class="font-bold text-slate-900 text-lg">{{ $t("buyer.my_orders") }}</h1>
    </div>

    <!-- Filter Tabs -->
    <div class="bg-white border-b border-slate-100 px-4 flex gap-1 overflow-x-auto no-scrollbar">
      <button type="button"
        v-for="tab in filterTabs"
        :key="tab.value"
        class="flex-shrink-0 py-3 px-3 text-sm font-medium border-b-2 transition-colors"
        :class="activeFilter === tab.value ? 'border-primary-600 text-primary-700' : 'border-transparent text-slate-500'"
        @click="activeFilter = tab.value"
      >
        {{ tab.label }}
      </button>
    </div>

    <div class="p-4">
      <div v-if="orderStore.loading" class="space-y-3">
        <div v-for="n in 3" :key="n" class="card">
          <div class="shimmer h-5 w-1/2 rounded mb-2"></div>
          <div class="shimmer h-4 w-3/4 rounded mb-2"></div>
          <div class="shimmer h-4 w-1/3 rounded"></div>
        </div>
      </div>

      <div v-else-if="filteredOrders.length === 0" class="empty-state">
        <svg class="w-16 h-16 text-slate-200 mb-3" fill="none" stroke="currentColor" stroke-width="1" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M3 6h18M16 10a4 4 0 01-8 0" />
        </svg>
        <p class="text-slate-500 font-medium">{{ $t("pages.no_orders_yet") }}</p>
      </div>

      <div v-else class="space-y-3">
        <NuxtLink v-for="order in filteredOrders" :key="order.id" :to="`/buyer/orders/${order.id}`">
          <div class="card">
            <div class="flex justify-between items-center mb-2">
              <p class="font-semibold text-slate-800 text-sm">{{ $t("order.id") }} #{{ order.id.slice(0, 8).toUpperCase() }}</p>
              <span class="text-xs px-2 py-0.5 rounded-full font-medium" :class="getOrderBadgeClass(order.status)">
                {{ getOrderStatusLabel(order.status) }}
              </span>
            </div>
            <p class="text-xs text-slate-500 mb-2">{{ $t("order.id") }} #{{ order.id.slice(0, 8).toUpperCase() }}</p>
            <div class="flex justify-between items-center">
              <span class="font-bold text-slate-900">{{ formatPrice(order.total_amount_minor, order.currency) }}</span>
              <span class="text-xs text-slate-400">{{ formatDate(order.created_at) }}</span>
            </div>

            <!-- Escrow status if available -->
            <div v-if="order.escrow" class="mt-2 pt-2 border-t border-slate-100 flex items-center gap-1.5">
              <svg class="w-3.5 h-3.5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd" />
              </svg>
              <span class="text-xs text-green-600 font-medium">{{ $t("pages.escrow") }}: {{ order.escrow.status }}</span>
            </div>
          </div>
        </NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";

definePageMeta({ layout: "buyer", middleware: ["buyer"] });
const { t } = useI18n({ useScope: "global" });
useHead({ title: t("buyer.my_orders") });

const orderStore = useOrderStore();
const { formatPrice, formatDate, getOrderStatusLabel } = useApiUtils();

const activeFilter = ref("ALL");
const filterTabs = computed(() => [
  { label: t("common.all"), value: "ALL" },
  { label: t("intent.active"), value: "ACTIVE" },
  { label: t("order.status_delivered"), value: "DELIVERED" },
  { label: t("order.status_accepted"), value: "ACCEPTED" },
  { label: t("order.status_disputed"), value: "DISPUTED" },
]);

const filteredOrders = computed(() => {
  if (activeFilter.value === "ALL") return orderStore.orders;
  if (activeFilter.value === "ACTIVE") {
    return orderStore.orders.filter((o) =>
      ["AWAITING_PAYMENT", "PAID_IN_ESCROW", "IN_PROGRESS", "DELIVERED"].includes(o.status)
    );
  }
  return orderStore.orders.filter((o) => o.status === activeFilter.value);
});

function getOrderBadgeClass(status: string) {
  const map: Record<string, string> = {
    CREATED: "badge-gray",
    AWAITING_PAYMENT: "badge-warning",
    PAID_IN_ESCROW: "badge-warning",
    IN_PROGRESS: "badge-primary",
    DELIVERED: "badge-success",
    ACCEPTED: "badge-success",
    DISPUTED: "badge-danger",
    REFUNDED: "badge-gray",
    PAYOUT_RELEASED: "badge-success",
    CANCELED: "badge-gray",
  };
  return map[status] || "badge-gray";
}

onMounted(() => orderStore.fetchMyOrders());
</script>
