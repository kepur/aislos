<template>
  <section class="space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-xs font-bold uppercase tracking-[0.2em] text-indigo-300">{{ $t('supplier.workspace') }}</p>
        <h1 class="mt-1 text-2xl font-bold text-white">{{ $t('supplier.dashTitle') }}</h1>
        <p class="mt-1 text-sm text-slate-400">{{ $t('supplier.dashSubtitle') }}</p>
      </div>
      <div class="flex flex-wrap gap-2">
        <NuxtLink :to="localized('/market/marketplace')" class="btn-secondary">{{ $t('supplier.browseMarket') }}</NuxtLink>
        <NuxtLink :to="localized('/supplier/pings')" class="btn-primary">{{ $t('supplier.viewMatches') }}</NuxtLink>
      </div>
    </div>

    <p v-if="error" class="pc-card text-sm text-red-300">{{ error }}</p>

    <!-- KPI cards -->
    <div class="grid grid-cols-2 gap-4 md:grid-cols-4">
      <NuxtLink v-for="kpi in kpis" :key="kpi.label" :to="localized(kpi.to)" class="pc-card transition hover:border-indigo-400/40">
        <div class="flex items-center gap-3">
          <div :class="['flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-lg', kpi.tone]">{{ kpi.icon }}</div>
          <div>
            <p class="text-2xl font-bold text-white">{{ kpi.value }}</p>
            <p class="text-xs text-slate-400">{{ kpi.label }}</p>
          </div>
        </div>
      </NuxtLink>
    </div>

    <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <!-- Recent matched requests -->
      <div class="pc-card">
        <div class="mb-4 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="h-2 w-2 rounded-full bg-indigo-400"></span>
            <h3 class="text-lg font-medium text-white">{{ $t('supplier.recentMatches') }}</h3>
          </div>
          <NuxtLink :to="localized('/supplier/pings')" class="text-sm text-indigo-300 hover:text-indigo-200">{{ $t('supplier.viewAll') }}</NuxtLink>
        </div>
        <div class="space-y-3">
          <div v-for="p in pings.slice(0, 4)" :key="p.id" class="rounded-xl border border-white/10 p-4 transition hover:border-indigo-400/40">
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <h4 class="truncate font-semibold text-white">{{ p.title || p.request_title || $t('supplier.reqFallback') }}</h4>
                <p class="mt-1 text-xs text-slate-500">{{ p.created_at ? timeAgo(p.created_at) : (p.status || '') }}</p>
              </div>
              <span v-if="p.pre_funded || p.is_pre_funded" class="rounded-full bg-emerald-500/15 px-2 py-0.5 text-xs text-emerald-300">{{ $t('supplier.prefunded') }}</span>
            </div>
            <div class="mt-3 flex items-center justify-between">
              <span class="text-sm text-slate-300">{{ $t('supplier.budgetLabel', { v: budgetOf(p) }) }}</span>
              <NuxtLink :to="pingLink(p)" class="text-xs text-indigo-300 hover:text-indigo-200">{{ $t('supplier.quoteNow') }}</NuxtLink>
            </div>
          </div>
          <p v-if="!pings.length" class="rounded-xl border border-dashed border-white/10 p-6 text-center text-sm text-slate-500">{{ $t('supplier.noMatches') }}</p>
        </div>
      </div>

      <!-- Orders requiring action -->
      <div class="pc-card">
        <div class="mb-4 flex items-center gap-2">
          <span class="h-2 w-2 rounded-full bg-amber-400"></span>
          <h3 class="text-lg font-medium text-white">{{ $t('supplier.todoOrders') }}</h3>
        </div>
        <div class="space-y-3">
          <NuxtLink v-for="o in actionOrders.slice(0, 5)" :key="o.id" :to="localized(`/supplier/orders/${o.id}`)" class="block rounded-xl border border-white/10 p-4 transition hover:border-indigo-400/40">
            <div class="flex items-center justify-between gap-3">
              <div>
                <p class="font-semibold text-white">{{ $t('supplier.orderNum') }} #{{ o.id.slice(0, 8) }}</p>
                <p class="mt-1 text-xs text-slate-500">{{ statusLabel(o.status) }}</p>
              </div>
              <span :class="['rounded-full px-2 py-0.5 text-xs', statusTone(o.status)]">{{ statusLabel(o.status) }}</span>
            </div>
          </NuxtLink>
          <p v-if="!actionOrders.length" class="rounded-xl border border-dashed border-white/10 p-6 text-center text-sm text-slate-500">{{ $t('supplier.noTodoOrders') }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()
const { t } = useI18n()
const api = useCommerce()
const stats = ref<any>({})
const pings = ref<any[]>([])
const orders = ref<any[]>([])
const error = ref('')

const kpis = computed(() => [
  { label: t('supplier.kpiPings'), value: stats.value.open_pings ?? pings.value.length ?? 0, icon: '📨', tone: 'bg-indigo-500/15 text-indigo-300', to: '/supplier/pings' },
  { label: t('supplier.kpiOffers'), value: stats.value.submitted_offers ?? 0, icon: '🏷️', tone: 'bg-blue-500/15 text-blue-300', to: '/supplier/offers' },
  { label: t('supplier.kpiListings'), value: stats.value.active_listings ?? 0, icon: '📦', tone: 'bg-emerald-500/15 text-emerald-300', to: '/supplier/catalog' },
  { label: t('supplier.kpiOrders'), value: stats.value.active_orders ?? activeCount.value, icon: '🚚', tone: 'bg-amber-500/15 text-amber-300', to: '/supplier/orders' },
])
const activeCount = computed(() => orders.value.filter(o => !['completed', 'cancelled', 'closed'].includes(String(o.status))).length)
const actionOrders = computed(() => orders.value.filter(o => /confirm|in_delivery|delivery|dispute|await/i.test(String(o.status || ''))))

function budgetOf(p: any) {
  const req = p.requirements_json || p.request?.requirements_json || {}
  const min = req.budget_min_minor, max = req.budget_max_minor, cur = req.currency || 'EUR'
  const f = (v: any) => (v == null ? null : new Intl.NumberFormat(undefined, { style: 'currency', currency: cur, maximumFractionDigits: 0 }).format(v / 100))
  if (min != null && max != null) return `${f(min)} - ${f(max)}`
  if (max != null) return `≤ ${f(max)}`
  return t('supplier.budgetOpen')
}
function pingLink(p: any) {
  const rid = p.procurement_request_id || p.request_id || p.id
  return `/supplier/offers/new?request_id=${rid}`
}
function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime()
  const m = Math.floor(diff / 60000)
  if (m < 60) return t('supplier.minAgo', { n: m })
  const h = Math.floor(m / 60)
  if (h < 24) return t('supplier.hourAgo', { n: h })
  return t('supplier.dayAgo', { n: Math.floor(h / 24) })
}
function statusLabel(s?: string) {
  const known = ['confirmed', 'in_delivery', 'delivered', 'completed', 'disputed', 'cancelled']
  const key = String(s || '')
  return known.includes(key) ? t(`orderStatus.${key}`) : (s || '—')
}
function statusTone(s?: string) {
  const v = String(s || '').toLowerCase()
  if (/complete|deliver/.test(v)) return 'bg-emerald-500/15 text-emerald-300'
  if (/dispute|cancel/.test(v)) return 'bg-red-500/15 text-red-300'
  return 'bg-blue-500/15 text-blue-300'
}

onMounted(async () => {
  const [s, p, o] = await Promise.allSettled([
    api.getSupplierDashboard(),
    api.listSupplierPings(),
    api.listOrders(),
  ])
  if (s.status === 'fulfilled') stats.value = s.value || {}
  if (p.status === 'fulfilled') pings.value = p.value.items || []
  if (o.status === 'fulfilled') orders.value = o.value.items || []
  if (s.status === 'rejected') error.value = (s.reason as any)?.data?.detail || (s.reason as any)?.message || ''
})
</script>
