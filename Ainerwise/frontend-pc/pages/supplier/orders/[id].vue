<template>
  <section class="space-y-6">
    <div class="flex items-center gap-3">
      <NuxtLink :to="localized('/supplier/orders')" class="text-sm text-indigo-300 hover:text-indigo-200">← {{ $t('supOrder.back') }}</NuxtLink>
    </div>

    <div v-if="order">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div class="flex items-center gap-3">
            <h1 class="text-2xl font-bold text-white">{{ $t('supplier.orderNum') }} #{{ order.id.slice(0, 8) }}</h1>
            <span :class="['rounded-full px-2 py-0.5 text-xs', statusTone(order.status)]">{{ statusLabel(order.status) }}</span>
          </div>
          <p class="mt-1 text-sm text-slate-400">{{ order.created_at ? $t('supOrder.awardedOn', { date: formatDay(order.created_at) }) : '' }}</p>
        </div>
        <NuxtLink :to="localized(`/supplier/messages?order_id=${order.id}`)" class="btn-secondary">{{ $t('supOrder.contactBuyer') }}</NuxtLink>
      </div>

      <!-- Settlement (ledger/PSP, not custody) -->
      <div class="pc-card mt-5 flex items-start justify-between gap-4 border-emerald-500/30 bg-emerald-500/[0.06]">
        <div>
          <h4 class="font-semibold text-white">{{ $t('supOrder.settlementAmount') }}</h4>
          <p class="mt-1 text-sm text-slate-400">{{ $t('supOrder.settlementDesc') }}</p>
        </div>
        <div class="text-right">
          <p class="text-xs text-slate-400">{{ $t('supOrder.due') }}</p>
          <p class="text-2xl font-bold text-emerald-300">{{ money(order.total_minor, order.currency) }}</p>
        </div>
      </div>

      <div class="mt-6 grid grid-cols-1 gap-6 md:grid-cols-2">
        <!-- Fulfillment -->
        <div class="pc-card">
          <h3 class="text-lg font-medium text-white">{{ $t('supOrder.fulfillStatus') }}</h3>
          <div class="mt-5 flex items-center justify-between">
            <div v-for="(s, i) in fulfillSteps" :key="s.key" class="flex flex-1 flex-col items-center">
              <div :class="['flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold', i <= currentStep ? 'bg-indigo-500 text-white' : 'bg-white/10 text-slate-500']">{{ i < currentStep ? '✓' : i + 1 }}</div>
              <span :class="['mt-2 text-xs', i <= currentStep ? 'text-indigo-200' : 'text-slate-500']">{{ $t(s.label) }}</span>
            </div>
          </div>

          <form class="mt-6 grid gap-3 border-t border-white/10 pt-5 sm:grid-cols-2" @submit.prevent="schedule">
            <input v-model.trim="delivery.carrier" class="input-field" :placeholder="$t('supOrder.carrierPh')" />
            <input v-model.trim="delivery.tracking_number" class="input-field" :placeholder="$t('supOrder.trackingPh')" />
            <button class="btn-primary sm:col-span-2" :disabled="busy">{{ busy ? $t('supOrder.processing') : $t('supOrder.schedule') }}</button>
          </form>

          <div class="mt-4 space-y-3">
            <div v-for="d in deliveries" :key="d.id" class="rounded-xl border border-white/10 p-3">
              <div class="flex items-center justify-between">
                <span :class="['rounded-full px-2 py-0.5 text-xs', statusTone(d.status)]">{{ deliveryLabel(d.status) }}</span>
                <button v-if="nextStatus[d.status]" class="text-xs text-indigo-300 hover:text-indigo-200" :disabled="busy" @click="advance(d.id, nextStatus[d.status])">{{ $t('supOrder.markAs', { status: deliveryLabel(nextStatus[d.status]) }) }}</button>
              </div>
              <p class="mt-2 text-xs text-slate-500">{{ d.carrier || '—' }} · {{ d.tracking_number || $t('supOrder.noTracking') }}</p>
            </div>
            <p v-if="!deliveries.length" class="rounded-xl border border-dashed border-white/10 p-4 text-center text-sm text-slate-500">{{ $t('supOrder.notScheduled') }}</p>
          </div>
        </div>

        <!-- Logistics / summary -->
        <div class="pc-card">
          <h3 class="text-lg font-medium text-white">{{ $t('supOrder.deliveryDetails') }}</h3>
          <dl class="mt-4 space-y-4 text-sm">
            <div><dt class="text-xs uppercase tracking-wider text-slate-500">{{ $t('sup.colBuyer') }}</dt><dd class="mt-1 font-medium text-white">{{ order.buyer_company_name || order.buyer_name || '—' }}</dd></div>
            <div class="border-t border-white/5 pt-3"><dt class="text-xs uppercase tracking-wider text-slate-500">{{ $t('supOrder.shippingAddress') }}</dt><dd class="mt-1 text-slate-300">{{ order.delivery_address || order.shipping_address || $t('supOrder.noAddress') }}</dd></div>
            <div class="border-t border-white/5 pt-3"><dt class="text-xs uppercase tracking-wider text-slate-500">{{ $t('supOrder.orderSummary') }}</dt>
              <dd class="mt-1 space-y-1">
                <div class="flex justify-between"><span class="text-slate-400">{{ $t('supOrder.items') }}</span><span class="text-white">{{ money(order.subtotal_minor ?? order.items_total_minor, order.currency) }}</span></div>
                <div class="flex justify-between"><span class="text-slate-400">{{ $t('offers.colDelivery') }}</span><span class="text-white">{{ money(order.delivery_fee_minor, order.currency) }}</span></div>
                <div class="flex justify-between border-t border-white/5 pt-1 font-semibold"><span class="text-slate-300">{{ $t('supOrder.total') }}</span><span class="text-white">{{ money(order.total_minor, order.currency) }}</span></div>
              </dd>
            </div>
          </dl>
        </div>
      </div>
    </div>

    <p v-else-if="error" class="pc-card text-sm text-red-300">{{ error }}</p>
    <p v-else class="pc-card text-sm text-slate-400">{{ $t('supOrder.loadingOrder') }}</p>
  </section>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()
