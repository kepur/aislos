<template>
  <section class="space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-xs font-bold uppercase tracking-[0.2em] text-indigo-300">Supplier workspace</p>
        <h1 class="mt-1 text-2xl font-bold text-white">供应商工作台</h1>
        <p class="mt-1 text-sm text-slate-400">匹配需求、报价、订单、交付与结算，一站管理。</p>
      </div>
      <div class="flex flex-wrap gap-2">
        <NuxtLink to="/market/marketplace" class="btn-secondary">浏览市场</NuxtLink>
        <NuxtLink to="/supplier/pings" class="btn-primary">查看匹配需求</NuxtLink>
      </div>
    </div>

    <p v-if="error" class="pc-card text-sm text-red-300">{{ error }}</p>

    <!-- KPI cards -->
    <div class="grid grid-cols-2 gap-4 md:grid-cols-4">
      <NuxtLink v-for="kpi in kpis" :key="kpi.label" :to="kpi.to" class="pc-card transition hover:border-indigo-400/40">
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
            <h3 class="text-lg font-medium text-white">最近匹配需求</h3>
          </div>
          <NuxtLink to="/supplier/pings" class="text-sm text-indigo-300 hover:text-indigo-200">查看全部</NuxtLink>
        </div>
        <div class="space-y-3">
          <div v-for="p in pings.slice(0, 4)" :key="p.id" class="rounded-xl border border-white/10 p-4 transition hover:border-indigo-400/40">
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <h4 class="truncate font-semibold text-white">{{ p.title || p.request_title || '采购需求' }}</h4>
                <p class="mt-1 text-xs text-slate-500">{{ p.created_at ? timeAgo(p.created_at) : (p.status || '') }}</p>
              </div>
              <span v-if="p.pre_funded || p.is_pre_funded" class="rounded-full bg-emerald-500/15 px-2 py-0.5 text-xs text-emerald-300">已预付</span>
            </div>
            <div class="mt-3 flex items-center justify-between">
              <span class="text-sm text-slate-300">预算：{{ budgetOf(p) }}</span>
              <NuxtLink :to="pingLink(p)" class="text-xs text-indigo-300 hover:text-indigo-200">立即报价</NuxtLink>
            </div>
          </div>
          <p v-if="!pings.length" class="rounded-xl border border-dashed border-white/10 p-6 text-center text-sm text-slate-500">暂无匹配需求</p>
        </div>
      </div>

      <!-- Orders requiring action -->
      <div class="pc-card">
        <div class="mb-4 flex items-center gap-2">
          <span class="h-2 w-2 rounded-full bg-amber-400"></span>
          <h3 class="text-lg font-medium text-white">待办订单</h3>
        </div>
        <div class="space-y-3">
          <NuxtLink v-for="o in actionOrders.slice(0, 5)" :key="o.id" :to="`/supplier/orders/${o.id}`" class="block rounded-xl border border-white/10 p-4 transition hover:border-indigo-400/40">
            <div class="flex items-center justify-between gap-3">
              <div>
                <p class="font-semibold text-white">订单 #{{ o.id.slice(0, 8) }}</p>
                <p class="mt-1 text-xs text-slate-500">{{ statusLabel(o.status) }}</p>
              </div>
              <span :class="['rounded-full px-2 py-0.5 text-xs', statusTone(o.status)]">{{ statusLabel(o.status) }}</span>
            </div>
          </NuxtLink>
          <p v-if="!actionOrders.length" class="rounded-xl border border-dashed border-white/10 p-6 text-center text-sm text-slate-500">暂无需处理的订单</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
const api = useCommerce()
const stats = ref<any>({})
const pings = ref<any[]>([])
const orders = ref<any[]>([])
const error = ref('')

const kpis = computed(() => [
  { label: '匹配需求', value: stats.value.open_pings ?? pings.value.length ?? 0, icon: '📨', tone: 'bg-indigo-500/15 text-indigo-300', to: '/supplier/pings' },
  { label: '已提交报价', value: stats.value.submitted_offers ?? 0, icon: '🏷️', tone: 'bg-blue-500/15 text-blue-300', to: '/supplier/offers' },
  { label: '有效目录', value: stats.value.active_listings ?? 0, icon: '📦', tone: 'bg-emerald-500/15 text-emerald-300', to: '/supplier/catalog' },
  { label: '进行中订单', value: stats.value.active_orders ?? activeCount.value, icon: '🚚', tone: 'bg-amber-500/15 text-amber-300', to: '/supplier/orders' },
])
const activeCount = computed(() => orders.value.filter(o => !['completed', 'cancelled', 'closed'].includes(String(o.status))).length)
const actionOrders = computed(() => orders.value.filter(o => /confirm|in_delivery|delivery|dispute|await/i.test(String(o.status || ''))))

function budgetOf(p: any) {
  const req = p.requirements_json || p.request?.requirements_json || {}
  const min = req.budget_min_minor, max = req.budget_max_minor, cur = req.currency || 'EUR'
  const f = (v: any) => (v == null ? null : new Intl.NumberFormat(undefined, { style: 'currency', currency: cur, maximumFractionDigits: 0 }).format(v / 100))
  if (min != null && max != null) return `${f(min)} - ${f(max)}`
  if (max != null) return `≤ ${f(max)}`
  return '开放'
}
function pingLink(p: any) {
  const rid = p.procurement_request_id || p.request_id || p.id
  return `/supplier/offers/new?request_id=${rid}`
}
function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime()
  const m = Math.floor(diff / 60000)
  if (m < 60) return `${m} 分钟前`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h} 小时前`
  return `${Math.floor(h / 24)} 天前`
}
function statusLabel(s?: string) {
  return { confirmed: '已确认', in_delivery: '配送中', delivered: '已送达', completed: '已完成', disputed: '争议中', cancelled: '已取消' }[String(s || '')] || s || '—'
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
