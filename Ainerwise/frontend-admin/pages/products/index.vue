<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="admin-page-title">{{ $t('admin.products') }}</h1>
      <NuxtLink to="products/create" class="btn-primary text-sm">{{ $t('common.create') }}</NuxtLink>
    </div>
    <div v-if="loadError" class="mb-4 rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
      {{ loadError }}
      <button class="ml-2 font-semibold underline" @click="loadProducts">Retry</button>
    </div>
    <div class="admin-panel">
      <table class="admin-table w-full text-sm">
        <thead>
          <tr>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Name</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Brand</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Source</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Price</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">{{ $t('common.status') }}</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">{{ $t('common.actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="product in products" :key="product.id" class="border-b">
            <td class="px-4 py-3 font-medium">{{ product.name }}</td>
            <td class="px-4 py-3">{{ product.brand || '-' }}</td>
            <td class="px-4 py-3"><StatusBadge :status="product.source_type" /></td>
            <td class="px-4 py-3">{{ product.list_price ? `€${product.list_price}` : '-' }}</td>
            <td class="px-4 py-3"><StatusBadge :status="product.status" /></td>
            <td class="px-4 py-3">
              <NuxtLink :to="`products/${product.id}/edit`" class="text-primary-600 hover:underline text-xs">{{ $t('common.edit') }}</NuxtLink>
            </td>
          </tr>
          <tr v-if="!products.length">
            <td colspan="6" class="px-4 py-8 text-center text-gray-500">{{ $t('common.noData') }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { apiFetch } = useApi()
const products = ref<any[]>([])
const loadError = ref('')

async function loadProducts() {
  loadError.value = ''
  try {
    const res = await apiFetch<any>('/products/admin/all')
    products.value = res.items || res || []
  } catch (e: any) {
    loadError.value = e?.data?.detail || e?.message || 'Unable to load products.'
  }
}

onMounted(loadProducts)
</script>
