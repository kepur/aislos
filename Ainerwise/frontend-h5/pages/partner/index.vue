<template>
  <div class="px-4 py-4">
    <div class="mb-4">
      <p class="text-[10px] font-bold uppercase tracking-widest text-blue-500">{{ $t('partner.kicker') }}</p>
      <h1 class="mt-1 text-xl font-bold text-slate-800">{{ $t('partner.title') }}</h1>
      <p class="mt-1 text-xs text-slate-400">{{ $t('partner.subtitle') }}</p>
    </div>

    <div v-if="loading" class="m-card text-center text-sm text-slate-400">{{ $t('partner.loading') }}</div>

    <template v-else-if="dashboard">
      <div class="mb-4 rounded-2xl border p-4 shadow-sm" :class="dashboard.partner.verification_status === 'verified' ? 'border-emerald-100 bg-emerald-50' : 'border-amber-100 bg-amber-50'">
        <div class="flex items-start justify-between gap-3">
          <div>
            <p class="text-[10px] font-bold uppercase tracking-wider" :class="dashboard.partner.verification_status === 'verified' ? 'text-emerald-600' : 'text-amber-600'">
              {{ $t('partner.accountStatus') }}
            </p>
            <p class="mt-1 text-sm font-bold capitalize text-slate-800">{{ dashboard.partner.verification_status.replace(/_/g, ' ') }}</p>
            <p class="mt-1 text-[11px] text-slate-500">{{ dashboard.partner.partner_type }}<template v-if="dashboard.partner.city"> · {{ dashboard.partner.city }}</template></p>
          </div>
          <span class="rounded-full bg-white px-2.5 py-1 text-[10px] font-bold text-slate-500">{{ dashboard.partner.availability_status }}</span>
        </div>
      </div>

      <div class="mb-4 grid grid-cols-4 gap-2">
        <NuxtLink to="/partner/rfqs" class="m-card p-3 text-center">
          <p class="text-xl font-bold text-blue-600">{{ dashboard.counts.open }}</p>
          <p class="text-[10px] font-medium text-slate-400">{{ $t('partner.open') }}</p>
        </NuxtLink>
        <NuxtLink to="/partner/rfqs" class="m-card p-3 text-center">
          <p class="text-xl font-bold text-emerald-600">{{ dashboard.counts.bid_submitted }}</p>
          <p class="text-[10px] font-medium text-slate-400">{{ $t('partner.submitted') }}</p>
        </NuxtLink>
        <div class="m-card p-3 text-center">
          <p class="text-xl font-bold text-slate-700">{{ dashboard.metric.composite_score ?? '—' }}</p>
          <p class="text-[10px] font-medium text-slate-400">{{ $t('partner.score') }}</p>
        </div>
        <NuxtLink to="/partner/tasks" class="m-card p-3 text-center">
          <p class="text-xl font-bold text-amber-600">{{ dashboard.tasks.open }}</p>
          <p class="text-[10px] font-medium text-slate-400">{{ $t('partner.openTasks') }}</p>
        </NuxtLink>
      </div>

      <div class="mb-4 grid grid-cols-2 gap-2">
        <NuxtLink to="/partner/rfqs" class="block rounded-2xl bg-gradient-to-r from-blue-500 to-indigo-500 px-3 py-3.5 text-center text-xs font-semibold text-white shadow-md shadow-blue-500/20">
          {{ $t('partner.reviewRequests') }}
        </NuxtLink>
        <NuxtLink to="/partner/calendar" class="block rounded-2xl border border-blue-100 bg-blue-50 px-3 py-3.5 text-center text-xs font-semibold text-blue-600">
          {{ $t('partner.openCalendar') }}
        </NuxtLink>
      </div>

      <div class="m-card">
        <div class="mb-3 flex items-center justify-between">
          <h2 class="text-sm font-bold text-slate-800">{{ $t('partner.recentRequests') }}</h2>
          <NuxtLink to="/partner/rfqs" class="text-[11px] font-semibold text-blue-500">{{ $t('dash.viewAll') }}</NuxtLink>
        </div>
        <div v-if="recent.length" class="space-y-2">
          <NuxtLink v-for="rfq in recent" :key="rfq.id" :to="`/partner/rfqs/${rfq.id}`" class="block rounded-xl bg-slate-50 p-3 active:bg-slate-100">
            <div class="flex items-start justify-between gap-2">
              <div class="min-w-0">
                <p class="truncate text-xs font-semibold text-slate-700">{{ rfq.title }}</p>
                <p class="mt-1 text-[10px] uppercase tracking-wide text-slate-400">{{ rfq.trade }}</p>
              </div>
              <span :class="['status-pill shrink-0', statusClass(rfq.invitation_status)]">{{ rfq.invitation_status.replace(/_/g, ' ') }}</span>
            </div>
          </NuxtLink>
        </div>
        <p v-else class="py-3 text-center text-xs text-slate-400">{{ $t('partner.noRequests') }}</p>
      </div>
    </template>

    <div v-else class="m-card text-center">
      <p class="text-sm font-semibold text-slate-700">{{ error }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const { apiFetch } = useApi()
const dashboard = ref<any>(null)
const recent = ref<any[]>([])
const loading = ref(true)
const error = ref('')

function statusClass(status: string) {
  if (status === 'bid_submitted') return 'bg-emerald-50 text-emerald-600'
  if (status === 'declined') return 'bg-slate-100 text-slate-500'
  return 'bg-blue-50 text-blue-600'
}

onMounted(async () => {
  try {
    const [summary, requests] = await Promise.all([
      apiFetch<any>('/partner/dashboard'),
      apiFetch<any>('/partner/rfqs?limit=3'),
    ])
    dashboard.value = summary
    recent.value = requests.items || []
  } catch (e: any) {
    error.value = e?.data?.detail || 'Partner workspace is unavailable.'
  } finally {
    loading.value = false
  }
})
</script>
