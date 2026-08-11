<template>
  <div class="space-y-6">
    <div><h1 class="text-xl font-bold ws-title">{{ $t('portal.assets.title') }}</h1><p class="mt-1 text-sm ws-faint">{{ $t('portal.assets.subtitle') }}</p></div>
    <section class="portal-card p-0 overflow-hidden">
      <table class="w-full text-sm">
        <thead><tr class="border-b ws-hairline ws-sunken/80"><th v-for="col in assetColumns" :key="col" class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider ws-faint">{{ $t(col) }}</th></tr></thead>
        <tbody>
          <tr v-for="asset in paged" :key="asset.id" class="border-b border-slate-50">
            <td class="px-4 py-3 font-semibold ws-title">{{ asset.name }}</td>
            <td class="px-4 py-3 ws-muted"><p>{{ asset.project_title }}</p><p class="text-xs ws-faint">{{ asset.site_name }}</p></td>
            <td class="px-4 py-3 ws-muted">{{ [asset.floor, asset.room].filter(Boolean).join(' / ') || '-' }}</td>
            <td class="px-4 py-3 font-mono text-xs ws-muted">{{ asset.serial_no || '-' }}</td>
            <td class="px-4 py-3 ws-muted">{{ asset.installed_at || '-' }}</td>
            <td class="px-4 py-3"><StatusBadge :status="asset.status" /></td>
          </tr>
          <tr v-if="!assets.length"><td colspan="6" class="px-4 py-12 text-center text-sm ws-faint">{{ $t('portal.assets.empty') }}</td></tr>
        </tbody>
      </table>
    </section>
      <WorkspacePagination v-model:page="page" :page-size="pageSize" :total="assets.length" />

  </div>
</template>

<script setup lang="ts">

definePageMeta({ layout: 'procurement', middleware: 'auth' })
const { apiFetch } = useApi()
const assets = ref<any[]>([])
// i18n keys for the column headers, kept in one place so the header row and
// any future export share the same labels.
const assetColumns = [
  'portal.assets.colAsset', 'portal.assets.colProject', 'portal.assets.colLocation',
  'portal.assets.colSerial', 'portal.assets.colInstalled', 'portal.assets.colStatus',
]

// Client-side paging: these lists already hold the full filtered set, so the
// pager slices it rather than adding a round trip per page.
const page = ref(1)
const pageSize = 20
const paged = computed(() => assets.value.slice((page.value - 1) * pageSize, page.value * pageSize))
watch(() => assets.value.length, () => { page.value = 1 })

onMounted(async () => { assets.value = (await apiFetch<any>('/customer/workspace/assets')).items || [] })
</script>
