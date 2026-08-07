<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1 class="admin-page-title">{{ t('admin.seoCenter') }}</h1>
        <p class="admin-page-desc">
          Manage multilingual and regional SEO for the AinerWise PC and H5 official sites. AI can generate drafts, but publishing stays under human review.
        </p>
      </div>
      <div class="flex flex-wrap gap-2">
        <button class="rounded-xl border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50" :disabled="loading" @click="loadConfig">
          Refresh
        </button>
        <button class="btn-primary px-4 py-2 text-sm" :disabled="saving || loading" @click="saveConfig">
          Save SEO config
        </button>
      </div>
    </div>

    <div v-if="error" class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      {{ error }}
    </div>
    <div v-if="success" class="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
      {{ success }}
    </div>

    <div class="grid gap-4 md:grid-cols-4">
      <div class="admin-panel p-4">
        <p class="text-xs font-semibold uppercase tracking-[0.2em] text-gray-500">Default region</p>
        <p class="mt-2 text-3xl font-black text-gray-900">{{ form.default_region_code || '-' }}</p>
        <p class="mt-1 text-xs text-gray-500">Controls regional copy when visitors have no region cookie.</p>
      </div>
      <div class="admin-panel p-4">
        <p class="text-xs font-semibold uppercase tracking-[0.2em] text-gray-500">Locales</p>
        <p class="mt-2 text-3xl font-black text-gray-900">{{ localeCount }}</p>
        <p class="mt-1 text-xs text-gray-500">{{ localeText }}</p>
      </div>
      <div class="admin-panel p-4">
        <p class="text-xs font-semibold uppercase tracking-[0.2em] text-gray-500">Regions</p>
        <p class="mt-2 text-3xl font-black text-gray-900">{{ regionCount }}</p>
        <p class="mt-1 text-xs text-gray-500">{{ regionText }}</p>
      </div>
      <div class="admin-panel p-4">
        <p class="text-xs font-semibold uppercase tracking-[0.2em] text-gray-500">LLM automation</p>
        <p class="mt-2 text-3xl font-black" :class="aiConfigured ? 'text-emerald-600' : 'text-amber-600'">
          {{ aiConfigured ? 'Ready' : 'Off' }}
        </p>
        <p class="mt-1 text-xs text-gray-500">Batch generation always saves as review draft.</p>
      </div>
    </div>

    <div class="grid gap-6 xl:grid-cols-[minmax(0,1fr)_430px]">
      <section class="admin-panel p-5">
        <div class="mb-4">
          <h2 class="text-lg font-bold text-gray-900">Global SEO policy</h2>
          <p class="text-sm text-gray-500">This config is shared by frontend-pc and frontend-h5 through the public SEO middleware.</p>
        </div>

        <div class="grid gap-4 md:grid-cols-2">
          <label class="space-y-1">
            <span class="text-sm font-semibold text-gray-700">Site name</span>
            <input v-model="form.site_name" class="input-field w-full" />
          </label>
          <label class="space-y-1">
            <span class="text-sm font-semibold text-gray-700">Brand tagline</span>
            <input v-model="form.brand_tagline" class="input-field w-full" />
          </label>
          <label class="space-y-1">
            <span class="text-sm font-semibold text-gray-700">Default region code</span>
            <input v-model="form.default_region_code" class="input-field w-full uppercase" placeholder="RS" />
          </label>
          <label class="space-y-1">
            <span class="text-sm font-semibold text-gray-700">Target portals</span>
            <input v-model="portalsText" class="input-field w-full" placeholder="pc, h5, store" />
          </label>
          <label class="space-y-1">
            <span class="text-sm font-semibold text-gray-700">Enabled locales</span>
            <input v-model="localeText" class="input-field w-full" placeholder="en, zh, sr, pl" />
          </label>
          <label class="space-y-1">
            <span class="text-sm font-semibold text-gray-700">Enabled regions</span>
            <input v-model="regionText" class="input-field w-full uppercase" placeholder="RS, PL, RO" />
          </label>
        </div>

        <div class="mt-4 grid gap-4 md:grid-cols-2">
          <label class="flex items-start gap-3 rounded-2xl border border-gray-200 p-4">
            <input v-model="form.llm_automation_enabled" type="checkbox" class="mt-1 h-4 w-4 rounded border-gray-300 text-primary-600" />
            <span>
              <span class="block text-sm font-semibold text-gray-900">Allow LLM optimization</span>
              <span class="block text-xs text-gray-500">Only used when the batch request explicitly turns on AI.</span>
            </span>
          </label>
          <label class="flex items-start gap-3 rounded-2xl border border-gray-200 p-4">
            <input v-model="form.review_required" type="checkbox" class="mt-1 h-4 w-4 rounded border-gray-300 text-primary-600" />
            <span>
              <span class="block text-sm font-semibold text-gray-900">Review required</span>
              <span class="block text-xs text-gray-500">AI drafts cannot publish directly from automation.</span>
            </span>
          </label>
        </div>

        <div class="mt-4 grid gap-4 lg:grid-cols-2">
          <label class="space-y-1">
            <span class="text-sm font-semibold text-gray-700">Keyword rules, one per line</span>
            <textarea v-model="keywordText" class="input-field min-h-32 w-full font-mono text-xs" placeholder="smart building Serbia&#10;AI procurement Poland"></textarea>
          </label>
          <label class="space-y-1">
            <span class="text-sm font-semibold text-gray-700">Region overrides JSON</span>
            <textarea v-model="regionOverridesText" class="input-field min-h-32 w-full font-mono text-xs" spellcheck="false"></textarea>
          </label>
          <label class="space-y-1 lg:col-span-2">
            <span class="text-sm font-semibold text-gray-700">Page overrides JSON</span>
            <textarea v-model="pageOverridesText" class="input-field min-h-36 w-full font-mono text-xs" spellcheck="false"></textarea>
          </label>
        </div>
      </section>

      <aside class="space-y-6">
        <section class="admin-panel p-5">
          <h2 class="text-lg font-bold text-gray-900">Batch optimizer</h2>
          <p class="mt-1 text-sm text-gray-500">Generate multilingual, country-aware SEO drafts for all official pages.</p>
          <div class="mt-4 space-y-3">
            <label class="space-y-1 block">
              <span class="text-sm font-semibold text-gray-700">Batch locales</span>
              <input v-model="batchLocalesText" class="input-field w-full" />
            </label>
            <label class="space-y-1 block">
              <span class="text-sm font-semibold text-gray-700">Batch regions</span>
              <input v-model="batchRegionsText" class="input-field w-full uppercase" />
            </label>
            <label class="space-y-1 block">
              <span class="text-sm font-semibold text-gray-700">Page paths</span>
              <textarea v-model="batchPagesText" class="input-field min-h-24 w-full font-mono text-xs"></textarea>
            </label>
            <label class="space-y-1 block">
              <span class="text-sm font-semibold text-gray-700">Prompt hint</span>
              <textarea v-model="promptHint" class="input-field min-h-20 w-full" placeholder="Focus on Serbia hotels, KNX, AI building brain..."></textarea>
            </label>
            <label class="flex items-start gap-3 rounded-2xl border border-gray-200 p-3">
              <input v-model="batchUseAi" type="checkbox" class="mt-1 h-4 w-4 rounded border-gray-300 text-primary-600" />
              <span>
                <span class="block text-sm font-semibold text-gray-900">Use LLM for this batch</span>
                <span class="block text-xs text-gray-500">Falls back to deterministic SEO when AI is not configured.</span>
              </span>
            </label>
            <div class="flex gap-2">
              <button class="rounded-xl border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50" :disabled="batchBusy" @click="runBatch('/admin/seo/batch/preview')">
                Preview
              </button>
              <button class="btn-primary px-4 py-2 text-sm" :disabled="batchBusy" @click="runBatch('/admin/seo/batch/optimize')">
                Generate draft
              </button>
            </div>
          </div>
        </section>

        <section class="admin-panel p-5">
          <h2 class="text-lg font-bold text-gray-900">Last draft</h2>
          <p v-if="lastBatchDraft" class="mt-2 text-sm text-gray-600">
            {{ lastBatchDraft.total || 0 }} items · {{ lastBatchDraft.status || 'draft' }} · AI: {{ lastBatchDraft.ai_used ? 'yes' : 'no' }}
          </p>
          <p v-else class="mt-2 text-sm text-gray-500">No saved SEO batch draft yet.</p>
          <p v-if="batchResult?.ai_reason" class="mt-2 rounded-xl bg-amber-50 px-3 py-2 text-xs text-amber-700">
            {{ batchResult.ai_reason }}
          </p>
        </section>
      </aside>
    </div>

    <section class="admin-panel">
      <div class="flex flex-wrap items-center justify-between gap-3 px-5 pt-5">
        <div>
          <h2 class="text-lg font-bold text-gray-900">Official page SEO registry</h2>
          <p class="text-sm text-gray-500">Every page below is emitted with title, meta description, canonical URL, hreflang and regional geo meta on PC and H5.</p>
        </div>
        <span class="rounded-full bg-gray-100 px-3 py-1 text-xs font-semibold text-gray-600">{{ staticPages.length }} pages</span>
      </div>
      <div class="overflow-x-auto">
        <table class="admin-table mt-4 w-full text-sm">
          <thead>
            <tr>
              <th class="px-5 py-3 text-left font-semibold text-gray-500">Path</th>
              <th class="px-5 py-3 text-left font-semibold text-gray-500">EN title</th>
              <th class="px-5 py-3 text-left font-semibold text-gray-500">Priority</th>
              <th class="px-5 py-3 text-left font-semibold text-gray-500">Locales x regions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="page in staticPages" :key="page.path" class="border-t border-gray-100">
              <td class="px-5 py-3 font-mono text-xs text-gray-700">{{ page.path }}</td>
              <td class="px-5 py-3 text-gray-900">{{ page.title?.en || page.key }}</td>
              <td class="px-5 py-3 text-gray-600">{{ page.priority }}</td>
              <td class="px-5 py-3 text-gray-600">{{ localeCount }} x {{ regionCount }}</td>
            </tr>
            <tr v-if="!staticPages.length">
              <td colspan="4" class="px-5 py-8 text-center text-gray-500">Loading SEO registry...</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section v-if="batchItems.length" class="admin-panel">
      <div class="flex flex-wrap items-center justify-between gap-3 px-5 pt-5">
        <div>
          <h2 class="text-lg font-bold text-gray-900">Batch draft preview</h2>
          <p class="text-sm text-gray-500">Review these drafts before copying selected items into page overrides.</p>
        </div>
        <span class="rounded-full bg-primary-50 px-3 py-1 text-xs font-semibold text-primary-700">{{ batchItems.length }} items</span>
      </div>
      <div class="max-h-[560px] overflow-auto">
        <table class="admin-table mt-4 w-full text-sm">
          <thead>
            <tr>
              <th class="px-5 py-3 text-left font-semibold text-gray-500">Page</th>
              <th class="px-5 py-3 text-left font-semibold text-gray-500">Locale</th>
              <th class="px-5 py-3 text-left font-semibold text-gray-500">Region</th>
              <th class="px-5 py-3 text-left font-semibold text-gray-500">Title / description</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in batchItems" :key="`${item.path}-${item.locale}-${item.region_code}-${index}`" class="border-t border-gray-100 align-top">
              <td class="px-5 py-3 font-mono text-xs text-gray-700">{{ item.path }}</td>
              <td class="px-5 py-3 text-gray-700">{{ item.locale }}</td>
              <td class="px-5 py-3 text-gray-700">{{ item.region_code }}</td>
              <td class="px-5 py-3">
                <p class="font-semibold text-gray-900">{{ item.title }}</p>
                <p class="mt-1 text-xs leading-5 text-gray-500">{{ item.description }}</p>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { t } = useI18n({ useScope: 'global' })
