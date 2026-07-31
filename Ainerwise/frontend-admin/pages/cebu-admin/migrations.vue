<template>
  <div class="space-y-6">
    <div>
      <h1 class="admin-page-title">Cebu Historical Migration</h1>
      <p class="admin-page-desc">
        Import dependency-ordered Cebu exports into AinerWise Core with idempotency and row-level evidence.
      </p>
    </div>

    <p v-if="error" class="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">
      {{ error }}
    </p>

    <section v-if="readiness" class="space-y-4">
      <div class="grid gap-3 md:grid-cols-4">
        <div class="admin-panel p-4">
          <p class="text-xs uppercase tracking-wide text-slate-400">Implementation ready</p>
          <p class="mt-2 text-xl font-semibold" :class="readiness.implementation_ready ? 'text-emerald-300' : 'text-amber-300'">
            {{ readiness.implementation_ready ? 'Yes' : 'No' }}
          </p>
        </div>
        <div class="admin-panel p-4">
          <p class="text-xs uppercase tracking-wide text-slate-400">Failed records</p>
          <p class="mt-2 text-xl font-semibold text-white">{{ readiness.records.failed }}</p>
        </div>
        <div class="admin-panel p-4">
          <p class="text-xs uppercase tracking-wide text-slate-400">Archive-only</p>
          <p class="mt-2 text-xl font-semibold text-white">{{ readiness.records.archive_only }}</p>
        </div>
        <div class="admin-panel p-4">
          <p class="text-xs uppercase tracking-wide text-slate-400">Identity gaps</p>
          <p class="mt-2 text-xl font-semibold text-white">{{ readiness.identities.incomplete }}</p>
        </div>
      </div>
      <div class="admin-panel border border-amber-400/20 p-5">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 class="font-semibold text-white">Legacy retirement gate</h2>
            <p class="mt-1 text-sm text-slate-400">
              Current action: {{ readiness.legacy_runtime_action }}. This screen cannot stop or delete Cebu.
            </p>
          </div>
          <StatusBadge :status="readiness.retirement_allowed ? 'APPROVED' : 'BLOCKED'" />
        </div>
        <ul class="mt-4 space-y-2 text-sm text-amber-100">
          <li v-for="blocker in readiness.blockers" :key="blocker">• {{ blocker }}</li>
        </ul>
      </div>
    </section>

    <section class="admin-panel space-y-4 p-5">
      <div class="grid gap-3 md:grid-cols-2">
        <input v-model="batchKey" class="input-field" placeholder="Unique batch key, e.g. cebu-prod-2026-06-12" />
        <input class="input-field" type="file" accept="application/json,.json" @change="loadFile" />
      </div>
      <textarea
        v-model="bundleText"
        class="input-field min-h-64 w-full font-mono text-xs"
        spellcheck="false"
        placeholder='{"companies":[],"users":[],"categories":[],"catalog_items":[],"intents":[],"offers":[],"orders":[]}'
      />
      <div class="flex flex-wrap items-center gap-3">
        <button class="btn-primary" :disabled="running" @click="runImport">
          {{ running ? 'Importing…' : 'Run idempotent import' }}
        </button>
        <span class="text-xs text-slate-400">
          Legacy passwords and secrets are removed. Unknown Cebu object groups are preserved as sanitized archives.
        </span>
      </div>
    </section>

    <section>
      <div class="mb-3 flex items-center justify-between">
        <h2 class="font-semibold text-white">Migration runs</h2>
        <button class="text-sm font-semibold text-cyan-300" @click="loadRuns">Refresh</button>
      </div>
      <div class="admin-panel overflow-x-auto">
        <table class="admin-table min-w-full text-sm">
          <thead><tr><th>Batch</th><th>Status</th><th>Total</th><th>Succeeded</th><th>Failed</th><th>Started</th></tr></thead>
          <tbody>
            <tr v-for="row in runs" :key="row.id" class="cursor-pointer hover:bg-white/5" @click="loadRun(row.id)">
              <td class="font-medium text-cyan-300">{{ row.batch_key }}</td>
              <td><StatusBadge :status="row.status" /></td>
              <td>{{ row.total_records }}</td>
              <td>{{ row.succeeded_records }}</td>
              <td>{{ row.failed_records }}</td>
              <td>{{ row.started_at || '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section v-if="selected" class="space-y-3">
      <div>
        <h2 class="font-semibold text-white">Run evidence: {{ selected.batch_key }}</h2>
        <p v-if="selected.error_summary" class="mt-2 whitespace-pre-wrap text-xs text-red-300">{{ selected.error_summary }}</p>
      </div>
      <div class="admin-panel overflow-x-auto">
        <table class="admin-table min-w-full text-xs">
          <thead><tr><th>Entity</th><th>Legacy ID</th><th>Core ID</th><th>Operation</th><th>Status</th><th>Error</th></tr></thead>
          <tbody>
            <tr v-for="record in selected.records" :key="record.id">
              <td>{{ record.entity_type }}</td>
              <td class="font-mono">{{ record.legacy_id }}</td>
              <td class="font-mono">{{ record.core_entity_id || '-' }}</td>
              <td>{{ record.operation || '-' }}</td>
              <td><StatusBadge :status="record.status" /></td>
              <td class="max-w-sm whitespace-normal text-red-300">{{ record.error_message || '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default', middleware: ['auth'] })
const { apiFetch } = useApi()
const batchKey = ref(`cebu-import-${new Date().toISOString().slice(0, 10)}`)
const bundleText = ref(JSON.stringify({
  companies: [], users: [], branches: [], regions: [], service_areas: [],
  categories: [], catalog_items: [],
  buyer_projects: [], project_files: [], project_ai_runs: [], project_messages: [],
  project_metric_templates: [], project_metric_values: [], intents: [], project_line_items: [],
  project_price_snapshots: [], project_reports: [], project_report_versions: [],
  project_report_columns: [], project_report_rows: [], project_report_change_logs: [],
  offers: [], orders: [], transaction_reviews: [],
  wallets: [], wallet_transactions: [], wallet_deposits: [], addresses: [],
  shipping_routes: [], shipping_rates: [], order_shipping: [], deliveries: [],
  ad_campaigns: [], escrow_transactions: [], payouts: [], disputes: [],
  trust_profiles: [], trust_score_events: [], company_documents: [],
  kyc_analysis_results: [], verification_reviews: [], risk_flags: [],
  payment_events: [], region_payment_configs: [], currency_configs: [],
  payment_method_configs: [], fee_rules: [], fx_quotes: [], payment_quotes: [],
  fee_line_items: [], payment_intents: [], settlement_events: [], settlement_adjustments: [],
  notifications: [], notification_templates: [], messages: [], admin_notes: [],
  platform_settings: [], audit_logs: [], backup_schedules: [], backup_jobs: [],
}, null, 2))
const runs = ref<any[]>([])
const selected = ref<any | null>(null)
const readiness = ref<any | null>(null)
const running = ref(false)
const error = ref('')

async function loadRuns() {
  try {
    const [runResult, readinessResult] = await Promise.all([
      apiFetch<any>('/admin/cebu/migrations'),
      apiFetch<any>('/admin/cebu/migrations/readiness'),
    ])
    runs.value = runResult.items
    readiness.value = readinessResult
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Unable to load migration runs'
  }
}

async function loadRun(id: string) {
  try {
    selected.value = await apiFetch<any>(`/admin/cebu/migrations/${id}`)
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Unable to load migration evidence'
  }
}

async function loadFile(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (file) bundleText.value = await file.text()
}

async function runImport() {
  error.value = ''
  running.value = true
  try {
    const payload = JSON.parse(bundleText.value)
    payload.batch_key = batchKey.value
    const result = await apiFetch<any>('/admin/cebu/migrations/import', { method: 'POST', body: payload })
    await loadRuns()
    await loadRun(result.id)
  } catch (e: any) {
    error.value = e instanceof SyntaxError ? `Invalid JSON: ${e.message}` : e?.data?.detail || e?.message || 'Import failed'
  } finally {
    running.value = false
  }
}

onMounted(loadRuns)
</script>
