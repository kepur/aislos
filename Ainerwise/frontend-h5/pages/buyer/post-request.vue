<template>
  <div class="space-y-4 p-4">
    <div>
      <p class="text-[10px] font-bold uppercase tracking-widest text-indigo-500">AI procurement</p>
      <h1 class="mt-1 text-xl font-bold text-slate-800">Post a request</h1>
    </div>
    <form class="m-card space-y-3" @submit.prevent="submit">
      <input v-model.trim="form.title" required class="m-input" placeholder="What do you need?" />
      <textarea v-model.trim="form.description" required rows="5" class="m-input" placeholder="Quantity, location, date and constraints" />
      <select v-model="form.category_schema_id" class="m-input">
        <option value="">Auto-classify category</option>
        <option v-for="item in categories" :key="item.id" :value="item.id">{{ item.name }}</option>
      </select>
      <select v-model="form.region_id" class="m-input">
        <option value="">Region not decided</option>
        <option v-for="item in regions" :key="item.id" :value="item.id">{{ item.name }}</option>
      </select>
      <p v-if="loadError" class="text-xs text-amber-600">{{ loadError }} <button type="button" class="font-semibold underline" @click="loadOptions">Retry</button></p>
      <label class="flex gap-2 text-xs text-slate-500"><input v-model="publishNow" type="checkbox" /> Publish immediately</label>
      <p v-if="error" class="text-xs text-red-600">{{ error }}</p>
      <button class="m-btn-primary">Create request</button>
    </form>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: ['auth'] })

const api = useCommerce()
const { apiFetch } = useApi()
const categories = ref<any[]>([])
const regions = ref<any[]>([])
const publishNow = ref(true)
const error = ref('')
const loadError = ref('')
const form = reactive({ title: '', description: '', category_schema_id: '', region_id: '' })

async function submit() {
  try {
    const row = await api.createProcurementRequest({
      ...form,
      category_schema_id: form.category_schema_id || undefined,
      region_id: form.region_id || undefined,
    })
    if (publishNow.value) await api.publishRequest(row.id)
    await navigateTo(`/buyer/requests/${row.id}`)
  } catch (cause: any) {
    error.value = cause?.data?.detail || cause?.message
  }
}

async function loadOptions() {
  loadError.value = ''
  try {
    const [categoryData, regionData] = await Promise.all([api.listPublicCategories(), apiFetch<any>('/regions')])
    categories.value = categoryData.items
    regions.value = regionData.items
  } catch (cause: any) {
    loadError.value = cause?.data?.detail || cause?.message || 'Unable to load matching options.'
  }
}

onMounted(loadOptions)
</script>
