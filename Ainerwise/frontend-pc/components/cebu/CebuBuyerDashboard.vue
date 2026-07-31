<template>
  <section class="space-y-6">
    <!-- Header -->
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-xs font-bold uppercase tracking-[0.2em] text-indigo-300">Buyer workspace</p>
        <h1 class="mt-1 text-2xl font-bold text-white">采购工作台</h1>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <NuxtLink to="/market/marketplace" class="btn-secondary">浏览市场</NuxtLink>
        <NuxtLink to="/market/marketplace?sort=trust" class="btn-secondary">找供应商</NuxtLink>
        <NuxtLink to="/market/post-request" class="btn-primary">+ 发布采购需求</NuxtLink>
      </div>
    </div>

    <!-- Shopping-first hero -->
    <div class="pc-card overflow-hidden !p-0">
      <div class="grid gap-0 lg:grid-cols-[1.15fr_0.85fr]">
        <div class="p-6 lg:p-8">
          <p class="text-sm font-semibold text-indigo-300">🛍 Shopping-first 采购</p>
          <h2 class="mt-3 text-3xl font-bold tracking-tight text-white">先逛市场，再下采购需求</h2>
          <p class="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
            浏览已认证供应商的挂牌，挑中即可一键转成采购需求；需求、挂牌、供应商报价始终关联在同一条商业记录里。
          </p>
          <div class="mt-6 flex flex-wrap gap-3">
            <NuxtLink to="/market/marketplace" class="btn-primary">进入市场 →</NuxtLink>
            <NuxtLink to="/market/marketplace?sort=trust" class="btn-secondary">按信任度排序</NuxtLink>
          </div>
        </div>
        <div class="border-t border-white/10 bg-indigo-500/[0.06] p-6 lg:border-l lg:border-t-0 lg:p-8">
          <div class="grid h-full content-center gap-3">
            <NuxtLink to="/market/marketplace" class="rounded-2xl border border-white/10 bg-white/5 p-4 transition hover:border-indigo-400/40">
              <p class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">在售挂牌</p>
              <p class="mt-1 text-2xl font-bold text-white">{{ totalListings }}</p>
            </NuxtLink>
            <div class="grid grid-cols-2 gap-3">
              <NuxtLink to="/market/marketplace" class="rounded-2xl border border-white/10 bg-white/5 p-4 transition hover:border-indigo-400/40">
                <p class="text-xs font-semibold text-slate-500">交易模式</p>
                <p class="mt-2 text-sm font-semibold text-indigo-300">Buy / Quote</p>
              </NuxtLink>
              <NuxtLink to="/market/buyer/requests" class="rounded-2xl border border-white/10 bg-white/5 p-4 transition hover:border-indigo-400/40">
                <p class="text-xs font-semibold text-slate-500">我的需求</p>
                <p class="mt-2 text-sm font-semibold text-indigo-300">{{ requests.length }} 条</p>
              </NuxtLink>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- KPI cards -->
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div v-for="kpi in kpis" :key="kpi.label" class="pc-card flex items-center gap-4">
        <div :class="['flex h-11 w-11 shrink-0 items-center justify-center rounded-xl text-lg', kpi.tone]">{{ kpi.icon }}</div>
        <div class="min-w-0">
          <p class="truncate text-sm text-slate-400">{{ kpi.label }}</p>
          <p class="text-2xl font-semibold text-white">{{ kpi.value }}</p>
        </div>
      </div>
    </div>

    <!-- AI Project Forge -->
    <NuxtLink to="/market/buyer/projects" class="pc-card flex flex-wrap items-center justify-between gap-6 transition hover:border-indigo-400/40">
      <div class="min-w-[280px] flex-1">
        <p class="text-sm font-semibold text-indigo-300">⚙ AI Project Forge</p>
        <h2 class="mt-2 text-xl font-bold tracking-tight text-white">描述你的项目，AI 自动生成采购清单</h2>
        <p class="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
          上传图纸、规格，或直接描述需求；AI 分析后生成结构化物料清单（BOQ），可直接进入寻源与报价。
        </p>
        <span class="btn-primary mt-4 inline-block">开始 AI 项目 →</span>
      </div>
      <div class="hidden select-none text-7xl opacity-30 lg:block">🏗️</div>
    </NuxtLink>

    <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <!-- Active requests table -->
      <div class="pc-card lg:col-span-2">
        <div class="mb-4 flex items-center justify-between">
          <h3 class="text-lg font-medium text-white">活跃采购需求</h3>
          <NuxtLink to="/market/buyer/requests" class="text-sm text-indigo-300 hover:text-indigo-200">查看全部</NuxtLink>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm">
            <thead class="text-slate-400">
              <tr class="border-b border-white/10">
                <th class="py-2 pr-4 font-medium">需求</th>
                <th class="py-2 pr-4 font-medium">状态</th>
                <th class="py-2 pr-4 font-medium">报价</th>
                <th class="py-2 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in requests.slice(0, 6)" :key="r.id" class="border-b border-white/5">
                <td class="py-3 pr-4 text-white">{{ r.title || '未命名需求' }}</td>
                <td class="py-3 pr-4"><span :class="['rounded-full px-2 py-0.5 text-xs', statusTone(r.status)]">{{ r.status || '—' }}</span></td>
                <td class="py-3 pr-4 font-medium text-indigo-300">{{ r.offer_count ?? r.offers_count ?? 0 }}</td>
                <td class="py-3"><NuxtLink :to="`/market/buyer/requests/${r.id}/offers`" class="text-xs text-indigo-300 hover:text-indigo-200">对比报价</NuxtLink></td>
              </tr>
              <tr v-if="!requests.length">
                <td colspan="4" class="py-6 text-center text-slate-500">还没有采购需求，<NuxtLink to="/market/post-request" class="text-indigo-300">去发布</NuxtLink></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="space-y-6">
        <!-- Recent messages -->
        <div class="pc-card">
          <h3 class="mb-3 text-lg font-medium text-white">最近消息</h3>
          <ul class="divide-y divide-white/5">
            <li v-for="t in threads.slice(0, 4)" :key="t.id" class="flex items-start gap-3 py-3">
              <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-indigo-500/15 text-sm text-indigo-200">{{ (t.subject || 'O').slice(0, 1) }}</div>
              <div class="min-w-0">
                <p class="truncate text-sm font-medium text-white">{{ t.subject || '订单会话' }}</p>
                <p class="truncate text-xs text-slate-500">{{ t.status || t.last_message_preview || '点击查看会话' }}</p>
              </div>
            </li>
            <li v-if="!threads.length" class="py-4 text-sm text-slate-500">暂无会话</li>
          </ul>
          <NuxtLink to="/market/buyer/messages" class="mt-3 block text-center text-sm text-indigo-300 hover:text-indigo-200">查看全部消息</NuxtLink>
        </div>

        <!-- Recommended categories -->
        <div class="pc-card">
          <h3 class="mb-3 text-lg font-medium text-white">推荐类目</h3>
          <div class="flex flex-wrap gap-2">
            <NuxtLink
              v-for="c in categories.slice(0, 8)"
              :key="c.id"
              :to="`/market/marketplace?category_schema_id=${c.id}`"
              class="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-200 transition hover:border-indigo-400/40 hover:text-indigo-200"
            >{{ c.name || c.title }}</NuxtLink>
            <span v-if="!categories.length" class="text-sm text-slate-500">暂无类目</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Today's recommendations -->
    <div v-if="recommendations.length" class="pc-card">
      <div class="mb-4 flex items-center justify-between">
        <div>
          <h3 class="text-lg font-semibold text-white">✨ 今日推荐</h3>
          <p class="mt-0.5 text-xs text-slate-500">为你的类目匹配的优选挂牌</p>
        </div>
        <NuxtLink to="/market/marketplace" class="text-sm text-indigo-300 hover:text-indigo-200">查看全部 →</NuxtLink>
      </div>
      <div class="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
        <NuxtLink
          v-for="item in recommendations"
          :key="item.id"
          :to="`/market/marketplace/${item.id}`"
          class="group overflow-hidden rounded-xl border border-white/10 transition hover:border-indigo-400/40"
        >
          <div class="flex aspect-square items-center justify-center bg-white/5 text-2xl">📦</div>
          <div class="p-2">
            <p class="line-clamp-2 text-xs font-semibold leading-tight text-white">{{ item.title }}</p>
            <p class="mt-1 text-xs font-bold text-indigo-300">{{ formatMinor(item.price_minor, item.currency) }}</p>
          </div>
        </NuxtLink>
      </div>
    </div>

    <p v-if="error" class="pc-card text-sm text-red-300">{{ error }}</p>
  </section>
