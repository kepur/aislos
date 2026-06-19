<template>
  <div class="space-y-6">
    <!-- Stats row -->
    <div class="grid grid-cols-4 gap-4">
      <div class="card p-4">
        <p class="text-xs text-slate-500 mb-1">Pending Review</p>
        <p class="text-2xl font-bold text-amber-600">{{ stats.pending }}</p>
      </div>
      <div class="card p-4">
        <p class="text-xs text-slate-500 mb-1">Active Campaigns</p>
        <p class="text-2xl font-bold text-green-600">{{ stats.active }}</p>
      </div>
      <div class="card p-4">
        <p class="text-xs text-slate-500 mb-1">Paused</p>
        <p class="text-2xl font-bold text-slate-500">{{ stats.paused }}</p>
      </div>
      <div class="card p-4">
        <p class="text-xs text-slate-500 mb-1">Rejected</p>
        <p class="text-2xl font-bold text-red-500">{{ stats.rejected }}</p>
      </div>
    </div>

    <!-- Filter tabs -->
    <div class="flex items-center gap-2 border-b border-slate-200 pb-0">
      <button
        v-for="tab in statusTabs"
        :key="tab.value"
        @click="statusFilter = tab.value; load()"
        :class="['px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors', statusFilter === tab.value ? 'border-indigo-600 text-indigo-700' : 'border-transparent text-slate-500 hover:text-slate-700']"
      >{{ tab.label }}</button>
    </div>

    <!-- Table -->
    <div class="card overflow-hidden">
      <table class="w-full">
        <thead>
          <tr>
            <th class="table-th">Campaign</th>
            <th class="table-th">Company</th>
            <th class="table-th">Placement</th>
            <th class="table-th">Budget</th>
            <th class="table-th">Performance</th>
            <th class="table-th">Status</th>
            <th class="table-th text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="7" class="table-td text-center py-10 text-slate-400">Loading...</td>
          </tr>
          <tr v-else-if="!campaigns.length">
            <td colspan="7" class="table-td text-center py-10 text-slate-400">No campaigns found</td>
          </tr>
          <tr v-for="c in campaigns" :key="c.id" class="hover:bg-slate-50">
            <td class="table-td">
              <div>
                <p class="text-sm font-semibold text-slate-800 max-w-[180px] truncate">{{ c.name || 'Untitled Campaign' }}</p>
                <p class="text-xs text-slate-400 mt-0.5">Bid: {{ formatMinor(c.bid_per_click_minor, c.currency) }}/click</p>
              </div>
            </td>
            <td class="table-td">
              <span class="text-sm text-slate-600">{{ c.company_id?.slice(0,8) }}…</span>
            </td>
            <td class="table-td">
              <span class="badge badge-blue text-xs">{{ c.placement?.replace('_', ' ') }}</span>
            </td>
            <td class="table-td">
              <div class="text-xs">
                <div class="font-semibold text-slate-800">{{ formatMinor(c.budget_minor, c.currency) }}</div>
                <div class="text-slate-400">Spent: {{ formatMinor(c.spent_minor, c.currency) }}</div>
                <!-- Budget bar -->
                <div class="w-20 h-1 bg-slate-100 rounded-full mt-1 overflow-hidden">
                  <div
                    class="h-full bg-indigo-500 rounded-full"
                    :style="{ width: `${Math.min(100, (c.spent_minor / Math.max(c.budget_minor, 1)) * 100)}%` }"
                  ></div>
                </div>
              </div>
            </td>
            <td class="table-td">
              <div class="text-xs text-slate-500 space-y-0.5">
                <div>{{ c.impressions?.toLocaleString() ?? 0 }} impr.</div>
                <div>{{ c.clicks ?? 0 }} clicks · {{ (c.ctr * 100).toFixed(1) }}% CTR</div>
              </div>
            </td>
            <td class="table-td">
              <span :class="['badge text-xs', statusClass(c.status)]">{{ c.status?.replace('_', ' ') }}</span>
              <p v-if="c.rejection_reason" class="text-xs text-red-400 mt-1 max-w-[120px] truncate" :title="c.rejection_reason">
                {{ c.rejection_reason }}
              </p>
            </td>
            <td class="table-td">
              <div class="flex justify-end gap-1.5">
                <button
                  v-if="c.status === 'PENDING_REVIEW'"
                  @click="approve(c)"
                  class="btn-secondary text-xs text-green-600 hover:bg-green-50"
                >✓ Approve</button>
                <button
                  v-if="c.status === 'PENDING_REVIEW' || c.status === 'ACTIVE'"
                  @click="openReject(c)"
                  class="btn-secondary text-xs text-red-600 hover:bg-red-50"
                >✗ Reject</button>
                <button
                  v-if="c.status === 'ACTIVE'"
                  @click="pause(c)"
                  class="btn-secondary text-xs"
                >⏸ Pause</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Reject modal -->
    <div v-if="rejectModal.open" class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
      <div class="bg-white rounded-2xl p-6 w-full max-w-md shadow-xl">
        <h3 class="font-semibold text-slate-800 mb-3">Reject Campaign</h3>
        <p class="text-sm text-slate-500 mb-4">
          Rejecting: <span class="font-medium text-slate-700">{{ rejectModal.campaign?.name || 'Untitled' }}</span>
        </p>
        <textarea
          v-model="rejectModal.reason"
          placeholder="Reason for rejection (required)..."
          class="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm resize-none h-24 outline-none focus:border-indigo-400"
        ></textarea>
        <div class="flex gap-3 mt-4">
          <button @click="rejectModal.open = false" class="btn-secondary flex-1">Cancel</button>
          <button @click="confirmReject" :disabled="!rejectModal.reason.trim()" class="btn-primary flex-1 disabled:opacity-40">Reject</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const API = import.meta.env.VITE_API_BASE

