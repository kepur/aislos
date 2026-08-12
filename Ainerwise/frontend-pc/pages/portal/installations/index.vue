<template>
  <div class="space-y-6">
    <div><h1 class="text-xl font-bold ws-title">{{ $t('pInst.title') }}</h1><p class="mt-1 text-sm ws-faint">{{ $t('pInst.subtitle') }}</p></div>
    <div class="grid gap-4 lg:grid-cols-2">
      <NuxtLink v-for="item in items" :key="item.id" :to="localized(`/portal/installations/${item.id}`)" class="portal-card transition hover:shadow-md">
        <div class="flex items-start justify-between gap-3"><div><p class="text-xs font-semibold uppercase tracking-wider ws-accent">{{ item.project_title }}</p><h2 class="mt-1 font-bold ws-title">{{ item.title }}</h2><p class="mt-1 text-sm ws-faint">{{ item.trade || $t('pInst.generalInstall') }}</p></div><StatusBadge :status="item.status" /></div>
        <div class="mt-4 flex gap-4 text-xs ws-muted"><span>{{ $t('pInst.start') }}: {{ item.planned_start || $t('ui.tbd') }}</span><span>{{ $t('pInst.end') }}: {{ item.planned_end || $t('ui.tbd') }}</span></div>
      </NuxtLink>
    </div>
    <div v-if="!items.length" class="portal-card py-12 text-center text-sm ws-faint">{{ $t('pInst.empty') }}</div>
  </div>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()
definePageMeta({ layout: 'procurement', middleware: 'auth' })
const { apiFetch } = useApi()
const items = ref<any[]>([])
onMounted(async () => { items.value = (await apiFetch<any>('/customer/workspace/installations')).items || [] })
</script>
