<template>
  <div class="space-y-4 p-4">
    <div>
      <h1 class="text-xl font-bold text-slate-800">Matching rules</h1>
      <p class="mt-1 text-xs text-slate-500">Control which published requests enter your supplier queue.</p>
    </div>
    <form v-if="loaded" class="m-card space-y-4" @submit.prevent="save">
      <label class="flex items-center justify-between gap-3 text-sm">
        <span>Matching request alerts</span>
        <input v-model="form.alerts_enabled" type="checkbox" />
      </label>
      <div>
        <label class="mb-1 block text-xs font-semibold text-slate-700">Categories</label>
        <select v-model="form.supplier_category_ids_json" class="m-input min-h-28" multiple>
          <option v-for="item in categories" :key="item.id" :value="item.id">{{ item.name }}</option>
        </select>
      </div>
      <div>
        <label class="mb-1 block text-xs font-semibold text-slate-700">Delivery regions</label>
        <select v-model="form.supplier_region_ids_json" class="m-input min-h-28" multiple>
          <option v-for="item in regions" :key="item.id" :value="item.id">{{ item.name }}</option>
        </select>
      </div>
      <button class="m-btn-primary w-full" :disabled="saving">{{ saving ? 'Saving...' : 'Save rules' }}</button>
      <p v-if="message" class="text-xs text-emerald-600">{{ message }}</p>
      <p v-if="error" class="text-xs text-red-600">{{ error }}</p>
    </form>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: ['auth'] })

const { apiFetch } = useApi()
const { listPublicCategories } = useCommerce()
const loaded = ref(false)
const saving = ref(false)
const message = ref('')
const error = ref('')
const categories = ref<any[]>([])
const regions = ref<any[]>([])
const form = reactive<Record<string, any>>({
  alerts_enabled: true,
  supplier_category_ids_json: [],
  supplier_region_ids_json: [],
})

async function save() {
  saving.value = true
  error.value = ''
  try {
    Object.assign(form, await apiFetch('/portal/notification-preferences', { method: 'PUT', body: form }))
    message.value = 'Matching rules saved.'
  } catch (cause: any) {
    error.value = cause?.data?.detail || cause?.message || 'Rules could not be saved.'
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  try {
    const [preferences, categoryData, regionData] = await Promise.all([
      apiFetch('/portal/notification-preferences'),
      listPublicCategories(),
      apiFetch('/regions'),
    ])
    Object.assign(form, preferences)
    categories.value = categoryData.items
    regions.value = regionData.items
    loaded.value = true
  } catch (cause: any) {
    error.value = cause?.data?.detail || cause?.message || 'Rules could not be loaded.'
  }
})
</script>
