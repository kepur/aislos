<template>
  <div class="space-y-4 p-4">
    <div>
      <NuxtLink to="/marketing-mobile/briefs" class="text-xs font-semibold text-violet-600">Back to briefs</NuxtLink>
      <div class="mt-2 flex items-start justify-between gap-3">
        <h1 class="text-xl font-bold text-slate-900">{{ brief?.title || 'Creative brief' }}</h1>
        <span v-if="version" class="status-pill bg-violet-50 text-violet-600">{{ version.status }}</span>
      </div>
      <p v-if="brief?.objective" class="mt-1 text-xs text-slate-500">{{ brief.objective }}</p>
    </div>

    <form v-if="version" class="m-card space-y-3" @submit.prevent="save">
      <label class="block text-[10px] font-bold uppercase tracking-wide text-slate-400">Headline / approved copy</label>
      <textarea v-model="edit.headline" :readonly="version.status !== 'draft'" rows="5" class="m-input" />
      <input v-model="edit.audience" :readonly="version.status !== 'draft'" class="m-input" placeholder="Audience segment" />
      <input v-model="edit.tone" :readonly="version.status !== 'draft'" class="m-input" placeholder="Brand tone" />
      <div v-for="item in version.deliverables_json || []" :key="item.key" class="rounded-xl bg-violet-50 p-3 text-xs text-violet-700">
        <p class="font-semibold">{{ item.key }}</p>
        <p class="mt-1">{{ item.media_type }} · {{ item.channel }} · {{ item.format }}</p>
      </div>
      <button v-if="version.status === 'draft'" :disabled="busy" class="m-btn-primary bg-violet-600">Save copy</button>
      <button v-if="version.status === 'draft'" type="button" :disabled="busy" class="m-btn border border-violet-200 text-violet-700" @click="sendReview">Submit for review</button>
      <button v-if="version.status === 'in_review'" type="button" :disabled="busy" class="m-btn-primary bg-emerald-600" @click="approve">Approve brief</button>
      <button v-if="version.status === 'in_review'" type="button" :disabled="busy" class="m-btn border border-red-200 text-red-600" @click="reject">Reject brief</button>
      <button v-if="version.status === 'rejected'" type="button" :disabled="busy" class="m-btn border border-violet-200 text-violet-700" @click="copy">Copy to new draft</button>
      <button v-if="version.status === 'approved'" type="button" :disabled="busy" class="m-btn-primary bg-violet-600" @click="publish">Export media requests</button>
    </form>

    <div v-if="requests.length" class="m-card">
      <h2 class="text-sm font-bold text-slate-800">External media requests</h2>
      <div v-for="request in requests" :key="request.id" class="mt-3 rounded-xl bg-slate-50 p-3">
        <div class="flex justify-between gap-3">
          <p class="text-xs font-semibold text-slate-700">{{ request.deliverable_key }}</p>
          <span class="status-pill bg-violet-50 text-violet-600">{{ request.status }}</span>
        </div>
        <p class="mt-2 text-[10px] text-slate-400">{{ request.progress_percent || 0 }}% · {{ request.submitted_asset_count }} assets imported</p>
      </div>
    </div>
    <p v-if="notice" class="m-card text-sm text-emerald-600">{{ notice }}</p>
    <p v-if="error" class="m-card text-sm text-red-600">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
import type { MarketingBrief } from '~/composables/useMarketingMobile'
definePageMeta({ middleware: 'auth', layout: 'marketing-mobile' })
const route = useRoute()
const api = useMarketingMobile()
const brief = ref<MarketingBrief | null>(null)
const requests = ref<any[]>([])
const edit = reactive({ headline: '', audience: '', tone: '' })
const busy = ref(false)
const error = ref('')
const notice = ref('')
const version = computed(() => brief.value?.current_version || null)
function body() {
  const current = version.value!
  return {
    copy_json: { ...(current.copy_json || {}), headline: edit.headline },
    audience_json: { ...(current.audience_json || {}), segment: edit.audience },
    brand_constraints_json: { ...(current.brand_constraints_json || {}), tone: edit.tone },
    channel_specs_json: current.channel_specs_json || {},
    deliverables_json: current.deliverables_json || [],
    source_refs_json: current.source_refs_json || {},
    compliance_json: current.compliance_json || {},
  }
}
async function load() {
  brief.value = await api.getBrief(String(route.params.id))
  edit.headline = String(version.value?.copy_json?.headline || '')
  edit.audience = String(version.value?.audience_json?.segment || '')
  edit.tone = String(version.value?.brand_constraints_json?.tone || '')
  requests.value = version.value?.status === 'approved' ? await api.listMediaRequests(version.value.id) : []
}
async function run(action: () => Promise<any>, message = '') {
  busy.value = true
  error.value = ''
  notice.value = ''
  try {
    await action()
    notice.value = message
    await load()
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message
  } finally {
    busy.value = false
  }
}
const save = () => version.value && run(() => api.updateVersion(version.value!.id, body()), 'Copy saved.')
const sendReview = () => version.value && run(async () => {
  await api.updateVersion(version.value!.id, body())
  await api.submitReview(version.value!.id)
}, 'Submitted for review.')
const approve = () => version.value && run(() => api.approveBrief(version.value!.id, window.prompt('Approval notes (optional)') || undefined), 'Brief approved.')
const reject = () => {
  const reason = window.prompt('Rejection reason (required)')
  if (reason?.trim() && version.value) run(() => api.rejectBrief(version.value!.id, reason.trim()), 'Brief rejected.')
}
const copy = () => version.value && run(() => api.copyDraft(version.value!.id), 'New draft created.')
const publish = () => version.value && run(async () => {
  requests.value = await api.createMediaRequests(version.value!.id)
}, 'Media requests exported.')
onMounted(() => run(load))
</script>

