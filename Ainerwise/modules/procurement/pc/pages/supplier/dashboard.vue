<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">{{ appStore.t('supplier.dashboard.title') }}</h1>
        <p class="mt-1 text-sm text-slate-500">{{ appStore.t('supplier.dashboard.subtitle') }}</p>
      </div>
      <div class="flex flex-wrap gap-2">
        <UButton to="/marketplace" color="gray" variant="outline" icon="i-heroicons-globe-alt">Browse Market</UButton>
        <UButton to="/supplier/settings" color="white" variant="solid" class="shadow-sm">{{ appStore.t('action.viewPublicProfile') }}</UButton>
        <UButton to="/supplier/inbox" color="indigo" icon="i-heroicons-inbox-arrow-down" class="shadow-md">{{ appStore.t('action.viewPings') }}</UButton>
        <UButton color="gray" variant="ghost" icon="i-heroicons-arrow-path" :loading="loading" @click="loadDashboard">Refresh</UButton>
      </div>
    </div>

    <UAlert
      v-if="error"
      color="red"
      variant="soft"
      icon="i-heroicons-exclamation-triangle"
      :title="error"
    />

    <div class="grid grid-cols-2 gap-4 md:grid-cols-4">
      <UCard v-for="metric in metrics" :key="metric.label" class="bg-white" :ui="{ body: { padding: 'p-4 sm:p-5' } }">
        <div class="flex flex-col">
          <dt class="mb-1 text-sm font-medium text-slate-500">{{ metric.label }}</dt>
          <dd :class="['text-2xl font-bold', metric.color]">{{ metric.value }}</dd>
          <p class="mt-1 text-xs text-slate-400">{{ metric.note }}</p>
        </div>
      </UCard>
    </div>

    <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <UCard class="flex flex-col">
        <template #header>
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <div class="h-2 w-2 rounded-full bg-indigo-500"></div>
              <h3 class="text-lg font-medium text-slate-900">{{ appStore.t('supplier.dashboard.recentPings') }}</h3>
            </div>
            <UButton variant="ghost" color="indigo" size="sm" to="/supplier/inbox">{{ appStore.t('action.viewAll') }}</UButton>
          </div>
        </template>

        <div v-if="loading" class="space-y-4">
          <USkeleton v-for="n in 3" :key="n" class="h-24 w-full" />
        </div>
        <div v-else-if="recentPings.length === 0" class="rounded-xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-500">
          No matching buyer requests yet. Add catalog items to improve matching.
        </div>
        <div v-else class="space-y-4">
          <div v-for="ping in recentPings" :key="ping.id" class="rounded-lg border border-slate-200 p-4 transition-colors hover:border-indigo-300">
            <div class="mb-2 flex items-start justify-between gap-4">
              <div>
                <h4 class="font-bold text-slate-900">{{ ping.title }}</h4>
                <div class="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500">
                  <span><UIcon name="i-heroicons-map-pin" class="mr-1 inline h-3 w-3" />{{ locationLabel(ping) }}</span>
                  <span><UIcon name="i-heroicons-clock" class="mr-1 inline h-3 w-3" />{{ formatDate(ping.created_at) }}</span>
                  <span>{{ ping.qty }} {{ ping.unit }}</span>
                </div>
              </div>
              <UBadge color="indigo" size="xs" variant="subtle">ACTIVE</UBadge>
            </div>
            <div class="mt-4 flex items-center justify-between gap-4">
              <div class="text-sm font-medium text-slate-700">
                {{ appStore.t('supplier.dashboard.budget') }}: {{ budgetLabel(ping) }}
              </div>
              <UButton size="sm" color="indigo" variant="soft" :to="`/supplier/offers/new?intent_id=${ping.id}`">
                {{ appStore.t('action.quoteNow') }}
              </UButton>
            </div>
          </div>
        </div>
      </UCard>

      <UCard class="flex flex-col">
        <template #header>
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <div class="h-2 w-2 rounded-full bg-yellow-500"></div>
              <h3 class="text-lg font-medium text-slate-900">{{ appStore.t('supplier.dashboard.actionRequired') }}</h3>
            </div>
            <UButton variant="ghost" color="indigo" size="sm" to="/supplier/orders">Orders</UButton>
          </div>
        </template>

        <div v-if="loading" class="space-y-4">
          <USkeleton v-for="n in 2" :key="n" class="h-24 w-full" />
        </div>
        <div v-else-if="actionOrders.length === 0" class="rounded-xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-500">
          No delivery action is required right now.
        </div>
        <div v-else class="space-y-4">
          <div v-for="order in actionOrders" :key="order.id" class="flex items-start rounded-lg border border-yellow-200 bg-yellow-50 p-4">
            <UIcon name="i-heroicons-truck" class="mr-3 mt-0.5 h-6 w-6 text-yellow-600" />
            <div class="flex-1">
              <div class="flex flex-wrap items-center justify-between gap-3">
                <h4 class="font-bold text-yellow-950">Order #{{ shortId(order.id).toUpperCase() }}</h4>
                <UBadge :color="statusColor(order.status)" variant="subtle">{{ orderStatusLabel(order.status) }}</UBadge>
              </div>
              <p class="mt-1 text-sm text-yellow-800">
                {{ formatPrice(order.total_amount_minor, order.currency) }} · Created {{ formatDate(order.created_at) }}
              </p>
              <div class="mt-3">
                <UButton size="sm" color="yellow" variant="solid" :to="`/supplier/orders/${order.id}`">Manage Delivery</UButton>
              </div>
            </div>
          </div>
        </div>
      </UCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Intent, Order } from '~/types'

