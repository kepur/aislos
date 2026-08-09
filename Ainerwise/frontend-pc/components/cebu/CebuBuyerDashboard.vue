<template>
  <section class="space-y-6">
    <!-- Header -->
    <div class="flex flex-wrap items-start justify-between gap-4">
      <div class="min-w-0">
        <div class="flex flex-wrap items-center gap-2">
          <p class="text-xs font-bold uppercase tracking-[0.2em] ws-accent">
            {{ $t('procurement.buyerHome.eyebrow') }}
          </p>
          <span
            v-if="trust?.trust_tier"
            :class="['rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider', tierTone]"
          >{{ trust.trust_tier }}</span>
          <span
            v-if="isBusiness"
            class="rounded-full border border-sky-400/30 bg-sky-500/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-sky-300"
          >{{ $t('procurement.buyerHome.business') }}</span>
        </div>
        <h1 class="mt-1 text-2xl font-bold ws-title">{{ $t('procurement.buyerHome.title') }}</h1>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <NuxtLink to="/market/marketplace" class="btn-secondary !py-2 !px-4 text-sm">
          {{ $t('procurement.buyerHome.browse') }}
        </NuxtLink>
        <NuxtLink to="/market/marketplace?sort=trust" class="btn-secondary !py-2 !px-4 text-sm">
          {{ $t('procurement.buyerHome.findSuppliers') }}
        </NuxtLink>
        <NuxtLink to="/market/post-request" class="btn-primary !py-2 !px-4 text-sm">
          + {{ $t('procurement.buyerHome.newRequest') }}
        </NuxtLink>
      </div>
    </div>

    <!-- Trust strip -->
    <div class="relative overflow-hidden rounded-2xl border ws-hairline backdrop-blur-md ws-trust">
      <div class="pointer-events-none absolute inset-0 opacity-60 ws-glow">
        <div class="absolute -left-24 -top-24 h-64 w-64 rounded-full bg-indigo-500/20 blur-3xl"></div>
        <div class="absolute -bottom-28 right-10 h-64 w-64 rounded-full bg-emerald-400/10 blur-3xl"></div>
      </div>
      <div class="relative grid gap-6 p-6 lg:grid-cols-[minmax(0,300px)_1fr] lg:items-center">
        <div>
          <div class="flex items-center gap-2">
            <span class="text-lg">🛡</span>
            <h2 class="text-lg font-semibold ws-title">{{ $t('procurement.buyerHome.trustTitle') }}</h2>
          </div>
          <p class="mt-1 text-sm leading-6 ws-muted">{{ $t('procurement.buyerHome.trustDesc') }}</p>
          <NuxtLink to="/market/buyer/company-profile" class="mt-3 inline-block text-sm ws-accent hover:opacity-80">
            {{ $t('procurement.buyerHome.improveTrust') }} →
          </NuxtLink>
        </div>
        <div class="grid grid-cols-2 gap-4 sm:grid-cols-3 xl:grid-cols-5">
          <div v-for="metric in trustMetrics" :key="metric.label" class="min-w-0">
            <p class="truncate text-xs font-medium ws-faint">{{ metric.label }}</p>
            <p class="mt-1 text-2xl font-bold ws-title">{{ metric.value }}</p>
            <div v-if="metric.percent !== null" class="mt-2 h-1 overflow-hidden rounded-full ws-soft">
              <div :class="['h-full rounded-full', metric.bar]" :style="{ width: `${metric.percent}%` }"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- KPI cards -->
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-5">
      <NuxtLink
        v-for="kpi in kpis"
        :key="kpi.label"
        :to="kpi.to"
        class="pc-card group flex items-center gap-4 !p-5 transition hover:border-[color:var(--accent)]"
      >
        <div :class="['flex h-11 w-11 shrink-0 items-center justify-center rounded-xl text-lg', kpi.tone]">
          {{ kpi.icon }}
        </div>
        <div class="min-w-0">
          <p class="truncate text-sm ws-muted">{{ kpi.label }}</p>
          <p class="truncate text-2xl font-semibold ws-title">{{ loading ? '…' : kpi.value }}</p>
        </div>
      </NuxtLink>
    </div>

    <!-- Shopping-first hero -->
    <div class="pc-card overflow-hidden !p-0">
      <div class="grid gap-0 lg:grid-cols-[1.15fr_0.85fr]">
        <div class="p-6 lg:p-8">
          <p class="text-sm font-semibold ws-accent">🛍 {{ $t('procurement.buyerHome.shopEyebrow') }}</p>
          <h2 class="mt-3 text-3xl font-bold tracking-tight ws-title">{{ $t('procurement.buyerHome.shopTitle') }}</h2>
          <p class="mt-3 max-w-2xl text-sm leading-6 ws-muted">{{ $t('procurement.buyerHome.shopDesc') }}</p>
          <div class="mt-6 flex flex-wrap gap-3">
            <NuxtLink to="/market/marketplace" class="btn-primary">{{ $t('procurement.buyerHome.enterMarket') }} →</NuxtLink>
            <NuxtLink to="/market/marketplace?sort=trust" class="btn-secondary">{{ $t('procurement.buyerHome.sortByTrust') }}</NuxtLink>
          </div>
        </div>
        <div class="border-t ws-hairline ws-sunken p-6 lg:border-l lg:border-t-0 lg:p-8">
          <div class="grid h-full content-center gap-3">
            <NuxtLink to="/market/marketplace" class="ws-tile">
              <p class="text-xs font-semibold uppercase tracking-[0.16em] ws-faint">{{ $t('procurement.buyerHome.statListings') }}</p>
              <p class="mt-1 text-2xl font-bold ws-title">{{ totalListings }}</p>
            </NuxtLink>
            <div class="grid grid-cols-2 gap-3">
              <NuxtLink to="/market/marketplace" class="ws-tile">
                <p class="text-xs font-semibold ws-faint">{{ $t('procurement.buyerHome.statModes') }}</p>
                <p class="mt-2 text-sm font-semibold ws-accent">Buy / Quote</p>
              </NuxtLink>
              <NuxtLink to="/market/buyer/requests" class="ws-tile">
                <p class="text-xs font-semibold ws-faint">{{ $t('procurement.buyerHome.statMyRequests') }}</p>
                <p class="mt-2 text-sm font-semibold ws-accent">{{ requests.length }}</p>
              </NuxtLink>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- AI Project Forge -->
    <NuxtLink
      to="/market/buyer/projects"
      class="pc-card relative flex flex-wrap items-center justify-between gap-6 overflow-hidden transition hover:border-[color:var(--accent)]"
    >
      <div class="pointer-events-none absolute -right-16 -top-24 h-64 w-64 rounded-full bg-purple-500/15 blur-3xl ws-glow"></div>
      <div class="relative min-w-[280px] flex-1">
        <p class="text-sm font-semibold ws-accent">⚙ AI Project Forge</p>
        <h2 class="mt-2 text-xl font-bold tracking-tight ws-title">{{ $t('procurement.buyerHome.forgeTitle') }}</h2>
        <p class="mt-2 max-w-2xl text-sm leading-6 ws-muted">{{ $t('procurement.buyerHome.forgeDesc') }}</p>
        <span class="btn-primary mt-4 inline-block">{{ $t('procurement.buyerHome.forgeCta') }} →</span>
      </div>
      <div class="relative hidden select-none text-7xl opacity-30 lg:block">🏗️</div>
    </NuxtLink>

    <!-- items-start keeps the table card at its natural height instead of being
         stretched to match the taller sidebar column. -->
    <div class="grid grid-cols-1 gap-6 lg:grid-cols-3 lg:items-start">
      <!-- Active requests table -->
      <div class="pc-card lg:col-span-2">
        <div class="mb-4 flex items-center justify-between">
          <h3 class="text-lg font-medium ws-title">{{ $t('procurement.buyerHome.activeRequests') }}</h3>
          <NuxtLink to="/market/buyer/requests" class="text-sm ws-accent hover:opacity-80">
            {{ $t('procurement.buyerHome.viewAll') }}
          </NuxtLink>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm">
            <thead class="ws-muted">
              <tr class="border-b ws-hairline">
                <th class="py-2 pr-4 font-medium">{{ $t('procurement.buyerHome.colRequest') }}</th>
                <th class="py-2 pr-4 font-medium">{{ $t('procurement.buyerHome.colBudget') }}</th>
                <th class="py-2 pr-4 font-medium">{{ $t('procurement.buyerHome.colStatus') }}</th>
                <th class="py-2 pr-4 font-medium">{{ $t('procurement.buyerHome.colOffers') }}</th>
                <th class="py-2 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in requests.slice(0, 6)" :key="r.id" class="border-b ws-hairline">
                <td class="py-3 pr-4 ws-title">{{ r.title || $t('procurement.buyerHome.untitled') }}</td>
                <td class="py-3 pr-4 ws-muted">{{ formatBudget(r) }}</td>
                <td class="py-3 pr-4">
                  <span :class="['rounded-full px-2 py-0.5 text-xs', statusTone(r.status)]">{{ r.status || '—' }}</span>
                </td>
                <td class="py-3 pr-4 font-medium ws-accent">{{ r.offer_count ?? r.offers_count ?? 0 }}</td>
                <td class="py-3">
                  <NuxtLink :to="`/market/buyer/requests/${r.id}/offers`" class="text-xs ws-accent hover:opacity-80">
                    {{ $t('procurement.buyerHome.compareOffers') }}
                  </NuxtLink>
                </td>
              </tr>
              <tr v-if="!requests.length">
                <td colspan="5" class="py-6 text-center ws-faint">
                  {{ $t('procurement.buyerHome.noRequests') }}
                  <NuxtLink to="/market/post-request" class="text-indigo-300">{{ $t('procurement.buyerHome.goPost') }}</NuxtLink>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="space-y-6">
        <!-- Recent messages -->
        <div class="pc-card">
          <h3 class="mb-3 text-lg font-medium ws-title">{{ $t('procurement.buyerHome.recentMessages') }}</h3>
          <ul class="divide-y ws-divide">
            <li v-for="t in threads.slice(0, 4)" :key="t.id" class="flex items-start gap-3 py-3">
              <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-indigo-500/15 text-sm text-indigo-200">
                {{ (t.subject || 'O').slice(0, 1) }}
              </div>
              <div class="min-w-0">
                <p class="truncate text-sm font-medium ws-title">{{ t.subject || $t('procurement.buyerHome.orderThread') }}</p>
                <p class="truncate text-xs ws-faint">{{ t.status || t.last_message_preview || $t('procurement.buyerHome.openThread') }}</p>
              </div>
            </li>
            <li v-if="!threads.length" class="py-4 text-sm ws-faint">{{ $t('procurement.buyerHome.noThreads') }}</li>
          </ul>
          <NuxtLink to="/market/buyer/messages" class="mt-3 block text-center text-sm ws-accent hover:opacity-80">
            {{ $t('procurement.buyerHome.viewAllMessages') }}
          </NuxtLink>
        </div>

        <!-- Recommended categories -->
        <div class="pc-card">
          <h3 class="mb-3 text-lg font-medium ws-title">{{ $t('procurement.buyerHome.recommendedCats') }}</h3>
          <div class="flex flex-wrap gap-2">
            <NuxtLink
              v-for="c in categories.slice(0, 8)"
              :key="c.id"
              :to="`/market/marketplace?category_schema_id=${c.id}`"
              class="ws-chip"
            >{{ c.name || c.title }}</NuxtLink>
            <span v-if="!categories.length" class="text-sm ws-faint">{{ $t('procurement.buyerHome.noCats') }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Enterprise shortcuts -->
    <div v-if="isBusiness" class="grid grid-cols-2 gap-4 lg:grid-cols-4">
      <NuxtLink
        v-for="link in enterpriseLinks"
        :key="link.to"
        :to="link.to"
        class="pc-card group flex items-center gap-3 !p-4 transition hover:border-[color:var(--accent)]"
      >
        <div :class="['flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-xl', link.tone]">{{ link.icon }}</div>
        <div class="min-w-0">
          <p class="truncate text-sm font-semibold ws-title">{{ link.title }}</p>
          <p class="truncate text-xs ws-faint">{{ link.desc }}</p>
        </div>
      </NuxtLink>
    </div>

    <!-- Today's recommendations -->
    <div v-if="recommendations.length" class="pc-card">
      <div class="mb-4 flex items-center justify-between">
        <div>
          <h3 class="text-lg font-semibold ws-title">✨ {{ $t('procurement.buyerHome.todayPicks') }}</h3>
          <p class="mt-0.5 text-xs ws-faint">{{ $t('procurement.buyerHome.todayPicksDesc') }}</p>
        </div>
        <NuxtLink to="/market/marketplace" class="text-sm ws-accent hover:opacity-80">
          {{ $t('procurement.buyerHome.viewAll') }} →
        </NuxtLink>
      </div>
      <div class="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
        <NuxtLink
          v-for="item in recommendations"
          :key="item.id"
          :to="`/market/marketplace/${item.id}`"
          class="group overflow-hidden rounded-xl border ws-hairline transition hover:border-[color:var(--accent)]"
        >
          <div class="flex aspect-square items-center justify-center overflow-hidden ws-soft text-2xl">
            <img
              v-if="item.images && item.images[0]"
              :src="item.images[0]"
              :alt="item.title"
              class="h-full w-full object-cover transition-transform duration-200 group-hover:scale-105"
            />
            <span v-else>📦</span>
          </div>
          <div class="p-2">
            <p class="line-clamp-2 text-xs font-semibold leading-tight ws-title">{{ item.title }}</p>
            <div class="mt-1 flex items-center justify-between gap-1">
              <p class="text-xs font-bold ws-accent">{{ formatMinor(item.price_minor, item.currency) }}</p>
              <span
                v-if="item.market_mode"
                :class="[
                  'rounded-full px-1.5 py-0.5 text-[9px] font-semibold',
                  item.market_mode === 'B2C' ? 'bg-emerald-500/15 text-emerald-300' : 'bg-sky-500/15 text-sky-300',
                ]"
              >{{ item.market_mode }}</span>
            </div>
          </div>
        </NuxtLink>
      </div>
    </div>

    <p v-if="error" class="pc-card text-sm text-red-300">{{ error }}</p>
  </section>
