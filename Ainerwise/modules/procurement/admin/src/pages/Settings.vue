<template>
  <div class="space-y-4">
    <p class="text-sm text-slate-500">Changes are saved immediately on blur or toggle.</p>

    <div class="card p-5 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
      <div>
        <p class="text-sm font-semibold text-slate-900">Demo Mode</p>
        <p class="mt-1 text-sm text-slate-500">
          Shows buyer/supplier demo credentials on PC and H5 login pages. When disabled, demo account login is blocked by the backend.
        </p>
      </div>
      <button
        class="w-14 h-8 rounded-full relative transition-colors flex-shrink-0"
        :class="demoSetting?.value === 'true' ? 'bg-primary-600' : 'bg-slate-200'"
        :disabled="!demoSetting"
        @click="demoSetting && toggle(demoSetting)"
      >
        <span class="absolute top-1 w-6 h-6 bg-white rounded-full shadow transition-all"
          :class="demoSetting?.value === 'true' ? 'left-7' : 'left-1'" />
      </button>
    </div>

    <div class="card p-5 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
      <div>
        <p class="text-sm font-semibold text-slate-900">Wallet Payments (Legacy Custody Mode)</p>
        <p class="mt-1 text-sm text-slate-500">
          OFF = direct-payment mode (AISLOS default): buyers pay suppliers directly and record the reference;
          the platform never holds funds. ON re-enables the legacy wallet top-up / escrow flow.
        </p>
      </div>
      <button
        class="w-14 h-8 rounded-full relative transition-colors flex-shrink-0"
        :class="walletPaymentsEnabled ? 'bg-amber-500' : 'bg-slate-200'"
        :disabled="savingPaymentMode"
        @click="togglePaymentMode"
      >
        <span class="absolute top-1 w-6 h-6 bg-white rounded-full shadow transition-all"
          :class="walletPaymentsEnabled ? 'left-7' : 'left-1'" />
      </button>
    </div>

    <div class="card p-5 space-y-5">
      <div class="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
        <div>
          <p class="text-sm font-semibold text-slate-900">Market Localization & Regions</p>
          <p class="mt-1 text-sm text-slate-500">
            Controls AISLOS Market URI languages such as /cn and /rs, plus the regions exposed to the standalone Market PC/H5.
          </p>
        </div>
        <button class="btn-primary" :disabled="savingMarket" @click="saveMarketConfig">
          {{ savingMarket ? 'Saving…' : 'Save Market Config' }}
        </button>
      </div>

      <div class="grid gap-5 xl:grid-cols-[1fr_260px]">
        <div>
          <p class="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">Enabled URI Languages</p>
          <div class="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            <label
              v-for="locale in marketLocaleOptions"
              :key="locale.prefix"
              class="flex items-center justify-between rounded-xl border border-slate-200 px-3 py-2 text-sm"
            >
              <span>
                <span class="font-semibold text-slate-800">{{ locale.label }}</span>
                <span class="ml-2 font-mono text-xs text-primary-600">/{{ locale.prefix }}</span>
              </span>
              <input type="checkbox" :checked="enabledLocalePrefixes.includes(locale.prefix)" @change="toggleLocalePrefix(locale.prefix)" />
            </label>
          </div>
        </div>

        <label class="block">
          <span class="mb-2 block text-xs font-semibold uppercase tracking-wide text-slate-400">Default URI</span>
          <select v-model="defaultLocalePrefix" class="input">
            <option v-for="locale in enabledLocaleOptions" :key="locale.prefix" :value="locale.prefix">
              /{{ locale.prefix }} · {{ locale.label }}
            </option>
          </select>
        </label>
      </div>

      <div>
        <p class="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">Supported Regions</p>
        <div v-if="regions.length" class="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          <label
            v-for="region in regions"
            :key="region.code"
            class="flex items-center justify-between rounded-xl border border-slate-200 px-3 py-2 text-sm"
            :class="region.status === 'ACTIVE' ? 'bg-white' : 'bg-slate-50 text-slate-400'"
          >
            <span>
              <span class="font-semibold">{{ region.name }}</span>
              <span class="ml-2 font-mono text-xs">{{ region.code }}</span>
            </span>
            <input type="checkbox" :disabled="region.status !== 'ACTIVE'" :checked="enabledRegionCodes.includes(region.code)" @change="toggleRegionCode(region.code)" />
          </label>
        </div>
        <input
          v-else
          v-model="regionCsvDraft"
          class="input"
          placeholder="RS,CN,PH"
        />
        <p class="mt-2 text-xs text-slate-400">
          Active regions are managed in Admin → Regions. This setting only decides which active regions the Market frontends should expose.
        </p>
      </div>
    </div>

    <div class="card overflow-hidden">
      <table class="w-full">
        <thead>
          <tr>
            <th class="table-th w-64">Key</th>
            <th class="table-th">Description</th>
            <th class="table-th w-48">Value</th>
            <th class="table-th w-24">Updated</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading"><td colspan="4" class="table-td text-center py-10 text-slate-400">Loading…</td></tr>
          <tr v-for="s in settings" :key="s.key" class="hover:bg-slate-50">
            <td class="table-td font-mono text-xs font-semibold text-slate-700">{{ s.key }}</td>
            <td class="table-td text-slate-500 text-xs">{{ s.description || '—' }}</td>
            <td class="table-td">
              <!-- Boolean toggle -->
              <template v-if="s.value === 'true' || s.value === 'false'">
                <button
                  class="w-11 h-6 rounded-full relative transition-colors"
                  :class="s.value === 'true' ? 'bg-primary-600' : 'bg-slate-200'"
                  @click="toggle(s)"
                >
                  <span class="absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-all"
                    :class="s.value === 'true' ? 'left-[22px]' : 'left-0.5'" />
                </button>
              </template>
              <!-- Text input -->
              <template v-else>
                <input v-model="s._draft" class="input py-1 text-xs" @blur="save(s)" @keyup.enter="save(s)" />
              </template>
            </td>
            <td class="table-td text-xs text-slate-400">{{ fmtDate(s.updated_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { api, fmtDate } from '@/utils/api'

const loading = ref(true)
const settings = ref([])
const regions = ref([])
const savingMarket = ref(false)
const walletPaymentsEnabled = ref(false)
const savingPaymentMode = ref(false)
const enabledLocalePrefixes = ref(['en', 'cn', 'rs'])
const defaultLocalePrefix = ref('en')
const enabledRegionCodes = ref(['RS', 'CN', 'PH'])
const regionCsvDraft = ref('RS,CN,PH')
const demoSetting = computed(() => settings.value.find(s => s.key === 'DEMO_MODE'))
const marketLocaleOptions = [
  { prefix: 'en', code: 'EN', label: 'English' },
  { prefix: 'cn', code: 'ZH', label: '中文' },
  { prefix: 'rs', code: 'SR', label: 'Srpski' },
  { prefix: 'ba', code: 'BS', label: 'Bosanski' },
  { prefix: 'pl', code: 'PL', label: 'Polski' },
  { prefix: 'de', code: 'DE', label: 'Deutsch' },
  { prefix: 'ro', code: 'RO', label: 'Română' },
]
const enabledLocaleOptions = computed(() => {
  const selected = marketLocaleOptions.filter(locale => enabledLocalePrefixes.value.includes(locale.prefix))
  return selected.length ? selected : [marketLocaleOptions[0]]
})

function splitCsv(value) {
  return String(value || '')
    .split(',')
    .map(item => item.trim())
    .filter(Boolean)
}

function settingValue(key, fallback = '') {
  return settings.value.find(s => s.key === key)?.value ?? fallback
}

function syncMarketConfigFromSettings() {
  enabledLocalePrefixes.value = splitCsv(settingValue('market_enabled_locale_prefixes', 'en,cn,rs')).map(item => item.toLowerCase())
  if (!enabledLocalePrefixes.value.length) enabledLocalePrefixes.value = ['en']
  defaultLocalePrefix.value = String(settingValue('market_default_locale_prefix', enabledLocalePrefixes.value[0] || 'en')).toLowerCase()
  if (!enabledLocalePrefixes.value.includes(defaultLocalePrefix.value)) defaultLocalePrefix.value = enabledLocalePrefixes.value[0]
  enabledRegionCodes.value = splitCsv(settingValue('market_enabled_region_codes', 'RS,CN,PH')).map(item => item.toUpperCase())
  regionCsvDraft.value = enabledRegionCodes.value.join(',')
}

function toggleLocalePrefix(prefix) {
  const set = new Set(enabledLocalePrefixes.value)
  if (set.has(prefix)) set.delete(prefix)
  else set.add(prefix)
  enabledLocalePrefixes.value = Array.from(set)
  if (!enabledLocalePrefixes.value.length) enabledLocalePrefixes.value = ['en']
  if (!enabledLocalePrefixes.value.includes(defaultLocalePrefix.value)) defaultLocalePrefix.value = enabledLocalePrefixes.value[0]
}

function toggleRegionCode(code) {
  const normalized = String(code || '').toUpperCase()
  const set = new Set(enabledRegionCodes.value)
  if (set.has(normalized)) set.delete(normalized)
  else set.add(normalized)
  enabledRegionCodes.value = Array.from(set).sort()
  regionCsvDraft.value = enabledRegionCodes.value.join(',')
}

async function upsertSetting(key, value, description) {
  const { data } = await api.put(`/admin/settings/${key}`, { value, description })
  const existing = settings.value.find(s => s.key === key)
  if (existing) {
    Object.assign(existing, { ...data, _draft: data.value })
  } else {
    settings.value.push({ ...data, _draft: data.value })
  }
  return data
}

async function save(s) {
  const val = s._draft ?? s.value
  if (val === s.value) return
  try {
    const { data } = await api.put(`/admin/settings/${s.key}`, { value: val })
    s.value = data.value
    s._draft = data.value
    s.updated_at = data.updated_at
  } catch (e) {
    alert(e.response?.data?.detail || 'Save failed')
    s._draft = s.value
  }
}

async function toggle(s) {
  s._draft = s.value === 'true' ? 'false' : 'true'
  await save(s)
}

async function saveMarketConfig() {
  savingMarket.value = true
  try {
    const regionCodes = regions.value.length
      ? enabledRegionCodes.value
      : splitCsv(regionCsvDraft.value).map(item => item.toUpperCase())
    await api.put('/localization/config', {
      enabled_locale_prefixes: enabledLocalePrefixes.value,
      default_locale_prefix: defaultLocalePrefix.value,
      enabled_region_codes: regionCodes,
    })
    enabledRegionCodes.value = regionCodes
    regionCsvDraft.value = regionCodes.join(',')
  } catch (e) {
    alert(e.response?.data?.detail || 'Save failed')
  } finally {
    savingMarket.value = false
  }
}

async function togglePaymentMode() {
  const next = !walletPaymentsEnabled.value
  if (next && !confirm('Re-enable the legacy wallet/escrow custody flow? AISLOS default is direct-payment (records only).')) return
  savingPaymentMode.value = true
  try {
    const { data } = await api.put('/admin/market-settings', { wallet_payments_enabled: next })
    walletPaymentsEnabled.value = Boolean(data?.wallet_payments_enabled)
  } catch (e) {
    alert(e.response?.data?.detail || 'Save failed')
  } finally {
    savingPaymentMode.value = false
  }
}

async function load() {
  loading.value = true
  try {
    const [settingsData, regionsData, localizationData, marketSettings] = await Promise.all([
      api.get('/admin/settings').then(r => r.data),
      api.get('/admin/regions').then(r => r.data).catch(() => []),
      api.get('/localization/config').then(r => r.data).catch(() => null),
      api.get('/admin/market-settings').then(r => r.data).catch(() => null),
    ])
    walletPaymentsEnabled.value = Boolean(marketSettings?.wallet_payments_enabled)
    settings.value = settingsData.map(s => ({ ...s, _draft: s.value }))
    regions.value = regionsData
    if (localizationData) {
      enabledLocalePrefixes.value = (localizationData.supported_locales || []).map(item => item.uri_prefix)
      defaultLocalePrefix.value = localizationData.default_locale_prefix || enabledLocalePrefixes.value[0] || 'en'
      enabledRegionCodes.value = (localizationData.enabled_region_codes || []).map(item => String(item).toUpperCase())
      regionCsvDraft.value = enabledRegionCodes.value.join(',')
    } else {
      syncMarketConfigFromSettings()
    }
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
