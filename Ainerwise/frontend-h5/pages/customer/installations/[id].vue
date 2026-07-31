<template>
  <div class="space-y-3 px-4 py-4">
    <NuxtLink to="/customer/installations" class="text-xs font-semibold text-blue-600">&larr; Installations</NuxtLink>
    <section v-if="item" class="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
      <div class="flex justify-between gap-2"><div><p class="text-[10px] font-semibold uppercase tracking-wider text-blue-500">{{ item.project_title }}</p><h1 class="mt-1 text-lg font-bold text-slate-800">{{ item.title }}</h1></div><StatusBadge :status="item.status" /></div>
      <p class="mt-3 text-xs text-slate-500">{{ item.planned_start || 'TBD' }} to {{ item.planned_end || 'TBD' }}</p>
    </section>
    <section v-for="task in item?.tasks || []" :key="task.id" class="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
      <div class="flex justify-between gap-2"><div><p class="text-sm font-semibold text-slate-700">{{ task.title }}</p><p class="text-[11px] text-slate-400">{{ task.task_type }} · {{ task.evidence_count }} evidence</p></div><StatusBadge :status="task.status" /></div>
      <div v-if="task.evidence?.length" class="mt-3 space-y-2">
        <div v-for="evidence in task.evidence" :key="evidence.id" class="rounded-xl bg-slate-50 p-3 text-[11px] text-slate-600"><p class="font-semibold">{{ evidence.evidence_type }}</p><p class="mt-1">{{ evidence.payload_json?.notes || evidence.payload_json?.device_label || evidence.payload_json?.object_key || 'Captured on site' }}</p></div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'customer-mobile', middleware: 'auth' })
const route = useRoute()
const { apiFetch } = useApi()
const item = ref<any>(null)
onMounted(async () => { item.value = await apiFetch(`/customer/workspace/installations/${route.params.id}`) })
</script>