</template>

<script setup lang="ts">
import type { AccountContext, TrustProfile } from '~/composables/useCommerce'

const { t } = useI18n()
const api = useCommerce()
const error = ref('')
const loading = ref(true)
const requests = ref<any[]>([])
const orders = ref<any[]>([])
const watchlist = ref<any[]>([])
const threads = ref<any[]>([])
const categories = ref<any[]>([])
const recommendations = ref<any[]>([])
const totalListingsRaw = ref<number>(0)
const trust = ref<TrustProfile | null>(null)
const accountContext = ref<AccountContext | null>(null)

const isBusiness = computed(() => String(accountContext.value?.account_type || '').toUpperCase() === 'BUSINESS')
const totalListings = computed(() => (totalListingsRaw.value ? `${totalListingsRaw.value}+` : '—'))
const offersReceived = computed(() =>
  requests.value.reduce((sum, r) => sum + (r.offer_count ?? r.offers_count ?? 0), 0),
)
const activeOrders = computed(() =>
  orders.value.filter(o => !['completed', 'cancelled', 'closed'].includes(String(o.status).toLowerCase())).length,
)

// Escrow is the sum of orders whose funds are already held by the platform but
// not yet released — the same status set the 4106 workspace uses.
const ESCROW_STATUSES = ['PAID_IN_ESCROW', 'IN_PROGRESS', 'DELIVERED', 'ACCEPTED']
const escrowHeldMinor = computed(() =>
  orders.value
    .filter(o => ESCROW_STATUSES.includes(String(o.status || '').toUpperCase()))
    .reduce((sum, o) => sum + Number(o.total_amount_minor ?? o.total_minor ?? 0), 0),
)
const escrowCurrency = computed(() => orders.value.find(o => o.currency)?.currency || 'EUR')
const escrowLabel = computed(() =>
  escrowHeldMinor.value ? formatMinor(escrowHeldMinor.value, escrowCurrency.value) : '—',
)

