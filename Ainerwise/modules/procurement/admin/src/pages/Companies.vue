<template>
  <div class="space-y-4">
    <div v-if="queue.length" class="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 flex items-center gap-3">
      <span>⚠️</span>
      <p class="text-sm text-amber-800 font-medium">{{ queue.length }} company verification{{ queue.length > 1 ? 's' : '' }} pending review</p>
    </div>

    <div class="card overflow-hidden">
      <table class="w-full">
        <thead>
          <tr>
            <th class="table-th">Company</th>
            <th class="table-th">Location</th>
            <th class="table-th">Verification</th>
            <th class="table-th">Status</th>
            <th class="table-th">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading"><td colspan="5" class="table-td text-center py-10 text-slate-400">Loading…</td></tr>
          <tr v-else-if="!companies.length"><td colspan="5" class="table-td text-center py-10 text-slate-400">No companies yet</td></tr>
          <tr v-for="co in companies" :key="co.id" class="hover:bg-slate-50">
            <td class="table-td">
              <p class="font-medium text-slate-900">{{ co.name }}</p>
              <p class="text-xs text-slate-400">{{ fmtDate(co.created_at) }}</p>
            </td>
            <td class="table-td text-slate-500">{{ co.city }}, {{ co.country }}</td>
            <td class="table-td">
              <select class="input py-1 text-xs w-32" :value="co.verification_level" @change="setVerif(co.id, $event.target.value)">
                <option v-for="l in verifLevels" :key="l" :value="l">{{ l }}</option>
              </select>
            </td>
            <td class="table-td"><span :class="co.status === 'ACTIVE' ? 'badge-green' : 'badge-red'" class="badge">{{ co.status }}</span></td>
            <td class="table-td">
              <button v-if="co.status === 'ACTIVE'" class="btn btn-danger py-1 px-3 text-xs" @click="setStatus(co.id, 'SUSPENDED')">Suspend</button>
              <button v-else class="btn btn-success py-1 px-3 text-xs" @click="setStatus(co.id, 'ACTIVE')">Activate</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api, fmtDate } from '@/utils/api'

const loading = ref(true)
const companies = ref([])
const queue = ref([])
const verifLevels = ['NONE', 'BASIC', 'BUSINESS', 'PREMIUM']

async function setVerif(id, level) {
  try {
    const { data } = await api.patch(`/admin/companies/${id}/verification?level=${level}`)
    const idx = companies.value.findIndex(c => c.id === id)
    if (idx >= 0) companies.value[idx] = data
  } catch (e) { alert(e.response?.data?.detail || 'Failed') }
}

async function setStatus(id, status) {
  try {
    const { data } = await api.patch(`/admin/companies/${id}/status?status=${status}`)
    const idx = companies.value.findIndex(c => c.id === id)
    if (idx >= 0) companies.value[idx] = data
  } catch (e) { alert(e.response?.data?.detail || 'Failed') }
}

onMounted(async () => {
  const [cos, q] = await Promise.all([
    api.get('/admin/companies').then(r => r.data),
    api.get('/admin/verification/queue').then(r => r.data),
  ])
  companies.value = cos
  queue.value = q
  loading.value = false
})
</script>
