<template>
  <div>
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-6">
      <div>
        <h1 class="admin-page-title">AI Runs</h1>
        <p class="admin-page-desc">Stored lead analysis workflows for admin review.</p>
      </div>
      <select v-model="statusFilter" class="input-field max-w-44" @change="loadRuns">
        <option value="">All statuses</option>
        <option value="running">Running</option>
        <option value="completed">Completed</option>
        <option value="failed">Failed</option>
      </select>
    </div>

    <div class="admin-panel">
      <table class="admin-table w-full text-sm">
        <thead>
          <tr>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Workflow</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Entity</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Model</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Status</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Result</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Created</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="run in runs" :key="run.id" class="border-b align-top">
            <td class="px-4 py-3">
              <p class="font-medium text-gray-900">{{ run.workflow_name }}</p>
              <p class="text-xs text-gray-500 font-mono">{{ run.id.slice(0, 8) }}</p>
            </td>
            <td class="px-4 py-3">
              <NuxtLink
                v-if="run.entity_type === 'lead'"
                :to="`leads/${run.entity_id}`"
                class="text-primary-600 hover:underline"
              >
                lead/{{ run.entity_id.slice(0, 8) }}
              </NuxtLink>
              <span v-else>{{ run.entity_type }}/{{ run.entity_id.slice(0, 8) }}</span>
            </td>
            <td class="px-4 py-3 text-gray-600">{{ run.model_name || '-' }}</td>
            <td class="px-4 py-3"><StatusBadge :status="run.status" /></td>
            <td class="px-4 py-3 max-w-sm">
              <div v-if="run.output_json" class="space-y-1">
                <p class="font-medium text-gray-900">
                  {{ run.output_json.classification?.project_class || 'Analysis completed' }}
                </p>
                <p class="text-xs text-gray-500">
                  Completeness: {{ run.output_json.completeness?.score ?? '-' }}%
                </p>
                <p class="text-xs text-gray-600 line-clamp-2">
                  {{ run.output_json.recommended_next_action }}
                </p>
              </div>
              <p v-else-if="run.error_message" class="text-xs text-red-600">{{ run.error_message }}</p>
              <p v-else class="text-xs text-gray-500">No output yet.</p>
            </td>
            <td class="px-4 py-3 text-gray-500 whitespace-nowrap">
              {{ new Date(run.created_at).toLocaleString() }}
            </td>
          </tr>
          <tr v-if="!runs.length">
            <td colspan="6" class="px-4 py-8 text-center text-gray-500">No AI runs yet.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { apiFetch } = useApi()
const runs = ref<any[]>([])
const statusFilter = ref('')

async function loadRuns() {
  const params = statusFilter.value ? `?status=${statusFilter.value}` : ''
  try {
    const res = await apiFetch<any>(`/ai-runs${params}`)
    runs.value = res.items || []
  } catch (e) {
    runs.value = []
  }
}

onMounted(loadRuns)
</script>
