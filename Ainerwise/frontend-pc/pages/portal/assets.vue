<template>
  <div class="space-y-6">
    <div><h1 class="text-xl font-bold text-slate-800">Installed Assets</h1><p class="mt-1 text-sm text-slate-400">Customer-visible installed device registry.</p></div>
    <section class="portal-card p-0 overflow-hidden">
      <table class="w-full text-sm">
        <thead><tr class="border-b border-slate-100 bg-slate-50/80"><th v-for="label in ['Asset','Project / Site','Location','Serial','Installed','Status']" :key="label" class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-400">{{ label }}</th></tr></thead>
        <tbody>
          <tr v-for="asset in assets" :key="asset.id" class="border-b border-slate-50">
            <td class="px-4 py-3 font-semibold text-slate-700">{{ asset.name }}</td>
            <td class="px-4 py-3 text-slate-500"><p>{{ asset.project_title }}</p><p class="text-xs text-slate-400">{{ asset.site_name }}</p></td>
            <td class="px-4 py-3 text-slate-500">{{ [asset.floor, asset.room].filter(Boolean).join(' / ') || '-' }}</td>
            <td class="px-4 py-3 font-mono text-xs text-slate-500">{{ asset.serial_no || '-' }}</td>
            <td class="px-4 py-3 text-slate-500">{{ asset.installed_at || '-' }}</td>
            <td class="px-4 py-3"><StatusBadge :status="asset.status" /></td>
          </tr>
          <tr v-if="!assets.length"><td colspan="6" class="px-4 py-12 text-center text-sm text-slate-400">Assets appear here after installation and commissioning.</td></tr>
        </tbody>
      </table>
    </section>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'customer-workspace', middleware: 'auth' })
const { apiFetch } = useApi()
const assets = ref<any[]>([])
onMounted(async () => { assets.value = (await apiFetch<any>('/customer/workspace/assets')).items || [] })
</script>
