<template>
  <div class="space-y-3 px-4 py-4">
    <div><h1 class="text-lg font-bold text-slate-800">Assets</h1><p class="text-xs text-slate-400">Installed equipment across your projects.</p></div>
    <div v-for="asset in assets" :key="asset.id" class="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
      <div class="flex items-start justify-between gap-2"><div><p class="text-sm font-bold text-slate-800">{{ asset.name }}</p><p class="text-[11px] text-slate-400">{{ asset.project_title }} · {{ asset.site_name }}</p></div><StatusBadge :status="asset.status" /></div>
      <dl class="mt-3 grid grid-cols-2 gap-2 text-[11px]"><div class="rounded-lg bg-slate-50 p-2"><dt class="text-slate-400">Location</dt><dd class="font-semibold text-slate-600">{{ [asset.floor, asset.room].filter(Boolean).join(' / ') || '-' }}</dd></div><div class="rounded-lg bg-slate-50 p-2"><dt class="text-slate-400">Serial</dt><dd class="truncate font-mono text-slate-600">{{ asset.serial_no || '-' }}</dd></div></dl>
    </div>
    <p v-if="!assets.length" class="rounded-2xl bg-white p-8 text-center text-xs text-slate-400">Assets appear after commissioning.</p>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'customer-mobile', middleware: 'auth' })
const { apiFetch } = useApi()
const assets = ref<any[]>([])
onMounted(async () => { assets.value = (await apiFetch<any>('/customer/workspace/assets')).items || [] })
</script>
