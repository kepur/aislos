<template>
  <div class="space-y-3 px-4 py-4">
    <div><h1 class="text-lg font-bold text-slate-800">Installations</h1><p class="text-xs text-slate-400">Site work, dates, tasks, and evidence.</p></div>
    <NuxtLink v-for="item in items" :key="item.id" :to="`/customer/installations/${item.id}`" class="block rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
      <div class="flex items-start justify-between gap-2"><div><p class="text-[10px] font-semibold uppercase tracking-wider text-blue-500">{{ item.project_title }}</p><p class="mt-1 text-sm font-bold text-slate-800">{{ item.title }}</p><p class="text-xs text-slate-400">{{ item.trade || 'General installation' }}</p></div><StatusBadge :status="item.status" /></div>
      <p class="mt-3 text-[11px] text-slate-500">{{ item.planned_start || 'TBD' }} to {{ item.planned_end || 'TBD' }}</p>
    </NuxtLink>
    <p v-if="!items.length" class="rounded-2xl bg-white p-8 text-center text-xs text-slate-400">No installation packages yet.</p>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'customer-mobile', middleware: 'auth' })
const { apiFetch } = useApi()
const items = ref<any[]>([])
onMounted(async () => { items.value = (await apiFetch<any>('/customer/workspace/installations')).items || [] })
</script>
