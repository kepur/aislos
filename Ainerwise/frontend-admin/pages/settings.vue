<template>
  <div>
    <h1 class="admin-page-title mb-6">{{ $t('admin.settings') }}</h1>
    <div class="grid grid-cols-1 gap-6">
      <div class="admin-card">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h2 class="admin-section-title">Demo Mode</h2>
            <p class="mt-1 text-sm text-gray-500">
              When enabled, PC/H5 login pages show prefilled demo credentials and demo-only accounts can log in.
            </p>
          </div>
          <button
            type="button"
            class="relative inline-flex h-7 w-12 shrink-0 items-center rounded-full transition"
            :class="demoMode.enabled ? 'bg-emerald-500' : 'bg-gray-300'"
            :disabled="loading"
            @click="toggleDemoMode"
          >
            <span
              class="inline-block h-5 w-5 transform rounded-full bg-white shadow transition"
              :class="demoMode.enabled ? 'translate-x-6' : 'translate-x-1'"
            ></span>
          </button>
        </div>

        <div class="mt-5 rounded-lg border p-4" :class="demoMode.enabled ? 'border-emerald-200 bg-emerald-50' : 'border-gray-200 bg-gray-50'">
          <p class="text-sm font-semibold" :class="demoMode.enabled ? 'text-emerald-700' : 'text-gray-600'">
            {{ demoMode.enabled ? 'Demo mode is currently enabled.' : 'Demo mode is currently disabled.' }}
          </p>
          <p class="mt-1 text-xs text-gray-500">
            The DB switch is served by backend API. Environment default is disabled; local demo can enable it here or with DEMO_MODE_ENABLED=true.
          </p>
        </div>

        <div class="mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            class="rounded-lg border border-cyan-500/40 px-4 py-2 text-sm text-cyan-200 hover:bg-cyan-500/10"
            :disabled="bootstrapping"
            @click="runBootstrap"
          >
            {{ bootstrapping ? 'Seeding…' : 'Seed demo data & enable' }}
          </button>
        </div>
        <p v-if="bootstrapNote" class="mt-2 text-xs text-emerald-400">{{ bootstrapNote }}</p>
        <p v-if="error" class="mt-3 text-sm text-red-600">{{ error }}</p>
      </div>

      <div class="admin-card">
        <h2 class="admin-section-title">Demo / Test Account Matrix</h2>
        <p class="mt-1 text-xs text-gray-500">
          Shows seeded account status, active switch, and real Portal grants from Core. Kiosk uses a revocable device token, not password login.
        </p>
        <div class="mt-4 overflow-x-auto">
          <table class="admin-table">
            <thead>
              <tr>
                <th>Account</th>
                <th>Credential</th>
                <th>Portal Grants</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in serviceAccounts" :key="row.key || row.email || row.label">
                <td>
                  <p class="font-semibold text-white">{{ row.label }}</p>
                  <p class="mt-1 text-xs text-slate-400">{{ row.actual_role || row.role }}</p>
                  <span v-if="row.demo_only" class="mt-2 inline-flex rounded-full bg-amber-500/10 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-amber-300">
                    blocked when demo off
                  </span>
                </td>
                <td>
                  <p v-if="row.email"><code class="text-xs">{{ row.email }}</code></p>
                  <p v-else class="text-xs text-slate-400">No email login</p>
                  <p class="mt-1"><code class="text-xs">{{ row.password || 'Device token issued once' }}</code></p>
                </td>
                <td class="text-xs">
                  <p class="text-slate-300">{{ ((row.portal_keys && row.portal_keys.length) ? row.portal_keys : row.portals || []).join(', ') || 'No portal grant yet' }}</p>
                  <p v-if="row.notes" class="mt-1 text-slate-500">{{ row.notes }}</p>
                </td>
                <td>
                  <span
                    class="rounded-full px-2 py-1 text-xs font-semibold"
                    :class="row.exists ? 'bg-emerald-500/10 text-emerald-300' : 'bg-slate-500/10 text-slate-300'"
                  >
                    {{ row.exists ? 'Created' : 'Missing' }}
                  </span>
                  <span
                    class="ml-2 rounded-full px-2 py-1 text-xs font-semibold"
                    :class="row.is_active ? 'bg-cyan-500/10 text-cyan-300' : 'bg-red-500/10 text-red-300'"
                  >
                    {{ row.auth_type === 'device_token' ? `${row.device_count || 0} active device(s)` : row.is_active ? 'Active' : 'Disabled' }}
                  </span>
                  <p v-if="row.grant_count !== undefined" class="mt-2 text-xs text-slate-500">
                    {{ row.membership_count || 0 }} membership(s) · {{ row.grant_count || 0 }} grant(s)
                  </p>
                </td>
                <td>
                  <button
                    v-if="row.id && row.actual_role !== 'super_admin'"
                    type="button"
                    class="rounded-lg border border-white/10 px-3 py-2 text-xs font-semibold text-slate-200 hover:bg-white/5 disabled:opacity-50"
                    :disabled="accountUpdating === row.id"
                    @click="toggleAccount(row)"
                  >
                    {{ accountUpdating === row.id ? 'Updating...' : row.is_active ? 'Disable' : 'Enable' }}
                  </button>
                  <span v-else class="text-xs text-slate-500">
                    {{ row.auth_type === 'device_token' ? 'Create/rotate in Showroom Devices' : 'Protected' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="admin-card">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h2 class="admin-section-title">Localization / Region Routing</h2>
            <p class="mt-1 text-xs text-gray-500">
              Controls URI language prefixes for every portal, plus the region list exposed to public sites and admin tools.
            </p>
          </div>
          <span class="rounded-full bg-indigo-500/10 px-3 py-1 text-xs font-semibold text-indigo-200">
            {{ localizationConfig?.translation_policy?.ai_output_policy || 'draft_only' }}
          </span>
        </div>

        <div class="mt-5 grid gap-4 lg:grid-cols-3">
          <label class="block">
            <span class="text-xs font-semibold uppercase tracking-wide text-slate-400">Enabled URI prefixes</span>
            <input
              v-model="localizationForm.enabled_locale_prefixes"
              class="mt-2 w-full rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-sm text-white outline-none focus:border-indigo-400"
              placeholder="en,cn,rs"
            />
            <span class="mt-1 block text-[11px] text-slate-500">Examples: /cn for Chinese, /rs for Serbian.</span>
          </label>
          <label class="block">
            <span class="text-xs font-semibold uppercase tracking-wide text-slate-400">Default prefix</span>
            <input
              v-model="localizationForm.default_locale_prefix"
              class="mt-2 w-full rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-sm text-white outline-none focus:border-indigo-400"
              placeholder="en"
            />
          </label>
          <label class="block">
            <span class="text-xs font-semibold uppercase tracking-wide text-slate-400">Enabled regions</span>
            <input
              v-model="localizationForm.enabled_region_codes"
              class="mt-2 w-full rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-sm text-white outline-none focus:border-indigo-400"
              placeholder="RS,PL,RO,CN"
            />
          </label>
        </div>

        <div class="mt-5 grid gap-3 lg:grid-cols-2">
          <label class="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 px-4 py-3">
            <span>
              <span class="block text-sm font-semibold text-white">AI translation drafts</span>
              <span class="block text-xs text-slate-500">Uses the configured AI integration; never publishes automatically.</span>
            </span>
            <input v-model="localizationForm.machine_translation_enabled" type="checkbox" class="h-5 w-5 rounded border-white/20 bg-slate-900" />
          </label>
          <label class="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 px-4 py-3">
            <span>
              <span class="block text-sm font-semibold text-white">Require admin review</span>
              <span class="block text-xs text-slate-500">Keep AI output in draft/review flow.</span>
            </span>
            <input v-model="localizationForm.translation_review_required" type="checkbox" class="h-5 w-5 rounded border-white/20 bg-slate-900" />
          </label>
        </div>

        <div class="mt-5 flex flex-wrap items-center gap-3">
          <button
            type="button"
            class="rounded-lg bg-indigo-500 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-400 disabled:opacity-50"
            :disabled="localizationSaving"
            @click="saveLocalizationConfig"
          >
            {{ localizationSaving ? 'Saving...' : 'Save localization config' }}
          </button>
          <button
            type="button"
            class="rounded-lg border border-white/10 px-4 py-2 text-sm font-semibold text-slate-200 hover:bg-white/5"
            @click="loadLocalizationConfig"
          >
            Reload
          </button>
          <span v-if="localizationNote" class="text-xs text-emerald-400">{{ localizationNote }}</span>
          <span v-if="localizationError" class="text-xs text-red-400">{{ localizationError }}</span>
        </div>

        <div v-if="localizationConfig" class="mt-5 grid gap-3 text-xs text-slate-400 lg:grid-cols-2">
          <div class="rounded-xl border border-white/10 bg-slate-950/50 p-3">
            <p class="font-semibold text-slate-200">Languages</p>
            <p class="mt-1">{{ localizationConfig.supported_locales?.map(item => `${item.uri_prefix}:${item.label}`).join(', ') || 'None' }}</p>
          </div>
          <div class="rounded-xl border border-white/10 bg-slate-950/50 p-3">
            <p class="font-semibold text-slate-200">Regions</p>
            <p class="mt-1">{{ localizationConfig.supported_regions?.map(item => `${item.code}:${item.name}`).join(', ') || 'No active region matched' }}</p>
          </div>
        </div>
      </div>

      <IntegrationSettings />
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { apiFetch } = useApi()
const { getDemoMode, updateDemoMode, defaultDemoMode } = useDemoMode()
const demoMode = ref(defaultDemoMode)
const loading = ref(false)
const bootstrapping = ref(false)
const accountUpdating = ref('')
const bootstrapNote = ref('')
const error = ref('')
const localizationConfig = ref<any | null>(null)
const localizationSaving = ref(false)
const localizationNote = ref('')
const localizationError = ref('')
const localizationForm = reactive({
  enabled_locale_prefixes: 'en,cn,rs',
  default_locale_prefix: 'en',
  enabled_region_codes: 'RS,PL,RO,CN',
  machine_translation_enabled: false,
  translation_review_required: true,
})

const serviceAccounts = computed(() => demoMode.value.account_matrix || demoMode.value.service_accounts || [])

onMounted(async () => {
  demoMode.value = await getDemoMode(true)
  await loadLocalizationConfig()
})

function hydrateLocalizationForm(payload: any) {
  localizationConfig.value = payload
  localizationForm.enabled_locale_prefixes = (payload.supported_locales || []).map((item: any) => item.uri_prefix).join(',')
  localizationForm.default_locale_prefix = payload.default_locale_prefix || 'en'
  localizationForm.enabled_region_codes = (payload.enabled_region_codes || []).join(',')
  localizationForm.machine_translation_enabled = Boolean(payload.translation_policy?.machine_translation_enabled)
  localizationForm.translation_review_required = payload.translation_policy?.review_required !== false
}

async function loadLocalizationConfig() {
  localizationError.value = ''
  try {
    hydrateLocalizationForm(await apiFetch('/localization/config'))
  } catch (e: any) {
    localizationError.value = e?.data?.detail || 'Failed to load localization config'
  }
}

async function saveLocalizationConfig() {
  localizationSaving.value = true
  localizationNote.value = ''
  localizationError.value = ''
  try {
    const payload = await apiFetch('/localization/config', {
      method: 'PUT',
      body: {
        enabled_locale_prefixes: localizationForm.enabled_locale_prefixes,
        default_locale_prefix: localizationForm.default_locale_prefix,
        enabled_region_codes: localizationForm.enabled_region_codes,
        machine_translation_enabled: localizationForm.machine_translation_enabled,
        translation_review_required: localizationForm.translation_review_required,
      },
    })
    hydrateLocalizationForm(payload)
    localizationNote.value = 'Localization config saved.'
  } catch (e: any) {
    localizationError.value = e?.data?.detail || 'Failed to save localization config'
  } finally {
    localizationSaving.value = false
  }
}

async function toggleDemoMode() {
  loading.value = true
  error.value = ''
  try {
    demoMode.value = await updateDemoMode(!demoMode.value.enabled)
  } catch (e: any) {
    error.value = e?.data?.detail || 'Failed to update demo mode'
  } finally {
    loading.value = false
  }
}

async function runBootstrap() {
  bootstrapping.value = true
  bootstrapNote.value = ''
  error.value = ''
  try {
    demoMode.value = await apiFetch('/demo-mode/bootstrap', { method: 'POST' })
    bootstrapNote.value = 'Demo data seeded; demo mode enabled.'
  } catch (e: any) {
    error.value = e?.data?.detail || 'Bootstrap failed'
  } finally {
    bootstrapping.value = false
  }
}

async function toggleAccount(row: any) {
  if (!row.id) return
  accountUpdating.value = row.id
  error.value = ''
  try {
    await apiFetch(`/users/${row.id}/active`, {
      method: 'PATCH',
      query: { is_active: !row.is_active },
    })
    demoMode.value = await getDemoMode(true)
  } catch (e: any) {
    error.value = e?.data?.detail || 'Failed to update account status'
  } finally {
    accountUpdating.value = ''
  }
}
</script>