const { apiFetch } = useApi()

const loading = ref(false)
const saving = ref(false)
const batchBusy = ref(false)
const error = ref('')
const success = ref('')
const aiConfigured = ref(false)
const staticPages = ref<any[]>([])
const lastBatchDraft = ref<any | null>(null)
const batchResult = ref<any | null>(null)

const form = reactive<any>({
  site_name: 'AinerWise',
  brand_tagline: 'AI Solution & Procurement Platform',
  default_region_code: 'RS',
  enabled_region_codes: ['RS', 'PL'],
  enabled_locales: ['en', 'zh', 'sr', 'pl'],
  target_portals: ['pc', 'h5', 'store'],
  llm_automation_enabled: false,
  review_required: true,
  region_overrides: {
    RS: { name: 'Serbia', cities: ['Belgrade', 'Novi Sad'], currency: 'EUR' },
    PL: { name: 'Poland', cities: ['Warsaw', 'Krakow'], currency: 'PLN' },
  },
  page_overrides: {},
  keyword_rules: ['AI smart building', 'AI procurement', 'KNX compatible', 'local installation', 'lifecycle maintenance'],
  batch_policy: { max_items: 80, publish_mode: 'manual_review' },
})

const localeText = ref('en, zh, sr, pl')
const regionText = ref('RS, PL')
const portalsText = ref('pc, h5, store')
const keywordText = ref('')
const regionOverridesText = ref('{}')
const pageOverridesText = ref('{}')
const batchLocalesText = ref('en, zh, sr, pl')
const batchRegionsText = ref('RS, PL')
const batchPagesText = ref('/, /solutions, /products, /ai-building-brain, /services, /submit-requirement, /about, /contact')
const batchUseAi = ref(false)
const promptHint = ref('')

