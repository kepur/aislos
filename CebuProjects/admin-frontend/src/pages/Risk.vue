<template>
  <div class="space-y-4">
    <div class="flex items-center gap-3 flex-wrap">
      <select v-model="statusFilter" class="input w-40" @change="load">
        <option value="">All status</option>
        <option value="OPEN">Open</option>
        <option value="IN_REVIEW">In Review</option>
        <option value="MITIGATED">Mitigated</option>
        <option value="FALSE_POSITIVE">False Positive</option>
        <option value="ACTION_TAKEN">Action Taken</option>
        <option value="CLOSED">Closed</option>
      </select>
      <select v-model="entityFilter" class="input w-36" @change="load">
        <option value="">All entities</option>
        <option value="USER">User</option>
        <option value="COMPANY">Company</option>
        <option value="ORDER">Order</option>
      </select>
      <span class="ml-auto text-sm text-slate-500">{{ flags.length }} flags</span>
      <button class="btn btn-primary" @click="showCreate=true">+ Create Flag</button>
    </div>

    <div class="card overflow-hidden">
      <table class="w-full">
        <thead><tr>
          <th class="table-th">Entity</th>
          <th class="table-th">Risk Type</th>
          <th class="table-th">Level</th>
          <th class="table-th">Status</th>
          <th class="table-th">Created</th>
          <th class="table-th">Actions</th>
        </tr></thead>
        <tbody>
          <tr v-if="loading"><td colspan="6" class="table-td text-center py-10 text-slate-400">Loading…</td></tr>
          <tr v-else-if="!flags.length"><td colspan="6" class="table-td text-center py-10 text-slate-400">No risk flags</td></tr>
          <tr v-for="f in flags" :key="f.id" class="hover:bg-slate-50">
            <td class="table-td">
              <p class="text-xs text-slate-500">{{ f.entity_type }}</p>
              <p class="font-mono text-xs">{{ f.entity_id?.slice(0,8) }}</p>
            </td>
            <td class="table-td text-xs">{{ f.risk_type?.replace(/_/g,' ') }}</td>
            <td class="table-td"><span :class="levelBadge(f.risk_level)" class="badge">{{ f.risk_level }}</span></td>
            <td class="table-td"><span :class="statBadge(f.status)" class="badge">{{ f.status?.replace(/_/g,' ') }}</span></td>
            <td class="table-td text-xs text-slate-400">{{ fmtDate(f.created_at) }}</td>
            <td class="table-td">
              <div class="flex gap-1" v-if="f.status==='OPEN' || f.status==='IN_REVIEW'">
                <button class="btn btn-secondary py-1 px-2 text-xs" @click="action(f.id,'IN_REVIEW')">Review</button>
                <button class="btn btn-success py-1 px-2 text-xs" @click="action(f.id,'MITIGATED')">Mitigate</button>
                <button class="btn badge-gray py-1 px-2 text-xs" @click="action(f.id,'FALSE_POSITIVE')">False +</button>
              </div>
              <span v-else class="text-xs text-slate-400">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create Flag Modal -->
    <div v-if="showCreate" class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" @click.self="showCreate=false">
      <div class="bg-white rounded-2xl w-full max-w-md p-6 space-y-4">
        <h3 class="font-bold text-lg text-slate-900">Create Risk Flag</h3>
        <select v-model="form.entity_type" class="input">
          <option value="USER">User</option>
          <option value="COMPANY">Company</option>
          <option value="ORDER">Order</option>
        </select>
        <input v-model="form.entity_id" class="input" placeholder="Entity ID (UUID)" />
        <select v-model="form.risk_type" class="input">
          <option v-for="rt in riskTypes" :key="rt" :value="rt">{{ rt.replace(/_/g,' ') }}</option>
        </select>
        <select v-model="form.risk_level" class="input">
          <option value="LOW">Low</option>
          <option value="MEDIUM">Medium</option>
          <option value="HIGH">High</option>
          <option value="CRITICAL">Critical</option>
        </select>
        <textarea v-model="form.description" class="input" rows="3" placeholder="Description (optional)"></textarea>
        <div class="flex gap-3">
          <button class="btn btn-secondary flex-1" @click="showCreate=false">Cancel</button>
          <button class="btn btn-primary flex-1" @click="create">Create</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { api, fmtDate } from '@/utils/api'

const loading = ref(true)
const flags = ref([])
const statusFilter = ref('')
const entityFilter = ref('')
const showCreate = ref(false)

const riskTypes = ['SUSPICIOUS_PRICE_LOW','SUSPICIOUS_PRICE_HIGH','NEW_SUPPLIER_HIGH_VALUE_ORDER','HIGH_DISPUTE_RATE','REPEATED_CANCELLATION','FAILED_LOGIN_SPIKE','DEVICE_MULTI_ACCOUNT','POSSIBLE_COUNTERFEIT','PAYMENT_MISMATCH','USDT_UNCONFIRMED','MANUAL_BANK_RECEIPT_SUSPICIOUS','OFF_PLATFORM_DEAL_ATTEMPT','OTHER']

const form = reactive({ entity_type:'USER', entity_id:'', risk_type:'OTHER', risk_level:'MEDIUM', description:'' })

function levelBadge(l) {
  return { LOW:'badge-gray', MEDIUM:'badge-amber', HIGH:'badge-red', CRITICAL:'badge-red' }[l] || 'badge-gray'
}
function statBadge(s) {
  return { OPEN:'badge-red', IN_REVIEW:'badge-amber', MITIGATED:'badge-green', FALSE_POSITIVE:'badge-gray', ACTION_TAKEN:'badge-blue', CLOSED:'badge-gray' }[s] || 'badge-gray'
}

async function load() {
  loading.value = true
  const params = {}
  if (statusFilter.value) params.status = statusFilter.value
  if (entityFilter.value) params.entity_type = entityFilter.value
  try {
    flags.value = await api.get('/admin/risk-flags', { params }).then(r => r.data)
  } catch { flags.value = [] }
  loading.value = false
}

async function action(id, status) {
  const actionTaken = prompt('Action note (optional):') || ''
  try {
    await api.post(`/admin/risk-flags/${id}/action`, { status, action_taken: actionTaken || null })
    await load()
  } catch (e) { alert(e.response?.data?.detail || 'Failed') }
}

async function create() {
  try {
    await api.post('/admin/risk-flags', {
      entity_type: form.entity_type,
      entity_id: form.entity_id,
      risk_type: form.risk_type,
      risk_level: form.risk_level,
      description: form.description || null
    })
    showCreate.value = false
    form.entity_id = ''; form.description = ''
    await load()
  } catch (e) { alert(e.response?.data?.detail || 'Failed') }
}

onMounted(load)
</script>
