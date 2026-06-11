<template>
  <div class="space-y-6">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="admin-page-title">{{ $t('marketingIntegration.importedTitle') }}</h1>
        <p class="admin-page-desc">{{ $t('marketingIntegration.importedDesc') }}</p>
      </div>
      <NuxtLink to="/marketing/integration" class="action-button">{{ $t('common.back') }}</NuxtLink>
    </div>

    <div class="admin-card p-3 flex flex-wrap gap-3 items-end">
      <label>
        <span class="block text-[10px] uppercase tracking-wider text-slate-500 mb-1">{{ $t('common.status') }}</span>
        <select v-model="statusFilter" class="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-200">
          <option value="">all</option>
          <option value="in_review">in_review</option>
          <option value="approved">approved</option>
          <option value="rejected">rejected</option>
          <option value="scheduled">scheduled</option>
        </select>
      </label>
      <button class="action-button" @click="load">{{ $t('common.search') }}</button>
    </div>

    <div v-if="error" class="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
      {{ error }}
    </div>

    <div class="admin-card p-0 overflow-hidden">
      <table class="admin-table w-full text-sm">
        <thead>
          <tr class="border-b border-white/5 bg-white/[0.02]">
            <th class="text-left py-3 px-4">{{ $t('marketingIntegration.preview') }}</th>
            <th class="text-left py-3 px-4">Kind / channel</th>
            <th class="text-left py-3 px-4">{{ $t('common.status') }}</th>
            <th class="text-left py-3 px-4">{{ $t('common.actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="asset in imported" :key="asset.id" class="border-b border-white/[0.03] align-top">
            <td class="px-4 py-3">
              <div class="w-16 h-16 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center text-xs text-slate-500">
                {{ asset.kind }}
              </div>
              <p class="mt-2 font-medium text-slate-200 max-w-xs truncate">{{ asset.title || '—' }}</p>
              <p class="text-xs text-slate-500">{{ asset.id }}</p>
            </td>
            <td class="px-4 py-3 text-slate-400">
              {{ asset.kind }} · {{ asset.channel || '—' }} · {{ asset.lang }}
            </td>
            <td class="px-4 py-3"><StatusBadge :status="asset.status" /></td>
            <td class="px-4 py-3 whitespace-nowrap">
              <div class="flex flex-wrap gap-2">
                <button
                  v-if="asset.status === 'in_review'"
                  class="action-button primary text-xs px-3 py-1.5"
                  :disabled="busy"
                  @click="approve(asset)"
                >
                  {{ $t('marketingIntegration.approveAsset') }}
                </button>
                <button
                  v-if="asset.status === 'in_review'"
                  class="text-xs px-3 py-1.5 rounded border border-red-500/40 text-red-300"
                  :disabled="busy"
                  @click="reject(asset)"
                >
                  {{ $t('marketingIntegration.rejectAsset') }}
                </button>
                <button
                  v-if="asset.status === 'approved'"
                  class="text-xs px-3 py-1.5 rounded border border-white/20 text-slate-200"
                  :disabled="busy"
                  @click="schedule(asset)"
                >
                  {{ $t('marketingIntegration.schedule') }}
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="!imported.length">
            <td colspan="4" class="px-4 py-10 text-center text-slate-500">{{ $t('marketingIntegration.noImported') }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { MarketingAssetRow } from '~/composables/useMarketingIntegration'

definePageMeta({ layout: 'default' })

const { listMarketingAssets, approveAsset, rejectAsset, scheduleAsset } = useMarketingIntegration()

const assets = ref<MarketingAssetRow[]>([])
const statusFilter = ref('in_review')
const busy = ref(false)
const error = ref('')

const imported = computed(() => assets.value.filter(a => !a.ai_generated))

async function load() {
  error.value = ''
  try {
    const res = await listMarketingAssets(statusFilter.value || undefined)
    assets.value = res.items
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message
  }
}

async function approve(asset: MarketingAssetRow) {
  busy.value = true
  try {
    await approveAsset(asset.id)
    await load()
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message
  } finally {
    busy.value = false
  }
}

async function reject(asset: MarketingAssetRow) {
  const notes = window.prompt('Rejection notes (required):')
  if (!notes?.trim()) return
  busy.value = true
  try {
    await rejectAsset(asset.id, notes.trim())
    await load()
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message
  } finally {
    busy.value = false
  }
}

async function schedule(asset: MarketingAssetRow) {
  const when = window.prompt(
    'Publish at (ISO):',
    new Date(Date.now() + 3600e3).toISOString(),
  )
  if (!when) return
  busy.value = true
  try {
    await scheduleAsset(asset.id, asset.channel || 'linkedin', when)
    await load()
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>
