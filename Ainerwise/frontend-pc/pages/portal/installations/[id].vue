<template>
  <div class="space-y-6">
    <NuxtLink to="/portal/installations" class="text-sm font-semibold text-blue-600">&larr; Installations</NuxtLink>
    <template v-if="item">
      <section class="portal-card">
        <div class="flex flex-wrap items-start justify-between gap-3"><div><p class="text-xs font-semibold uppercase tracking-wider text-blue-500">{{ item.project_title }}</p><h1 class="mt-1 text-xl font-bold text-slate-800">{{ item.title }}</h1><p class="mt-1 text-sm text-slate-400">{{ item.trade || 'General installation' }}</p></div><StatusBadge :status="item.status" /></div>
        <dl class="mt-5 grid gap-3 text-sm sm:grid-cols-3"><div><dt class="text-slate-400">Planned start</dt><dd class="font-semibold text-slate-700">{{ item.planned_start || 'TBD' }}</dd></div><div><dt class="text-slate-400">Planned end</dt><dd class="font-semibold text-slate-700">{{ item.planned_end || 'TBD' }}</dd></div><div><dt class="text-slate-400">Site</dt><dd class="font-semibold text-slate-700">{{ item.site_json?.address || item.site_json?.name || 'Project site' }}</dd></div></dl>
      </section>
      <section class="portal-card">
        <h2 class="text-sm font-bold text-slate-800">Field tasks and evidence</h2>
        <div class="mt-4 space-y-4">
          <div v-for="task in item.tasks || []" :key="task.id" class="rounded-xl border border-slate-100 p-4">
            <div class="flex justify-between gap-3"><div><p class="font-semibold text-slate-700">{{ task.title }}</p><p class="text-xs text-slate-400">{{ task.task_type }} · {{ task.evidence_count }} evidence records</p></div><StatusBadge :status="task.status" /></div>
            <div v-if="task.evidence?.length" class="mt-3 grid gap-2 md:grid-cols-2">
              <div v-for="evidence in task.evidence" :key="evidence.id" class="rounded-lg bg-slate-50 p-3 text-xs text-slate-600"><p class="font-semibold text-slate-700">{{ evidence.evidence_type }}</p><p class="mt-1">{{ evidence.payload_json?.notes || evidence.payload_json?.device_label || evidence.payload_json?.object_key || 'Evidence captured on site' }}</p></div>
            </div>
          </div>
          <p v-if="!(item.tasks || []).length" class="py-8 text-center text-sm text-slate-400">No field tasks published yet.</p>
        </div>
      </section>
    </template>
    <div v-else class="portal-card py-16 text-center text-sm text-slate-400">Loading installation...</div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'customer-workspace', middleware: 'auth' })
const route = useRoute()
const { apiFetch } = useApi()
const item = ref<any>(null)
onMounted(async () => { item.value = await apiFetch(`/customer/workspace/installations/${route.params.id}`) })
</script>
