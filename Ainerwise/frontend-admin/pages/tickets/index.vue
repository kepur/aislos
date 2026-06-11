<template>
  <div>
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-6">
      <div>
        <h1 class="admin-page-title">Support Tickets</h1>
        <p class="admin-page-desc">Manage buyer support requests.</p>
      </div>
      <select v-model="statusFilter" class="input-field max-w-40" @change="loadTickets">
        <option value="">All statuses</option>
        <option value="open">Open</option>
        <option value="in_progress">In Progress</option>
        <option value="resolved">Resolved</option>
        <option value="closed">Closed</option>
      </select>
    </div>

    <div class="admin-panel">
      <table class="admin-table w-full text-sm">
        <thead>
          <tr>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Ticket</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Type</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Priority</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Status</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Created</th>
            <th class="text-right px-4 py-3 font-medium text-gray-500">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="ticket in tickets" :key="ticket.id" class="border-b">
            <td class="px-4 py-3">
              <p class="font-medium text-gray-900">{{ ticket.title }}</p>
              <p class="text-xs text-gray-500 font-mono">{{ ticket.id.slice(0, 8) }}</p>
            </td>
            <td class="px-4 py-3 text-gray-600">{{ ticket.issue_type || '-' }}</td>
            <td class="px-4 py-3">
              <span
                class="px-2 py-0.5 text-xs font-medium rounded-full"
                :class="priorityClass(ticket.priority)"
              >{{ ticket.priority || 'normal' }}</span>
            </td>
            <td class="px-4 py-3"><StatusBadge :status="ticket.status" /></td>
            <td class="px-4 py-3 text-gray-500 whitespace-nowrap">{{ new Date(ticket.created_at).toLocaleDateString() }}</td>
            <td class="px-4 py-3 text-right">
              <div class="flex justify-end gap-1">
                <button
                  v-if="ticket.status === 'open'"
                  class="px-2 py-1 text-xs font-medium rounded bg-blue-100 text-blue-700 hover:bg-blue-200"
                  @click="changeStatus(ticket.id, 'in_progress')"
                >Start</button>
                <button
                  v-if="ticket.status === 'in_progress'"
                  class="px-2 py-1 text-xs font-medium rounded bg-green-100 text-green-700 hover:bg-green-200"
                  @click="changeStatus(ticket.id, 'resolved')"
                >Resolve</button>
                <button
                  v-if="ticket.status === 'resolved'"
                  class="px-2 py-1 text-xs font-medium rounded bg-gray-100 text-gray-700 hover:bg-gray-200"
                  @click="changeStatus(ticket.id, 'closed')"
                >Close</button>
                <button
                  v-if="ticket.status === 'resolved' || ticket.status === 'closed'"
                  class="px-2 py-1 text-xs font-medium rounded bg-yellow-100 text-yellow-700 hover:bg-yellow-200"
                  @click="changeStatus(ticket.id, 'open')"
                >Reopen</button>
              </div>
            </td>
          </tr>
          <tr v-if="!tickets.length">
            <td colspan="6" class="px-4 py-8 text-center text-gray-500">No tickets found.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { apiFetch } = useApi()
const tickets = ref<any[]>([])
const statusFilter = ref('')

function priorityClass(priority: string) {
  if (priority === 'urgent') return 'bg-red-100 text-red-700'
  if (priority === 'high') return 'bg-orange-100 text-orange-700'
  if (priority === 'low') return 'bg-gray-100 text-gray-500'
  return 'bg-blue-100 text-blue-700'
}

async function loadTickets() {
  const params = statusFilter.value ? `?status=${statusFilter.value}` : ''
  try {
    const res = await apiFetch<any>(`/tickets${params}`)
    tickets.value = res.items || []
  } catch {
    tickets.value = []
  }
}

async function changeStatus(id: string, newStatus: string) {
  try {
    await apiFetch(`/tickets/${id}/status`, { method: 'PATCH', body: { status: newStatus } })
    await loadTickets()
  } catch (e: any) {
    console.error('Status update failed:', e)
  }
}

onMounted(loadTickets)
</script>
