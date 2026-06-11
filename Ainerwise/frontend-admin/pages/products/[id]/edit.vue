<template>
  <div v-if="product">
    <NuxtLink to="products" class="text-sm text-primary-600 hover:underline">&larr; Back to Products</NuxtLink>
    <h1 class="admin-page-title mt-4 mb-6">Edit Product</h1>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <form class="lg:col-span-2 space-y-6" @submit.prevent="handleSubmit">
        <div class="admin-card space-y-4">
          <h2 class="admin-section-title">Basic Information</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Name *</label>
              <input v-model="form.name" type="text" required class="input-field" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Brand</label>
              <input v-model="form.brand" type="text" class="input-field" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Category</label>
              <select v-model="form.category_id" class="input-field">
                <option value="">No category</option>
                <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
              </select>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea v-model="form.description" rows="4" class="input-field" />
          </div>
        </div>

        <div class="admin-card space-y-4">
          <h2 class="admin-section-title">Pricing & Logistics</h2>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">List Price</label>
              <input v-model.number="form.list_price" type="number" step="0.01" class="input-field" />
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
            {{ loading ? 'Saving...' : 'Save Changes' }}
          </button>
          <NuxtLink to="products" class="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50">Cancel</NuxtLink>
        </div>
      </form>

      <!-- Right column: Status -->
      <div class="space-y-6">
        <StatusWorkflow
          :current-status="product.status"
          entity="product"
          :loading="statusLoading"
          @transition="handleStatusChange"
        />
        <div class="admin-card">
          <h2 class="admin-section-title mb-4">Details</h2>
          <dl class="text-xs space-y-2">
            <div class="flex justify-between"><dt class="text-gray-500">ID</dt><dd class="font-mono">{{ product.id.slice(0, 8) }}...</dd></div>
            <div class="flex justify-between"><dt class="text-gray-500">Slug</dt><dd>{{ product.slug }}</dd></div>
            <div class="flex justify-between"><dt class="text-gray-500">Created</dt><dd>{{ new Date(product.created_at).toLocaleString() }}</dd></div>
          </dl>
        </div>
      </div>
    </div>
  </div>
  <div v-else class="text-center py-12 text-gray-500">{{ $t('common.loading') }}</div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const route = useRoute()
const { apiFetch } = useApi()
const product = ref<any>(null)
const loading = ref(false)
const statusLoading = ref(false)
const categories = ref<any[]>([])

const form = reactive({
  name: '',
  brand: '',
  category_id: '',
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
    const [prod, catRes] = await Promise.all([
      apiFetch<any>(`/products/${route.params.id}`),
      apiFetch<any>('/product-categories'),
    ])
    product.value = prod
    categories.value = catRes.items || catRes || []
    // Populate form
    Object.assign(form, {
      name: prod.name || '',
      brand: prod.brand || '',
      category_id: prod.category_id || '',
      description: prod.description || '',
      list_price: prod.list_price,
      currency: prod.currency || 'EUR',
      moq: prod.moq || 1,
      lead_time_days: prod.lead_time_days,
      warranty_years: prod.warranty_years,
      service_available: prod.service_available || false,
    })
  } catch {}
})

async function handleSubmit() {
  loading.value = true
  try {
    const payload: Record<string, any> = { ...form }
    if (!payload.category_id) payload.category_id = null
    product.value = await apiFetch<any>(`/products/${route.params.id}`, {
      method: 'PUT',
      body: payload,
    })
  } catch (e: any) {
    console.error('Update failed:', e)
  } finally {
    loading.value = false
  }
}

async function handleStatusChange(newStatus: string) {
  statusLoading.value = true
  try {
    product.value = await apiFetch<any>(`/products/${route.params.id}/status`, {
      method: 'PATCH',
      body: { status: newStatus },
    })
  } catch (e: any) {
    console.error('Status change failed:', e)
  } finally {
    statusLoading.value = false
  }
}
</script>
