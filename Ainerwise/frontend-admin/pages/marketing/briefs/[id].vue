<template>
  <div class="space-y-6 max-w-5xl">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <NuxtLink to="/marketing/briefs" class="text-xs text-cyan-400 hover:underline">← {{ $t('marketingIntegration.briefsTitle') }}</NuxtLink>
        <h1 class="admin-page-title mt-2">{{ brief?.title || $t('common.loading') }}</h1>
        <p v-if="brief?.objective" class="admin-page-desc">{{ brief.objective }}</p>
      </div>
      <div v-if="version" class="flex flex-wrap gap-2">
        <StatusBadge :status="version.status" />
        <span class="text-xs text-slate-500 self-center">v{{ version.version }}</span>
      </div>
    </div>

    <div v-if="error" class="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
      {{ error }}
    </div>
    <div v-if="notice" class="rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
      {{ notice }}
    </div>

    <div v-if="brief && version" class="space-y-6">
      <div class="admin-card p-5 space-y-4">
        <h2 class="text-sm font-semibold text-slate-200">{{ $t('marketingIntegration.briefContent') }}</h2>

        <label class="block">
          <span class="text-[10px] uppercase tracking-wider text-slate-500">Headline</span>
          <input
            v-model="edit.copy_json!.headline"
            :readonly="!isDraft"
            class="mt-1 w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-200"
          />
        </label>

        <DeliverableEditor v-model="edit.deliverables_json!" :readonly="!isDraft" />

        <div v-if="isDraft" class="flex flex-wrap gap-2">
          <button type="button" class="action-button primary" :disabled="busy" @click="saveDraft">
            {{ $t('common.save') }}
          </button>
          <button type="button" class="action-button" :disabled="busy" @click="submitReview">
            {{ $t('marketingIntegration.submitReview') }}
          </button>
        </div>

        <div v-if="version.status === 'in_review'" class="flex flex-wrap gap-2">
          <button type="button" class="action-button primary" :disabled="busy" @click="approve">
            {{ $t('marketingIntegration.approve') }}
          </button>
          <button type="button" class="action-button" :disabled="busy" @click="reject">
            {{ $t('marketingIntegration.reject') }}
          </button>
        </div>

        <div v-if="version.status === 'rejected'" class="flex flex-wrap gap-2">
          <button type="button" class="action-button" :disabled="busy" @click="copyDraft">
            {{ $t('marketingIntegration.copyToDraft') }}
          </button>
        </div>

        <div v-if="version.status === 'approved'" class="flex flex-wrap gap-2">
          <button type="button" class="action-button primary" :disabled="busy" @click="publishRequests">
            {{ $t('marketingIntegration.publishMediaRequests') }}
          </button>
          <button type="button" class="action-button" :disabled="busy" @click="refreshRequests">
            {{ $t('marketingIntegration.refreshProgress') }}
          </button>
        </div>
      </div>

      <div v-if="mediaRequests.length" class="admin-card p-0 overflow-hidden">
        <div class="px-4 py-3 border-b border-white/5">
          <h2 class="text-sm font-semibold text-slate-200">{{ $t('marketingIntegration.mediaRequests') }}</h2>
        </div>
        <table class="admin-table w-full text-sm">
          <thead>
            <tr class="border-b border-white/5 bg-white/[0.02]">
              <th class="text-left py-3 px-4">Deliverable</th>
              <th class="text-left py-3 px-4">{{ $t('common.status') }}</th>
              <th class="text-left py-3 px-4">{{ $t('marketingIntegration.progress') }}</th>
              <th class="text-left py-3 px-4">{{ $t('marketingIntegration.assetsSubmitted') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="req in mediaRequests" :key="req.id" class="border-b border-white/[0.03]">
              <td class="px-4 py-3 text-slate-300">{{ req.deliverable_key }}</td>
              <td class="px-4 py-3"><StatusBadge :status="req.status" /></td>
              <td class="px-4 py-3 text-slate-400 text-xs">
                <span v-if="req.progress_percent != null">{{ req.progress_percent }}%</span>
                <span v-if="req.progress_message" class="block text-slate-500">{{ req.progress_message }}</span>
                <span v-if="req.failure_message" class="block text-red-400">{{ req.failure_message }}</span>
              </td>
              <td class="px-4 py-3 text-slate-400">{{ req.submitted_asset_count }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { BriefVersionContent, CreativeBrief, MediaRequest } from '~/composables/useMarketingIntegration'
import { emptyBriefVersion } from '~/composables/useMarketingIntegration'

definePageMeta({ layout: 'default' })

const route = useRoute()
const briefId = computed(() => String(route.params.id))

const {
  getBrief,
  updateBriefVersion,
  submitBriefReview,
  approveBrief,
  rejectBrief,
  copyRejectedToDraft,
  listMediaRequests,
  createMediaRequests,
} = useMarketingIntegration()

const brief = ref<CreativeBrief | null>(null)
const edit = ref<BriefVersionContent>(emptyBriefVersion())
const mediaRequests = ref<MediaRequest[]>([])
const busy = ref(false)
const error = ref('')
const notice = ref('')

const version = computed(() => brief.value?.current_version ?? null)
const isDraft = computed(() => version.value?.status === 'draft')

function syncEditFromVersion() {
  const v = version.value
  if (!v) return
  edit.value = {
    copy_json: { ...(v.copy_json || {}) },
    audience_json: { ...(v.audience_json || {}) },
    brand_constraints_json: { ...(v.brand_constraints_json || {}) },
    channel_specs_json: { ...(v.channel_specs_json || {}) },
    deliverables_json: [...(v.deliverables_json || [])],
    source_refs_json: { ...(v.source_refs_json || {}) },
    compliance_json: { ...(v.compliance_json || {}) },
  }
}

async function load() {
  error.value = ''
  brief.value = await getBrief(briefId.value)
  syncEditFromVersion()
  if (version.value?.status === 'approved') {
    await refreshRequests()
  }
}

async function refreshRequests() {
  if (!version.value) return
  mediaRequests.value = await listMediaRequests(version.value.id)
}

async function saveDraft() {
  if (!version.value) return
  busy.value = true
  error.value = ''
  notice.value = ''
  try {
    await updateBriefVersion(version.value.id, edit.value)
    notice.value = 'Saved'
    await load()
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Save failed'
  } finally {
    busy.value = false
  }
}

async function submitReview() {
  if (!version.value) return
  busy.value = true
  error.value = ''
  try {
    await updateBriefVersion(version.value.id, edit.value)
    await submitBriefReview(version.value.id)
    await load()
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Submit failed'
  } finally {
    busy.value = false
  }
}

async function approve() {
  if (!version.value) return
  const notes = window.prompt('Approval notes (optional):') ?? ''
  busy.value = true
  error.value = ''
  try {
    await approveBrief(version.value.id, notes || undefined)
    await load()
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Approve failed'
  } finally {
    busy.value = false
  }
}

async function reject() {
  if (!version.value) return
  const reason = window.prompt('Rejection reason (required):')
  if (!reason?.trim()) return
  busy.value = true
  error.value = ''
  try {
    await rejectBrief(version.value.id, reason.trim())
    await load()
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Reject failed'
  } finally {
    busy.value = false
  }
}

async function copyDraft() {
  if (!version.value) return
  busy.value = true
  error.value = ''
  try {
    await copyRejectedToDraft(version.value.id)
    await load()
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Copy failed'
  } finally {
    busy.value = false
  }
}

async function publishRequests() {
  if (!version.value) return
  busy.value = true
  error.value = ''
  try {
    mediaRequests.value = await createMediaRequests(version.value.id)
    notice.value = 'Media requests published'
  } catch (e: any) {
    const detail = e?.data?.detail
    error.value = typeof detail === 'string' ? detail : JSON.stringify(detail) || e?.message
  } finally {
    busy.value = false
  }
}

onMounted(async () => {
  try {
    await load()
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Failed to load brief'
  }
})
</script>
