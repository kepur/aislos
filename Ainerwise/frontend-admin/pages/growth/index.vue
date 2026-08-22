<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="admin-page-title">Growth · Sourcing &amp; Syndication</h1>
      <div class="flex gap-2 text-xs">
        <span v-for="p in providers" :key="p.key"
          class="rounded-full border border-gray-300 px-2.5 py-1 text-gray-600">
          {{ p.label }}
        </span>
      </div>
    </div>

    <div v-if="error" class="mb-4 rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
      {{ error }}
      <button class="ml-2 font-semibold underline" @click="loadAll">Retry</button>
    </div>
    <div v-if="notice" class="mb-4 rounded-lg border border-emerald-300 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
      {{ notice }}
    </div>

    <!-- Tabs -->
    <div class="mb-5 flex gap-1 border-b border-gray-200">
      <button v-for="t in tabs" :key="t.key" @click="tab = t.key"
        :class="['px-4 py-2 text-sm font-medium -mb-px border-b-2',
                 tab === t.key ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700']">
        {{ t.label }}
      </button>
    </div>

    <!-- ── Import & Pipeline ── -->
    <div v-show="tab === 'pipeline'" class="admin-panel p-5">
      <h2 class="text-base font-semibold mb-4">Import a source item &amp; run the full chain</h2>
      <p class="text-xs text-gray-500 mb-4">
        Import → translate → auto-price → create a marketing draft. Source is normalised only
        (no scraping); paste an item or connect a licensed feed later.
      </p>
      <form @submit.prevent="runPipeline" class="grid grid-cols-2 gap-4">
        <div>
          <label class="lbl">Source</label>
          <input v-model="pf.source" class="input-field" placeholder="1688 / taobao / manual" />
        </div>
        <div>
          <label class="lbl">External ID *</label>
          <input v-model="pf.external_id" required class="input-field" placeholder="SKU-..." />
        </div>
        <div class="col-span-2">
          <label class="lbl">Title</label>
          <input v-model="pf.title" class="input-field" />
        </div>
        <div class="col-span-2">
          <label class="lbl">Description</label>
          <textarea v-model="pf.description" rows="2" class="input-field"></textarea>
        </div>
        <div>
          <label class="lbl">Source price (minor)</label>
          <input v-model.number="pf.price_minor" type="number" class="input-field" placeholder="8000 = ¥80.00" />
        </div>
        <div>
          <label class="lbl">Source currency</label>
          <input v-model="pf.price_currency" class="input-field" placeholder="CNY" />
        </div>
        <div>
          <label class="lbl">Target language</label>
          <select v-model="pf.target_lang" class="input-field">
            <option value="en">English</option>
            <option value="sr">Srpski</option>
            <option value="pl">Polski</option>
            <option value="zh">中文</option>
          </select>
        </div>
        <div>
          <label class="lbl">FX rate (source→sell)</label>
          <input v-model.number="pf.fx_rate" type="number" step="0.0001" class="input-field" placeholder="0.13" />
        </div>
        <div>
          <label class="lbl">Price rule *</label>
          <select v-model="pf.price_rule_id" required class="input-field">
            <option value="" disabled>Select a rule…</option>
            <option v-for="r in rules" :key="r.id" :value="r.id">{{ r.name }} ({{ r.sell_currency }})</option>
          </select>
        </div>
        <div>
          <label class="lbl">Publish channel (draft)</label>
          <input v-model="pf.channel" class="input-field" placeholder="instagram" />
        </div>
        <div class="col-span-2">
          <button type="submit" :disabled="busy || !rules.length" class="btn-primary text-sm">
            {{ busy ? 'Running…' : 'Run pipeline' }}
          </button>
          <span v-if="!rules.length" class="ml-3 text-xs text-amber-600">Create a price rule first.</span>
        </div>
      </form>
    </div>

    <!-- ── Price Rules ── -->
    <div v-show="tab === 'rules'" class="space-y-5">
      <div class="admin-panel p-5">
        <h2 class="text-base font-semibold mb-4">New price rule</h2>
        <form @submit.prevent="createRule" class="grid grid-cols-3 gap-4">
          <div class="col-span-3"><label class="lbl">Name *</label><input v-model="rf.name" required class="input-field" /></div>
          <div><label class="lbl">Sell currency</label><input v-model="rf.sell_currency" class="input-field" /></div>
          <div><label class="lbl">Freight %</label><input v-model.number="rf.freight_pct" type="number" step="0.01" class="input-field" /></div>
          <div><label class="lbl">Freight fixed (minor)</label><input v-model.number="rf.freight_fixed_minor" type="number" class="input-field" /></div>
          <div><label class="lbl">Duties %</label><input v-model.number="rf.duties_pct" type="number" step="0.01" class="input-field" /></div>
          <div><label class="lbl">Target margin %</label><input v-model.number="rf.target_margin_pct" type="number" step="0.01" class="input-field" /></div>
          <div><label class="lbl">Platform fee %</label><input v-model.number="rf.platform_fee_pct" type="number" step="0.01" class="input-field" /></div>
          <div><label class="lbl">Round to (minor)</label><input v-model.number="rf.round_to_minor" type="number" class="input-field" placeholder="100 = round to whole" /></div>
          <div><label class="lbl">Reprice cadence</label>
            <select v-model="rf.reprice_cadence" class="input-field"><option>manual</option><option>daily</option><option>weekly</option></select>
          </div>
          <div><label class="lbl">Reprice threshold %</label><input v-model.number="rf.reprice_threshold_pct" type="number" step="0.01" class="input-field" /></div>
          <div class="col-span-3"><button type="submit" :disabled="busy" class="btn-primary text-sm">{{ busy ? 'Saving…' : 'Create rule' }}</button></div>
        </form>
      </div>
      <div class="admin-panel">
        <table class="admin-table w-full text-sm">
          <thead><tr>
            <th class="th">Name</th><th class="th">Sell</th><th class="th">Freight</th><th class="th">Duties</th>
            <th class="th">Margin</th><th class="th">Fee</th><th class="th">Round</th><th class="th">Reprice</th><th class="th"></th>
          </tr></thead>
          <tbody>
            <tr v-for="r in rules" :key="r.id" class="border-b">
              <td class="td font-medium">{{ r.name }}</td>
              <td class="td">{{ r.sell_currency }}</td>
              <td class="td">{{ pct(r.freight_pct) }}<span v-if="r.freight_fixed_minor"> +{{ money(r.freight_fixed_minor, r.sell_currency) }}</span></td>
              <td class="td">{{ pct(r.duties_pct) }}</td>
              <td class="td">{{ pct(r.target_margin_pct) }}</td>
              <td class="td">{{ pct(r.platform_fee_pct) }}</td>
              <td class="td">{{ r.round_to_minor || '-' }}</td>
              <td class="td">{{ r.reprice_cadence }} / {{ pct(r.reprice_threshold_pct) }}</td>
              <td class="td"><button @click="repriceRule(r)" class="text-primary-600 hover:underline text-xs">Reprice now</button></td>
            </tr>
            <tr v-if="!rules.length"><td colspan="9" class="px-4 py-8 text-center text-gray-500">No price rules yet.</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ── Arbitrage / Listings ── -->
    <div v-show="tab === 'listings'" class="admin-panel">
      <div class="flex items-center justify-between p-4">
        <h2 class="text-base font-semibold">Sourced listings — cost → sell → margin</h2>
        <button @click="loadListings" class="text-xs text-primary-600 hover:underline">Refresh</button>
      </div>
      <table class="admin-table w-full text-sm">
        <thead><tr>
          <th class="th">Item</th><th class="th">Source</th><th class="th">Cost</th><th class="th">Sell</th>
          <th class="th">Margin</th><th class="th">Status</th><th class="th">Actions</th>
        </tr></thead>
        <tbody>
          <tr v-for="l in listings" :key="l.id" class="border-b align-top">
            <td class="td">
              <div class="font-medium">{{ l.translated_title || l.title || l.external_id }}</div>
              <div class="text-xs text-gray-400 font-mono">{{ l.external_id }}</div>
            </td>
            <td class="td">{{ l.source }}</td>
            <td class="td">{{ l.source_price_minor ? money(l.source_price_minor, l.source_currency) : '-' }}</td>
            <td class="td font-semibold">{{ l.sell_price_minor ? money(l.sell_price_minor, l.sell_currency) : '-' }}</td>
            <td class="td">
              <span v-if="marginOf(l) !== null" :class="marginOf(l)! >= 0.2 ? 'text-emerald-600' : 'text-amber-600'">
                {{ (marginOf(l)! * 100).toFixed(1) }}%
              </span><span v-else>-</span>
            </td>
            <td class="td"><span class="rounded-full bg-gray-100 px-2 py-0.5 text-xs">{{ l.status }}</span></td>
            <td class="td">
              <div class="flex flex-wrap gap-2 text-xs">
                <button @click="translateOne(l)" class="text-primary-600 hover:underline">Translate</button>
                <button @click="draftAndPublish(l)" class="text-primary-600 hover:underline">Draft→Publish</button>
              </div>
            </td>
          </tr>
          <tr v-if="!listings.length"><td colspan="7" class="px-4 py-8 text-center text-gray-500">No listings yet — run a pipeline.</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { apiFetch } = useApi()
