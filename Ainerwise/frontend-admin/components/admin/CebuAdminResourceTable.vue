<template>
  <div class="space-y-5">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="admin-page-title">{{ title }}</h1>
        <p class="admin-page-desc">Unified Core data · Cebu compatibility workbench</p>
      </div>
      <button class="btn-secondary" :disabled="loading" @click="load">{{ loading ? 'Loading…' : 'Refresh' }}</button>
    </div>
    <p v-if="error" class="text-sm text-red-400">{{ error }}</p>
    <div class="admin-panel overflow-x-auto">
      <table class="admin-table min-w-full text-sm">
        <thead>
          <tr>
            <th v-for="column in columns" :key="column.key">{{ column.label }}</th>
            <th v-if="statusPath">Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td v-for="column in columns" :key="column.key">
              <StatusBadge v-if="column.badge" :status="String(item[column.key] ?? '-')" />
              <span v-else>{{ display(item[column.key]) }}</span>
            </td>
            <td v-if="statusPath">
              <select
                class="input-field min-w-32"
                :value="item[statusField]"
                @change="changeStatus(item, ($event.target as HTMLSelectElement).value)"
              >
                <option v-for="option in statusOptions" :key="option" :value="option">{{ option }}</option>
              </select>
            </td>
          </tr>
          <tr v-if="!loading && !items.length">
            <td :colspan="columns.length + (statusPath ? 1 : 0)" class="py-8 text-center text-slate-400">No Core records</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
type Column = { key: string; label: string; badge?: boolean }
const props = withDefaults(defineProps<{
  title: string
  endpoint: string
  columns: Column[]
  statusPath?: string
  statusField?: string
  statusBodyKey?: string
  statusOptions?: string[]
}>(), {
  statusPath: '',
  statusField: 'status',
  statusBodyKey: 'status',
  statusOptions: () => [],
})
const { apiFetch } = useApi()
const items = ref<any[]>([])
const loading = ref(false)
const error = ref('')

function display(value: any) {
  if (value == null || value === '') return '-'
  if (typeof value === 'object') return JSON.stringify(value)
  if (typeof value === 'string' && /^\d{4}-\d\d-\d\dT/.test(value)) return new Date(value).toLocaleString()
  return String(value)
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const response = await apiFetch<any>(props.endpoint)
    items.value = response.items || []
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Load failed'
  } finally {
    loading.value = false
  }
}

async function changeStatus(item: any, status: string) {
  if (!props.statusPath || status === item[props.statusField]) return
  error.value = ''
  try {
    const path = props.statusPath.replace('{id}', item.id)
    const updated = await apiFetch<any>(path, {
      method: 'PATCH',
      body: { [props.statusBodyKey]: status, reason: 'Cebu Admin workbench update' },
    })
    Object.assign(item, updated)
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Update failed'
    await load()
  }
}

onMounted(load)
</script>
