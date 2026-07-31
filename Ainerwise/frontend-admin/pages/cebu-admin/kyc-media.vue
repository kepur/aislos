<template>
  <div class="space-y-5">
    <div>
      <h1 class="admin-page-title">Cebu KYC Media Review</h1>
      <p class="admin-page-desc">Review uploaded company evidence and create linked risk flags.</p>
    </div>
    <p v-if="error" class="text-sm text-red-400">{{ error }}</p>
    <div class="grid gap-4">
      <article v-for="row in items" :key="row.id" class="admin-panel p-4 text-sm">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p class="font-semibold text-white">{{ row.original_filename || row.doc_type }}</p>
            <p class="mt-1 text-slate-400">Company {{ row.company_id }} · {{ row.doc_type }}</p>
          </div>
          <StatusBadge :status="row.status" />
        </div>
        <p v-if="row.reviewer_note" class="mt-3 text-amber-300">{{ row.reviewer_note }}</p>
        <div class="mt-4 flex flex-wrap gap-2">
          <a class="btn-secondary" :href="row.file_url" target="_blank" rel="noopener">Open evidence</a>
          <button class="btn-secondary" type="button" @click="inspect(row)">View AI analysis</button>
          <button v-if="row.status !== 'REJECTED'" class="btn-primary" type="button" @click="flag(row)">Flag risk</button>
        </div>
        <div v-if="selected?.id === row.id" class="mt-4 rounded-lg border border-white/5 bg-slate-950/40 p-3">
          <p class="mb-2 font-medium text-white">AI analysis history</p>
          <p v-if="!selected.analyses?.length" class="text-slate-400">No AI analysis recorded.</p>
          <div v-for="analysis in selected.analyses" :key="analysis.id" class="mb-2 rounded bg-white/5 p-3 text-slate-300">
            <p>{{ analysis.authenticity }} · confidence {{ analysis.confidence }} · risk {{ analysis.overall_risk_score }}</p>
            <p class="mt-1 text-slate-400">{{ analysis.recommended_action }}</p>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default', middleware: ['auth'] })
const { apiFetch } = useApi()
const items = ref<any[]>([])
const selected = ref<any | null>(null)
const error = ref('')
async function load() { items.value = (await apiFetch<any>('/admin/cebu/kyc-media/files')).items }
async function inspect(row: any) {
  try { selected.value = await apiFetch(`/admin/cebu/kyc-media/files/${row.id}`) }
  catch (e: any) { error.value = e?.data?.detail || e?.message }
}
async function flag(row: any) {
  const note = window.prompt('Risk reason')
  if (!note) return
  const severity = window.prompt('Severity: low, medium, high or critical', 'high')
  if (!severity) return
  try {
    await apiFetch(`/admin/cebu/kyc-media/files/${row.id}/flag-risk`, {
      method: 'POST', body: { note, severity },
    })
    selected.value = null
    await load()
  } catch (e: any) { error.value = e?.data?.detail || e?.message }
}
onMounted(() => load().catch((e: any) => { error.value = e?.data?.detail || e?.message }))
</script>
