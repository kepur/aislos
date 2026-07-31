<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div><h1 class="text-xl font-bold text-slate-800">Procurement</h1><p class="mt-1 text-sm text-slate-400">Your sourcing requests and awarded orders.</p></div>
      <NuxtLink to="/procurement" class="rounded-xl bg-gradient-to-r from-blue-500 to-indigo-500 px-5 py-2.5 text-sm font-semibold text-white">Open AI Procurement Workspace</NuxtLink>
    </div>
    <div class="grid gap-6 xl:grid-cols-2">
      <section class="portal-card">
        <h2 class="text-sm font-bold text-slate-800">Requests</h2>
        <div class="mt-4 space-y-3">
          <div v-for="item in requests" :key="item.id" class="rounded-xl border border-slate-100 p-4">
            <div class="flex justify-between gap-3"><p class="font-semibold text-slate-700">{{ item.title }}</p><StatusBadge :status="item.status" /></div>
            <p class="mt-1 text-xs text-slate-400">{{ item.description || 'No description' }}</p>
          </div>
          <p v-if="!requests.length" class="py-8 text-center text-sm text-slate-400">No procurement requests yet.</p>
        </div>
      </section>
      <section class="portal-card">
        <h2 class="text-sm font-bold text-slate-800">Orders</h2>
        <div class="mt-4 space-y-3">
          <div v-for="item in orders" :key="item.id" class="rounded-xl border border-slate-100 p-4">
            <div class="flex justify-between gap-3"><p class="font-semibold text-slate-700">{{ money(item.total_minor, item.currency) }}</p><StatusBadge :status="item.status" /></div>
            <p class="mt-1 font-mono text-xs text-slate-400">{{ item.id }}</p>
          </div>
          <p v-if="!orders.length" class="py-8 text-center text-sm text-slate-400">No awarded orders yet.</p>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'customer-workspace', middleware: 'auth' })
const commerce = useCommerce()
const requests = ref<any[]>([])
const orders = ref<any[]>([])
const money = (minor: number, currency = 'EUR') => `${currency} ${(Number(minor || 0) / 100).toLocaleString(undefined, { minimumFractionDigits: 2 })}`
onMounted(async () => {
  const [requestResult, orderResult] = await Promise.allSettled([commerce.listProcurementRequests(), commerce.listOrders()])
  requests.value = requestResult.status === 'fulfilled' ? requestResult.value.items || [] : []
  orders.value = orderResult.status === 'fulfilled' ? orderResult.value.items || [] : []
})
</script>
