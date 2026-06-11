<template>
  <div>
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Audit Logs</h1>
        <p class="text-sm text-gray-500 mt-1">Track admin actions across the platform.</p>
      </div>
      <div class="flex gap-2">
        <select v-model="entityTypeFilter" class="input-field max-w-40" @change="loadLogs">
          <option value="">All entities</option>
          <option value="lead">Lead</option>
          <option value="product">Product</option>
          <option value="project">Project</option>
          <option value="vendor">Vendor</option>
          <option value="quote">Quote</option>
          <option value="ticket">Ticket</option>
          <option value="user">User</option>
        </select>
        <select v-model="actionFilter" class="input-field max-w-44" @change="loadLogs">
          <option value="">All actions</option>
          <option value="status_change">Status Change</option>
          <option value="create">Create</option>
          <option value="update">Update</option>
          <option value="delete">Delete</option>
          <option value="assign">Assign</option>
        </select>
      </div>
    </div>

    <div class="bg-white rounded-xl border overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 border-b">
          <tr>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Time</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Action</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Entity</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Actor</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Changes</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="log in logs" :key="log.id" class="border-b align-top">
            <td class="px-4 py-3 text-gray-500 whitespace-nowrap text-xs">
              {{ new Date(log.created_at).toLocaleString() }}
            </td>
            <td class="px-4 py-3">
              <span
                class="px-2 py-0.5 text-xs font-medium rounded-full"
                :class="actionBadgeClass(log.action)"
              >{{ log.action }}</span>
            </td>
            <td class="px-4 py-3">
              <p class="font-medium text-gray-900">{{ log.entity_type }}</p>
              <p v-if="log.entity_id" class="text-xs text-gray-500 font-mono">{{ log.entity_id.slice(0, 8) }}</p>
            </td>
            <td class="px-4 py-3 text-xs">
              <span v-if="log.actor_user_id" class="font-mono text-gray-600">{{ log.actor_user_id.slice(0, 8) }}</span>
              <span v-else class="text-gray-400">system</span>
              <p v-if="log.ip" class="text-gray-400">{{ log.ip }}</p>
            </td>
            <td class="px-4 py-3 max-w-sm">
              <div v-if="log.before_json || log.after_json" class="text-xs">
                <div v-if="log.before_json" class="text-red-600">
                  <span class="font-medium">Before:</span> {{ summarize(log.before_json) }}
                </div>
                <div v-if="log.after_json" class="text-green-600">
                  <span class="font-medium">After:</span> {{ summarize(log.after_json) }}
                </div>
              </div>
              <span v-else class="text-xs text-gray-400">-</span>
            </td>
          </tr>
          <tr v-if="!logs.length">
            <td colspan="5" class="px-4 py-8 text-center text-gray-500">No audit logs found.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div v-if="total > limit" class="mt-4 flex items-center justify-between text-sm">
      <p class="text-gray-500">Showing {{ skip + 1 }}-{{ Math.min(skip + limit, total) }} of {{ total }}</p>
      <div class="flex gap-2">
        <button
          class="px-3 py-1.5 rounded-lg border text-gray-600 hover:bg-gray-50 disabled:opacity-40"
          :disabled="skip === 0"
          @click="skip -= limit; loadLogs()"
        >Previous</button>
        <button
          class="px-3 py-1.5 rounded-lg border text-gray-600 hover:bg-gray-50 disabled:opacity-40"
          :disabled="skip + limit >= total"
          @click="skip += limit; loadLogs()"
        >Next</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'admin' })

const { apiFetch } = useApi()
const logs = ref<any[]>([])
const total = ref(0)
const skip = ref(0)
const limit = 30
const entityTypeFilter = ref('')
const actionFilter = ref('')

function actionBadgeClass(action: string) {
  if (action === 'status_change') return 'bg-blue-100 text-blue-700'
  if (action === 'create') return 'bg-green-100 text-green-700'
  if (action === 'delete') return 'bg-red-100 text-red-700'
  if (action === 'assign') return 'bg-purple-100 text-purple-700'
  return 'bg-gray-100 text-gray-700'
}

function summarize(obj: any) {
  if (!obj) return '-'
  return Object.entries(obj).map(([k, v]) => `${k}: ${v}`).join(', ')
}

async function loadLogs() {
  const params = new URLSearchParams()
  params.set('skip', String(skip.value))
  params.set('limit', String(limit))
  if (entityTypeFilter.value) params.set('entity_type', entityTypeFilter.value)
  if (actionFilter.value) params.set('action', actionFilter.value)
  try {
    const res = await apiFetch<any>(`/audit-logs?${params.toString()}`)
    logs.value = res.items || []
    total.value = res.total || 0
  } catch {
    logs.value = []
    total.value = 0
  }
}

onMounted(loadLogs)
</script>
