<template>
  <div class="space-y-6">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="admin-page-title">{{ $t('marketingIntegration.briefsTitle') }}</h1>
        <p class="admin-page-desc">{{ total }} {{ $t('marketingIntegration.briefsListed') }}</p>
      </div>
      <div class="flex gap-2">
        <NuxtLink to="/marketing/integration" class="action-button">{{ $t('common.back') }}</NuxtLink>
        <NuxtLink to="/marketing/briefs/new" class="action-button primary">+ {{ $t('marketingIntegration.newBrief') }}</NuxtLink>
      </div>
    </div>

    <div class="admin-card p-3 flex flex-wrap gap-3 items-end">
      <label>
        <span class="block text-[10px] uppercase tracking-wider text-slate-500 mb-1">{{ $t('common.status') }}</span>
        <select v-model="statusFilter" class="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-200">
          <option value="">{{ $t('marketingIntegration.allStatuses') }}</option>
          <option value="draft">draft</option>
          <option value="in_review">in_review</option>
          <option value="approved">approved</option>
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
            <th class="text-left py-3 px-4">{{ $t('marketingIntegration.briefTitle') }}</th>
            <th class="text-left py-3 px-4">{{ $t('common.status') }}</th>
            <th class="text-left py-3 px-4">{{ $t('marketingIntegration.version') }}</th>
            <th class="text-left py-3 px-4">{{ $t('marketingIntegration.updated') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="brief in briefs"
            :key="brief.id"
            class="border-b border-white/[0.03] hover:bg-white/[0.02] cursor-pointer"
            @click="navigateTo(`/marketing/briefs/${brief.id}`)"
          >
            <td class="px-4 py-3">
              <p class="font-medium text-slate-200">{{ brief.title }}</p>
              <p v-if="brief.objective" class="text-xs text-slate-500 line-clamp-1">{{ brief.objective }}</p>
            </td>
            <td class="px-4 py-3"><StatusBadge :status="brief.status" /></td>
            <td class="px-4 py-3 text-slate-400">v{{ brief.current_version?.version ?? '—' }}</td>
            <td class="px-4 py-3 text-slate-500 text-xs whitespace-nowrap">{{ formatDate(brief.updated_at) }}</td>
          </tr>
          <tr v-if="!briefs.length">
            <td colspan="4" class="px-4 py-10 text-center text-slate-500">{{ $t('common.noData') }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { CreativeBrief } from '~/composables/useMarketingIntegration'

definePageMeta({ layout: 'default' })

const { listBriefs } = useMarketingIntegration()

const briefs = ref<CreativeBrief[]>([])
const total = ref(0)
const statusFilter = ref('')
const error = ref('')

function formatDate(iso: string) {
  return new Date(iso).toLocaleString()
}

async function load() {
  error.value = ''
  try {
    const res = await listBriefs({ status: statusFilter.value || undefined })
    briefs.value = res.items
    total.value = res.total
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Failed to load briefs'
  }
}

onMounted(load)
</script>
