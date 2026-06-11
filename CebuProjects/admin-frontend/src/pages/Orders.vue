<template>
  <div class="space-y-4">
    <div class="card overflow-hidden">
      <table class="w-full">
        <thead>
          <tr>
            <th class="table-th">Order ID</th>
            <th class="table-th">Amount</th>
            <th class="table-th">Status</th>
            <th class="table-th">Created</th>
            <th class="table-th">Change Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading"><td colspan="5" class="table-td text-center py-10 text-slate-400">Loading…</td></tr>
          <tr v-else-if="!orders.length"><td colspan="5" class="table-td text-center py-10 text-slate-400">No orders yet</td></tr>
          <tr v-for="o in orders" :key="o.id" class="hover:bg-slate-50">
            <td class="table-td font-mono text-xs text-slate-600">#{{ o.id.slice(0,8).toUpperCase() }}</td>
            <td class="table-td font-semibold">{{ fmtPrice(o.total_amount_minor, o.currency) }}</td>
            <td class="table-td"><span :class="orderBadge(o.status)" class="badge">{{ o.status }}</span></td>
            <td class="table-td text-slate-400 text-xs">{{ fmtDate(o.created_at) }}</td>
            <td class="table-td">
              <select class="input py-1 text-xs w-40" :value="o.status" @change="changeStatus(o.id, $event.target.value)">
                <option v-for="s in statuses" :key="s" :value="s">{{ s }}</option>
              </select>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api, fmtDate, fmtPrice } from '@/utils/api'

const loading = ref(true)
const orders = ref([])
const statuses = ['PAID_IN_ESCROW','IN_PROGRESS','DELIVERED','ACCEPTED','PAYOUT_RELEASED','DISPUTED','CANCELED','REFUNDED']

function orderBadge(s) {
  const m = { PAID_IN_ESCROW:'badge-amber', IN_PROGRESS:'badge-blue', DELIVERED:'badge-green', ACCEPTED:'badge-green', PAYOUT_RELEASED:'badge-green', DISPUTED:'badge-red', CANCELED:'badge-gray', REFUNDED:'badge-gray' }
  return m[s] || 'badge-gray'
}

async function changeStatus(id, status) {
  try {
    const { data } = await api.post(`/admin/orders/${id}/status`, { status })
    const idx = orders.value.findIndex(o => o.id === id)
    if (idx >= 0) orders.value[idx] = data
  } catch (e) { alert(e.response?.data?.detail || 'Failed') }
}

onMounted(async () => {
  orders.value = await api.get('/admin/orders').then(r => r.data)
  loading.value = false
})
</script>
