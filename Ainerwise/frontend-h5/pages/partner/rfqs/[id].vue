<template>
  <div class="px-4 py-4">
    <NuxtLink to="/partner/rfqs" class="mb-4 inline-flex items-center gap-1 text-xs font-semibold text-blue-500">
      <span aria-hidden="true">&larr;</span> {{ $t('partner.backToRequests') }}
    </NuxtLink>

    <div v-if="loading" class="m-card text-center text-sm text-slate-400">{{ $t('partner.loading') }}</div>
    <div v-else-if="rfq" class="space-y-4">
      <div class="m-card">
        <div class="flex items-start justify-between gap-3">
          <div>
            <p class="text-[10px] font-bold uppercase tracking-widest text-blue-500">{{ rfq.trade }}</p>
            <h1 class="mt-1 text-lg font-bold text-slate-800">{{ rfq.title }}</h1>
          </div>
          <span :class="['status-pill shrink-0', statusClass(rfq.invitation_status)]">{{ rfq.invitation_status.replace(/_/g, ' ') }}</span>
        </div>
        <dl class="mt-4 space-y-2 text-xs">
          <div class="flex justify-between gap-4"><dt class="text-slate-400">{{ $t('partner.location') }}</dt><dd class="text-right font-medium text-slate-700">{{ location }}</dd></div>
          <div class="flex justify-between gap-4"><dt class="text-slate-400">{{ $t('partner.deadline') }}</dt><dd class="text-right font-medium text-slate-700">{{ rfq.bid_deadline ? date(rfq.bid_deadline) : $t('partner.notSet') }}</dd></div>
          <div class="flex justify-between gap-4"><dt class="text-slate-400">{{ $t('partner.budgetHint') }}</dt><dd class="text-right font-medium text-slate-700">{{ rfq.budget_hint ? `${rfq.currency} ${Number(rfq.budget_hint).toLocaleString()}` : $t('partner.notSet') }}</dd></div>
        </dl>
      </div>

      <div class="m-card">
        <h2 class="text-sm font-bold text-slate-800">{{ $t('partner.scope') }}</h2>
        <p v-if="rfq.scope_json?.summary" class="mt-3 whitespace-pre-line text-xs leading-relaxed text-slate-600">{{ rfq.scope_json.summary }}</p>
        <div v-if="scopeDetails.length" class="mt-3 space-y-2">
          <div v-for="item in scopeDetails" :key="item.key" class="rounded-xl bg-slate-50 px-3 py-2.5">
            <p class="text-[10px] font-bold uppercase tracking-wide text-slate-400">{{ item.key.replace(/_/g, ' ') }}</p>
            <p class="mt-1 text-xs text-slate-700">{{ item.value }}</p>
          </div>
        </div>
      </div>

      <div v-if="rfq.bid" class="rounded-2xl border border-emerald-100 bg-emerald-50 p-4 shadow-sm">
        <p class="text-[10px] font-bold uppercase tracking-wider text-emerald-600">{{ $t('partner.yourBid') }}</p>
        <p class="mt-1 text-xl font-bold text-emerald-800">{{ rfq.bid.currency }} {{ Number(rfq.bid.amount).toLocaleString() }}</p>
        <p class="mt-1 text-xs text-emerald-700">{{ rfq.bid.lead_time_days ?? '—' }} {{ $t('partner.days') }}</p>
        <p v-if="rfq.bid.notes" class="mt-3 text-xs leading-relaxed text-emerald-700">{{ rfq.bid.notes }}</p>
      </div>

      <form v-else-if="canRespond" class="m-card space-y-3" @submit.prevent="submitBid">
        <div>
          <h2 class="text-sm font-bold text-slate-800">{{ $t('partner.submitBid') }}</h2>
          <p class="mt-1 text-[11px] text-slate-400">{{ $t('partner.bidNote') }}</p>
        </div>
        <div class="grid grid-cols-3 gap-2">
          <div class="col-span-2">
            <label class="mb-1 block text-[10px] font-bold uppercase tracking-wide text-slate-400">{{ $t('partner.amount') }}</label>
            <input v-model.number="form.amount" type="number" min="0.01" step="0.01" required class="m-input" />
          </div>
          <div>
            <label class="mb-1 block text-[10px] font-bold uppercase tracking-wide text-slate-400">{{ $t('partner.currency') }}</label>
            <input v-model="form.currency" type="text" maxlength="10" class="m-input" />
          </div>
        </div>
        <div>
          <label class="mb-1 block text-[10px] font-bold uppercase tracking-wide text-slate-400">{{ $t('partner.leadTime') }}</label>
          <input v-model.number="form.lead_time_days" type="number" min="0" max="3650" required class="m-input" />
        </div>
        <div>
          <label class="mb-1 block text-[10px] font-bold uppercase tracking-wide text-slate-400">{{ $t('partner.notes') }}</label>
          <textarea v-model="form.notes" rows="4" class="m-input resize-none"></textarea>
        </div>
        <p v-if="error" class="text-xs font-medium text-red-500">{{ error }}</p>
        <button type="submit" :disabled="saving" class="m-btn-primary disabled:opacity-50">{{ saving ? $t('partner.saving') : $t('partner.submitBid') }}</button>
        <button type="button" :disabled="saving" class="m-btn border border-slate-200 bg-white text-slate-500 disabled:opacity-50" @click="decline">{{ $t('partner.decline') }}</button>
      </form>
    </div>
    <div v-else class="m-card text-center text-sm text-slate-500">{{ error }}</div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const route = useRoute()
const { apiFetch } = useApi()
const rfq = ref<any>(null)
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const form = reactive({ amount: null as number | null, currency: 'EUR', lead_time_days: null as number | null, notes: '' })

const canRespond = computed(() => rfq.value && ['sent', 'viewed'].includes(rfq.value.invitation_status) && !['awarded', 'cancelled'].includes(rfq.value.status))
const location = computed(() => [rfq.value?.scope_json?.city, rfq.value?.scope_json?.country].filter(Boolean).join(', ') || '—')
const scopeDetails = computed(() => Object.entries(rfq.value?.scope_json || {})
  .filter(([key, value]) => !['summary', 'city', 'country'].includes(key) && value !== null && value !== '')
  .map(([key, value]) => ({ key, value: typeof value === 'object' ? JSON.stringify(value) : String(value) })))

function statusClass(status: string) {
  if (status === 'bid_submitted') return 'bg-emerald-50 text-emerald-600'
  if (status === 'declined') return 'bg-slate-100 text-slate-500'
  return 'bg-blue-50 text-blue-600'
}
function date(value: string) {
  return new Date(value).toLocaleDateString()
}
async function load() {
  loading.value = true
  error.value = ''
  try {
    rfq.value = await apiFetch<any>(`/partner/rfqs/${route.params.id}`)
    form.currency = rfq.value.currency || 'EUR'
  } catch (e: any) {
    error.value = e?.data?.detail || 'RFQ is unavailable.'
  } finally {
    loading.value = false
  }
}
async function submitBid() {
  saving.value = true
  error.value = ''
  try {
    await apiFetch(`/partner/rfqs/${route.params.id}/bids`, { method: 'POST', body: form })
    await load()
  } catch (e: any) {
    error.value = e?.data?.detail || 'Bid could not be submitted.'
  } finally {
    saving.value = false
  }
}
async function decline() {
  saving.value = true
  error.value = ''
  try {
    await apiFetch(`/partner/rfqs/${route.params.id}/decline`, { method: 'POST' })
    await load()
  } catch (e: any) {
    error.value = e?.data?.detail || 'Request could not be declined.'
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>
