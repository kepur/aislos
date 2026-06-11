<template>
  <div>
    <NuxtLink to="products" class="text-sm text-primary-600 hover:underline">&larr; Back to Products</NuxtLink>
    <h1 class="admin-page-title mt-4 mb-6">Create Product</h1>

    <form class="max-w-3xl space-y-6" @submit.prevent="handleSubmit">
      <div class="admin-card space-y-4">
        <h2 class="admin-section-title">Basic Information</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Name *</label>
            <input v-model="form.name" type="text" required class="input-field" placeholder="Product name" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Brand</label>
            <input v-model="form.brand" type="text" class="input-field" placeholder="Brand name" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Category</label>
            <select v-model="form.category_id" class="input-field">
              <option value="">No category</option>
              <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Source Type</label>
            <select v-model="form.source_type" class="input-field">
              <option value="official">Official</option>
              <option value="verified_supplier">Verified Supplier</option>
              <option value="marketplace">Marketplace</option>
            </select>
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
          <textarea v-model="form.description" rows="4" class="input-field" placeholder="Product description..." />
        </div>
      </div>

      <div class="admin-card space-y-4">
        <h2 class="admin-section-title">Pricing & Logistics</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">List Price</label>
            <input v-model.number="form.list_price" type="number" step="0.01" class="input-field" placeholder="0.00" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Currency</label>
            <select v-model="form.currency" class="input-field">
              <option value="EUR">EUR</option>
              <option value="USD">USD</option>
              <option value="RSD">RSD</option>
              <option value="CNY">CNY</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">MOQ</label>
            <input v-model.number="form.moq" type="number" min="1" class="input-field" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Lead Time (days)</label>
            <input v-model.number="form.lead_time_days" type="number" class="input-field" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Warranty (years)</label>
            <input v-model.number="form.warranty_years" type="number" class="input-field" />
          </div>
          <div class="flex items-end">
            <label class="flex items-center gap-2 text-sm">
              <input v-model="form.service_available" type="checkbox" class="rounded border-gray-300" />
              Local Service Available
            </label>
          </div>
        </div>
      </div>

      <div class="flex gap-3">
        <button type="submit" :disabled="loading" class="btn-primary text-sm">
          {{ loading ? 'Creating...' : 'Create Product' }}
        </button>
        <NuxtLink to="products" class="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50">Cancel</NuxtLink>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { apiFetch } = useApi()
const loading = ref(false)
const categories = ref<any[]>([])

const form = reactive({
  name: '',
  brand: '',
  category_id: '',
  source_type: 'official',
  description: '',
  list_price: null as number | null,
  currency: 'EUR',
  moq: 1,
  lead_time_days: null as number | null,
  warranty_years: null as number | null,
  service_available: false,
})

onMounted(async () => {
  try {
    const res = await apiFetch<any>('/product-categories')
    categories.value = res.items || res || []
  } catch {}
})

async function handleSubmit() {
  loading.value = true
  try {
    const payload: Record<string, any> = { ...form }
    if (!payload.category_id) delete payload.category_id
    await apiFetch('/products', { method: 'POST', body: payload })
    navigateTo('products')
  } catch (e: any) {
    console.error('Create failed:', e)
  } finally {
    loading.value = false
  }
}
</script>
