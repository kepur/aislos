<template><div class="space-y-4 p-4"><div><p class="text-[10px] font-bold uppercase tracking-widest text-emerald-600">Supplier</p><h1 class="text-xl font-bold text-slate-800">供应商工作台</h1></div><div v-if="dashboard" class="grid grid-cols-3 gap-2"><NuxtLink v-for="item in cards" :key="item.to" :to="item.to" class="m-card p-3 text-center"><p class="text-xl font-bold text-emerald-600">{{ item.value }}</p><p class="text-[10px] text-slate-400">{{ item.label }}</p></NuxtLink></div><div class="grid grid-cols-2 gap-3"><NuxtLink to="/supplier/pings" class="m-btn-primary block text-center">匹配需求</NuxtLink><NuxtLink to="/supplier/catalog" class="m-card block text-center text-sm font-semibold">管理目录</NuxtLink><NuxtLink to="/supplier/messages" class="m-card block text-center text-sm font-semibold">消息</NuxtLink><NuxtLink to="/supplier/team" class="m-card block text-center text-sm font-semibold">团队</NuxtLink><NuxtLink to="/supplier/profile" class="m-card block text-center text-sm font-semibold">设置</NuxtLink></div><p v-if="error" class="m-card text-red-600">{{ error }}</p></div></template>

<script setup lang="ts">
definePageMeta({ layout: 'default', middleware: ['auth'] })

const { getSupplierDashboard } = useCommerce()
const dashboard = ref<any>(null)
const error = ref('')
const cards = computed(() => dashboard.value ? [
  { label: 'Pings', value: dashboard.value.open_pings, to: '/supplier/pings' },
  { label: 'Offers', value: dashboard.value.submitted_offers, to: '/supplier/offers' },
  { label: 'Orders', value: dashboard.value.active_orders, to: '/supplier/orders' },
] : [])

onMounted(async () => {
  try {
    dashboard.value = await getSupplierDashboard()
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Access denied'
  }
})
</script>