const tierTone = computed(() => {
  const tier = String(trust.value?.trust_tier || '').toUpperCase()
  return {
    BRONZE: 'border-orange-400/30 bg-orange-500/10 text-orange-300',
    SILVER: 'border-slate-300/30 bg-slate-400/10 text-slate-300',
    GOLD: 'border-amber-400/30 bg-amber-500/10 text-amber-300',
    PLATINUM: 'border-sky-400/30 bg-sky-500/10 text-sky-300',
    DIAMOND: 'border-emerald-400/30 bg-emerald-500/10 text-emerald-300',
  }[tier] || 'ws-hairline ws-soft ws-muted'
})

const trustMetrics = computed(() => {
  const p = trust.value
  const pct = (value: unknown) => (p && value != null ? Math.max(0, Math.min(100, Number(value))) : null)
  return [
    {
      label: t('procurement.buyerHome.trustScore'),
      value: p?.trust_score ?? '—',
      percent: pct(p?.trust_score),
      bar: 'bg-indigo-400',
    },
    {
      label: t('procurement.buyerHome.dealRate'),
      value: p?.deal_completion_rate != null ? `${p.deal_completion_rate}%` : '—',
      percent: pct(p?.deal_completion_rate),
      bar: 'bg-emerald-400',
    },
    {
      label: t('procurement.buyerHome.profileRate'),
      value: p?.profile_completion_rate != null ? `${p.profile_completion_rate}%` : '—',
      percent: pct(p?.profile_completion_rate),
      bar: 'bg-sky-400',
    },
    {
      label: t('procurement.buyerHome.deposit'),
      value: p?.deposit_amount_minor != null ? formatMinor(p.deposit_amount_minor, p.deposit_currency) : '—',
      percent: null,
      bar: '',
    },
    {
      label: t('procurement.buyerHome.disputeRate'),
      value: p?.dispute_rate != null ? `${p.dispute_rate}%` : '—',
      percent: pct(p?.dispute_rate),
      bar: 'bg-rose-400',
    },
  ]
})

