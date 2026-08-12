<template>
  <div class="section-padding">
    <div class="container-main max-w-5xl">
      <div class="flex items-end justify-between gap-4 mb-8">
        <div>
          <p class="text-xs font-bold tracking-[0.25em] text-primary-400 uppercase">{{ $t('store.eyebrow') }}</p>
          <h1 class="mt-2 text-3xl font-bold text-white">{{ $t('store.ordersTitle') }}</h1>
          <p class="mt-2 text-slate-400">{{ $t('store.ordersSubtitle') }}</p>
        </div>
        <NuxtLink :to="localized('/store')" class="btn-secondary">{{ $t('store.backCatalog') }}</NuxtLink>
      </div>
      <div class="space-y-5">
        <article v-for="order in orders" :key="order.id" class="glass-panel p-5">
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 class="font-semibold text-white">{{ $t('store.request') }} {{ order.id.slice(0, 8) }}</h2>
              <p class="mt-1 text-xs text-slate-500">{{ formatDate(order.created_at) }}</p>
            </div>
            <span class="rounded-full border border-primary-400/30 px-3 py-1 text-xs text-primary-300">{{ order.status }}</span>
          </div>
          <div class="mt-4 space-y-2 text-sm">
            <div v-for="item in order.items" :key="item.id" class="flex justify-between gap-4 text-slate-300">
              <span>{{ item.product_name }} × {{ item.quantity }}</span>
              <span>{{ money(item.line_total, order.currency) }}</span>
            </div>
          </div>
          <div class="mt-4 flex justify-between border-t border-white/10 pt-4">
            <span class="text-xs text-amber-200">{{ $t('store.noPayment') }}</span>
            <b class="text-white">{{ money(order.subtotal, order.currency) }}</b>
          </div>
        </article>
        <p v-if="!orders.length" class="glass-panel p-8 text-center text-slate-400">{{ $t('store.noOrders') }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()
const { formatDate } = useLocaleFormat()
definePageMeta({ middleware: 'auth' })
const { apiFetch } = useApi()
const orders = ref<any[]>([])
function money(value: number, currency: string) {
  return new Intl.NumberFormat('en', { style: 'currency', currency }).format(Number(value || 0))
}
onMounted(async () => {
  const res = await apiFetch<any>('/store/orders/my')
  orders.value = res.items || []
})
</script>
