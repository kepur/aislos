<template>
  <div class="space-y-6">
    <!-- Window picker -->
    <div class="flex items-center justify-between gap-4">
      <div class="flex items-center gap-2">
        <button
          v-for="w in windows"
          :key="w.days"
          @click="days = w.days; loadAll()"
          :class="['rounded-lg px-3 py-1.5 text-sm font-medium transition-colors',
                   days === w.days ? 'bg-primary-600 text-white' : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200']"
        >{{ w.label }}</button>
      </div>
      <button class="btn-secondary" :disabled="loading" @click="loadAll">
        {{ loading ? 'Refreshing…' : 'Refresh' }}
      </button>
    </div>

    <!-- Funnel -->
    <div class="card p-5">
      <div class="mb-1 flex items-center justify-between">
        <h2 class="text-sm font-semibold text-slate-900">Funnel</h2>
        <span class="text-xs text-slate-400">last {{ days }} days</span>
      </div>
      <p class="mb-5 text-xs text-slate-500">Where buyers drop off. Each percentage is conversion from the step above.</p>

      <div v-if="!funnel.length" class="py-8 text-center text-sm text-slate-400">No events in this window.</div>
      <div v-else class="space-y-2">
        <div v-for="step in funnel" :key="step.step" class="flex items-center gap-4">
          <span class="w-40 flex-shrink-0 text-sm text-slate-600">{{ stepLabel(step.step) }}</span>
          <div class="h-8 flex-1 overflow-hidden rounded-lg bg-slate-100">
            <div
              class="flex h-full items-center justify-end rounded-lg bg-primary-500 px-3 text-xs font-semibold text-white transition-all"
              :style="{ width: barWidth(step.count) }"
            >
              <span v-if="step.count">{{ step.count }}</span>
            </div>
          </div>
          <span class="w-32 flex-shrink-0 text-right text-sm">
            <template v-if="step.conversion_from_previous !== null">
              <span :class="step.exceeds_previous_step ? 'text-amber-600 font-semibold' : 'text-slate-500'">
                {{ step.conversion_from_previous }}%
              </span>
              <span v-if="step.exceeds_previous_step" class="ml-1 cursor-help text-amber-500"
                    title="Over 100% is expected when sales arrive from channels we don't track upstream (e.g. an external classifieds post).">ⓘ</span>
            </template>
            <span v-else class="text-slate-300">—</span>
          </span>
        </div>
      </div>
      <p v-if="funnel.some(s => s.exceeds_previous_step)" class="mt-4 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">
        A step above 100% means activity arrived without passing the previous step — normally a sale from an
        external channel. It is real data, not an error.
      </p>
    </div>

    <div class="grid grid-cols-2 gap-6">
      <!-- Channels -->
      <div class="card overflow-hidden">
        <div class="border-b border-slate-200 px-5 py-3">
          <h2 class="text-sm font-semibold text-slate-900">Channels</h2>
          <p class="mt-0.5 text-xs text-slate-500">Which channel actually converts.</p>
        </div>
        <table class="w-full">
          <thead>
            <tr>
              <th class="table-th">Channel</th>
              <th class="table-th w-20 text-right">Views</th>
              <th class="table-th w-20 text-right">Leads</th>
              <th class="table-th w-20 text-right">Sold</th>
              <th class="table-th w-28 text-right">Revenue</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!channels.length"><td colspan="5" class="table-td py-8 text-center text-slate-400">No data</td></tr>
            <tr v-for="c in channels" :key="c.channel_account_id || 'onsite'" class="hover:bg-slate-50">
              <td class="table-td">
                <p class="text-sm font-medium text-slate-800">{{ c.channel_name || '—' }}</p>
                <p class="text-xs text-slate-400">
                  {{ c.channel }}
                  <span v-if="c.lead_conversion_pct !== null"> · view→lead {{ c.lead_conversion_pct }}%</span>
                </p>
              </td>
              <td class="table-td text-right text-sm">{{ c.views }}</td>
              <td class="table-td text-right text-sm">{{ c.leads }}</td>
              <td class="table-td text-right text-sm font-semibold">{{ c.sold }}</td>
              <td class="table-td text-right text-sm font-semibold">{{ money(c.revenue_minor) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Creatives -->
      <div class="card overflow-hidden">
        <div class="border-b border-slate-200 px-5 py-3">
          <h2 class="text-sm font-semibold text-slate-900">Ad creatives</h2>
          <p class="mt-0.5 text-xs text-slate-500">Click-through per image, best first.</p>
        </div>
        <table class="w-full">
          <thead>
            <tr>
              <th class="table-th">Variant</th>
              <th class="table-th w-24 text-right">Impr.</th>
              <th class="table-th w-20 text-right">Clicks</th>
              <th class="table-th w-20 text-right">CTR</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!creatives.length"><td colspan="4" class="table-td py-8 text-center text-slate-400">No creative data</td></tr>
            <tr v-for="(c, i) in creatives" :key="c.creative_id" class="hover:bg-slate-50">
              <td class="table-td">
                <div class="flex items-center gap-2">
                  <img v-if="c.image_url" :src="c.image_url" class="h-8 w-8 rounded object-cover" alt="" @error="onImgError" />
                  <div>
                    <p class="text-sm font-medium text-slate-800">{{ c.variant_label || '—' }}</p>
                    <p class="text-xs text-slate-400">
                      <span :class="c.generated_by === 'ai' ? 'text-indigo-500' : ''">{{ c.generated_by || '—' }}</span>
                      <span v-if="i === 0 && creatives.length > 1" class="ml-1 text-green-600">· best</span>
                    </p>
                  </div>
                </div>
              </td>
              <td class="table-td text-right text-sm">{{ c.impressions }}</td>
              <td class="table-td text-right text-sm">{{ c.clicks }}</td>
              <td class="table-td text-right text-sm font-semibold" :class="ctrClass(c, i)">
                {{ c.ctr_pct !== null ? c.ctr_pct + '%' : '—' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- SKUs -->
    <div class="card overflow-hidden">
      <div class="border-b border-slate-200 px-5 py-3">
        <h2 class="text-sm font-semibold text-slate-900">SKU performance</h2>
        <p class="mt-0.5 text-xs text-slate-500">What sells, ranked by revenue. Low view→lead means the listing is being seen but not wanted.</p>
      </div>
      <table class="w-full">
        <thead>
          <tr>
            <th class="table-th">Item</th>
            <th class="table-th w-20 text-right">Impr.</th>
            <th class="table-th w-20 text-right">Views</th>
            <th class="table-th w-20 text-right">Leads</th>
            <th class="table-th w-24 text-right">View→lead</th>
            <th class="table-th w-20 text-right">Sold</th>
            <th class="table-th w-28 text-right">Revenue</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading"><td colspan="7" class="table-td py-10 text-center text-slate-400">Loading…</td></tr>
          <tr v-else-if="!skus.length"><td colspan="7" class="table-td py-10 text-center text-slate-400">No SKU activity in this window.</td></tr>
          <tr v-for="s in skus" :key="s.listing_id" class="hover:bg-slate-50">
            <td class="table-td">
              <p class="max-w-[320px] truncate text-sm font-medium text-slate-800">{{ s.title || s.listing_id }}</p>
            </td>
            <td class="table-td text-right text-sm text-slate-500">{{ s.impressions }}</td>
            <td class="table-td text-right text-sm">{{ s.views }}</td>
            <td class="table-td text-right text-sm">{{ s.leads }}</td>
            <td class="table-td text-right text-sm" :class="leadRateClass(s)">
              {{ s.view_to_lead_pct !== null ? s.view_to_lead_pct + '%' : '—' }}
            </td>
            <td class="table-td text-right text-sm font-semibold">{{ s.sold }}</td>
            <td class="table-td text-right text-sm font-semibold">{{ money(s.revenue_minor) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Spine health -->
    <div class="card p-5">
      <h2 class="mb-3 text-sm font-semibold text-slate-900">Data sources</h2>
      <div class="flex flex-wrap items-center gap-3">
        <span v-for="(n, app) in health.by_source_app" :key="app"
              class="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-600">
          {{ app }} · {{ n }}
        </span>
        <span v-if="!Object.keys(health.by_source_app || {}).length" class="text-xs text-slate-400">
          No events recorded yet.
        </span>
      </div>
      <p class="mt-3 text-xs text-slate-400">
        Total {{ health.total_events || 0 }} events · latest {{ fmtDate(health.latest_event_at) }}
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { api, fmtDate } from '@/utils/api'

const windows = [
  { days: 7, label: '7 days' },
  { days: 30, label: '30 days' },
  { days: 90, label: '90 days' },
]

const days = ref(30)
const loading = ref(true)
const funnel = ref([])
const skus = ref([])
const channels = ref([])
const creatives = ref([])
const health = ref({})

const maxFunnel = computed(() => Math.max(1, ...funnel.value.map((s) => s.count || 0)))

function stepLabel(step) {
  return {
    'listing.impression': 'Shown in a list',
    'listing.view': 'Opened the listing',
    'contact.requested': 'Asked for address',
    'deal.reserved': 'Reserved',
    'deal.completed': 'Collected & paid',
  }[step] || step
}

function barWidth(count) {
  // Always leave a sliver so a zero step is still visibly a step.
  return `${Math.max(2, ((count || 0) / maxFunnel.value) * 100)}%`
}

function money(minor) {
  return new Intl.NumberFormat('en', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 })
    .format((minor || 0) / 100)
}

function ctrClass(c, i) {
  if (c.ctr_pct === null) return 'text-slate-400'
  return i === 0 && creatives.value.length > 1 ? 'text-green-600' : 'text-slate-800'
}

function leadRateClass(s) {
  if (s.view_to_lead_pct === null) return 'text-slate-400'
  // Seen a lot but nobody asks -> the price or the photos are the problem.
  if (s.views >= 5 && s.view_to_lead_pct === 0) return 'text-rose-600 font-semibold'
  return 'text-slate-600'
}

function onImgError(e) {
  e.target.style.display = 'none'
}

async function loadAll() {
  loading.value = true
  const q = `?days=${days.value}`
  const [f, s, c, cr, h] = await Promise.all([
    api.get(`/analytics/funnel${q}`).then((r) => r.data).catch(() => ({ steps: [] })),
    api.get(`/analytics/sku${q}&limit=50`).then((r) => r.data).catch(() => ({ items: [] })),
    api.get(`/analytics/channel${q}`).then((r) => r.data).catch(() => ({ items: [] })),
    api.get(`/analytics/creative${q}`).then((r) => r.data).catch(() => ({ items: [] })),
    api.get('/analytics/health').then((r) => r.data).catch(() => ({})),
  ])
  funnel.value = f.steps || []
  skus.value = s.items || []
  channels.value = c.items || []
  creatives.value = cr.items || []
  health.value = h
  loading.value = false
}

onMounted(loadAll)
</script>
