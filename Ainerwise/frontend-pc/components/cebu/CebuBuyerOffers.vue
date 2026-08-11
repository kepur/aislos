<template>
  <section class="space-y-6">
    <div class="flex flex-wrap items-start justify-between gap-4">
      <div>
        <NuxtLink :to="localized(`/market/buyer/requests/${id}`)" class="text-sm text-indigo-300 hover:text-indigo-200">← {{ $t('offers.back') }}</NuxtLink>
        <p class="mt-4 text-xs font-bold uppercase tracking-[0.2em] text-indigo-300">{{ $t('offers.eyebrow') }}</p>
        <h1 class="mt-2 text-3xl font-bold tracking-tight text-white">{{ request?.title || $t('offers.titleFallback') }}</h1>
        <p class="mt-3 text-sm text-slate-400">
          {{ $t('offers.requestLabel') }} {{ shortId(id) }}
          <span v-if="request?.status"> · {{ request.status }}</span>
          <span v-if="requestBudget"> · {{ requestBudget }}</span>
        </p>
      </div>
      <div class="flex flex-wrap gap-2">
        <NuxtLink :to="localized('/market/marketplace')" class="btn-secondary">{{ $t('offers.continueFind') }}</NuxtLink>
        <NuxtLink :to="localized(`/market/buyer/requests/${id}`)" class="btn-primary">{{ $t('offers.viewCandidates') }}</NuxtLink>
      </div>
    </div>

    <p v-if="message" class="pc-card text-sm text-emerald-300">{{ message }}</p>
    <p v-if="error" class="pc-card text-sm text-red-300">{{ error }}</p>

    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <div v-for="card in summaryCards" :key="card.label" class="pc-card">
        <p class="text-sm text-slate-400">{{ card.label }}</p>
        <p class="mt-2 text-3xl font-bold text-white">{{ card.value }}</p>
        <p class="mt-1 text-xs text-slate-500">{{ card.hint }}</p>
      </div>
    </div>

    <div class="pc-card">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p class="text-xs font-bold uppercase tracking-[0.18em] text-indigo-300">{{ $t('offers.compareEyebrow') }}</p>
          <h2 class="mt-2 text-xl font-semibold text-white">{{ $t('offers.compareTitle') }}</h2>
        </div>
        <div class="flex flex-wrap gap-2">
          <select v-model="filters.sort" class="rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-slate-200 outline-none focus:border-indigo-400/60">
            <option value="landed">{{ $t('offers.sortLanded') }}</option>
            <option value="offer">{{ $t('offers.sortOffer') }}</option>
            <option value="newest">{{ $t('offers.sortNewest') }}</option>
            <option value="stock">{{ $t('offers.sortStock') }}</option>
          </select>
          <select v-model="filters.eta" class="rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-slate-200 outline-none focus:border-indigo-400/60">
            <option value="any">{{ $t('offers.etaAny') }}</option>
            <option value="today">{{ $t('offers.etaToday') }}</option>
            <option value="2d">{{ $t('offers.eta2d') }}</option>
            <option value="week">{{ $t('offers.etaWeek') }}</option>
          </select>
          <label class="flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-slate-300">
            <input v-model="filters.inStock" type="checkbox" class="accent-indigo-400">
            {{ $t('offers.inStockOnly') }}
          </label>
        </div>
      </div>

      <div v-if="loading" class="mt-6 rounded-2xl border border-white/10 bg-white/[0.03] p-6 text-sm text-slate-400">{{ $t('offers.loadingOffers') }}</div>

      <div v-else-if="filteredOffers.length" class="mt-6 overflow-x-auto">
        <table class="w-full min-w-[980px] text-left text-sm">
          <thead class="text-slate-400">
            <tr class="border-b border-white/10">
              <th class="py-3 pr-4 font-medium">{{ $t('offers.colSupplier') }}</th>
              <th class="py-3 pr-4 font-medium">{{ $t('offers.colUnit') }}</th>
              <th class="py-3 pr-4 font-medium">{{ $t('offers.colDelivery') }}</th>
              <th class="py-3 pr-4 font-medium">{{ $t('offers.colOfferTotal') }}</th>
              <th class="py-3 pr-4 font-medium">{{ $t('offers.colLanded') }}</th>
              <th class="py-3 pr-4 font-medium">{{ $t('offers.colEta') }}</th>
              <th class="py-3 pr-4 font-medium">{{ $t('offers.colStock') }}</th>
              <th class="py-3 pr-4 font-medium">{{ $t('offers.colWarranty') }}</th>
              <th class="py-3 pr-4 font-medium">{{ $t('common.status') }}</th>
              <th class="py-3 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="offer in filteredOffers" :key="offer.id" class="border-b border-white/5">
              <td class="py-4 pr-4">
                <p class="font-semibold text-white">{{ supplierLabel(offer) }}</p>
                <p class="mt-1 text-xs text-slate-500">{{ $t('offers.offerLabel') }} {{ shortId(offer.id) }}</p>
              </td>
              <td class="py-4 pr-4 font-semibold text-indigo-200">{{ formatMinor(unitPriceMinor(offer), offer.currency) }}</td>
              <td class="py-4 pr-4 text-slate-300">{{ formatMinor(deliveryFeeMinor(offer), offer.currency, $t('ui.tbd')) }}</td>
              <td class="py-4 pr-4 font-semibold text-white">{{ formatMinor(offerTotalMinor(offer), offer.currency) }}</td>
              <td class="py-4 pr-4 font-semibold text-emerald-300">{{ formatMinor(landedTotalMinor(offer), offer.currency) }}</td>
              <td class="py-4 pr-4 text-slate-300">{{ etaLabel(offer) }}</td>
              <td class="py-4 pr-4 text-slate-300">{{ stockLabel(offer) }}</td>
              <td class="py-4 pr-4 text-slate-300">{{ warrantyLabel(offer) }}</td>
              <td class="py-4 pr-4"><span :class="['rounded-full px-2 py-0.5 text-xs font-semibold', statusTone(offer.status)]">{{ offer.status }}</span></td>
              <td class="py-4">
                <div class="flex justify-end gap-2">
                  <NuxtLink :to="localized(`/market/buyer/offers/${offer.id}`)" class="btn-secondary">{{ $t('offers.details') }}</NuxtLink>
                  <button
                    v-if="canAward(offer)"
                    class="btn-primary"
                    :disabled="awardingId === offer.id"
                    @click="award(offer)"
                  >
                    {{ awardingId === offer.id ? $t('offers.awarding') : $t('offers.award') }}
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-else class="mt-6 rounded-2xl border border-dashed border-white/10 p-6 text-sm text-slate-500">
        {{ $t('offers.emptyOffers') }}
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()
const { t } = useI18n()
const props = defineProps<{ id: string }>()
const api = useCommerce()

