<template>
  <div class="space-y-6">
    <div><h1 class="text-xl font-bold ws-title">Installed Assets</h1><p class="mt-1 text-sm ws-faint">Customer-visible installed device registry.</p></div>
    <section class="portal-card p-0 overflow-hidden">
      <table class="w-full text-sm">
        <thead><tr class="border-b ws-hairline ws-sunken/80"><th v-for="label in ['Asset','Project / Site','Location','Serial','Installed','Status']" :key="label" class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider ws-faint">{{ label }}</th></tr></thead>
        <tbody>
          <tr v-for="asset in assets" :key="asset.id" class="border-b border-slate-50">
            <td class="px-4 py-3 font-semibold ws-title">{{ asset.name }}</td>
            <td class="px-4 py-3 ws-muted"><p>{{ asset.project_title }}</p><p class="text-xs ws-faint">{{ asset.site_name }}</p></td>
            <td class="px-4 py-3 ws-muted">{{ [asset.floor, asset.room].filter(Boolean).join(' / ') || '-' }}</td>
            <td class="px-4 py-3 font-mono text-xs ws-muted">{{ asset.serial_no || '-' }}</td>
            <td class="px-4 py-3 ws-muted">{{ asset.installed_at || '-' }}</td>
            <td class="px-4 py-3"><StatusBadge :status="asset.status" /></td>
          </tr>
          <tr v-if="!assets.length"><td colspan="6" class="px-4 py-12 text-center text-sm ws-faint">Assets appear here after installation and commissioning.</td></tr>
        </tbody>
      </table>
    </section>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'procurement', middleware: 'auth' })
const { apiFetch } = useApi()
const assets = ref<any[]>([])
onMounted(async () => { assets.value = (await apiFetch<any>('/customer/workspace/assets')).items || [] })
</script>
