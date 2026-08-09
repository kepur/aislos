<template>
  <div class="space-y-6">
    <NuxtLink to="/portal/leads" class="text-sm font-semibold ws-accent">&larr; Requirements</NuxtLink>
    <section v-if="lead" class="portal-card">
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p class="text-xs font-semibold uppercase tracking-wider ws-accent">Customer requirement</p>
          <h1 class="mt-1 text-xl font-bold ws-title">{{ lead.project_type || 'Solution request' }}</h1>
          <p class="mt-1 text-sm ws-faint">{{ [lead.city, lead.country].filter(Boolean).join(', ') || 'Location not provided' }}</p>
        </div>
        <span :class="['rounded-full px-3 py-1 text-xs font-semibold', statusClass(lead.status)]">{{ lead.status?.replace(/_/g, ' ') }}</span>
      </div>
      <dl class="mt-6 grid gap-4 text-sm md:grid-cols-3">
        <div><dt class="ws-faint">Budget</dt><dd class="mt-1 font-semibold ws-title">{{ lead.budget_range || 'To be assessed' }}</dd></div>
        <div><dt class="ws-faint">Solution line</dt><dd class="mt-1 font-semibold ws-title">{{ lead.solution_line || 'Under analysis' }}</dd></div>
        <div><dt class="ws-faint">Submitted</dt><dd class="mt-1 font-semibold ws-title">{{ formatDate(lead.created_at) }}</dd></div>
      </dl>
      <div class="mt-6 grid gap-4 lg:grid-cols-2">
        <div class="rounded-xl ws-sunken p-4">
          <h2 class="text-sm font-bold ws-title">Description</h2>
          <p class="mt-2 whitespace-pre-wrap text-sm leading-relaxed ws-muted">{{ lead.description || 'No description supplied.' }}</p>
        </div>
        <div class="rounded-xl ws-sunken p-4">
          <h2 class="text-sm font-bold ws-title">Requested systems</h2>
          <div class="mt-2 flex flex-wrap gap-2">
            <span v-for="item in lead.systems_needed_json || []" :key="String(item)" class="rounded-full bg-blue-50 px-3 py-1 text-xs font-medium ws-accent">{{ item }}</span>
            <span v-if="!(lead.systems_needed_json || []).length" class="text-sm ws-faint">AI analysis will identify the systems.</span>
          </div>
        </div>
      </div>
      <div v-if="lead.ai_analysis_json" class="mt-4 rounded-xl border border-indigo-100 bg-indigo-50/60 p-4">
        <h2 class="text-sm font-bold text-indigo-800">AI analysis</h2>
        <pre class="mt-2 whitespace-pre-wrap text-xs leading-relaxed text-indigo-700">{{ JSON.stringify(lead.ai_analysis_json, null, 2) }}</pre>
      </div>
    </section>
    <div v-else class="portal-card py-16 text-center text-sm ws-faint">{{ loading ? 'Loading requirement...' : error || 'Requirement not found' }}</div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'procurement', middleware: 'auth' })
const route = useRoute()
const { apiFetch } = useApi()
const lead = ref<any>(null)
const loading = ref(true)
const error = ref('')
const formatDate = (value: string) => value ? new Date(value).toLocaleString() : '-'
const statusClass = (status: string) => ['won', 'converted', 'matched'].includes(status) ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300' : status === 'lost' ? 'bg-red-500/15 text-red-600 dark:text-red-300' : 'bg-blue-500/15 ws-accent dark:text-blue-300'
onMounted(async () => {
 try { lead.value = await apiFetch(`/leads/my/${route.params.id}`) }
 catch (e: any) { error.value = e?.data?.detail || 'Unable to load requirement' }
 finally { loading.value = false }
})
</script>