const kpis = computed(() => [
  {
    label: t('procurement.buyerHome.kpiRequests'),
    value: requests.value.length,
    icon: '📋',
    tone: 'bg-blue-500/15 text-blue-300',
    to: '/market/buyer/requests',
  },
  {
    label: t('procurement.buyerHome.kpiOffers'),
    value: offersReceived.value,
    icon: '✉️',
    tone: 'bg-indigo-500/15 text-indigo-300',
    to: '/market/buyer/requests',
  },
  {
    label: t('procurement.buyerHome.kpiOrders'),
    value: activeOrders.value,
    icon: '🚚',
    tone: 'bg-emerald-500/15 text-emerald-300',
    to: '/market/buyer/orders',
  },
  {
    label: t('procurement.buyerHome.kpiEscrow'),
    value: escrowLabel.value,
    icon: '🔒',
    tone: 'bg-amber-500/15 text-amber-300',
    to: '/market/buyer/wallet',
  },
  {
    label: t('procurement.buyerHome.kpiWatchlist'),
    value: watchlist.value.length,
    icon: '⭐',
    tone: 'bg-fuchsia-500/15 text-fuchsia-300',
    to: '/market/buyer/ideal-list',
  },
])

const enterpriseLinks = computed(() => [
  {
    to: '/market/buyer/company-profile',
    icon: '🏢',
    tone: 'bg-blue-500/15',
    title: t('procurement.buyerHome.companyProfile'),
    desc: t('procurement.buyerHome.companyProfileDesc'),
  },
  {
    to: '/market/buyer/team',
    icon: '👥',
    tone: 'bg-purple-500/15',
    title: t('procurement.buyerHome.team'),
    desc: t('procurement.buyerHome.teamDesc'),
  },
  {
    to: '/market/buyer/company-profile',
    icon: '✅',
    tone: 'bg-amber-500/15',
    title: t('procurement.buyerHome.kyb'),
    desc: t('procurement.buyerHome.kybDesc'),
  },
  {
    to: '/market/buyer/orders',
    icon: '📄',
    tone: 'bg-emerald-500/15',
    title: t('procurement.buyerHome.ordersPo'),
    desc: t('procurement.buyerHome.ordersPoDesc'),
  },
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

function formatBudget(row: any) {
  const currency = row.currency || 'EUR'
  const min = Number(row.budget_min_minor || 0)
  const max = Number(row.budget_max_minor || 0)
  if (min && max) return `${formatMinor(min, currency)} – ${formatMinor(max, currency)}`
  if (max) return formatMinor(max, currency)
  if (min) return formatMinor(min, currency)
  return t('procurement.buyerHome.budgetOpen')
}

onMounted(async () => {
  const [reqs, ords, watch, thr, cats, listings, trustRes, ctx] = await Promise.allSettled([
    api.listProcurementRequests(),
    api.listOrders(),
    api.listWatchlist(),
    api.listThreads(),
    api.listPublicCategories(),
    api.listPublicListings(),
    api.getTrustProfile(),
    api.getAccountContext(),
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
  // /trust/me returns the profile at the top level; older callers assumed a
  // { user } wrapper, so accept either shape.
  if (trustRes.status === 'fulfilled') trust.value = trustRes.value?.user ?? trustRes.value ?? null
  if (ctx.status === 'fulfilled') accountContext.value = ctx.value || null
  if (reqs.status === 'rejected') error.value = (reqs.reason as any)?.data?.detail || (reqs.reason as any)?.message || ''
  loading.value = false
})
</script>
