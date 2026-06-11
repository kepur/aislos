<template>
  <div>
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-6">
      <div>
        <h1 class="admin-page-title">AI Business Brain</h1>
        <p class="admin-page-desc">Daily CEO briefing — auto at 06:30 UTC to Telegram, on demand here.</p>
      </div>
      <button class="btn-primary text-sm px-4 py-2" :disabled="busy" @click="run">
        {{ busy ? 'Generating...' : 'Run briefing now' }}
      </button>
    </div>

    <div v-if="latest" class="admin-panel p-5 mb-6">
      <p class="text-xs text-gray-400 mb-3">{{ new Date(latest.created_at).toLocaleString() }}
        <span v-if="latest.model" class="ml-2">· {{ latest.model }}</span>
        <span v-else class="ml-2">· template mode (no LLM configured)</span>
      </p>
      <pre class="whitespace-pre-wrap text-sm text-gray-800 font-sans leading-relaxed">{{ latest.text }}</pre>
      <div v-if="latest.metrics" class="grid grid-cols-2 md:grid-cols-4 gap-3 mt-5">
        <div v-for="(label, key) in metricLabels" :key="key" class="bg-gray-50 rounded-lg px-3 py-2">
          <p class="text-xs text-gray-500">{{ label }}</p>
          <p class="text-lg font-semibold text-gray-900">{{ latest.metrics[key] ?? '-' }}</p>
        </div>
      </div>
      <div v-if="latest.metrics?.partner_risk?.length" class="mt-4 bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-sm text-red-700">
        ⚠ {{ latest.metrics.partner_risk.length }} partner(s) with score drops — review before dispatching.
      </div>
    </div>
    <p v-else class="admin-panel p-8 text-center text-gray-500 mb-6">No briefing yet — click "Run briefing now".</p>

    <div class="admin-panel">
      <h2 class="font-medium text-gray-900 px-4 pt-4">History</h2>
      <table class="admin-table w-full text-sm mt-2">
        <tbody>
          <tr v-for="b in history" :key="b.id" class="border-b">
            <td class="px-4 py-3 text-gray-500 whitespace-nowrap">{{ new Date(b.created_at).toLocaleString() }}</td>
            <td class="px-4 py-3 text-gray-700 text-xs">{{ (b.text || '').slice(0, 140) }}…</td>
          </tr>
          <tr v-if="!history.length"><td class="px-4 py-6 text-center text-gray-400">No history.</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { apiFetch } = useApi()
const latest = ref<any>(null)
const history = ref<any[]>([])
const busy = ref(false)

const metricLabels: Record<string, string> = {
  leads_yesterday: 'Leads yesterday',
  quotes_yesterday: 'Quotes yesterday',
  rfqs_awarded_yesterday: 'RFQs awarded',
  revenue_funded_yesterday: 'Revenue funded €',
  open_rfqs_bidding: 'RFQs in bidding',
  reviews_pending: 'AI drafts pending',
  maintenance_due_7d: 'Maintenance due 7d',
  leads_need_followup: 'Need follow-up',
}

async function load() {
  const res = await apiFetch<any>('/admin/business-brain/latest')
  latest.value = res.briefing
  const hist = await apiFetch<any>('/admin/business-brain/history')
  history.value = hist.items || []
}

async function run() {
  busy.value = true
  try {
    await apiFetch('/admin/business-brain/run', { method: 'POST' })
    await load()
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>
