<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between gap-3 flex-wrap">
      <h1 class="text-2xl font-bold text-slate-900">{{ appStore.t('buyer.dashboard.title') }}</h1>
      <div class="flex items-center gap-2 flex-wrap">
        <UButton to="/marketplace" color="gray" variant="outline" icon="i-heroicons-shopping-bag" size="md">{{ appStore.t('action.browseMarketplace') }}</UButton>
        <UButton to="/marketplace?sort=trust" color="gray" variant="outline" icon="i-heroicons-magnifying-glass" size="md">{{ appStore.t('action.findSuppliers') }}</UButton>
        <UButton to="/post-request" color="indigo" icon="i-heroicons-plus" size="lg">{{ appStore.t('action.newRequest') }}</UButton>
      </div>
    </div>

    <section class="overflow-hidden rounded-3xl border border-indigo-100 bg-white shadow-sm">
      <div class="grid gap-0 lg:grid-cols-[1.15fr_0.85fr]">
        <div class="p-6 lg:p-8">
          <div class="flex items-center gap-2 text-sm font-semibold text-indigo-600">
            <UIcon name="i-heroicons-shopping-bag" class="h-5 w-5" />
            <span>{{ appStore.t('layout.shoppingFirst') }}</span>
          </div>
          <h2 class="mt-3 text-3xl font-bold tracking-tight text-slate-950">{{ appStore.t('buyer.dashboard.shopTitle') }}</h2>
          <p class="mt-3 max-w-2xl text-sm leading-6 text-slate-600">{{ appStore.t('buyer.dashboard.shopDesc') }}</p>
          <div class="mt-6 flex flex-wrap gap-3">
            <UButton to="/marketplace" color="indigo" icon="i-heroicons-arrow-right" trailing size="lg">
              {{ appStore.t('buyer.dashboard.shopPrimary') }}
            </UButton>
            <UButton to="/marketplace?sort=trust" color="gray" variant="soft" icon="i-heroicons-sparkles" size="lg">
              {{ appStore.t('buyer.dashboard.shopSecondary') }}
            </UButton>
          </div>
        </div>
        <div class="border-t border-indigo-50 bg-gradient-to-br from-indigo-50 via-white to-amber-50 p-6 lg:border-l lg:border-t-0 lg:p-8">
          <div class="grid h-full content-center gap-3">
            <NuxtLink to="/marketplace" class="rounded-2xl border border-white/80 bg-white/80 p-4 shadow-sm transition hover:border-indigo-200 hover:shadow-md">
              <p class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{{ appStore.t('buyer.dashboard.shopStatProducts') }}</p>
              <p class="mt-1 text-2xl font-bold text-slate-950">{{ totalMarketplaceItems }}</p>
            </NuxtLink>
            <div class="grid grid-cols-2 gap-3">
              <NuxtLink to="/marketplace?market_mode=B2B_B2C" class="rounded-2xl border border-white/80 bg-white/80 p-4 shadow-sm transition hover:border-indigo-200 hover:shadow-md">
                <p class="text-xs font-semibold text-slate-500">{{ appStore.t('buyer.dashboard.shopStatModes') }}</p>
                <p class="mt-2 text-sm font-semibold text-indigo-600">Buy / Quote</p>
              </NuxtLink>
              <NuxtLink to="/marketplace?sort=rank" class="rounded-2xl border border-white/80 bg-white/80 p-4 shadow-sm transition hover:border-indigo-200 hover:shadow-md">
                <p class="text-xs font-semibold text-slate-500">{{ appStore.t('buyer.dashboard.shopStatRank') }}</p>
                <p class="mt-2 text-sm font-semibold text-indigo-600">Best match</p>
              </NuxtLink>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- KPI Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <UCard class="bg-white">
        <div class="flex items-center">
          <div class="flex-shrink-0 bg-blue-100 rounded-md p-3">
            <UIcon name="i-heroicons-clipboard-document-list" class="h-6 w-6 text-blue-600" />
          </div>
          <div class="ml-4 w-0 flex-1">
            <dl>
              <dt class="text-sm font-medium text-slate-500 truncate">{{ appStore.t('buyer.dashboard.activeRequests') }}</dt>
              <dd class="flex items-baseline">
                <div class="text-2xl font-semibold text-slate-900">{{ dashboardLoading ? '...' : activeRequestsCount }}</div>
              </dd>
            </dl>
          </div>
        </div>
      </UCard>

      <UCard class="bg-white">
        <div class="flex items-center">
          <div class="flex-shrink-0 bg-indigo-100 rounded-md p-3">
            <UIcon name="i-heroicons-envelope-open" class="h-6 w-6 text-indigo-600" />
          </div>
          <div class="ml-4 w-0 flex-1">
            <dl>
              <dt class="text-sm font-medium text-slate-500 truncate">{{ appStore.t('buyer.dashboard.offersReceived') }}</dt>
              <dd class="flex items-baseline">
                <div class="text-2xl font-semibold text-slate-900">{{ dashboardLoading ? '...' : offersReceivedCount }}</div>
              </dd>
            </dl>
          </div>
        </div>
      </UCard>

      <UCard class="bg-white">
        <div class="flex items-center">
          <div class="flex-shrink-0 bg-green-100 rounded-md p-3">
            <UIcon name="i-heroicons-truck" class="h-6 w-6 text-green-600" />
          </div>
          <div class="ml-4 w-0 flex-1">
            <dl>
              <dt class="text-sm font-medium text-slate-500 truncate">{{ appStore.t('buyer.dashboard.ordersProgress') }}</dt>
              <dd class="flex items-baseline">
                <div class="text-2xl font-semibold text-slate-900">{{ dashboardLoading ? '...' : ordersInProgressCount }}</div>
              </dd>
            </dl>
          </div>
        </div>
      </UCard>

      <UCard class="bg-white">
        <div class="flex items-center">
          <div class="flex-shrink-0 bg-yellow-100 rounded-md p-3">
            <UIcon name="i-heroicons-lock-closed" class="h-6 w-6 text-yellow-600" />
          </div>
          <div class="ml-4 w-0 flex-1">
            <dl>
              <dt class="text-sm font-medium text-slate-500 truncate">{{ appStore.t('buyer.dashboard.escrowHeld') }}</dt>
              <dd class="flex items-baseline">
                <div class="text-2xl font-semibold text-slate-900">{{ dashboardLoading ? '...' : escrowHeldLabel }}</div>
              </dd>
            </dl>
          </div>
        </div>
      </UCard>
    </div>

    <!-- AI Project Forge Entry -->
    <section class="overflow-hidden rounded-3xl border border-purple-100 bg-gradient-to-r from-indigo-50 via-purple-50 to-pink-50 shadow-sm">
      <div class="p-6 lg:p-8 flex items-center justify-between gap-6 flex-wrap">
        <div class="flex-1 min-w-[280px]">
          <div class="flex items-center gap-2 text-sm font-semibold text-purple-600">
            <UIcon name="i-heroicons-cpu-chip" class="h-5 w-5" />
            <span>AI Project Forge</span>
          </div>
          <h2 class="mt-2 text-xl font-bold tracking-tight text-slate-950">
            Describe your project. AI builds your procurement list.
          </h2>
          <p class="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
            Upload blueprints, specs, or just describe what you need. Our AI analyzes everything and generates a structured list of materials — ready to source.
          </p>
          <div class="mt-4 flex flex-wrap gap-3">
            <UButton to="/buyer/projects" color="indigo" icon="i-heroicons-sparkles" trailing size="lg">
              Start AI Project
            </UButton>
          </div>
        </div>
        <div class="text-7xl opacity-40 select-none hidden lg:block">🏗️</div>
      </div>
    </section>

    <UCard v-if="trustProfile" class="bg-white border border-slate-200">
      <div class="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <div class="flex items-center gap-3">
            <h3 class="text-lg font-semibold text-slate-900">{{ appStore.t('buyer.dashboard.trustTitle') }}</h3>
            <UBadge :color="trustTierColor(trustProfile.trust_tier)" variant="subtle">
              {{ trustTierLabel(trustProfile.trust_tier) }}
            </UBadge>
          </div>
          <p class="text-sm text-slate-500 mt-1">{{ appStore.t('buyer.dashboard.trustDesc') }}</p>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-5 gap-4 min-w-0 lg:min-w-[620px]">
          <div>
            <p class="text-xs text-slate-500 font-medium">{{ appStore.t('trust.score') }}</p>
            <p class="text-2xl font-bold text-slate-900">{{ trustProfile.trust_score }}</p>
          </div>
          <div>
            <p class="text-xs text-slate-500 font-medium">{{ appStore.t('trust.dealRate') }}</p>
            <p class="text-2xl font-bold text-slate-900">{{ trustProfile.deal_completion_rate }}%</p>
          </div>
          <div>
            <p class="text-xs text-slate-500 font-medium">{{ appStore.t('trust.profile') }}</p>
            <p class="text-2xl font-bold text-slate-900">{{ trustProfile.profile_completion_rate }}%</p>
          </div>
          <div>
            <p class="text-xs text-slate-500 font-medium">{{ appStore.t('trust.deposit') }}</p>
            <p class="text-2xl font-bold text-slate-900">{{ formatMinor(trustProfile.deposit_amount_minor, trustProfile.deposit_currency) }}</p>
          </div>
          <div>
            <p class="text-xs text-slate-500 font-medium">{{ appStore.t('trust.disputes') }}</p>
            <p class="text-2xl font-bold text-slate-900">{{ trustProfile.dispute_rate }}%</p>
          </div>
        </div>
      </div>
    </UCard>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Active Requests Table -->
      <UCard class="lg:col-span-2 flex flex-col">
        <template #header>
          <div class="flex justify-between items-center">
            <h3 class="text-lg font-medium text-slate-900">{{ appStore.t('buyer.dashboard.activeRequests') }}</h3>
            <UButton variant="ghost" color="indigo" size="sm" to="/buyer/requests">{{ appStore.t('action.viewAll') }}</UButton>
          </div>
        </template>

        <div v-if="dashboardError" class="mb-4 rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700">
          {{ dashboardError }}
        </div>

        <UTable :columns="columns" :rows="requests" :loading="dashboardLoading">
          <template #status-data="{ row }">
            <UBadge :color="intentStatusColor(row.statusKey)" variant="subtle">{{ row.status }}</UBadge>
          </template>
          <template #offers-data="{ row }">
            <span class="font-medium text-indigo-600">{{ row.offers }}</span>
          </template>
          <template #actions-data="{ row }">
            <UButton size="xs" color="indigo" variant="soft" :to="`/buyer/requests/${row.id}/offers`">{{ appStore.t('action.compareOffers') }}</UButton>
          </template>
        </UTable>
      </UCard>

      <div class="space-y-6 lg:col-span-1 flex flex-col">
        <!-- Recent Messages -->
        <UCard>
          <template #header>
            <h3 class="text-lg font-medium text-slate-900">{{ appStore.t('buyer.dashboard.recentMessages') }}</h3>
          </template>
          <div class="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-6 text-center">
            <p class="text-sm font-medium text-slate-600">No recent message threads yet.</p>
            <p class="mt-1 text-xs text-slate-400">Order conversations will appear after a real buyer/supplier thread exists.</p>
          </div>
          <UButton block variant="ghost" color="indigo" class="mt-4" to="/buyer/messages">{{ appStore.t('action.viewAllMessages') }}</UButton>
        </UCard>

        <!-- Recommended Categories -->
        <UCard>
          <template #header>
            <h3 class="text-lg font-medium text-slate-900">{{ appStore.t('buyer.dashboard.recommended') }}</h3>
          </template>
          <div v-if="recommendedTags.length" class="flex flex-wrap gap-2">
            <NuxtLink v-for="tag in recommendedTags" :key="tag" :to="`/marketplace?keyword=${encodeURIComponent(tag)}`">
              <UBadge color="gray" variant="solid" class="cursor-pointer hover:bg-slate-200">{{ tag }}</UBadge>
            </NuxtLink>
          </div>
          <div v-else class="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-5 text-sm text-slate-500">
            Recommendations will appear after marketplace or request activity creates real category signals.
          </div>
        </UCard>
      </div>
    </div>

    <!-- Business Enterprise Links (shown only for BUSINESS account type) -->
    <div v-if="isBusiness" class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <NuxtLink to="/buyer/company-profile" class="flex items-center gap-3 bg-white rounded-2xl border border-blue-100 p-4 hover:border-blue-300 hover:shadow-sm transition-all group">
        <div class="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center text-xl">🏢</div>
        <div>
          <p class="text-sm font-semibold text-slate-900 group-hover:text-blue-700">Company Profile</p>
          <p class="text-xs text-slate-400">Manage business info</p>
        </div>
      </NuxtLink>
      <NuxtLink to="/buyer/team" class="flex items-center gap-3 bg-white rounded-2xl border border-purple-100 p-4 hover:border-purple-300 hover:shadow-sm transition-all group">
        <div class="w-10 h-10 bg-purple-50 rounded-xl flex items-center justify-center text-xl">👥</div>
        <div>
          <p class="text-sm font-semibold text-slate-900 group-hover:text-purple-700">Team Members</p>
          <p class="text-xs text-slate-400">Invite & manage team</p>
        </div>
      </NuxtLink>
      <NuxtLink to="/buyer/company-profile" class="flex items-center gap-3 bg-white rounded-2xl border border-amber-100 p-4 hover:border-amber-300 hover:shadow-sm transition-all group">
        <div class="w-10 h-10 bg-amber-50 rounded-xl flex items-center justify-center text-xl">✅</div>
        <div>
          <p class="text-sm font-semibold text-slate-900 group-hover:text-amber-700">KYB Verification</p>
          <p class="text-xs text-slate-400">Business verification</p>
        </div>
      </NuxtLink>
      <NuxtLink to="/buyer/orders" class="flex items-center gap-3 bg-white rounded-2xl border border-green-100 p-4 hover:border-green-300 hover:shadow-sm transition-all group">
        <div class="w-10 h-10 bg-green-50 rounded-xl flex items-center justify-center text-xl">📄</div>
        <div>
          <p class="text-sm font-semibold text-slate-900 group-hover:text-green-700">Orders & POs</p>
          <p class="text-xs text-slate-400">B2B orders & records</p>
        </div>
      </NuxtLink>
    </div>

    <!-- Today's Recommendations -->
    <UCard v-if="recommendations.length > 0">
      <template #header>
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-lg font-semibold text-slate-900">✨ Today's Recommendations</h3>
            <p class="text-xs text-slate-400 mt-0.5">Top-ranked products for your categories</p>
          </div>
          <UButton to="/marketplace" color="indigo" variant="ghost" size="sm">View all →</UButton>
        </div>
      </template>
      <div class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
        <NuxtLink
          v-for="item in recommendations"
          :key="item.id"
          to="/marketplace"
          class="group border border-slate-100 rounded-xl overflow-hidden hover:border-indigo-200 hover:shadow-sm transition-all"
        >
          <div class="aspect-square bg-slate-50 overflow-hidden">
            <img v-if="item.images && item.images[0]" :src="item.images[0]" :alt="item.title" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200" />
            <div v-else class="w-full h-full flex items-center justify-center text-2xl">📦</div>
          </div>
          <div class="p-2">
            <p class="text-xs font-semibold text-slate-900 leading-tight line-clamp-2">{{ item.title }}</p>
            <p class="text-xs text-indigo-600 font-bold mt-1">{{ formatMinor(item.price_minor, item.currency) }}</p>
            <span :class="['text-[9px] font-semibold px-1.5 py-0.5 rounded-full', item.market_mode === 'B2C' ? 'bg-green-50 text-green-600' : 'bg-blue-50 text-blue-600']">{{ item.market_mode }}</span>
          </div>
        </NuxtLink>
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
import type { TrustMe, TrustProfile, TrustTier } from '~/types'