const error = ref('')
const notice = ref('')
const busy = ref(false)
const tab = ref('pipeline')
const tabs = [
  { key: 'pipeline', label: 'Import & Pipeline' },
  { key: 'rules', label: 'Price Rules' },
  { key: 'listings', label: 'Arbitrage / Listings' },
]

const providers = ref<any[]>([])
const rules = ref<any[]>([])
const listings = ref<any[]>([])

const pf = reactive<any>({
  source: '1688', external_id: '', title: '', description: '',
  price_minor: null, price_currency: 'CNY', target_lang: 'en',
  fx_rate: 0.13, price_rule_id: '', channel: 'instagram',
})
const rf = reactive<any>({
  name: '', sell_currency: 'EUR', freight_pct: 0.15, freight_fixed_minor: null,
  duties_pct: 0, target_margin_pct: 0.30, platform_fee_pct: 0.08,
  round_to_minor: 100, reprice_cadence: 'manual', reprice_threshold_pct: 0.02,
})

onMounted(loadAll)

async function loadAll() {
  error.value = ''
  try {
    const [prov, rl] = await Promise.all([
      apiFetch<any>('/growth/providers'),
      apiFetch<any>('/growth/price-rules'),
    ])
    providers.value = prov.providers || []
    rules.value = rl || []
    if (!pf.price_rule_id && rules.value.length) pf.price_rule_id = rules.value[0].id
    await loadListings()
  } catch (e: any) { error.value = errText(e, 'load Growth data') }
}

