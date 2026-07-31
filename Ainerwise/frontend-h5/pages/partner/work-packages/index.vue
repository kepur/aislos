<template>
  <div class="space-y-4 p-4">
    <div><p class="text-[10px] font-bold uppercase tracking-widest text-blue-500">Delivery operations</p><h1 class="mt-1 text-xl font-bold text-slate-800">Work packages</h1></div>
    <NuxtLink v-for="item in items" :key="item.id" :to="`/partner/work-packages/${item.id}`" class="m-card block">
      <div class="flex items-start justify-between gap-3"><div><p class="text-sm font-bold text-slate-800">{{ item.title }}</p><p class="mt-1 text-xs text-slate-400">{{ label(item.trade || 'general delivery') }}</p></div><span class="status-pill bg-blue-50 text-blue-600">{{ label(item.status) }}</span></div>
      <p class="mt-3 text-[10px] text-slate-400">{{ item.planned_start || 'Start pending' }} to {{ item.planned_end || 'finish pending' }}</p>
    </NuxtLink>
    <p v-if="!items.length && !error" class="m-card text-center text-sm text-slate-400">No delivery packages.</p>
    <p v-if="error" class="m-card text-sm text-red-600">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth' })
const { apiFetch } = useApi()
const items = ref<any[]>([])
const error = ref('')
const label = (value: string) => value?.replaceAll('_', ' ') || 'unknown'
onMounted(async () => {
  try {
    items.value = (await apiFetch<any>('/partner/field-ops/work-packages')).items || []
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message
  }
})
</script>