definePageMeta({
  layout: 'buyer',
  middleware: ['buyer']
})

const authStore = useAuthStore()
const appStore = useAppStore()
const config = useRuntimeConfig()
const trustProfile = ref<TrustProfile | null>(null)
const accountContext = ref<{ account_type: string; features: Record<string, boolean> } | null>(null)
const recommendations = ref<any[]>([])
const marketplaceTotal = ref<number | null>(null)
const buyerIntents = ref<any[]>([])
const buyerOrders = ref<any[]>([])
const dashboardLoading = ref(false)
const dashboardError = ref('')

const isBusiness = computed(() => accountContext.value?.account_type === 'BUSINESS')
const totalMarketplaceItems = computed(() => marketplaceTotal.value ? `${marketplaceTotal.value}+` : `${recommendations.value.length || 0}+`)
const activeRequestsCount = computed(() => buyerIntents.value.filter((row) => isActiveIntent(row.status)).length)
const offersReceivedCount = computed(() => buyerIntents.value.reduce((sum, row) => sum + Number(row.offer_count ?? row.offers ?? 0), 0))
const ordersInProgressCount = computed(() => buyerOrders.value.filter((row) => isInProgressOrder(row.status)).length)
const escrowHeldMinor = computed(() => buyerOrders.value
  .filter((row) => ['PAID_IN_ESCROW', 'IN_PROGRESS', 'DELIVERED', 'ACCEPTED'].includes(String(row.status || '').toUpperCase()))
  .reduce((sum, row) => sum + Number(row.total_amount_minor ?? row.total_minor ?? 0), 0))
