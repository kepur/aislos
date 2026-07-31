<template>
  <div class="space-y-5">
    <div class="flex items-center justify-between gap-3">
      <div>
        <h1 class="admin-page-title">{{ title }}</h1>
        <p class="admin-page-desc">Cebu trade data migrated into AinerWise Core</p>
      </div>
      <button class="btn-secondary" :disabled="loading" @click="load">Refresh</button>
    </div>
    <p v-if="error" class="text-sm text-red-400">{{ error }}</p>
    <div class="grid gap-3 md:grid-cols-3">
      <article v-for="item in items" :key="item.id" class="admin-panel p-4 text-sm">
        <p class="font-semibold text-white">{{ item.title || item.name || item.id }}</p>
        <p v-for="field in summaryFields" :key="field" class="mt-1 text-slate-400">
          <span class="text-slate-500">{{ field }}:</span> {{ display(item[field]) }}
        </p>
      </article>
      <p v-if="!loading && !items.length" class="text-sm text-slate-400">No Core records</p>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ title: string; section: string; summaryFields: string[] }>()
const { apiFetch } = useApi()
const items = ref<any[]>([])
const loading = ref(false)
const error = ref('')
const display = (value: any) => value == null ? '-' : typeof value === 'object' ? JSON.stringify(value) : String(value)
async function load() {
  loading.value = true
  error.value = ''
  try {
    const response = await apiFetch<any>('/admin/cebu/trade')
    items.value = response[props.section]?.items || []
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Load failed'
  } finally {
    loading.value = false
  }
}
onMounted(load)
</script>
