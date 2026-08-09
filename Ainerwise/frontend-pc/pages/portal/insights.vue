<template>
  <section class="space-y-6">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold ws-title">{{ $t('insightsPage.title') }}</h1>
        <p class="mt-1 text-sm ws-muted">{{ $t('insightsPage.subtitle') }}</p>
      </div>
      <p class="text-xs ws-faint">{{ $t('insightsPage.scope') }}</p>
    </div>

    <div v-if="loading" class="pc-card py-12 text-center text-sm ws-muted">{{ $t('insightsPage.loading') }}</div>

    <template v-else>
      <!-- Headline numbers -->
      <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div v-for="stat in headline" :key="stat.label" class="pc-card !p-5">
          <p class="text-xs font-medium ws-faint">{{ stat.label }}</p>
          <p class="mt-1 text-2xl font-bold ws-title">{{ stat.value }}</p>
          <p class="mt-1 text-xs ws-muted">{{ stat.hint }}</p>
        </div>
      </div>

      <div class="grid gap-6 lg:grid-cols-2 lg:items-start">
        <!-- Requests by status -->
        <div class="pc-card">
          <h2 class="mb-4 text-lg font-medium ws-title">{{ $t('insightsPage.requestsByStatus') }}</h2>
          <div v-if="requestStatuses.length" class="space-y-3">
            <div v-for="row in requestStatuses" :key="row.key">
              <div class="mb-1 flex items-center justify-between text-sm">
                <span class="ws-muted">{{ row.key }}</span>
                <span class="font-semibold ws-title">{{ row.count }}</span>
              </div>
              <div class="h-2 overflow-hidden rounded-full ws-soft">
                <div class="h-full rounded-full" :style="{ width: `${row.percent}%`, background: 'var(--accent)' }"></div>
              </div>
            </div>
          </div>
          <p v-else class="py-6 text-center text-sm ws-muted">{{ $t('insightsPage.noData') }}</p>
        </div>

        <!-- Spend by order status -->
        <div class="pc-card">
          <h2 class="mb-4 text-lg font-medium ws-title">{{ $t('insightsPage.spendByStage') }}</h2>
          <div v-if="spendStages.length" class="space-y-3">
            <div
              v-for="stage in spendStages"
              :key="stage.key"
              class="flex items-center justify-between rounded-xl px-3 py-2.5 ws-sunken"
            >
              <div class="min-w-0">
                <p class="truncate text-sm font-medium ws-title">{{ stage.label }}</p>
                <p class="text-xs ws-faint">{{ stage.count }} {{ $t('insightsPage.orders') }}</p>
              </div>
              <span class="shrink-0 text-sm font-bold ws-accent">{{ stage.amount }}</span>
            </div>
          </div>
          <p v-else class="py-6 text-center text-sm ws-muted">{{ $t('insightsPage.noData') }}</p>
        </div>
      </div>

      <!-- Delivery pipeline -->
      <div class="pc-card">
        <div class="mb-4 flex items-center justify-between">
          <h2 class="text-lg font-medium ws-title">{{ $t('insightsPage.pipeline') }}</h2>
          <NuxtLink to="/portal/projects" class="text-sm ws-accent hover:opacity-80">
            {{ $t('insightsPage.viewProjects') }} →
          </NuxtLink>
        </div>
        <div v-if="pipeline.length" class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <div v-for="stage in pipeline" :key="stage.key" class="ws-tile">
            <p class="text-xs font-semibold uppercase tracking-[0.14em] ws-faint">{{ stage.label }}</p>
            <p class="mt-2 text-2xl font-bold ws-title">{{ stage.count }}</p>
          </div>
        </div>
        <p v-else class="py-6 text-center text-sm ws-muted">{{ $t('insightsPage.noData') }}</p>
      </div>
    </template>

    <p v-if="error" class="pc-card text-sm text-red-400">{{ error }}</p>
  </section>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'procurement', middleware: 'auth' })

const { t } = useI18n()
const { apiFetch } = useApi()
const api = useCommerce()

const loading = ref(true)
const error = ref('')
const leads = ref<any[]>([])
const orders = ref<any[]>([])
const projects = ref<any[]>([])
const tickets = ref<any[]>([])

// Escrow-bearing order states, matching the buyer workspace KPI.
const ESCROW_STATES = ['PAID_IN_ESCROW', 'IN_PROGRESS', 'DELIVERED', 'ACCEPTED']