</template>

<script setup lang="ts">
const api = useCommerce()
const error = ref('')
const requests = ref<any[]>([])
const orders = ref<any[]>([])
const watchlist = ref<any[]>([])
const threads = ref<any[]>([])
const categories = ref<any[]>([])
const recommendations = ref<any[]>([])
const totalListingsRaw = ref<number>(0)

const totalListings = computed(() => (totalListingsRaw.value ? `${totalListingsRaw.value}+` : '—'))
const offersReceived = computed(() =>
  requests.value.reduce((sum, r) => sum + (r.offer_count ?? r.offers_count ?? 0), 0),
)
const activeOrders = computed(() =>
  orders.value.filter(o => !['completed', 'cancelled', 'closed'].includes(String(o.status))).length,
)

const kpis = computed(() => [
  { label: '活跃采购需求', value: requests.value.length, icon: '📋', tone: 'bg-blue-500/15 text-blue-300' },
  { label: '收到报价', value: offersReceived.value, icon: '✉️', tone: 'bg-indigo-500/15 text-indigo-300' },
  { label: '进行中订单', value: activeOrders.value, icon: '🚚', tone: 'bg-emerald-500/15 text-emerald-300' },
  { label: '收藏挂牌', value: watchlist.value.length, icon: '⭐', tone: 'bg-amber-500/15 text-amber-300' },
])

