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
                <div class="text-2xl font-semibold text-slate-900">4</div>
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
                <div class="text-2xl font-semibold text-slate-900">12</div>
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
                <div class="text-2xl font-semibold text-slate-900">2</div>
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
                <div class="text-2xl font-semibold text-slate-900">$4,500.00</div>
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
        
        <UTable :columns="columns" :rows="requests">
          <template #status-data="{ row }">
            <UBadge :color="row.statusKey === 'receivingOffers' ? 'blue' : 'yellow'" variant="subtle">{{ row.status }}</UBadge>
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
          <ul class="divide-y divide-slate-200">
            <li v-for="i in 3" :key="i" class="py-3 flex">
              <UAvatar :src="`https://i.pravatar.cc/150?u=sup${i}`" class="mr-3" />
              <div>
                <p class="text-sm font-medium text-slate-900">Global Build Supply Co.</p>
                <p class="text-sm text-slate-500 truncate w-48">{{ appStore.t('buyer.dashboard.messagePreview') }}</p>
              </div>
            </li>
          </ul>
          <UButton block variant="ghost" color="indigo" class="mt-4" to="/buyer/messages">{{ appStore.t('action.viewAllMessages') }}</UButton>
        </UCard>
        
        <!-- Recommended Categories -->
        <UCard>
          <template #header>
            <h3 class="text-lg font-medium text-slate-900">{{ appStore.t('buyer.dashboard.recommended') }}</h3>
          </template>
          <div class="flex flex-wrap gap-2">
            <UBadge color="gray" variant="solid" class="cursor-pointer hover:bg-slate-200">Construction</UBadge>
            <UBadge color="gray" variant="solid" class="cursor-pointer hover:bg-slate-200">Cement</UBadge>
            <UBadge color="gray" variant="solid" class="cursor-pointer hover:bg-slate-200">Lumber</UBadge>
            <UBadge color="gray" variant="solid" class="cursor-pointer hover:bg-slate-200">Steel Rebar</UBadge>
            <UBadge color="gray" variant="solid" class="cursor-pointer hover:bg-slate-200">Heavy Machinery</UBadge>
          </div>
        </UCard>
      </div>
    </div>

    <!-- Business Enterprise Links (shown only for BUSINESS account type) -->
    <div v-if="isBusiness" class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <NuxtLink to="/buyer/company" class="flex items-center gap-3 bg-white rounded-2xl border border-blue-100 p-4 hover:border-blue-300 hover:shadow-sm transition-all group">
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
      <NuxtLink to="/buyer/kyb" class="flex items-center gap-3 bg-white rounded-2xl border border-amber-100 p-4 hover:border-amber-300 hover:shadow-sm transition-all group">
        <div class="w-10 h-10 bg-amber-50 rounded-xl flex items-center justify-center text-xl">✅</div>
        <div>
          <p class="text-sm font-semibold text-slate-900 group-hover:text-amber-700">KYB Verification</p>
          <p class="text-xs text-slate-400">Business verification</p>
        </div>
      </NuxtLink>
      <NuxtLink to="/buyer/contracts" class="flex items-center gap-3 bg-white rounded-2xl border border-green-100 p-4 hover:border-green-300 hover:shadow-sm transition-all group">
        <div class="w-10 h-10 bg-green-50 rounded-xl flex items-center justify-center text-xl">📄</div>
        <div>
          <p class="text-sm font-semibold text-slate-900 group-hover:text-green-700">Contracts</p>
          <p class="text-xs text-slate-400">B2B contracts & POs</p>
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

const isBusiness = computed(() => accountContext.value?.account_type === 'BUSINESS')
const totalMarketplaceItems = computed(() => marketplaceTotal.value ? `${marketplaceTotal.value}+` : `${recommendations.value.length || 0}+`)

const columns = computed(() => [
  { key: 'title', label: appStore.t('buyer.table.requestTitle') },
  { key: 'budget', label: appStore.t('buyer.table.budget') },
  { key: 'status', label: appStore.t('buyer.table.status') },
  { key: 'offers', label: appStore.t('buyer.table.offers') },
  { key: 'actions', label: appStore.t('buyer.table.actions') }
])

const requests = computed(() => [
  { id: 1, title: '500 bags Portland Cement', budget: '$2,000 - $2,500', statusKey: 'receivingOffers', status: appStore.t('buyer.status.receivingOffers'), offers: 5 },
  { id: 2, title: 'Office Laptops (x10)', budget: '$8,000 - $10,000', statusKey: 'reviewing', status: appStore.t('buyer.status.reviewing'), offers: 12 },
  { id: 3, title: 'Marine Engine Parts', budget: '$1,500 Max', statusKey: 'receivingOffers', status: appStore.t('buyer.status.receivingOffers'), offers: 2 },
  { id: 4, title: 'Custom Aluminum Extrusion', budget: 'Open', statusKey: 'reviewing', status: appStore.t('buyer.status.reviewing'), offers: 4 }
])

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

onMounted(async () => {
  if (!authStore.accessToken) return
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
