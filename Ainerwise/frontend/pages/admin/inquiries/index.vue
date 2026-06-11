<template>
  <div class="glass-panel p-6">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-white">Product Inquiries</h1>
        <p class="text-sm text-slate-400 mt-1">Manage product inquiries from buyers and visitors.</p>
      </div>
      <div class="flex gap-2">
        <select v-model="statusFilter" class="input-field max-w-40 bg-white/5 border-white/10 text-white" @change="loadInquiries">
          <option value="" class="text-slate-900">All statuses</option>
          <option value="new" class="text-slate-900">New</option>
          <option value="contacted" class="text-slate-900">Contacted</option>
          <option value="quoted" class="text-slate-900">Quoted</option>
          <option value="converted" class="text-slate-900">Converted</option>
          <option value="closed" class="text-slate-900">Closed</option>
        </select>
      </div>
    </div>

    <div class="rounded-xl border border-white/10 overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-white/5 border-b border-white/10">
          <tr>
            <th class="text-left px-4 py-3 font-medium text-slate-400">Contact</th>
            <th class="text-left px-4 py-3 font-medium text-slate-400">Product</th>
            <th class="text-left px-4 py-3 font-medium text-slate-400">Qty</th>
            <th class="text-left px-4 py-3 font-medium text-slate-400">Message</th>
            <th class="text-left px-4 py-3 font-medium text-slate-400">Status</th>
            <th class="text-left px-4 py-3 font-medium text-slate-400">Created</th>
            <th class="text-right px-4 py-3 font-medium text-slate-400">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="inq in inquiries" :key="inq.id" class="border-b border-white/10 hover:bg-white/5 transition">
            <td class="px-4 py-3">
              <p class="font-medium text-white">{{ inq.contact_name || 'Anonymous' }}</p>
              <p class="text-xs text-slate-400">{{ inq.contact_email || '-' }}</p>
              <p v-if="inq.contact_phone" class="text-xs text-slate-500">{{ inq.contact_phone }}</p>
            </td>
            <td class="px-4 py-3">
              <p class="text-slate-300 font-mono text-xs">{{ inq.product_id ? inq.product_id.slice(0, 8) + '...' : '-' }}</p>
            </td>
            <td class="px-4 py-3 text-slate-300">{{ inq.quantity || '-' }}</td>
            <td class="px-4 py-3 text-slate-300 max-w-xs truncate">{{ inq.message || '-' }}</td>
            <td class="px-4 py-3"><StatusBadge :status="inq.status" /></td>
            <td class="px-4 py-3 text-slate-400 whitespace-nowrap">{{ new Date(inq.created_at).toLocaleDateString() }}</td>
            <td class="px-4 py-3 text-right">
              <div class="flex justify-end gap-1">
                <button
                  class="px-2 py-1 text-xs font-medium rounded bg-blue-500/20 text-blue-300 hover:bg-blue-500/40 transition"
                  @click="openDetail(inq)"
                >View</button>
                <button
                  v-if="inq.status === 'new'"
                  class="px-2 py-1 text-xs font-medium rounded bg-green-500/20 text-green-300 hover:bg-green-500/40 transition"
                  @click="changeStatus(inq.id, 'contacted')"
                >Contact</button>
                <button
                  v-if="inq.status === 'contacted'"
                  class="px-2 py-1 text-xs font-medium rounded bg-purple-500/20 text-purple-300 hover:bg-purple-500/40 transition"
                  @click="changeStatus(inq.id, 'quoted')"
                >Quoted</button>
                <button
                  v-if="inq.status === 'quoted'"
                  class="px-2 py-1 text-xs font-medium rounded bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/40 transition"
                  @click="changeStatus(inq.id, 'converted')"
                >Convert</button>
                <button
                  v-if="inq.status !== 'closed' && inq.status !== 'converted'"
                  class="px-2 py-1 text-xs font-medium rounded bg-white/10 text-slate-300 hover:bg-white/20 transition"
                  @click="changeStatus(inq.id, 'closed')"
                >Close</button>
              </div>
            </td>
          </tr>
          <tr v-if="!inquiries.length">
            <td colspan="7" class="px-4 py-8 text-center text-slate-500">No inquiries found.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div v-if="total > limit" class="flex items-center justify-between mt-4">
      <p class="text-sm text-slate-400">{{ total }} total inquiries</p>
      <div class="flex gap-2">
        <button
          class="px-3 py-1 text-sm border border-white/10 rounded hover:bg-white/10 transition disabled:opacity-50 disabled:hover:bg-transparent"
          :disabled="page === 0"
          @click="page--; loadInquiries()"
        >Previous</button>
        <button
          class="px-3 py-1 text-sm border border-white/10 rounded hover:bg-white/10 transition disabled:opacity-50 disabled:hover:bg-transparent"
          :disabled="(page + 1) * limit >= total"
          @click="page++; loadInquiries()"
        >Next</button>
      </div>
    </div>

    <!-- Detail Modal -->
    <div v-if="selectedInquiry" class="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center z-50 p-4" @click.self="selectedInquiry = null">
      <div class="glass-panel max-w-lg w-full p-6 max-h-[80vh] overflow-y-auto border-primary-500/30 shadow-[0_0_20px_rgba(14,165,233,0.2)]">
        <div class="flex items-start justify-between mb-4">
          <h2 class="text-lg font-bold text-white">Inquiry Detail</h2>
          <button @click="selectedInquiry = null" class="text-slate-400 hover:text-white text-xl transition">&times;</button>
        </div>

        <div class="space-y-3 text-sm">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <p class="text-slate-400">Contact Name</p>
              <p class="font-medium text-white">{{ selectedInquiry.contact_name || '-' }}</p>
            </div>
            <div>
              <p class="text-slate-400">Email</p>
              <p class="font-medium text-white">{{ selectedInquiry.contact_email || '-' }}</p>
            </div>
            <div>
              <p class="text-slate-400">Phone</p>
              <p class="font-medium text-white">{{ selectedInquiry.contact_phone || '-' }}</p>
            </div>
            <div>
              <p class="text-slate-400">Quantity</p>
              <p class="font-medium text-white">{{ selectedInquiry.quantity || '-' }}</p>
            </div>
            <div>
              <p class="text-slate-400">Status</p>
              <StatusBadge :status="selectedInquiry.status" />
            </div>
            <div>
              <p class="text-slate-400">Created</p>
              <p class="font-medium text-white">{{ new Date(selectedInquiry.created_at).toLocaleString() }}</p>
            </div>
          </div>

          <div>
            <p class="text-slate-400 mb-1">Message</p>
            <p class="bg-white/5 border border-white/10 rounded p-3 text-slate-300 whitespace-pre-wrap">{{ selectedInquiry.message || 'No message' }}</p>
          </div>

          <div>
            <p class="text-slate-400 mb-1">Admin Notes</p>
            <textarea
              v-model="adminNotes"
              class="input-field w-full bg-white/5 border-white/10 text-white placeholder-slate-500"
              rows="3"
              placeholder="Add internal notes..."
            ></textarea>
            <button
              class="mt-2 px-3 py-1 text-sm bg-primary-600 text-white rounded hover:bg-primary-500 transition"
              @click="saveNotes"
            >Save Notes</button>
          </div>

          <div v-if="selectedInquiry.product_id" class="pt-4 border-t border-white/10 mt-4">
            <p class="text-slate-400">Product ID</p>
            <p class="font-mono text-xs text-primary-400">{{ selectedInquiry.product_id }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'admin' })

