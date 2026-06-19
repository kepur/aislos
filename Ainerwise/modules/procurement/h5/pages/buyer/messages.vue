<template>
  <div>
    <div class="bg-white border-b border-slate-100 px-4 h-14 flex items-center sticky top-0 z-40 pt-safe">
      <h1 class="font-bold text-slate-900 text-lg">Messages</h1>
    </div>

    <div class="p-4">
      <div v-if="loading" class="space-y-3">
        <div v-for="n in 4" :key="n" class="flex gap-3 items-center">
          <div class="shimmer w-12 h-12 rounded-full flex-shrink-0"></div>
          <div class="flex-1">
            <div class="shimmer h-4 w-1/2 rounded mb-1.5"></div>
            <div class="shimmer h-3 w-3/4 rounded"></div>
          </div>
        </div>
      </div>

      <div v-else-if="orderStore.orders.length === 0" class="empty-state">
        <svg class="w-16 h-16 text-slate-200 mb-3" fill="none" stroke="currentColor" stroke-width="1" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
        </svg>
        <p class="text-slate-500 font-medium">No conversations yet</p>
        <p class="text-slate-400 text-xs mt-1">Messages appear here after you create an order</p>
      </div>

      <div v-else class="space-y-1">
        <NuxtLink
          v-for="order in orderStore.orders"
          :key="order.id"
          :to="`/messages/${order.id}`"
          class="flex items-center gap-3 bg-white rounded-2xl p-3 shadow-card active:bg-slate-50"
        >
          <div class="w-12 h-12 rounded-full bg-amber-100 flex items-center justify-center flex-shrink-0">
            <span class="text-lg font-bold text-amber-700">S</span>
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex justify-between items-center">
              <p class="font-semibold text-slate-800 text-sm truncate">Supplier</p>
              <span class="text-xs text-slate-400 flex-shrink-0 ml-2">{{ formatRelativeTime(order.created_at) }}</span>
            </div>
            <p class="text-xs text-slate-500 truncate">Order #{{ order.id.slice(0, 8).toUpperCase() }}</p>
          </div>
        </NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: "buyer", middleware: ["buyer"] });
useHead({ title: "Messages" });

const orderStore = useOrderStore();
const { formatRelativeTime } = useApiUtils();
const loading = ref(true);

onMounted(async () => {
  await orderStore.fetchMyOrders();
  loading.value = false;
});
</script>
