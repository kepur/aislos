<template>
  <div class="space-y-4">
    <!-- Filters -->
    <div class="flex items-center gap-3 flex-wrap">
      <select v-model="statusFilter" class="input w-40" @change="load">
        <option value="">{{ t('common.allStatus') }}</option>
        <option value="OPEN">Open</option>
        <option value="UNDER_REVIEW">Under Review</option>
        <option value="RESOLVED">Resolved</option>
        <option value="DISMISSED">Dismissed</option>
      </select>
      <span class="ml-auto text-sm text-slate-500">{{ disputes.length }} {{ t('nav.disputes') }}</span>
    </div>

    <div v-if="!loading && !disputes.length" class="card p-12 text-center">
      <p class="text-3xl mb-3">✅</p>
      <p class="font-medium text-slate-700">{{ t('disputes.noDisputes') }}</p>
    </div>

    <div v-else class="space-y-4">
      <div v-if="loading" v-for="n in 3" :key="n" class="card p-5 animate-pulse"><div class="h-4 bg-slate-100 rounded w-1/2 mb-2"></div><div class="h-3 bg-slate-100 rounded w-3/4"></div></div>

      <div v-for="d in disputes" :key="d.id" class="card p-5">
        <div class="flex items-start justify-between mb-3">
          <div>
            <p class="font-semibold text-slate-900">Dispute #{{ d.id.slice(0,8).toUpperCase() }}</p>
            <p class="text-xs text-slate-400 mt-0.5">{{ t('orders.order') }}: {{ d.order_id?.slice?.(0,8).toUpperCase() }} · {{ fmtRelative(d.created_at) }}</p>
          </div>
          <span :class="disputeBadge(d.status)" class="badge">{{ d.status }}</span>
        </div>

        <!-- Dispute details -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-4">
          <div><p class="text-xs text-slate-400">{{ t('disputes.reason') }}</p><p class="font-medium">{{ (d.reason||'').replace(/_/g,' ') }}</p></div>
          <div><p class="text-xs text-slate-400">{{ t('disputes.filedBy') }}</p><p class="font-medium">{{ d.filed_by_role || d.opened_by_user_id?.slice(0,8) || '—' }}</p></div>
          <div v-if="d.resolution"><p class="text-xs text-slate-400">{{ t('disputes.resolution') }}</p><p class="font-medium">{{ d.resolution }}</p></div>
          <div v-if="d.resolved_at"><p class="text-xs text-slate-400">{{ t('disputes.resolved') }}</p><p class="font-medium">{{ fmtRelative(d.resolved_at) }}</p></div>
        </div>

        <!-- Evidence section -->
        <div v-if="d._evidence" class="mb-4 bg-slate-50 rounded-lg p-3 space-y-2">
          <p class="text-xs font-semibold text-slate-600 uppercase">{{ t('disputes.evidence') }} ({{ d._evidence.length }})</p>
          <div v-for="(ev, idx) in d._evidence" :key="idx" class="flex items-center gap-2 text-xs">
            <span>📎</span>
            <span class="text-slate-700 flex-1">{{ ev.description || ev.file_url || 'Attachment' }}</span>
            <span class="text-slate-400">{{ ev.submitted_by_role || '—' }}</span>
            <a v-if="ev.file_url" :href="ev.file_url" target="_blank" class="text-primary-600 font-medium hover:underline">{{ t('common.view') }}</a>
          </div>
          <p v-if="!d._evidence.length" class="text-xs text-slate-400">{{ t('disputes.noEvidence') }}</p>
        </div>

        <!-- Action buttons for open disputes -->
        <div v-if="['OPEN','UNDER_REVIEW'].includes(d.status)" class="pt-3 border-t border-slate-100 space-y-3">
          <div class="flex gap-2 items-center flex-wrap">
            <button class="btn btn-secondary text-xs py-1.5 px-3" @click="requestEvidence(d.id, 'BUYER')">{{ t('disputes.requestBuyerEvidence') }}</button>
            <button class="btn btn-secondary text-xs py-1.5 px-3" @click="requestEvidence(d.id, 'SUPPLIER')">{{ t('disputes.requestSupplierEvidence') }}</button>
            <button v-if="!d._evidence" class="btn badge-blue text-xs py-1.5 px-3" @click="loadEvidence(d)">{{ t('disputes.loadEvidence') }}</button>
          </div>
          <div class="flex gap-2">
            <button class="btn btn-success flex-1 text-xs py-2" @click="resolve(d.id, 'BUYER_FAVOR')">{{ t('disputes.favorBuyer') }}</button>
            <button class="btn btn-primary flex-1 text-xs py-2" @click="resolve(d.id, 'SUPPLIER_FAVOR')">{{ t('disputes.favorSupplier') }}</button>
            <button class="btn bg-amber-500 text-white hover:bg-amber-600 flex-1 text-xs py-2" @click="resolve(d.id, 'SPLIT')">{{ t('disputes.split') }}</button>
            <button class="btn btn-secondary flex-1 text-xs py-2" @click="resolve(d.id, 'DISMISSED')">{{ t('common.dismiss') }}</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { api, fmtRelative } from '@/utils/api'

const { t } = useI18n()
const loading = ref(true)
const disputes = ref([])
const statusFilter = ref('')

function disputeBadge(s) {
  return { OPEN:'badge-red', UNDER_REVIEW:'badge-amber', RESOLVED:'badge-green', DISMISSED:'badge-gray' }[s] || 'badge-gray'
}

async function load() {
  loading.value = true
  const p = statusFilter.value ? `?status=${statusFilter.value}` : ''
  try {
    disputes.value = await api.get(`/admin/disputes${p}`).then(r => r.data)
  } catch { disputes.value = [] }
  loading.value = false
}

async function loadEvidence(d) {
  try {
    const { data } = await api.get(`/admin/disputes/${d.id}`)
    const raw = data.evidence_json
    d._evidence = Array.isArray(raw) ? raw : (raw ? JSON.parse(raw) : [])
  } catch { d._evidence = [] }
}

async function requestEvidence(id, party) {
  try {
    await api.post(`/admin/disputes/${id}/request-evidence?from_party=${party}`)
    alert(t('disputes.evidenceSent', { party: party.toLowerCase() }))
  } catch (e) { alert(e.response?.data?.detail || 'Failed') }
}

async function resolve(id, decision) {
  const resolution = prompt(t('disputes.resolutionNote')) || `Admin resolved as ${decision}`
  try {
    const { data } = await api.post(`/admin/disputes/${id}/resolve?decision=${decision}&resolution=${encodeURIComponent(resolution)}`)
    const idx = disputes.value.findIndex(d => d.id === id)
    if (idx >= 0) disputes.value[idx] = data
  } catch (e) { alert(e.response?.data?.detail || 'Failed') }
}

onMounted(load)
</script>
