<template>
  <div class="space-y-6">
    <div><h1 class="text-xl font-bold text-slate-800">Installations</h1><p class="mt-1 text-sm text-slate-400">Track work packages, site dates, field progress, and evidence.</p></div>
    <div class="grid gap-4 lg:grid-cols-2">
      <NuxtLink v-for="item in items" :key="item.id" :to="`/portal/installations/${item.id}`" class="portal-card transition hover:shadow-md">
        <div class="flex items-start justify-between gap-3"><div><p class="text-xs font-semibold uppercase tracking-wider text-blue-500">{{ item.project_title }}</p><h2 class="mt-1 font-bold text-slate-800">{{ item.title }}</h2><p class="mt-1 text-sm text-slate-400">{{ item.trade || 'General installation' }}</p></div><StatusBadge :status="item.status" /></div>
        <div class="mt-4 flex gap-4 text-xs text-slate-500"><span>Start: {{ item.planned_start || 'TBD' }}</span><span>End: {{ item.planned_end || 'TBD' }}</span></div>
      </NuxtLink>
    </div>
    <div v-if="!items.length" class="portal-card py-12 text-center text-sm text-slate-400">Installation packages appear after project dispatch.</div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'customer-workspace', middleware: 'auth' })
const { apiFetch } = useApi()
const items = ref<any[]>([])
onMounted(async () => { items.value = (await apiFetch<any>('/customer/workspace/installations')).items || [] })
</script>
