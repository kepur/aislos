<template>
  <div class="space-y-6">
    <NuxtLink :to="localized('/portal/leads')" class="text-sm font-semibold ws-accent">&larr; {{ $t('pLeadD.back') }}</NuxtLink>
    <section v-if="lead" class="portal-card">
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p class="text-xs font-semibold uppercase tracking-wider ws-accent">{{ $t('pLeadD.eyebrow') }}</p>
          <h1 class="mt-1 text-xl font-bold ws-title">{{ lead.project_type || $t('pLeadD.titleFallback') }}</h1>
          <p class="mt-1 text-sm ws-faint">{{ [lead.city, lead.country].filter(Boolean).join(', ') || $t('pLeadD.noLocation') }}</p>
        </div>
        <span :class="['rounded-full px-3 py-1 text-xs font-semibold', statusClass(lead.status)]">{{ lead.status?.replace(/_/g, ' ') }}</span>
      </div>
      <dl class="mt-6 grid gap-4 text-sm md:grid-cols-3">
        <div><dt class="ws-faint">{{ $t('pLeadD.budget') }}</dt><dd class="mt-1 font-semibold ws-title">{{ lead.budget_range || $t('pLeadD.budgetTbd') }}</dd></div>
        <div><dt class="ws-faint">{{ $t('pLeadD.solutionLine') }}</dt><dd class="mt-1 font-semibold ws-title">{{ lead.solution_line || $t('pLeadD.underAnalysis') }}</dd></div>
        <div><dt class="ws-faint">{{ $t('pLeadD.submitted') }}</dt><dd class="mt-1 font-semibold ws-title">{{ formatDate(lead.created_at) }}</dd></div>
      </dl>
      <div class="mt-6 grid gap-4 lg:grid-cols-2">
        <div class="rounded-xl ws-sunken p-4">
          <h2 class="text-sm font-bold ws-title">{{ $t('pLeadD.description') }}</h2>
          <p class="mt-2 whitespace-pre-wrap text-sm leading-relaxed ws-muted">{{ lead.description || $t('pLeadD.noDesc') }}</p>
        </div>
        <div class="rounded-xl ws-sunken p-4">
          <h2 class="text-sm font-bold ws-title">{{ $t('pLeadD.requestedSystems') }}</h2>
          <div class="mt-2 flex flex-wrap gap-2">
            <span v-for="item in lead.systems_needed_json || []" :key="String(item)" class="rounded-full bg-blue-50 px-3 py-1 text-xs font-medium ws-accent">{{ item }}</span>
            <span v-if="!(lead.systems_needed_json || []).length" class="text-sm ws-faint">{{ $t('pLeadD.aiWillIdentify') }}</span>
          </div>
        </div>
      </div>
      <div v-if="lead.ai_analysis_json" class="mt-4 rounded-xl border border-indigo-100 bg-indigo-50/60 p-4">
        <h2 class="text-sm font-bold text-indigo-800">{{ $t('pLeadD.aiAnalysis') }}</h2>
        <pre class="mt-2 whitespace-pre-wrap text-xs leading-relaxed text-indigo-700">{{ JSON.stringify(lead.ai_analysis_json, null, 2) }}</pre>
      </div>
    </section>
    <div v-else class="portal-card py-16 text-center text-sm ws-faint">{{ loading ? $t('pLeadD.loading') : error || $t('pLeadD.notFound') }}</div>
  </div>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()
definePageMeta({ layout: 'procurement', middleware: 'auth' })
const route = useRoute()
const { t } = useI18n()
const { apiFetch } = useApi()
const lead = ref<any>(null)
const loading = ref(true)
const error = ref('')
const { formatDate } = useLocaleFormat()
const statusClass = (status: string) => ['won', 'converted', 'matched'].includes(status) ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300' : status === 'lost' ? 'bg-red-500/15 text-red-600 dark:text-red-300' : 'bg-blue-500/15 ws-accent dark:text-blue-300'
onMounted(async () => {
 try { lead.value = await apiFetch(`/leads/my/${route.params.id}`) }
 catch (e: any) { error.value = e?.data?.detail || t('pLeadD.loadFailed') }
 finally { loading.value = false }
})
</script>
