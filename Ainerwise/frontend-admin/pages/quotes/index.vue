<template>
  <div>
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-6">
      <div>
        <h1 class="admin-page-title">Quotes</h1>
        <p class="admin-page-desc">Manage quotations for leads and projects.</p>
      </div>
      <div class="flex gap-2">
        <select v-model="statusFilter" class="input-field max-w-40" @change="loadQuotes">
          <option value="">All statuses</option>
          <option value="draft">Draft</option>
          <option value="sent">Sent</option>
          <option value="accepted">Accepted</option>
          <option value="rejected">Rejected</option>
          <option value="expired">Expired</option>
        </select>
        <button @click="showCreate = true" class="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700">
          + New Quote
        </button>
      </div>
    </div>

    <div class="admin-panel">
      <table class="admin-table w-full text-sm">
        <thead>
          <tr>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Quote ID</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Lead</th>
            <th class="text-right px-4 py-3 font-medium text-gray-500">Total</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Status</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Valid Until</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Created</th>
            <th class="text-right px-4 py-3 font-medium text-gray-500">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="quote in quotes" :key="quote.id" class="border-b">
            <td class="px-4 py-3">
              <p class="font-medium text-gray-900 font-mono text-xs">{{ quote.id.slice(0, 8) }}</p>
            </td>
            <td class="px-4 py-3">
              <NuxtLink v-if="quote.lead_id" :to="`leads/${quote.lead_id}`" class="text-primary-600 hover:underline text-xs">
                {{ quote.lead_id.slice(0, 8) }}
              </NuxtLink>
              <span v-else class="text-gray-400">-</span>
            </td>
            <td class="px-4 py-3 text-right font-medium">{{ quote.total.toLocaleString() }} {{ quote.currency }}</td>
            <td class="px-4 py-3"><StatusBadge :status="quote.status" /></td>
            <td class="px-4 py-3 text-gray-600">{{ quote.valid_until || '-' }}</td>
            <td class="px-4 py-3 text-gray-500 whitespace-nowrap">{{ new Date(quote.created_at).toLocaleDateString() }}</td>
            <td class="px-4 py-3 text-right">
              <div class="flex justify-end gap-1">
                <button
                  class="px-2 py-1 text-xs font-medium rounded bg-gray-100 text-gray-700 hover:bg-gray-200"
                  @click="downloadPdf(quote.id)"
                >PDF</button>
                <button
                  v-if="quote.status === 'draft'"
                  class="px-2 py-1 text-xs font-medium rounded bg-blue-100 text-blue-700 hover:bg-blue-200"
                  @click="changeStatus(quote.id, 'sent')"
                >Send</button>
                <button
                  v-if="quote.status === 'sent'"
                  class="px-2 py-1 text-xs font-medium rounded bg-green-100 text-green-700 hover:bg-green-200"
                  @click="changeStatus(quote.id, 'accepted')"
                >Accept</button>
                <button
                  v-if="quote.status === 'sent'"
                  class="px-2 py-1 text-xs font-medium rounded bg-red-100 text-red-700 hover:bg-red-200"
                  @click="changeStatus(quote.id, 'rejected')"
                >Reject</button>
              </div>
            </td>
          </tr>
          <tr v-if="!quotes.length">
            <td colspan="7" class="px-4 py-8 text-center text-gray-500">No quotes found.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create Modal -->
    <div v-if="showCreate" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showCreate = false">
      <div class="bg-white rounded-xl w-full max-w-lg mx-4 p-6 max-h-[80vh] overflow-y-auto">
        <h2 class="text-lg font-bold text-gray-900 mb-4">Create Quote</h2>
        <form class="space-y-4" @submit.prevent="createQuote">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Lead ID (optional)</label>
            <input v-model="createForm.lead_id" type="text" class="input-field" placeholder="UUID of linked lead" />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Device Total</label>
              <input v-model.number="createForm.device_total" type="number" step="0.01" class="input-field" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Service Total</label>
              <input v-model.number="createForm.service_total" type="number" step="0.01" class="input-field" />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Platform Fee</label>
              <input v-model.number="createForm.platform_fee" type="number" step="0.01" class="input-field" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Logistics Fee</label>
              <input v-model.number="createForm.logistics_fee" type="number" step="0.01" class="input-field" />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Total</label>
              <input v-model.number="createForm.total" type="number" step="0.01" class="input-field" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Currency</label>
              <input v-model="createForm.currency" type="text" class="input-field" placeholder="EUR" />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Valid Until</label>
            <input v-model="createForm.valid_until" type="date" class="input-field" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Notes</label>
            <textarea v-model="createForm.notes" rows="3" class="input-field" placeholder="Quote notes..." />
          </div>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" class="px-4 py-2 text-sm border rounded-lg text-gray-600 hover:bg-gray-50" @click="showCreate = false">Cancel</button>
            <button type="submit" class="px-4 py-2 text-sm font-medium bg-primary-600 text-white rounded-lg hover:bg-primary-700" :disabled="saving">
              {{ saving ? 'Creating...' : 'Create Quote' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { apiFetch } = useApi()
const quotes = ref<any[]>([])
const statusFilter = ref('')
const showCreate = ref(false)
const saving = ref(false)

const createForm = reactive({
  lead_id: '',
  device_total: 0,
  service_total: 0,
  platform_fee: 0,
  logistics_fee: 0,
  total: 0,
  currency: 'EUR',
  valid_until: '',
  notes: '',
})

async function loadQuotes() {
  const params = statusFilter.value ? `?status=${statusFilter.value}` : ''
  try {
    const res = await apiFetch<any>(`/quotes${params}`)
    quotes.value = res.items || []
  } catch {
    quotes.value = []
  }
}

async function changeStatus(id: string, newStatus: string) {
  try {
    await apiFetch(`/quotes/${id}/status`, { method: 'PATCH', body: { status: newStatus } })
    await loadQuotes()
  } catch (e: any) {
    console.error('Status update failed:', e)
  }
}

async function createQuote() {
  saving.value = true
  try {
    const body: any = {
      device_total: createForm.device_total,
      service_total: createForm.service_total,
      platform_fee: createForm.platform_fee,
      logistics_fee: createForm.logistics_fee,
      total: createForm.total,
      currency: createForm.currency || 'EUR',
    }
    if (createForm.lead_id) body.lead_id = createForm.lead_id
    if (createForm.valid_until) body.valid_until = createForm.valid_until
    if (createForm.notes) body.notes = createForm.notes

    await apiFetch('/quotes', { method: 'POST', body })
    showCreate.value = false
    await loadQuotes()
  } catch (e: any) {
    console.error('Create quote failed:', e)
  } finally {
    saving.value = false
  }
}

async function downloadPdf(id: string) {
  try {
    const { token } = useAuth()
    const baseUrl = useApiBase()
    const res = await fetch(`${baseUrl}/quotes/${id}/pdf`, {
      headers: { Authorization: `Bearer ${token.value}` },
    })
    if (!res.ok) throw new Error('PDF download failed')
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `quote-${id.slice(0, 8).toUpperCase()}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e: any) {
    console.error('PDF download failed:', e)
  }
}

onMounted(loadQuotes)
</script>
