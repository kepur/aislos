<template>
  <div class="space-y-4">
    <div class="card overflow-hidden">
      <table class="w-full">
        <thead>
          <tr>
            <th class="table-th">ID</th>
            <th class="table-th">Held</th>
            <th class="table-th">Captured</th>
            <th class="table-th">Released</th>
            <th class="table-th">Status</th>
            <th class="table-th">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading"><td colspan="6" class="table-td text-center py-10 text-slate-400">Loading…</td></tr>
          <tr v-else-if="!txs.length"><td colspan="6" class="table-td text-center py-10 text-slate-400">No escrow transactions yet</td></tr>
          <tr v-for="tx in txs" :key="tx.id" class="hover:bg-slate-50">
            <td class="table-td font-mono text-xs">{{ tx.id.slice(0,8).toUpperCase() }}</td>
            <td class="table-td font-semibold">{{ fmtPrice(tx.auth_amount_minor, tx.currency) }}</td>
            <td class="table-td">{{ fmtPrice(tx.captured_amount_minor, tx.currency) }}</td>
            <td class="table-td">{{ fmtPrice(tx.released_amount_minor, tx.currency) }}</td>
            <td class="table-td"><span :class="escrowBadge(tx.status)" class="badge">{{ tx.status }}</span></td>
            <td class="table-td">
              <div v-if="['AUTH_HELD','CAPTURED'].includes(tx.status)" class="flex gap-2">
                <button class="btn btn-success py-1 px-3 text-xs" @click="release(tx.id)">Release</button>
                <button class="btn btn-danger py-1 px-3 text-xs" @click="refund(tx.id)">Refund</button>
              </div>
              <span v-else class="text-xs text-slate-400">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api, fmtPrice } from '@/utils/api'

const loading = ref(true)
const txs = ref([])

function escrowBadge(s) {
  return { RELEASED:'badge-green', CAPTURED:'badge-amber', AUTH_HELD:'badge-amber', REFUNDED:'badge-gray', FAILED:'badge-red' }[s] || 'badge-gray'
}

async function release(id) {
  try {
    const { data } = await api.post(`/admin/escrow/${id}/release`, { reason_code:'ADMIN_MANUAL', reason_text:'Admin manual release' })
    const idx = txs.value.findIndex(t => t.id === id)
    if (idx >= 0) txs.value[idx] = { ...txs.value[idx], status: data.status }
  } catch (e) { alert(e.response?.data?.detail || 'Failed') }
}

async function refund(id) {
  if (!confirm('Confirm refund?')) return
  try {
    const { data } = await api.post(`/admin/escrow/${id}/refund`, { reason_code:'ADMIN_MANUAL', reason_text:'Admin manual refund' })
    const idx = txs.value.findIndex(t => t.id === id)
    if (idx >= 0) txs.value[idx] = { ...txs.value[idx], status: data.status }
  } catch (e) { alert(e.response?.data?.detail || 'Failed') }
}

onMounted(async () => {
  txs.value = await api.get('/admin/escrow').then(r => r.data)
  loading.value = false
})
</script>
