<template>
  <div class="p-4 space-y-4">
    <h1 class="text-xl font-semibold text-gray-900">订单</h1>
    <p class="text-sm text-gray-500">Core Commerce 订单（供应商视角）</p>
    <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
    <p v-if="loading" class="text-sm text-gray-500">加载中…</p>
    <ul v-else class="space-y-3">
      <NuxtLink v-for="o in items" :key="o.id" :to="`/supplier/orders/${o.id}`" class="block rounded-lg border p-3 bg-white">
        <p class="font-medium text-sm">订单 {{ o.id.slice(0, 8) }}…</p>
        <p class="text-xs text-gray-500">
          {{ o.status }} · {{ (o.total_minor / 100).toFixed(2) }} {{ o.currency }}
        </p>
      </NuxtLink>
      <li v-if="!items.length" class="text-sm text-gray-500">暂无订单</li>
    </ul>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default', middleware: ['auth'] })

const { listOrders } = useCommerce()
const items = ref<any[]>([])
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    const res = await listOrders()
    items.value = res.items
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Load failed'
  } finally {
    loading.value = false
  }
})
</script>
