<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div><h1 class="text-xl font-bold ws-title">{{ $t('portal.procure.title') }}</h1><p class="mt-1 text-sm ws-faint">{{ $t('portal.procure.subtitle') }}</p></div>
      <NuxtLink :to="localized('/procurement')" class="rounded-xl bg-gradient-to-r from-blue-500 to-indigo-500 px-5 py-2.5 text-sm font-semibold text-white">{{ $t('portal.procure.openWorkspace') }}</NuxtLink>
    </div>
    <div class="grid gap-6 xl:grid-cols-2">
      <section class="portal-card">
        <h2 class="text-sm font-bold ws-title">{{ $t('portal.procure.requests') }}</h2>
        <div class="mt-4 space-y-3">
          <div v-for="item in requests" :key="item.id" class="rounded-xl border ws-hairline p-4">
            <div class="flex justify-between gap-3"><p class="font-semibold ws-title">{{ item.title }}</p><StatusBadge :status="item.status" /></div>
            <p class="mt-1 text-xs ws-faint">{{ item.description || $t('portal.procure.noDescription') }}</p>
          </div>
          <p v-if="!requests.length" class="py-8 text-center text-sm ws-faint">{{ $t('portal.procure.noRequests') }}</p>
        </div>
      </section>
      <section class="portal-card">
        <h2 class="text-sm font-bold ws-title">{{ $t('portal.procure.orders') }}</h2>
        <div class="mt-4 space-y-3">
          <div v-for="item in orders" :key="item.id" class="rounded-xl border ws-hairline p-4">
            <div class="flex justify-between gap-3"><p class="font-semibold ws-title">{{ money(item.total_minor, item.currency) }}</p><StatusBadge :status="item.status" /></div>
            <p class="mt-1 font-mono text-xs ws-faint">{{ item.id }}</p>
          </div>
          <p v-if="!orders.length" class="py-8 text-center text-sm ws-faint">{{ $t('portal.procure.noOrders') }}</p>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()
definePageMeta({ layout: 'procurement', middleware: 'auth' })
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