const campaigns = ref([])
const loading = ref(false)
const statusFilter = ref('PENDING_REVIEW')

const rejectModal = reactive({
  open: false,
  campaign: null,
  reason: '',
})

const statusTabs = [
  { label: 'Pending Review', value: 'PENDING_REVIEW' },
  { label: 'Active', value: 'ACTIVE' },
  { label: 'Paused', value: 'PAUSED' },
  { label: 'Rejected', value: 'REJECTED' },
  { label: 'All', value: '' },
]

const stats = computed(() => ({
  pending:  campaigns.value.filter(c => c.status === 'PENDING_REVIEW').length,
  active:   campaigns.value.filter(c => c.status === 'ACTIVE').length,
  paused:   campaigns.value.filter(c => c.status === 'PAUSED').length,
  rejected: campaigns.value.filter(c => c.status === 'REJECTED').length,
}))

onMounted(() => load())

async function load() {
  loading.value = true
  try {
    const params = statusFilter.value ? `?status=${statusFilter.value}` : ''
    const r = await fetch(`${API}/admin/ad-campaigns${params}`, { headers: authHeaders() })
    if (r.ok) campaigns.value = await r.json()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function approve(campaign) {
  const r = await fetch(`${API}/admin/ad-campaigns/${campaign.id}/approve`, {
    method: 'POST',
    headers: authHeaders(),
  })
  if (r.ok) {
    campaign.status = 'ACTIVE'
  } else {
    const err = await r.json()
    alert(err.detail ?? 'Failed')
  }
}

function openReject(campaign) {
  rejectModal.campaign = campaign
  rejectModal.reason = ''
  rejectModal.open = true
}

async function confirmReject() {
  if (!rejectModal.reason.trim()) return
  const r = await fetch(`${API}/admin/ad-campaigns/${rejectModal.campaign.id}/reject`, {
    method: 'POST',
    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason: rejectModal.reason.trim() }),
  })
  if (r.ok) {
    rejectModal.campaign.status = 'REJECTED'
    rejectModal.campaign.rejection_reason = rejectModal.reason.trim()
    rejectModal.open = false
  } else {
    const err = await r.json()
    alert(err.detail ?? 'Failed')
  }
}

async function pause(campaign) {
  if (!confirm('Pause this campaign?')) return
  const r = await fetch(`${API}/admin/ad-campaigns/${campaign.id}/pause`, {
    method: 'POST',
    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason: 'Paused by admin' }),
  })
  if (r.ok) {
    campaign.status = 'PAUSED'
  }
}

function authHeaders() {
  return { Authorization: `Bearer ${auth.token}` }
}

function formatMinor(minor, currency) {
  if (!minor) return '—'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency || 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  }).format(minor / 100)
}

function statusClass(status) {
  const map = {
    PENDING_REVIEW: 'badge-amber',
    ACTIVE: 'badge-green',
    PAUSED: 'badge-gray',
    REJECTED: 'badge-red',
    DRAFT: 'badge-blue',
    EXPIRED: 'badge-gray',
  }
  return map[status] ?? 'badge-gray'
}
</script>
