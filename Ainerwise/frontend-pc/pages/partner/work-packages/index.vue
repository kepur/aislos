<template>
  <section class="space-y-5">
    <div>
      <p class="text-xs font-bold uppercase tracking-wider text-blue-300">{{ $t('partner.gcDelivery') }}</p>
      <h1 class="mt-1 text-3xl font-bold text-white">{{ $t('partner.workPackages') }}</h1>
      <p class="mt-2 text-sm text-slate-400">{{ $t('partner.wpDesc') }}</p>
    </div>
    <div class="flex flex-wrap gap-2">
      <button v-for="tab in tabs" :key="tab.key" class="rounded-lg border px-4 py-2 text-sm" :class="status===tab.key?'border-blue-400/40 bg-blue-500/15 text-blue-200':'border-white/10 text-slate-400'" @click="status=tab.key">{{ tab.label }}</button>
    </div>
    <NuxtLink v-for="item in filtered" :key="item.id" :to="localized(`/partner/work-packages/${item.id}`)" class="pc-card block">
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p class="text-xl font-semibold text-white">{{ item.title }}</p>
          <p class="mt-2 text-sm text-slate-400">{{ item.trade ? label(item.trade) : $t('partner.generalDelivery') }}</p>
          <p class="mt-3 text-xs text-slate-500">{{ item.planned_start || $t('partner.startPending') }} {{ $t('partner.toWord') }} {{ item.planned_end || $t('partner.finishPending') }}</p>
        </div>
        <span class="rounded-full bg-blue-500/10 px-3 py-1 text-xs uppercase text-blue-300">{{ label(item.status) }}</span>
      </div>
    </NuxtLink>
    <p v-if="!filtered.length && !error" class="pc-card text-slate-500">{{ $t('partner.noPackagesView') }}</p>
    <p v-if="error" class="pc-card text-red-300">{{ error }}</p>
  </section>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()
definePageMeta({ layout: 'partner-workspace', middleware: ['auth'] })
const { apiFetch } = useApi()
const items = ref<any[]>([])
const error = ref('')
const status = ref('all')
const { t } = useI18n()
const tabs = computed(() => [{key:'all',label:t('partner.tabAll')},{key:'draft',label:t('partner.wpDraft')},{key:'active',label:t('partner.wpActive')},{key:'completed',label:t('partner.wpCompleted')}])
const label = (value: string) => value?.replaceAll('_', ' ') || t('partner.unknown')
const filtered = computed(() => status.value === 'all' ? items.value : items.value.filter(item => item.status === status.value))
onMounted(async () => {
  try {
    items.value = (await apiFetch<any>('/partner/field-ops/work-packages')).items || []
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message
  }
})
</script>

