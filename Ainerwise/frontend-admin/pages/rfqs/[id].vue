<template>
  <div v-if="rfq">
    <div class="mb-6">
      <NuxtLink to="/rfqs" class="text-xs text-gray-500 hover:underline">← RFQs</NuxtLink>
      <h1 class="admin-page-title mt-1">{{ rfq.title }}</h1>
      <p class="admin-page-desc">
        {{ rfq.trade }} · <StatusBadge :status="rfq.status" />
        <span v-if="rfq.project_id" class="ml-2 text-xs">project: {{ rfq.project_id.slice(0, 8) }}</span>
      </p>
    </div>

    <!-- Candidates -->
    <div class="admin-panel p-4 mb-6">
      <div class="flex items-center justify-between mb-3">
        <h2 class="font-medium text-gray-900">Partner candidates</h2>
        <button class="text-xs px-3 py-1.5 rounded border border-gray-300 hover:bg-gray-50" @click="loadCandidates">Match partners</button>
      </div>
      <div v-if="candidates.length" class="space-y-2">
        <label v-for="c in candidates" :key="c.partner_id" class="flex items-center gap-3 text-sm">
          <input v-model="selected" type="checkbox" :value="c.partner_id" />
          <span class="font-mono text-xs text-gray-500">{{ c.partner_id.slice(0, 8) }}</span>
          <span class="text-gray-800">{{ c.partner_type }}</span>
          <span class="text-gray-500">{{ c.city || '-' }} {{ c.country || '' }}</span>
          <span class="text-gray-500">score {{ c.score }}</span>
          <span v-if="c.has_telegram" class="text-emerald-600 text-xs">TG</span>
        </label>
        <button class="btn-primary text-sm px-4 py-2 mt-2" :disabled="busy || !selected.length" @click="invite">
          Invite {{ selected.length }} partner(s)
        </button>
      </div>
      <p v-else class="text-sm text-gray-500">Click "Match partners" to find candidates by trade/country/score.</p>
    </div>

    <!-- Record bid -->
    <div class="admin-panel p-4 mb-6">
      <h2 class="font-medium text-gray-900 mb-3">Record bid (received via Telegram/email)</h2>
      <div class="grid gap-2 md:grid-cols-4">
        <input v-model="bidForm.partner_id" placeholder="Partner ID" class="input-field md:col-span-2" />
        <input v-model.number="bidForm.amount" type="number" placeholder="Amount" class="input-field" />
        <input v-model.number="bidForm.lead_time_days" type="number" placeholder="Lead time (days)" class="input-field" />
      </div>
      <button class="btn-primary text-sm px-4 py-2 mt-3" :disabled="busy || !bidForm.partner_id || !bidForm.amount" @click="recordBid">Save bid</button>
    </div>

    <!-- Bids -->
    <div class="admin-panel">
      <div class="flex items-center justify-between px-4 pt-4">
        <h2 class="font-medium text-gray-900">Bids</h2>
        <button class="text-xs px-3 py-1.5 rounded border border-gray-300 hover:bg-gray-50"
                :disabled="busy || !rfq.bids?.length" @click="evaluate">AI evaluate</button>
      </div>
      <table class="admin-table w-full text-sm mt-2">
        <thead>
          <tr>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Partner</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Amount</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Lead time</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">AI score</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Status</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="bid in sortedBids" :key="bid.id" class="border-b align-top">
            <td class="px-4 py-3 font-mono text-xs text-gray-600">{{ bid.partner_id.slice(0, 8) }}</td>
            <td class="px-4 py-3 font-medium">{{ bid.amount }} {{ bid.currency }}</td>
            <td class="px-4 py-3 text-gray-600">{{ bid.lead_time_days ?? '-' }} d</td>
            <td class="px-4 py-3">
              <span v-if="bid.ai_score !== null" class="font-medium">{{ bid.ai_score }}</span>
              <span v-else class="text-gray-400">-</span>
              <p v-if="bid.ai_score_breakdown" class="text-[11px] text-gray-500">
                price {{ bid.ai_score_breakdown.price_score }} · partner {{ bid.ai_score_breakdown.partner_score }} · time {{ bid.ai_score_breakdown.lead_time_score }}
              </p>
            </td>
            <td class="px-4 py-3"><StatusBadge :status="bid.status" /></td>
            <td class="px-4 py-3">
              <button v-if="rfq.status !== 'awarded' && bid.status === 'submitted'"
                      class="btn-primary text-xs px-3 py-1.5" :disabled="busy" @click="award(bid)">Award</button>
            </td>
          </tr>
          <tr v-if="!rfq.bids?.length">
            <td colspan="6" class="px-4 py-8 text-center text-gray-500">No bids recorded yet.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const route = useRoute()
const { apiFetch } = useApi()
const rfq = ref<any>(null)
const candidates = ref<any[]>([])
const selected = ref<string[]>([])
const busy = ref(false)
const bidForm = ref<any>({ partner_id: '', amount: null, lead_time_days: null })

const sortedBids = computed(() =>
  [...(rfq.value?.bids || [])].sort((a, b) => (b.ai_score ?? -1) - (a.ai_score ?? -1)),
)

async function load() {
  rfq.value = await apiFetch<any>(`/admin/rfqs/${route.params.id}`)
}

async function loadCandidates() {
  const res = await apiFetch<any>(`/admin/rfqs/${route.params.id}/match-partners`)
  candidates.value = res.candidates || []
}

async function invite() {
  busy.value = true
  try {
    await apiFetch(`/admin/rfqs/${route.params.id}/invite`, { method: 'POST', body: { partner_ids: selected.value } })
    selected.value = []
    await load()
  } finally {
    busy.value = false
  }
}

async function recordBid() {
  busy.value = true
  try {
    await apiFetch(`/admin/rfqs/${route.params.id}/bids`, { method: 'POST', body: bidForm.value })
    bidForm.value = { partner_id: '', amount: null, lead_time_days: null }
    await load()
  } finally {
    busy.value = false
  }
}

async function evaluate() {
  busy.value = true
  try {
    await apiFetch(`/admin/rfqs/${route.params.id}/evaluate`, { method: 'POST' })
    await load()
  } finally {
    busy.value = false
  }
}

async function award(bid: any) {
  if (!window.confirm(`Award this RFQ to bid ${bid.amount} ${bid.currency}?`)) return
  busy.value = true
  try {
    await apiFetch(`/admin/rfqs/${route.params.id}/award`, { method: 'POST', body: { bid_id: bid.id } })
    await load()
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>