definePageMeta({
  layout: 'supplier',
  middleware: ['supplier'],
})

const appStore = useAppStore()
const offerStore = useOfferStore()
const orderStore = useOrderStore()
const { formatPrice } = useApiUtils()

const loading = ref(false)
const error = ref('')

const activeOfferStatuses = ['SUBMITTED', 'VIEWED', 'SHORTLISTED']
const deliveryActionStatuses = ['PAID_IN_ESCROW', 'IN_PROGRESS', 'DELIVERED']

const recentPings = computed(() => offerStore.pings.slice(0, 5))
const actionOrders = computed(() => orderStore.orders.filter((order) => deliveryActionStatuses.includes(order.status)).slice(0, 5))
const activeOffers = computed(() => offerStore.myOffers.filter((offer) => activeOfferStatuses.includes(offer.status)).length)
const awardedOffers = computed(() => offerStore.myOffers.filter((offer) => offer.status === 'AWARDED').length)
const escrowPayoutMinor = computed(() => orderStore.orders
  .filter((order) => ['ACCEPTED', 'PAYOUT_RELEASED'].includes(order.status))
  .reduce((sum, order) => sum + Number(order.total_amount_minor || 0), 0))
const defaultCurrency = computed(() => orderStore.orders[0]?.currency || offerStore.myOffers[0]?.currency || 'PHP')

const metrics = computed(() => [
  {
    label: appStore.t('supplier.dashboard.newPings'),
    value: String(offerStore.pings.length),
    note: 'Real matching requests',
    color: 'text-indigo-600',
  },
  {
    label: appStore.t('supplier.dashboard.activeOffers'),
    value: String(activeOffers.value),
    note: 'Submitted, viewed, or shortlisted',
    color: 'text-slate-900',
  },
  {
    label: appStore.t('supplier.dashboard.awardedOrders'),
    value: String(awardedOffers.value),
    note: 'Awarded supplier offers',
    color: 'text-slate-900',
  },
  {
    label: appStore.t('supplier.dashboard.pendingDelivery'),
    value: String(actionOrders.value.length),
    note: 'Orders needing delivery attention',
    color: 'text-slate-900',
  },
  {
    label: appStore.t('supplier.dashboard.escrowPayout'),
    value: escrowPayoutMinor.value ? formatPrice(escrowPayoutMinor.value, defaultCurrency.value) : 'N/A',
    note: 'Accepted or released orders',
    color: 'text-slate-900',
  },
  {
    label: appStore.t('supplier.dashboard.responseSla'),
    value: 'N/A',
    note: 'No response-time metric yet',
    color: 'text-slate-900',
  },
  {
    label: appStore.t('supplier.dashboard.rating'),
    value: 'N/A',
    note: 'Review aggregate not connected yet',
    color: 'text-slate-900',
  },
  {
    label: appStore.t('supplier.dashboard.disputeRate'),
    value: 'N/A',
    note: 'Dispute aggregate not connected yet',
    color: 'text-slate-900',
  },
])

function budgetLabel(ping: Intent) {
  if (ping.budget_min_minor && ping.budget_max_minor) {
    return `${formatPrice(ping.budget_min_minor, ping.currency)} - ${formatPrice(ping.budget_max_minor, ping.currency)}`
  }
  if (ping.budget_max_minor) return formatPrice(ping.budget_max_minor, ping.currency)
  if (ping.budget_min_minor) return formatPrice(ping.budget_min_minor, ping.currency)
  return 'Open'
}

function locationLabel(ping: Intent) {
  return [ping.city, ping.country].filter(Boolean).join(', ') || 'No location'
}

function shortId(value?: string | null) {
  return value ? String(value).slice(0, 8) : 'N/A'
}

function formatDate(value?: string) {
  if (!value) return 'N/A'
  try {
    return new Intl.DateTimeFormat('en-PH', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
  } catch {
    return value
  }
}

function statusColor(status: Order['status']) {
  const map: Record<string, string> = {
    PAID_IN_ESCROW: 'indigo',
    IN_PROGRESS: 'blue',
    DELIVERED: 'green',
    ACCEPTED: 'green',
    DISPUTED: 'red',
    CANCELED: 'gray',
  }
  return map[status] || 'gray'
}

async function loadDashboard() {
  loading.value = true
  error.value = ''
  try {
    await Promise.all([
      offerStore.fetchPings(),
      offerStore.fetchMyOffers(),
      orderStore.fetchMyOrders(),
    ])
  } catch (e: any) {
    const detail = e?.data?.detail || e?.message
    error.value = typeof detail === 'string' ? detail : 'Failed to load supplier dashboard.'
  } finally {
    loading.value = false
  }
}

onMounted(loadDashboard)
</script>