const request = ref<any>()
const offers = ref<any[]>([])
const loading = ref(true)
const error = ref('')
const message = ref('')
const awardingId = ref('')
const filters = reactive({
  sort: 'landed',
  eta: 'any',
  inStock: false,
})

const requestBudget = computed(() => {
  const req = request.value?.requirements_json || {}
  const attrs = request.value?.attrs_json || {}
  const max = pickNumber(req.budget_max_minor, req.budget_max, attrs.budget_max_minor)
  const min = pickNumber(req.budget_min_minor, req.budget_min, attrs.budget_min_minor)
  const currency = req.currency || attrs.currency || 'EUR'
  if (min != null && max != null) return `${formatMinor(min, currency)} - ${formatMinor(max, currency)}`
  if (max != null) return t('offers.budgetMax', { v: formatMinor(max, currency) })
  if (min != null) return t('offers.budgetMin', { v: formatMinor(min, currency) })
  return ''
})

const filteredOffers = computed(() => {
  let rows = [...offers.value]
  if (filters.inStock) rows = rows.filter(row => stockCount(row) > 0)
  if (filters.eta !== 'any') rows = rows.filter(row => etaMatches(row, filters.eta))
  if (filters.sort === 'offer') {
    rows.sort((a, b) => offerTotalMinor(a) - offerTotalMinor(b))
  } else if (filters.sort === 'newest') {
    rows.sort((a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime())
  } else if (filters.sort === 'stock') {
    rows.sort((a, b) => stockCount(b) - stockCount(a))
  } else {
    rows.sort((a, b) => landedTotalMinor(a) - landedTotalMinor(b))
  }
  return rows
})

const summaryCards = computed(() => {
  const awardable = offers.value.filter(canAward).length
  const cheapest = offers.value.length ? Math.min(...offers.value.map(landedTotalMinor)) : null
  return [
    { label: t('offers.sumTotal'), value: offers.value.length, hint: t('offers.sumTotalHint') },
    { label: t('offers.sumAwardable'), value: awardable, hint: t('offers.sumAwardableHint') },
    { label: t('offers.sumCheapest'), value: cheapest == null ? '—' : formatMinor(cheapest, offers.value[0]?.currency || 'EUR'), hint: t('offers.sumCheapestHint') },
    { label: t('offers.sumStatus'), value: request.value?.status || '—', hint: t('offers.sumStatusHint') },
  ]
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [r, o] = await Promise.all([
      api.getProcurementRequest(props.id),
      api.listOffers(props.id),
    ])
    request.value = r
    offers.value = o.items || []
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || t('offers.loadFailed')
  } finally {
    loading.value = false
  }
}

async function award(offer: any) {
  if (!canAward(offer)) return
  if (import.meta.client && !window.confirm(t('offers.confirmAward'))) return
  awardingId.value = offer.id
  error.value = ''
  message.value = ''
  try {
    const order = await api.awardOffer(offer.id)
    message.value = t('offers.awardSuccess')
    await navigateTo(`/market/buyer/orders/${order.id}`)
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || t('offers.awardFailed')
  } finally {
    awardingId.value = ''
  }
}

function canAward(offer: any) {
  return String(offer?.status || '').toLowerCase() === 'submitted'
}

function supplierLabel(offer: any) {
  return offer?.supplier_name || offer?.supplier_company_name || `Supplier ${shortId(offer?.supplier_company_id)}`
}

function terms(offer: any) {
  return offer?.terms_json && typeof offer.terms_json === 'object' ? offer.terms_json : {}
}

function unitPriceMinor(offer: any) {
  return pickNumber(offer?.unit_price_minor, terms(offer).unit_price_minor, offer?.price_minor) || 0
}

function deliveryFeeMinor(offer: any) {
  return pickNumber(offer?.delivery_fee_minor, terms(offer).delivery_fee_minor, terms(offer).shipping_fee_minor)
}

function offerTotalMinor(offer: any) {
  return pickNumber(offer?.total_price_minor, offer?.total_minor, terms(offer).total_price_minor, offer?.price_minor) || 0
}

function landedTotalMinor(offer: any) {
  return offerTotalMinor(offer) + (deliveryFeeMinor(offer) || 0)
}

function etaLabel(offer: any) {
  const value = offer?.eta || terms(offer).eta || terms(offer).delivery_eta || terms(offer).delivery_window
  return value || t('ui.tbd')
}

function stockCount(offer: any) {
  return pickNumber(offer?.stock, offer?.stock_qty, terms(offer).stock, terms(offer).stock_qty) || 0
}

function stockLabel(offer: any) {
  const count = stockCount(offer)
  if (count > 0) return t('offers.stockUnit', { n: count })
  const stock = terms(offer).stock_status || offer?.stock_status
  return stock || t('ui.tbd')
}

function warrantyLabel(offer: any) {
  const months = terms(offer).warranty_months
  return offer?.warranty || terms(offer).warranty || (months && t('offers.warrantyMonths', { n: months })) || t('ui.tbd')
}

function etaMatches(offer: any, target: string) {
  const days = pickNumber(offer?.eta_days, terms(offer).eta_days, terms(offer).delivery_days)
  if (days == null) return false
  if (target === 'today') return days <= 0
  if (target === '2d') return days <= 2
  if (target === 'week') return days <= 7
  return true
}

function pickNumber(...values: any[]) {
  for (const value of values) {
    if (value === null || value === undefined || value === '') continue
    const num = Number(value)
    if (Number.isFinite(num)) return num
  }
  return null
}

function statusTone(status?: string) {
  const s = String(status || '').toLowerCase()
  if (s.includes('award')) return 'bg-emerald-500/15 text-emerald-300'
  if (s.includes('submit')) return 'bg-blue-500/15 text-blue-300'
  if (s.includes('withdraw') || s.includes('reject')) return 'bg-red-500/15 text-red-300'
  return 'bg-white/10 text-slate-300'
}

function formatMinor(minor?: number | null, currency = 'EUR', empty = '—') {
  if (minor == null) return empty
  try {
    return new Intl.NumberFormat(undefined, { style: 'currency', currency, maximumFractionDigits: 0 }).format(minor / 100)
  } catch {
    return `${(minor / 100).toLocaleString()} ${currency}`
  }
}

function shortId(value?: string) {
  return value ? String(value).slice(0, 8) : ''
}

onMounted(load)
</script>
