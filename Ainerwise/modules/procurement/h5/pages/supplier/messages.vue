<template>
  <div>
    <div class="bg-white border-b border-slate-100 px-4 h-14 flex items-center sticky top-0 z-40 pt-safe">
      <h1 class="font-bold text-slate-900 text-lg">Messages</h1>
    </div>

    <div class="p-4">
      <div v-if="loading" class="space-y-3">
        <div v-for="n in 3" :key="n" class="flex gap-3 items-center">
          <div class="shimmer w-12 h-12 rounded-full flex-shrink-0"></div>
          <div class="flex-1">
            <div class="shimmer h-4 w-1/2 rounded mb-1.5"></div>
            <div class="shimmer h-3 w-3/4 rounded"></div>
          </div>
        </div>
      </div>

      <div v-else-if="orderStore.orders.length === 0" class="empty-state">
        <p class="text-slate-500 font-medium">No conversations yet</p>
        <p class="text-slate-400 text-xs mt-1">Messages will appear here when you have active orders</p>
      </div>

      <div v-else class="space-y-1">
        <NuxtLink
          v-for="order in orderStore.orders"
          :key="order.id"
          :to="`/messages/${order.id}`"
          class="flex items-center gap-3 bg-white rounded-2xl p-3 shadow-card"
        >
          <div class="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
            <svg class="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex justify-between items-center">
              <p class="font-semibold text-slate-800 text-sm">Buyer</p>
              <span class="text-xs text-slate-400">{{ formatRelativeTime(order.created_at) }}</span>
            </div>
            <p class="text-xs text-slate-500 truncate">Order #{{ order.id.slice(0, 8).toUpperCase() }}</p>
          </div>
        </NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: "supplier", middleware: ["supplier"] });
useHead({ title: "Messages" });

const orderStore = useOrderStore();
const { formatRelativeTime } = useApiUtils();
const loading = ref(true);

onMounted(async () => {
  await orderStore.fetchMyOrders();
  loading.value = false;
});
</script>