const escrowCurrency = computed(() => buyerOrders.value.find((row) => row.currency)?.currency || 'PHP')
const escrowHeldLabel = computed(() => escrowHeldMinor.value ? formatMinor(escrowHeldMinor.value, escrowCurrency.value) : '—')
const recommendedTags = computed(() => {
  const tags = new Set<string>()
  for (const item of recommendations.value) {
    if (item.category_name) tags.add(String(item.category_name))
    if (Array.isArray(item.tags)) item.tags.slice(0, 2).forEach((tag: unknown) => tags.add(String(tag)))
  }
  for (const row of buyerIntents.value) {
    if (row.category_name) tags.add(String(row.category_name))
  }
  return Array.from(tags).filter(Boolean).slice(0, 6)
})

const columns = computed(() => [
  { key: 'title', label: appStore.t('buyer.table.requestTitle') },
  { key: 'budget', label: appStore.t('buyer.table.budget') },
  { key: 'status', label: appStore.t('buyer.table.status') },
  { key: 'offers', label: appStore.t('buyer.table.offers') },
  { key: 'actions', label: appStore.t('buyer.table.actions') }
])

const requests = computed(() => buyerIntents.value.slice(0, 6).map((row) => ({
  id: row.id,
  title: row.title || row.name || 'Untitled request',
  budget: formatIntentBudget(row),
  statusKey: String(row.status || 'DRAFT').toUpperCase(),
  status: formatIntentStatus(row.status),
  offers: Number(row.offer_count ?? row.offers ?? 0),
})))