function money(minor: number, currency = 'EUR') {
  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency,
      maximumFractionDigits: 0,
    }).format(minor / 100)
  } catch {
    return `${(minor / 100).toLocaleString()} ${currency}`
  }
}

const currency = computed(() => orders.value.find(o => o.currency)?.currency || 'EUR')

const totalCommitted = computed(() =>
  orders.value.reduce((sum, o) => sum + Number(o.total_amount_minor ?? o.total_minor ?? 0), 0),
)
const inEscrow = computed(() =>
  orders.value
    .filter(o => ESCROW_STATES.includes(String(o.status || '').toUpperCase()))
    .reduce((sum, o) => sum + Number(o.total_amount_minor ?? o.total_minor ?? 0), 0),
)
const conversion = computed(() => {
  if (!leads.value.length) return '—'
  return `${Math.round((orders.value.length / leads.value.length) * 100)}%`
})

const headline = computed(() => [
  {
    label: t('insightsPage.kpiRequests'),
    value: leads.value.length,
    hint: t('insightsPage.kpiRequestsHint'),
  },
  {
    label: t('insightsPage.kpiCommitted'),
    value: totalCommitted.value ? money(totalCommitted.value, currency.value) : '—',
    hint: t('insightsPage.kpiCommittedHint'),
  },
  {
    label: t('insightsPage.kpiEscrow'),
    value: inEscrow.value ? money(inEscrow.value, currency.value) : '—',
    hint: t('insightsPage.kpiEscrowHint'),
  },
  {
    label: t('insightsPage.kpiConversion'),
    value: conversion.value,
    hint: t('insightsPage.kpiConversionHint'),
  },
])

function groupBy(rows: any[], field: string) {
  const counts: Record<string, number> = {}
  for (const row of rows) {
    const key = String(row[field] || 'unknown')
    counts[key] = (counts[key] || 0) + 1
  }
  const max = Math.max(1, ...Object.values(counts))
  return Object.entries(counts)
    .map(([key, count]) => ({ key, count, percent: Math.round((count / max) * 100) }))
    .sort((a, b) => b.count - a.count)
}

const requestStatuses = computed(() => groupBy(leads.value, 'status'))

const spendStages = computed(() => {
  const buckets: Record<string, { count: number; minor: number }> = {}
  for (const order of orders.value) {
    const key = String(order.status || 'unknown').toUpperCase()
    buckets[key] = buckets[key] || { count: 0, minor: 0 }
    buckets[key].count += 1
    buckets[key].minor += Number(order.total_amount_minor ?? order.total_minor ?? 0)
  }
  return Object.entries(buckets)
    .map(([key, value]) => ({
      key,
      label: key.replaceAll('_', ' '),
      count: value.count,
      amount: value.minor ? money(value.minor, currency.value) : '—',
    }))
    .sort((a, b) => b.count - a.count)
})

const pipeline = computed(() => {
  const stages = [
    { key: 'planning', label: t('insightsPage.stagePlanning'), match: ['planning', 'draft', 'new'] },
    { key: 'sourcing', label: t('insightsPage.stageSourcing'), match: ['sourcing', 'rfq', 'quote'] },
    { key: 'delivery', label: t('insightsPage.stageDelivery'), match: ['delivery', 'install', 'progress', 'active'] },
    { key: 'service', label: t('insightsPage.stageService'), match: ['maintenance', 'service', 'closed', 'complete'] },
  ]
  return stages.map(stage => ({
    ...stage,
    count: projects.value.filter(project =>
      stage.match.some(token => String(project.status || '').toLowerCase().includes(token)),
    ).length,
  }))
})

onMounted(async () => {
  const [leadRes, orderRes, projectRes, ticketRes] = await Promise.allSettled([
    apiFetch<any>('/leads/my?limit=100'),
    api.listOrders(),
    apiFetch<any>('/projects/my?limit=100'),
    apiFetch<any>('/tickets/my?limit=100'),
  ])
  if (leadRes.status === 'fulfilled') leads.value = leadRes.value.items || []
  if (orderRes.status === 'fulfilled') orders.value = orderRes.value.items || []
  if (projectRes.status === 'fulfilled') projects.value = projectRes.value.items || []
  if (ticketRes.status === 'fulfilled') tickets.value = ticketRes.value.items || []
  const failed = [leadRes, orderRes, projectRes, ticketRes].filter(r => r.status === 'rejected').length
  if (failed) error.value = t('insightsPage.partialError', { count: failed })
  loading.value = false
})
</script>
