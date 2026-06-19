<template>
  <div class="space-y-4">
    <div class="flex items-center gap-3 flex-wrap">
      <select v-model="riskFilter" class="input w-40" @change="load">
        <option value="">All risk levels</option>
        <option value="CRITICAL">🔴 Critical</option>
        <option value="HIGH">🟠 High</option>
        <option value="MEDIUM">🟡 Medium</option>
        <option value="LOW">⚪ Low</option>
      </select>
      <input v-model="actionFilter" type="search" placeholder="Filter action…" class="input max-w-xs" @input="load" />
      <button class="btn btn-secondary ml-auto" @click="load">Refresh</button>
    </div>

    <div class="card overflow-hidden">
      <table class="w-full">
        <thead>
          <tr>
            <th class="table-th w-8"></th>
            <th class="table-th">Action</th>
            <th class="table-th">Entity</th>
            <th class="table-th">Actor Role</th>
            <th class="table-th">Risk</th>
            <th class="table-th">When</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading"><td colspan="6" class="table-td text-center py-10 text-slate-400">Loading…</td></tr>
          <tr v-else-if="!logs.length"><td colspan="6" class="table-td text-center py-10 text-slate-400">No logs found</td></tr>
          <tr v-for="log in logs" :key="log.id" class="hover:bg-slate-50">
            <td class="table-td text-center">{{ riskIcon(log.risk_level) }}</td>
            <td class="table-td font-mono text-xs font-medium">{{ log.action }}</td>
            <td class="table-td text-xs text-slate-500">{{ log.entity_type }}</td>
            <td class="table-td"><span v-if="log.actor_role" class="badge badge-gray">{{ log.actor_role }}</span><span v-else class="text-slate-300">—</span></td>
            <td class="table-td"><span :class="riskBadge(log.risk_level)" class="badge">{{ log.risk_level }}</span></td>
            <td class="table-td text-xs text-slate-400">{{ fmtDatetime(log.created_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="logs.length >= limit" class="text-center">
      <button class="btn btn-secondary" @click="loadMore">Load more</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api, fmtDatetime } from '@/utils/api'

const loading = ref(true)
const logs = ref([])
const riskFilter = ref('')
const actionFilter = ref('')
const limit = ref(100)

function riskIcon(l) { return { CRITICAL:'🔴', HIGH:'🟠', MEDIUM:'🟡', LOW:'⚪' }[l] || '⚪' }
function riskBadge(l) { return { CRITICAL:'badge-red', HIGH:'badge-amber', MEDIUM:'bg-yellow-100 text-yellow-700', LOW:'badge-gray' }[l] || 'badge-gray' }

let debounce = null
async function load() {
  clearTimeout(debounce)
  debounce = setTimeout(async () => {
    loading.value = true
    const p = new URLSearchParams({ limit: limit.value })
    if (riskFilter.value) p.set('risk_level', riskFilter.value)
    if (actionFilter.value) p.set('action', actionFilter.value)
    logs.value = await api.get(`/admin/audit-logs?${p}`).then(r => r.data)
    loading.value = false
  }, 300)
}

async function loadMore() {
  limit.value += 100
  await load()
}

onMounted(load)
</script>