const localeCount = computed(() => splitCsv(localeText.value).length)
const regionCount = computed(() => splitCsv(regionText.value).length)
const batchItems = computed(() => batchResult.value?.items || lastBatchDraft.value?.items || [])

function splitCsv(value: string) {
  return value
    .split(/[,\n]/)
    .map(item => item.trim())
    .filter(Boolean)
}

function parseJsonBlock(value: string, label: string) {
  try {
    return JSON.parse(value || '{}')
  } catch {
    throw new Error(`${label} must be valid JSON.`)
  }
}

function prettify(value: any) {
  return JSON.stringify(value || {}, null, 2)
}

function applyConfig(payload: any) {
  const config = payload?.config || payload || {}
  Object.assign(form, {
    site_name: config.site_name || 'AinerWise',
    brand_tagline: config.brand_tagline || 'AI Solution & Procurement Platform',
    default_region_code: String(config.default_region_code || 'RS').toUpperCase(),
    enabled_region_codes: config.enabled_region_codes || ['RS', 'PL'],
    enabled_locales: config.enabled_locales || ['en', 'zh', 'sr', 'pl'],
    target_portals: config.target_portals || ['pc', 'h5', 'store'],
    llm_automation_enabled: Boolean(config.llm_automation_enabled),
    review_required: config.review_required !== false,
    region_overrides: config.region_overrides || {},
    page_overrides: config.page_overrides || {},
    keyword_rules: config.keyword_rules || [],
    batch_policy: config.batch_policy || { max_items: 80, publish_mode: 'manual_review' },
  })
  localeText.value = form.enabled_locales.join(', ')
  regionText.value = form.enabled_region_codes.join(', ')
  portalsText.value = form.target_portals.join(', ')
  keywordText.value = form.keyword_rules.join('\n')
  regionOverridesText.value = prettify(form.region_overrides)
  pageOverridesText.value = prettify(form.page_overrides)
  batchLocalesText.value = localeText.value
  batchRegionsText.value = regionText.value
  aiConfigured.value = Boolean(payload?.ai_configured)
  staticPages.value = payload?.static_pages || staticPages.value
  lastBatchDraft.value = payload?.last_batch_draft || lastBatchDraft.value
}

