<template>
  <section class="space-y-6">
    <div class="flex flex-wrap items-start justify-between gap-4">
      <div>
        <NuxtLink :to="localized(`/market/buyer/requests/${id}`)" class="text-sm text-indigo-300 hover:text-indigo-200">← 返回需求详情</NuxtLink>
        <p class="mt-4 text-xs font-bold uppercase tracking-[0.2em] text-indigo-300">Live offers</p>
        <h1 class="mt-2 text-3xl font-bold tracking-tight text-white">{{ request?.title || 'Compare supplier offers' }}</h1>
        <p class="mt-3 text-sm text-slate-400">
          Request {{ shortId(id) }}
          <span v-if="request?.status"> · {{ request.status }}</span>
          <span v-if="requestBudget"> · {{ requestBudget }}</span>
        </p>
      </div>
      <div class="flex flex-wrap gap-2">
        <NuxtLink :to="localized('/market/marketplace')" class="btn-secondary">继续找供应商</NuxtLink>
        <NuxtLink :to="localized(`/market/buyer/requests/${id}`)" class="btn-primary">查看候选</NuxtLink>
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
          <p class="text-xs font-bold uppercase tracking-[0.18em] text-indigo-300">Compare table</p>
          <h2 class="mt-2 text-xl font-semibold text-white">报价对比</h2>
        </div>
        <div class="flex flex-wrap gap-2">
          <select v-model="filters.sort" class="rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-slate-200 outline-none focus:border-indigo-400/60">
            <option value="landed">到岸总价最低</option>
            <option value="offer">报价最低</option>
            <option value="newest">最新报价</option>
            <option value="stock">有库存优先</option>
          </select>
          <select v-model="filters.eta" class="rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-slate-200 outline-none focus:border-indigo-400/60">
            <option value="any">任意 ETA</option>
            <option value="today">今天</option>
            <option value="2d">1-2 天</option>
            <option value="week">一周内</option>
          </select>
          <label class="flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-slate-300">
            <input v-model="filters.inStock" type="checkbox" class="accent-indigo-400">
            只看有库存
          </label>
        </div>
      </div>

      <div v-if="loading" class="mt-6 rounded-2xl border border-white/10 bg-white/[0.03] p-6 text-sm text-slate-400">正在加载报价...</div>

      <div v-else-if="filteredOffers.length" class="mt-6 overflow-x-auto">
        <table class="w-full min-w-[980px] text-left text-sm">
          <thead class="text-slate-400">
            <tr class="border-b border-white/10">
              <th class="py-3 pr-4 font-medium">Supplier</th>
              <th class="py-3 pr-4 font-medium">Unit price</th>
              <th class="py-3 pr-4 font-medium">Delivery fee</th>
              <th class="py-3 pr-4 font-medium">Offer total</th>
              <th class="py-3 pr-4 font-medium">Landed total</th>
              <th class="py-3 pr-4 font-medium">ETA</th>
              <th class="py-3 pr-4 font-medium">Stock</th>
              <th class="py-3 pr-4 font-medium">Warranty</th>
              <th class="py-3 pr-4 font-medium">Status</th>
              <th class="py-3 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="offer in filteredOffers" :key="offer.id" class="border-b border-white/5">
              <td class="py-4 pr-4">
                <p class="font-semibold text-white">{{ supplierLabel(offer) }}</p>
                <p class="mt-1 text-xs text-slate-500">Offer {{ shortId(offer.id) }}</p>
              </td>
              <td class="py-4 pr-4 font-semibold text-indigo-200">{{ formatMinor(unitPriceMinor(offer), offer.currency) }}</td>
              <td class="py-4 pr-4 text-slate-300">{{ formatMinor(deliveryFeeMinor(offer), offer.currency, '待确认') }}</td>
              <td class="py-4 pr-4 font-semibold text-white">{{ formatMinor(offerTotalMinor(offer), offer.currency) }}</td>
              <td class="py-4 pr-4 font-semibold text-emerald-300">{{ formatMinor(landedTotalMinor(offer), offer.currency) }}</td>
              <td class="py-4 pr-4 text-slate-300">{{ etaLabel(offer) }}</td>
              <td class="py-4 pr-4 text-slate-300">{{ stockLabel(offer) }}</td>
              <td class="py-4 pr-4 text-slate-300">{{ warrantyLabel(offer) }}</td>
              <td class="py-4 pr-4"><span :class="['rounded-full px-2 py-0.5 text-xs font-semibold', statusTone(offer.status)]">{{ offer.status }}</span></td>
              <td class="py-4">
                <div class="flex justify-end gap-2">
                  <NuxtLink :to="localized(`/market/buyer/offers/${offer.id}`)" class="btn-secondary">详情</NuxtLink>
                  <button
                    v-if="canAward(offer)"
                    class="btn-primary"
                    :disabled="awardingId === offer.id"
                    @click="award(offer)"
                  >
                    {{ awardingId === offer.id ? '授标中...' : '授标' }}
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-else class="mt-6 rounded-2xl border border-dashed border-white/10 p-6 text-sm text-slate-500">
        当前还没有可对比的供应商报价。可以返回需求详情刷新候选并绑定挂牌，或让供应商从 Partner 端提交报价。
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()
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
  if (max != null) return `预算 ≤ ${formatMinor(max, currency)}`
  if (min != null) return `预算 ≥ ${formatMinor(min, currency)}`
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
    { label: '总报价数', value: offers.value.length, hint: '当前需求收到的报价' },
    { label: '可授标', value: awardable, hint: '状态为 submitted' },
    { label: '最低到岸价', value: cheapest == null ? '—' : formatMinor(cheapest, offers.value[0]?.currency || 'EUR'), hint: '报价 + 已知运费' },
    { label: '需求状态', value: request.value?.status || '—', hint: '授标后进入订单交付' },
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
    error.value = e?.data?.detail || e?.message || '加载报价失败'
  } finally {
    loading.value = false
  }
}

async function award(offer: any) {
  if (!canAward(offer)) return
  if (import.meta.client && !window.confirm('确认把这个报价授标给供应商，并创建订单？')) return
  awardingId.value = offer.id
  error.value = ''
  message.value = ''
  try {
    const order = await api.awardOffer(offer.id)
    message.value = '授标成功，正在进入订单交付页...'
    await navigateTo(`/market/buyer/orders/${order.id}`)
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || '授标失败'
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
  return value || '待确认'
}

function stockCount(offer: any) {
  return pickNumber(offer?.stock, offer?.stock_qty, terms(offer).stock, terms(offer).stock_qty) || 0
}

function stockLabel(offer: any) {
  const count = stockCount(offer)
  if (count > 0) return `${count} 件`
  const stock = terms(offer).stock_status || offer?.stock_status
  return stock || '待确认'
}

function warrantyLabel(offer: any) {
  return offer?.warranty || terms(offer).warranty || terms(offer).warranty_months && `${terms(offer).warranty_months} 个月` || '待确认'
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
