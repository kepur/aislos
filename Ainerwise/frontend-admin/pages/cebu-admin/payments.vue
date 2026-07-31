<template>
  <div class="space-y-6">
    <div>
      <h1 class="admin-page-title">Cebu Payments & Reconciliation</h1>
      <p class="admin-page-desc">Regional payment policy, provider events, quotes and settlement reconciliation.</p>
    </div>
    <p v-if="error" class="text-sm text-red-400">{{ error }}</p>

    <section class="admin-panel p-5">
      <h2 class="mb-4 font-semibold text-white">Regional payment policy</h2>
      <form class="grid gap-3 md:grid-cols-4" @submit.prevent="saveRegion">
        <input v-model.trim="form.country_code" required maxlength="2" class="input-field" placeholder="Country code" />
        <input v-model.trim="form.country_name" required class="input-field" placeholder="Country name" />
        <input v-model.trim="form.local_currency" required class="input-field" placeholder="Local currency" />
        <input v-model.trim="form.default_settlement_currency" required class="input-field" placeholder="Settlement currency" />
        <input v-model.trim="enabledCurrencies" class="input-field md:col-span-2" placeholder="Enabled currencies, comma separated" />
        <input v-model.trim="enabledMethods" class="input-field" placeholder="Payment methods, comma separated" />
        <button class="btn-primary">Save audited policy</button>
      </form>
      <div class="mt-5 grid gap-3 md:grid-cols-2">
        <article v-for="row in configs.regions?.items || []" :key="row.id" class="rounded-lg border border-white/5 bg-slate-950/30 p-4 text-sm">
          <div class="flex justify-between gap-3"><p class="font-medium text-white">{{ row.country_name }} ({{ row.country_code }})</p><StatusBadge :status="row.is_active ? 'active' : 'inactive'" /></div>
          <p class="mt-2 text-slate-400">{{ row.local_currency }} → {{ row.default_settlement_currency }} · {{ row.default_transaction_mode }}</p>
          <button class="btn-secondary mt-3" type="button" @click="editRegion(row)">Edit policy</button>
        </article>
      </div>
    </section>

    <section class="grid gap-4 md:grid-cols-3">
      <div class="admin-panel p-4"><p class="text-sm text-slate-400">Payment events</p><p class="mt-2 text-2xl font-semibold text-white">{{ reconciliation.summary?.payment_event_count || 0 }}</p></div>
      <div class="admin-panel p-4"><p class="text-sm text-slate-400">Settlement events</p><p class="mt-2 text-2xl font-semibold text-white">{{ reconciliation.summary?.settlement_event_count || 0 }}</p></div>
      <div class="admin-panel p-4"><p class="text-sm text-slate-400">Unmatched events</p><p class="mt-2 text-2xl font-semibold text-amber-300">{{ reconciliation.summary?.unmatched_payment_events || 0 }}</p></div>
    </section>

    <section class="admin-panel overflow-x-auto p-4">
      <h2 class="mb-4 font-semibold text-white">Payment and settlement records</h2>
      <table class="admin-table min-w-full text-sm">
        <thead><tr><th>Kind</th><th>Reference / Order</th><th>Amount</th><th>Currency</th><th>Status</th><th>Created</th></tr></thead>
        <tbody><tr v-for="row in payments" :key="`${row.kind}-${row.id}`"><td>{{ row.kind }}</td><td>{{ row.external_ref || row.provider_reference || row.commerce_order_id || row.order_id || 'n/a' }}</td><td>{{ row.amount_minor ?? row.gross_amount_minor }}</td><td>{{ row.currency }}</td><td><StatusBadge :status="row.status" /></td><td>{{ row.created_at }}</td></tr></tbody>
      </table>
    </section>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default', middleware: ['auth'] })
const { apiFetch } = useApi()
const configs = ref<any>({})
const reconciliation = ref<any>({})
const payments = ref<any[]>([])
const error = ref('')
const enabledCurrencies = ref('PHP, USD')
const enabledMethods = ref('PHP_MANUAL_BANK')
const form = reactive({ country_code: 'PH', country_name: 'Philippines', local_currency: 'PHP', default_settlement_currency: 'PHP', default_transaction_mode: 'LOCAL_ONLY', is_active: true })
async function load() {
  const [configResult, reconciliationResult, paymentResult] = await Promise.all([
    apiFetch<any>('/admin/cebu/payment-configs'),
    apiFetch<any>('/admin/cebu/reconciliation/payment-events'),
    apiFetch<any>('/admin/cebu/payments'),
  ])
  configs.value = configResult; reconciliation.value = reconciliationResult; payments.value = paymentResult.items
}
function editRegion(row: any) {
  Object.assign(form, { country_code: row.country_code, country_name: row.country_name, local_currency: row.local_currency, default_settlement_currency: row.default_settlement_currency, default_transaction_mode: row.default_transaction_mode, is_active: row.is_active })
  enabledCurrencies.value = (row.enabled_currencies || []).join(', ')
  enabledMethods.value = (row.enabled_payment_methods || []).join(', ')
}
async function saveRegion() {
  try {
    await apiFetch(`/admin/cebu/payment-region-configs/${form.country_code.toUpperCase()}`, {
      method: 'PUT',
      body: {
        ...form, country_code: form.country_code.toUpperCase(),
        enabled_currencies: enabledCurrencies.value.split(',').map(v => v.trim()).filter(Boolean),
        enabled_payment_methods: enabledMethods.value.split(',').map(v => v.trim()).filter(Boolean),
        cross_border_currencies: ['USD'],
      },
    })
    await load()
  } catch (e: any) { error.value = e?.data?.detail || e?.message }
}
onMounted(() => load().catch((e: any) => { error.value = e?.data?.detail || e?.message }))
</script>