const { apiFetch } = useApi()
const inquiries = ref<any[]>([])
const statusFilter = ref('')
const total = ref(0)
const page = ref(0)
const limit = 20
const selectedInquiry = ref<any>(null)
const adminNotes = ref('')

async function loadInquiries() {
  const params = new URLSearchParams()
  if (statusFilter.value) params.set('status', statusFilter.value)
  params.set('skip', String(page.value * limit))
  params.set('limit', String(limit))
  const query = params.toString()
  try {
    const res = await apiFetch<any>(`/inquiries${query ? '?' + query : ''}`)
    inquiries.value = res.items || []
    total.value = res.total || 0
  } catch {
    inquiries.value = []
  }
}

async function changeStatus(id: string, newStatus: string) {
  try {
    await apiFetch(`/inquiries/${id}/status`, { method: 'PATCH', body: { status: newStatus } })
    await loadInquiries()
  } catch (e: any) {
    console.error('Status update failed:', e)
  }
}

function openDetail(inq: any) {
  selectedInquiry.value = inq
  adminNotes.value = inq.admin_notes || ''
}

async function saveNotes() {
  if (!selectedInquiry.value) return
  try {
    await apiFetch(`/inquiries/${selectedInquiry.value.id}`, {
      method: 'PUT',
      body: { admin_notes: adminNotes.value },
    })
    selectedInquiry.value.admin_notes = adminNotes.value
    await loadInquiries()
  } catch (e: any) {
    console.error('Save notes failed:', e)
  }
}

onMounted(loadInquiries)
</script>
