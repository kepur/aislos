<template>
  <div class="space-y-6 max-w-4xl">
    <div class="flex items-center justify-between gap-3">
      <div>
        <h1 class="admin-page-title">{{ $t('marketingIntegration.newBrief') }}</h1>
        <p class="admin-page-desc">{{ $t('marketingIntegration.newBriefDesc') }}</p>
      </div>
      <NuxtLink to="/marketing/briefs" class="action-button">{{ $t('common.cancel') }}</NuxtLink>
    </div>

    <div v-if="error" class="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
      {{ error }}
    </div>

    <form class="admin-card p-5 space-y-5" @submit.prevent="submit">
      <label class="block">
        <span class="text-[10px] uppercase tracking-wider text-slate-500">{{ $t('marketingIntegration.briefTitle') }}</span>
        <input v-model="title" required class="mt-1 w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-200" />
      </label>
      <label class="block">
        <span class="text-[10px] uppercase tracking-wider text-slate-500">{{ $t('marketingIntegration.objective') }}</span>
        <textarea v-model="objective" rows="2" class="mt-1 w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-200" />
      </label>

      <label class="block">
        <span class="text-[10px] uppercase tracking-wider text-slate-500">Headline (copy)</span>
        <input v-model="version.copy_json!.headline" class="mt-1 w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-200" />
      </label>

      <DeliverableEditor v-model="version.deliverables_json!" />

      <div class="flex justify-end gap-2">
        <NuxtLink to="/marketing/briefs" class="action-button">{{ $t('common.cancel') }}</NuxtLink>
        <button type="submit" class="action-button primary" :disabled="busy">
          {{ busy ? $t('common.loading') : $t('common.create') }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { emptyBriefVersion } from '~/composables/useMarketingIntegration'

definePageMeta({ layout: 'default' })

const { createBrief } = useMarketingIntegration()

const title = ref('')
const objective = ref('')
const version = ref(emptyBriefVersion())
version.value.deliverables_json = version.value.deliverables_json || []

const busy = ref(false)
const error = ref('')

async function submit() {
  busy.value = true
  error.value = ''
  try {
    const brief = await createBrief({
      title: title.value,
      objective: objective.value || undefined,
      version: version.value,
    })
    await navigateTo(`/marketing/briefs/${brief.id}`)
  } catch (e: any) {
    const detail = e?.data?.detail
    error.value = typeof detail === 'string' ? detail : JSON.stringify(detail) || e?.message || 'Create failed'
  } finally {
    busy.value = false
  }
}
</script>
