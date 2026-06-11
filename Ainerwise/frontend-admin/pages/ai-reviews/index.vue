<template>
  <div>
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-6">
      <div>
        <h1 class="admin-page-title">AI Reviews</h1>
        <p class="admin-page-desc">Preliminary AI drafts awaiting human approval. Nothing AI-generated goes out without review.</p>
      </div>
      <div class="flex gap-2">
        <select v-model="statusFilter" class="input-field max-w-44" @change="load">
          <option value="">All statuses</option>
          <option value="preliminary">Preliminary</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
        </select>
        <select v-model="targetFilter" class="input-field max-w-44" @change="load">
          <option value="">All types</option>
          <option value="lead_draft">Lead draft</option>
          <option value="quote_draft">Quote draft</option>
          <option value="marketing_content">Marketing content</option>
          <option value="crm_summary">CRM summary</option>
          <option value="mission_plan">Mission plan</option>
          <option value="mission_final_report">Mission final report</option>
          <option value="ticket_triage">Ticket triage</option>
          <option value="marketing_weekly_report">Marketing weekly report</option>
        </select>
      </div>
    </div>

    <div class="admin-panel">
      <table class="admin-table w-full text-sm">
        <thead>
          <tr>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Type</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Draft</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Status</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Created</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="review in reviews" :key="review.id" class="border-b align-top">
            <td class="px-4 py-3">
              <p class="font-medium text-gray-900">{{ review.target_type }}</p>
              <p class="text-xs text-gray-500 font-mono">{{ review.id.slice(0, 8) }}</p>
            </td>
            <td class="px-4 py-3 max-w-md">
              <pre class="text-xs text-gray-600 whitespace-pre-wrap max-h-40 overflow-y-auto bg-gray-50 rounded p-2">{{ pretty(review.draft_json) }}</pre>
              <p v-if="review.review_notes" class="text-xs text-gray-500 mt-1">Notes: {{ review.review_notes }}</p>
            </td>
            <td class="px-4 py-3"><StatusBadge :status="review.status" /></td>
            <td class="px-4 py-3 text-gray-500 whitespace-nowrap">
              {{ new Date(review.created_at).toLocaleString() }}
            </td>
            <td class="px-4 py-3 whitespace-nowrap">
              <div v-if="review.status === 'preliminary'" class="flex gap-2">
                <NuxtLink v-if="review.target_type === 'mission_plan'" to="/agent-missions" class="btn-primary text-xs px-3 py-1.5">Approve in Missions</NuxtLink>
                <button v-else class="btn-primary text-xs px-3 py-1.5" :disabled="busy" @click="decide(review, 'approve')">Approve</button>
                <button class="text-xs px-3 py-1.5 rounded border border-red-300 text-red-600 hover:bg-red-50" :disabled="busy" @click="decide(review, 'reject')">Reject</button>
              </div>
              <span v-else class="text-xs text-gray-400">{{ review.reviewed_at ? new Date(review.reviewed_at).toLocaleString() : '' }}</span>
            </td>
          </tr>
          <tr v-if="!reviews.length">
            <td colspan="5" class="px-4 py-8 text-center text-gray-500">No AI reviews yet.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { apiFetch } = useApi()
const route = useRoute()
const reviews = ref<any[]>([])
const statusFilter = ref('preliminary')
const targetFilter = ref(String(route.query.target_type || ''))
const busy = ref(false)

function pretty(value: any) {
  if (!value) return '-'
  return JSON.stringify(value, null, 2)
}

async function load() {
  const params = new URLSearchParams()
  if (statusFilter.value) params.set('status', statusFilter.value)
  if (targetFilter.value) params.set('target_type', targetFilter.value)
  try {
    const res = await apiFetch<any>(`/admin/ai-reviews?${params.toString()}`)
    reviews.value = res.items || []
  } catch {
    reviews.value = []
  }
}

async function decide(review: any, action: 'approve' | 'reject') {
  let notes: string | null = null
  if (action === 'reject') {
    notes = window.prompt('Rejection notes (optional):') || null
  }
  busy.value = true
  try {
    await apiFetch(`/admin/ai-reviews/${review.id}/${action}`, { method: 'POST', body: { notes } })
    await load()
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>
