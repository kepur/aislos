<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">{{ $t('admin.products') }}</h1>
      <NuxtLink to="/admin/products/create" class="btn-primary text-sm">{{ $t('common.create') }}</NuxtLink>
    </div>
    <div class="bg-white rounded-xl border overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 border-b">
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
          <tr v-for="product in products" :key="product.id" class="border-b hover:bg-gray-50">
            <td class="px-4 py-3 font-medium">{{ product.name }}</td>
            <td class="px-4 py-3">{{ product.brand || '-' }}</td>
            <td class="px-4 py-3"><StatusBadge :status="product.source_type" /></td>
            <td class="px-4 py-3">{{ product.list_price ? `€${product.list_price}` : '-' }}</td>
            <td class="px-4 py-3"><StatusBadge :status="product.status" /></td>
            <td class="px-4 py-3">
              <NuxtLink :to="`/admin/products/${product.id}/edit`" class="text-primary-600 hover:underline text-xs">{{ $t('common.edit') }}</NuxtLink>
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
definePageMeta({ layout: 'admin', middleware: 'admin' })

const { apiFetch } = useApi()
const products = ref<any[]>([])

onMounted(async () => {
  try {
    const res = await apiFetch<any>('/products?include_all=true')
    products.value = res.items || res || []
  } catch {}
})
</script>