function statusTone(status?: string) {
  const s = String(status || '').toLowerCase()
  if (s.includes('publish') || s.includes('receiv') || s.includes('open')) return 'bg-blue-500/15 text-blue-300'
  if (s.includes('award') || s.includes('complete') || s.includes('accept')) return 'bg-emerald-500/15 text-emerald-300'
  if (s.includes('draft') || s.includes('pending') || s.includes('review')) return 'bg-amber-500/15 text-amber-300'
  return 'bg-white/10 text-slate-300'
}

function formatMinor(minor?: number, currency = 'EUR') {
  if (minor == null) return '—'
  try {
    return new Intl.NumberFormat(undefined, { style: 'currency', currency, maximumFractionDigits: 0 }).format(minor / 100)
  } catch {
    return `${(minor / 100).toLocaleString()} ${currency}`
  }
}

onMounted(async () => {
  const [reqs, ords, watch, thr, cats, listings] = await Promise.allSettled([
    api.listProcurementRequests(),
    api.listOrders(),
    api.listWatchlist(),
    api.listThreads(),
    api.listPublicCategories(),
    api.listPublicListings(),
  ])
  if (reqs.status === 'fulfilled') requests.value = (reqs.value.items || []).filter((item: any) => item.portal_key === 'cebu')
  if (ords.status === 'fulfilled') orders.value = ords.value.items || []
  if (watch.status === 'fulfilled') watchlist.value = watch.value.items || []
  if (thr.status === 'fulfilled') threads.value = thr.value.items || []
  if (cats.status === 'fulfilled') categories.value = cats.value.items || []
  if (listings.status === 'fulfilled') {
    recommendations.value = (listings.value.items || []).slice(0, 6)
    totalListingsRaw.value = listings.value.total || (listings.value.items || []).length
  }
  if (reqs.status === 'rejected') error.value = (reqs.reason as any)?.data?.detail || (reqs.reason as any)?.message || ''
})
</script>
