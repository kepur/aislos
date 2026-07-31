<template>
  <section class="space-y-5">
    <div>
      <p class="text-xs font-bold uppercase tracking-wider text-blue-300">General contractor delivery</p>
      <h1 class="mt-1 text-3xl font-bold text-white">Work packages</h1>
      <p class="mt-2 text-sm text-slate-400">Company-scoped packages, field tasks, crews and worker assignments.</p>
    </div>
    <div class="flex flex-wrap gap-2">
      <button v-for="tab in tabs" :key="tab" class="rounded-lg border px-4 py-2 text-sm capitalize" :class="status===tab?'border-blue-400/40 bg-blue-500/15 text-blue-200':'border-white/10 text-slate-400'" @click="status=tab">{{ tab }}</button>
    </div>
    <NuxtLink v-for="item in filtered" :key="item.id" :to="`/partner/work-packages/${item.id}`" class="pc-card block">
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p class="text-xl font-semibold text-white">{{ item.title }}</p>
          <p class="mt-2 text-sm text-slate-400">{{ label(item.trade || 'general delivery') }}</p>
          <p class="mt-3 text-xs text-slate-500">{{ item.planned_start || 'Start pending' }} to {{ item.planned_end || 'finish pending' }}</p>
        </div>
        <span class="rounded-full bg-blue-500/10 px-3 py-1 text-xs uppercase text-blue-300">{{ label(item.status) }}</span>
      </div>
    </NuxtLink>
    <p v-if="!filtered.length && !error" class="pc-card text-slate-500">No delivery packages in this view.</p>
    <p v-if="error" class="pc-card text-red-300">{{ error }}</p>
  </section>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'partner-workspace', middleware: ['auth'] })
const { apiFetch } = useApi()
const items = ref<any[]>([])
const error = ref('')
const status = ref('all')
const tabs = ['all', 'draft', 'active', 'completed']
const label = (value: string) => value?.replaceAll('_', ' ') || 'unknown'
const filtered = computed(() => status.value === 'all' ? items.value : items.value.filter(item => item.status === status.value))
onMounted(async () => {
  try {
    items.value = (await apiFetch<any>('/partner/field-ops/work-packages')).items || []
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message
  }
})
</script>