function buildConfigPayload() {
  return {
    site_name: form.site_name,
    brand_tagline: form.brand_tagline,
    default_region_code: String(form.default_region_code || 'RS').toUpperCase(),
    enabled_region_codes: splitCsv(regionText.value).map(item => item.toUpperCase()),
    enabled_locales: splitCsv(localeText.value).map(item => item.toLowerCase()),
    target_portals: splitCsv(portalsText.value).map(item => item.toLowerCase()),
    llm_automation_enabled: Boolean(form.llm_automation_enabled),
    review_required: Boolean(form.review_required),
    region_overrides: parseJsonBlock(regionOverridesText.value, 'Region overrides'),
    page_overrides: parseJsonBlock(pageOverridesText.value, 'Page overrides'),
    keyword_rules: keywordText.value.split('\n').map(item => item.trim()).filter(Boolean),
    batch_policy: form.batch_policy || { max_items: 80, publish_mode: 'manual_review' },
  }
}

function buildBatchPayload(saveDraft: boolean) {
  return {
    locales: splitCsv(batchLocalesText.value).map(item => item.toLowerCase()),
    region_codes: splitCsv(batchRegionsText.value).map(item => item.toUpperCase()),
    page_paths: splitCsv(batchPagesText.value),
    use_ai: Boolean(batchUseAi.value),
    save_draft: saveDraft,
    prompt_hint: promptHint.value || null,
  }
}

async function loadConfig() {
  loading.value = true
  error.value = ''
  success.value = ''
  try {
    const payload = await apiFetch<any>('/admin/seo/config')
    applyConfig(payload)
  } catch (err: any) {
    error.value = err?.data?.detail || err?.message || 'Unable to load SEO config.'
  } finally {
    loading.value = false
  }
}

async function saveConfig() {
  saving.value = true
  error.value = ''
  success.value = ''
  try {
    const payload = await apiFetch<any>('/admin/seo/config', {
      method: 'PUT',
      body: buildConfigPayload(),
    })
    applyConfig(payload)
    success.value = 'SEO config saved. PC and H5 will use it through /seo/config.'
  } catch (err: any) {
    error.value = err?.data?.detail || err?.message || 'Unable to save SEO config.'
  } finally {
    saving.value = false
  }
}

async function runBatch(path: '/admin/seo/batch/preview' | '/admin/seo/batch/optimize') {
  batchBusy.value = true
  error.value = ''
  success.value = ''
  try {
    const payload = await apiFetch<any>(path, {
      method: 'POST',
      body: buildBatchPayload(path.endsWith('/optimize')),
    })
    batchResult.value = payload
    if (path.endsWith('/optimize')) {
      lastBatchDraft.value = payload
      success.value = `SEO draft generated: ${payload.total || 0} items, review required.`
    } else {
      success.value = `SEO preview ready: ${payload.total || 0} items.`
    }
  } catch (err: any) {
    error.value = err?.data?.detail || err?.message || 'Unable to run SEO batch.'
  } finally {
    batchBusy.value = false
  }
}

onMounted(loadConfig)
</script>