async function loadListings() {
  try { listings.value = await apiFetch<any>('/growth/listings') || [] }
  catch (e: any) { error.value = errText(e, 'load listings') }
}

async function createRule() {
  busy.value = true; error.value = ''; notice.value = ''
  try {
    await apiFetch('/growth/price-rules', { method: 'POST', body: { ...rf } })
    notice.value = 'Price rule created.'
    await loadAll()
  } catch (e: any) { error.value = errText(e, 'create rule') } finally { busy.value = false }
}

async function repriceRule(r: any) {
  busy.value = true; error.value = ''; notice.value = ''
  try {
    const res = await apiFetch<any>(`/growth/price-rules/${r.id}/reprice`, { method: 'POST', body: {} })
    notice.value = `Repriced ${res.changed}/${res.listings} listing(s).`
    await loadListings()
  } catch (e: any) { error.value = errText(e, 'reprice') } finally { busy.value = false }
}

async function runPipeline() {
  busy.value = true; error.value = ''; notice.value = ''
  try {
    const body: any = { ...pf }
    if (body.price_minor == null) delete body.price_minor
    const res = await apiFetch<any>('/growth/pipeline', { method: 'POST', body })
    notice.value = `Pipeline done — listing priced ${money(res.listing.sell_price_minor, res.listing.sell_currency)}, draft ${res.marketing_asset_id}.`
    tab.value = 'listings'
    await loadListings()
  } catch (e: any) { error.value = errText(e, 'run pipeline') } finally { busy.value = false }
}

async function translateOne(l: any) {
  busy.value = true; error.value = ''; notice.value = ''
  try {
    await apiFetch(`/growth/listings/${l.id}/translate`, { method: 'POST', body: { target_lang: l.target_lang || 'en' } })
    notice.value = 'Translation requested (passthrough if no AI provider configured).'
    await loadListings()
  } catch (e: any) { error.value = errText(e, 'translate') } finally { busy.value = false }
}

async function draftAndPublish(l: any) {
  busy.value = true; error.value = ''; notice.value = ''
  try {
    const d = await apiFetch<any>(`/growth/listings/${l.id}/draft`, { method: 'POST', body: { channel: 'instagram' } })
    await apiFetch('/growth/publish', { method: 'POST', body: { asset_id: d.marketing_asset_id, platforms: ['instagram', 'facebook'] } })
    notice.value = 'Draft created and scheduled to Instagram + Facebook.'
    await loadListings()
  } catch (e: any) { error.value = errText(e, 'draft/publish') } finally { busy.value = false }
}

function marginOf(l: any): number | null {
  const m = l?.price_quote_json?.margin_pct
  return m != null ? Number(m) : null
}
function pct(v: any): string { return v != null ? `${(Number(v) * 100).toFixed(1)}%` : '-' }
function money(minor: any, cur: string): string {
  if (minor == null) return '-'
  return `${(Number(minor) / 100).toFixed(2)} ${cur || ''}`.trim()
}
function errText(e: any, what: string): string {
  return e?.data?.detail || e?.message || `Unable to ${what}.`
}
</script>

<style scoped>
.lbl { @apply block text-sm font-medium text-gray-700 mb-1; }
.th { @apply text-left px-4 py-3 font-medium text-gray-500; }
.td { @apply px-4 py-3; }
</style>