const { t } = useI18n()
const { formatDay } = useLocaleFormat()
definePageMeta({ layout: 'procurement', middleware: ['auth'] })

const route = useRoute()
const { apiFetch } = useApi()
const api = useCommerce()
const order = ref<any>()
const deliveries = ref<any[]>([])
const error = ref('')
const busy = ref(false)
const delivery = reactive({ carrier: '', tracking_number: '' })
const nextStatus: Record<string, string> = { scheduled: 'shipped', shipped: 'in_transit', in_transit: 'delivered' }

const fulfillSteps = [
  { key: 'awarded', label: 'supOrder.stAwarded' },
  { key: 'shipped', label: 'supOrder.stShipped' },
  { key: 'in_transit', label: 'supOrder.stInTransit' },
  { key: 'delivered', label: 'supOrder.stDelivered' },
]
const currentStep = computed(() => {
  const latest = deliveries.value[deliveries.value.length - 1]?.status || order.value?.status || 'awarded'
  const map: Record<string, number> = { scheduled: 0, awarded: 0, confirmed: 0, shipped: 1, in_transit: 2, in_delivery: 2, delivered: 3, completed: 3 }
  return map[String(latest)] ?? 0
})

function statusLabel(s?: string) {
  const key = String(s || '')
  if (key === 'awarded') return t('supOrder.stAwarded')
  const known = ['confirmed', 'in_delivery', 'delivered', 'completed', 'disputed', 'cancelled']
  return known.includes(key) ? t(`orderStatus.${key}`) : (s || '—')
}
function deliveryLabel(s?: string) {
  const map: Record<string, string> = { scheduled: 'dScheduled', shipped: 'dShipped', in_transit: 'dInTransit', delivered: 'dDelivered', accepted: 'dAccepted' }
  const key = map[String(s || '')]
  return key ? t(`supOrder.${key}`) : (s || '—')
}
function statusTone(s?: string) {
  const v = String(s || '').toLowerCase()
  if (/complete|deliver|accept/.test(v)) return 'bg-emerald-500/15 text-emerald-300'
  if (/dispute|cancel/.test(v)) return 'bg-red-500/15 text-red-300'
  return 'bg-blue-500/15 text-blue-300'
}
function money(v?: number, c = 'EUR') {
  if (v == null) return '—'
  try { return new Intl.NumberFormat(undefined, { style: 'currency', currency: c, maximumFractionDigits: 2 }).format(v / 100) } catch { return `${(v / 100).toLocaleString()} ${c}` }
}

async function load() {
  order.value = await api.getOrder(String(route.params.id))
  deliveries.value = (await api.listDeliveries(String(route.params.id))).items || []
}
async function schedule() {
  if (!delivery.carrier && !delivery.tracking_number) return
  busy.value = true
  try { await apiFetch(`/commerce/orders/${route.params.id}/deliveries`, { method: 'POST', body: { ...delivery } }); delivery.carrier = ''; delivery.tracking_number = ''; await load() }
  catch (e: any) { error.value = e?.data?.detail || e?.message || t('supOrder.scheduleFailed') }
  finally { busy.value = false }
}
async function advance(id: string, status: string) {
  busy.value = true
  try { await apiFetch(`/commerce/deliveries/${id}/status`, { method: 'PATCH', body: { status } }); await load() }
  catch (e: any) { error.value = e?.data?.detail || e?.message || t('supOrder.updateFailed') }
  finally { busy.value = false }
}

onMounted(() => load().catch((e: any) => { error.value = e?.data?.detail || e?.message || t('orders.loadFailed') }))
</script>
