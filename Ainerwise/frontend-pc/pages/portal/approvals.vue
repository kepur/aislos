<template>
  <div class="space-y-6">
    <div><h1 class="text-xl font-bold ws-title">{{ $t('portal.approvals.title') }}</h1><p class="mt-1 text-sm ws-faint">{{ $t('portal.approvals.subtitle') }}</p></div>
    <p v-if="message" class="rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{{ message }}</p>
    <div class="grid gap-6 xl:grid-cols-2">
      <section class="portal-card">
        <h2 class="text-sm font-bold ws-title">{{ $t('portal.approvals.quotesTitle') }}</h2>
        <div class="mt-4 space-y-3">
          <div v-for="quote in data.quotes || []" :key="quote.id" class="rounded-xl border ws-hairline p-4">
            <div class="flex items-start justify-between gap-3"><div><p class="text-lg font-bold ws-title">{{ quote.currency }} {{ Number(quote.total || 0).toLocaleString() }}</p><p class="text-xs ws-faint">{{ $t('portal.approvals.validUntil', { date: quote.valid_until || '-' }) }}</p></div><StatusBadge :status="quote.status" /></div>
            <div class="mt-4 flex gap-2">
              <button class="rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white" @click="respondQuote(quote.id, 'accepted')">{{ $t('portal.approvals.accept') }}</button>
              <button class="rounded-lg bg-red-50 px-4 py-2 text-xs font-semibold text-red-600" @click="respondQuote(quote.id, 'rejected')">{{ $t('portal.approvals.decline') }}</button>
              <button class="rounded-lg bg-blue-50 px-4 py-2 text-xs font-semibold ws-accent" @click="respondQuote(quote.id, 'client_questions')">{{ $t('portal.approvals.askQuestions') }}</button>
            </div>
          </div>
          <p v-if="!(data.quotes || []).length" class="py-8 text-center text-sm ws-faint">{{ $t('portal.approvals.noQuotes') }}</p>
        </div>
      </section>
      <section class="portal-card">
        <h2 class="text-sm font-bold ws-title">{{ $t('portal.approvals.deliveriesTitle') }}</h2>
        <div class="mt-4 space-y-3">
          <div v-for="delivery in data.deliveries || []" :key="delivery.id" class="rounded-xl border ws-hairline p-4">
            <div class="flex items-start justify-between gap-3"><div><p class="font-semibold ws-title">{{ delivery.request_title }}</p><p class="text-xs ws-faint">{{ delivery.carrier || $t('portal.approvals.carrierPending') }} · {{ delivery.tracking_number || $t('portal.approvals.noTracking') }}</p></div><StatusBadge :status="delivery.status" /></div>
            <button class="mt-4 rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white" @click="acceptDelivery(delivery.id)">{{ $t('portal.approvals.acceptDelivery') }}</button>
          </div>
          <p v-if="!(data.deliveries || []).length" class="py-8 text-center text-sm ws-faint">{{ $t('portal.approvals.noDeliveries') }}</p>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'procurement', middleware: 'auth' })
const { t } = useI18n()
const { apiFetch } = useApi()
const commerce = useCommerce()
const data = ref<any>({ quotes: [], deliveries: [] })
const message = ref('')
async function load() { data.value = await apiFetch('/customer/workspace/approvals') }
async function respondQuote(id: string, status: string) {
 await apiFetch(`/quotes/${id}/status`, { method: 'PATCH', body: { status } })
 const key = status === 'accepted' ? 'quoteAccepted' : status === 'rejected' ? 'quoteDeclined' : 'quoteQuestions'
 message.value = t(`portal.approvals.${key}`)
 await load()
}
async function acceptDelivery(id: string) {
 await commerce.acceptDelivery(id)
 message.value = t('portal.approvals.deliveryAccepted')
 await load()
}
onMounted(load)
</script>