function trustTierLabel(tier: TrustTier) {
  return appStore.t(`trust.tier.${tier}`) || tier
}

function trustTierColor(tier: TrustTier) {
  return {
    BRONZE: 'orange',
    SILVER: 'gray',
    GOLD: 'yellow',
    PLATINUM: 'blue',
    DIAMOND: 'green',
  }[tier] || 'gray'
}

function formatMinor(minor: number, currency = 'PHP') {
  const amount = (minor || 0) / 100
  if (currency === 'USDT') {
    return `${amount.toLocaleString('en-PH', { maximumFractionDigits: 2 })} USDT`
  }
  try {
    return new Intl.NumberFormat('en-PH', {
      style: 'currency',
      currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  } catch {
    return `${amount.toLocaleString('en-PH', { maximumFractionDigits: 2 })} ${currency}`
  }
}

function normalizeList(data: any, keys: string[]) {
  if (Array.isArray(data)) return data
  for (const key of keys) {
    if (Array.isArray(data?.[key])) return data[key]
  }
  return []
}

function isActiveIntent(status: string) {
  const normalized = String(status || '').toUpperCase()
  return !['AWARDED', 'CLOSED', 'CANCELED', 'CANCELLED', 'EXPIRED'].includes(normalized)
}

function isInProgressOrder(status: string) {
  return ['AWAITING_PAYMENT', 'PAID_IN_ESCROW', 'IN_PROGRESS', 'DELIVERED'].includes(String(status || '').toUpperCase())
}

function formatIntentBudget(row: any) {
  const min = Number(row.budget_min_minor || 0)
  const max = Number(row.budget_max_minor || 0)
  const currency = row.currency || 'PHP'
  if (min && max) return `${formatMinor(min, currency)} - ${formatMinor(max, currency)}`
  if (max) return `Up to ${formatMinor(max, currency)}`
  if (min) return `From ${formatMinor(min, currency)}`
  return 'Open'
}

function formatIntentStatus(status: string) {
  const normalized = String(status || 'DRAFT').toUpperCase()
  const known: Record<string, string> = {
    DRAFT: 'Draft',
    ACTIVE: 'Receiving Offers',
    PUBLISHED: 'Receiving Offers',
    AWARDED: 'Awarded',
    CLOSED: 'Closed',
    CANCELED: 'Canceled',
    CANCELLED: 'Canceled',
    EXPIRED: 'Expired',
  }
  return known[normalized] || normalized.replaceAll('_', ' ')
}

function intentStatusColor(status: string) {
  return {
    DRAFT: 'gray',
    ACTIVE: 'blue',
    PUBLISHED: 'blue',
    AWARDED: 'green',
    CLOSED: 'gray',
    CANCELED: 'red',
    CANCELLED: 'red',
    EXPIRED: 'orange',
  }[String(status || '').toUpperCase()] || 'gray'
}

async function loadBuyerDashboardData() {
  dashboardLoading.value = true
  dashboardError.value = ''
  try {
    const [intentData, orderData] = await Promise.all([
      $fetch<any>(`${config.public.apiBase}/intents/my`, {
        params: { page: 1, page_size: 20 },
        headers: { Authorization: `Bearer ${authStore.accessToken}` },
      }),
      $fetch<any>(`${config.public.apiBase}/orders/my`, {
        params: { page: 1, page_size: 20 },
        headers: { Authorization: `Bearer ${authStore.accessToken}` },
      }),
    ])
    buyerIntents.value = normalizeList(intentData, ['items', 'intents'])
    buyerOrders.value = normalizeList(orderData, ['orders', 'items'])
  } catch (error: any) {
    buyerIntents.value = []
    buyerOrders.value = []
    dashboardError.value = error?.data?.detail || error?.message || 'Unable to load buyer dashboard data.'
  } finally {
    dashboardLoading.value = false
  }
}

onMounted(async () => {
  if (!authStore.accessToken) return
  await loadBuyerDashboardData()
  // Trust profile
  try {
    const trust = await $fetch<TrustMe>(`${config.public.apiBase}/trust/me`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    })
    trustProfile.value = trust?.user || null
  } catch (error) {
    console.error("Dashboard fetch error:", error)
    trustProfile.value = null
  }
  // Account context
  try {
    accountContext.value = await $fetch<any>(`${config.public.apiBase}/auth/me/account-context`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    })
  } catch {}
  // Today's Recommendations
  try {
    const feed = await $fetch<any>(`${config.public.apiBase}/marketplace/feed`, {
      params: { page: 1, page_size: 6, sort: 'rank' },
    })
    recommendations.value = feed.items || []
    marketplaceTotal.value = feed.total ?? null
  } catch {}
})
</script>
