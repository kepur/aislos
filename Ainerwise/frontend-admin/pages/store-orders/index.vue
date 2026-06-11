<template>
  <div>
    <div class="mb-6">
      <h1 class="admin-page-title">Ainerwise Store Requests</h1>
      <p class="admin-page-desc">Review product intent, compatibility and service needs before issuing any formal quote. No customer funds are handled here.</p>
    </div>
    <div class="admin-panel">
      <table class="admin-table">
        <thead><tr><th>Request</th><th>Items</th><th>Reference subtotal</th><th>Status</th><th>Next action</th></tr></thead>
        <tbody>
          <tr v-for="order in orders" :key="order.id">
            <td><p class="text-white font-medium">{{ order.id.slice(0, 8) }}</p><p class="text-xs">{{ new Date(order.created_at).toLocaleString() }}</p></td>
            <td><p v-for="item in order.items" :key="item.id" class="text-xs">{{ item.product_name }} × {{ item.quantity }}</p></td>
            <td class="font-medium text-white">{{ order.subtotal }} {{ order.currency }}</td>
            <td><StatusBadge :status="order.status" /></td>
            <td>
              <div class="flex flex-wrap gap-2">
                <button v-for="next in transitions[order.status] || []" :key="next" class="rounded bg-cyan-500/15 px-2 py-1 text-xs text-cyan-300 hover:bg-cyan-500/25" @click.stop="changeStatus(order, next)">
                  {{ next }}
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="!orders.length" class="p-8 text-center text-sm text-slate-400">No Store requests yet.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })
const { apiFetch } = useApi()
const orders = ref<any[]>([])
const transitions: Record<string, string[]> = {
  requested: ['reviewing', 'cancelled'],
  reviewing: ['quoted', 'cancelled'],
  quoted: ['confirmed', 'cancelled'],
}
async function load() {
  const res = await apiFetch<any>('/admin/store/orders')
  orders.value = res.items || []
}
async function changeStatus(order: any, status: string) {
  await apiFetch(`/admin/store/orders/${order.id}/status`, { method: 'PATCH', body: { status } })
  await load()
}
onMounted(load)
</script>
