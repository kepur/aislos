<template>
  <div>
    <div class="bg-white border-b border-slate-100 px-4 h-14 flex items-center sticky top-0 z-40 pt-safe">
      <h1 class="font-bold text-slate-900 text-lg">{{ $t("nav.orders") }}</h1>
    </div>

    <div class="p-4">
      <div v-if="orderStore.loading" class="space-y-3">
        <div v-for="n in 3" :key="n" class="card"><div class="shimmer h-24 rounded"></div></div>
      </div>

      <div v-else-if="orderStore.orders.length === 0" class="empty-state">
        <p class="text-slate-500 font-medium">{{ $t("pages.no_orders_yet") }}</p>
        <p class="text-slate-400 text-xs mt-1">{{ $t("pages.supplier_orders_hint") }}</p>
      </div>

      <div v-else class="space-y-3">
        <NuxtLink v-for="order in orderStore.orders" :key="order.id" :to="`/supplier/orders/${order.id}`">
          <div class="card">
            <div class="flex justify-between items-center mb-2">
              <p class="font-semibold text-slate-800 text-sm">#{{ order.id.slice(0, 8).toUpperCase() }}</p>
              <span class="text-xs px-2 py-0.5 rounded-full font-medium" :class="getOrderBadgeClass(order.status)">
                {{ getOrderStatusLabel(order.status) }}
              </span>
            </div>
            <div class="flex justify-between items-center">
              <span class="font-bold text-slate-900">{{ formatPrice(order.total_amount_minor, order.currency) }}</span>
              <span class="text-xs text-slate-400">{{ formatDate(order.created_at) }}</span>
            </div>
            <!-- Action hint -->
            <div v-if="order.status === 'PAID_IN_ESCROW'" class="mt-2 pt-2 border-t border-amber-100">
              <p class="text-xs text-amber-700 font-medium">{{ $t("pages.action_needed_prepare") }}</p>
            </div>
            <div v-if="order.status === 'IN_PROGRESS'" class="mt-2 pt-2 border-t border-primary-100">
              <p class="text-xs text-primary-700 font-medium">{{ $t("pages.ready_to_ship") }}</p>
            </div>
          </div>
        </NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";

definePageMeta({ layout: "supplier", middleware: ["supplier"] });
const { t } = useI18n({ useScope: "global" });
useHead({ title: t("nav.orders") });

const orderStore = useOrderStore();
const { formatPrice, formatDate, getOrderStatusLabel } = useApiUtils();

function getOrderBadgeClass(status: string) {
  const map: Record<string, string> = {
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
