<template>
  <div class="space-y-6">
    <div class="flex gap-2 border-b border-slate-200">
      <button
        v-for="item in tabs"
        :key="item.key"
        class="px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors"
        :class="tab === item.key ? 'border-primary-600 text-primary-700' : 'border-transparent text-slate-500 hover:text-slate-700'"
        @click="tab = item.key"
      >
        {{ item.label }}
      </button>
    </div>

    <div v-if="tab === 'routes'" class="grid grid-cols-1 xl:grid-cols-[1fr_360px] gap-6">
      <div class="card overflow-hidden">
        <div class="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
          <div>
            <p class="text-sm font-semibold text-slate-900">{{ t('shipping.routesTitle') }}</p>
            <p class="text-xs text-slate-500">{{ t('shipping.routesDesc') }}</p>
          </div>
          <button class="btn-secondary" @click="loadRoutes">{{ t('common.refresh') }}</button>
        </div>
        <table class="w-full">
          <thead>
            <tr>
              <th class="table-th">{{ t('shipping.origin') }}</th>
              <th class="table-th">{{ t('shipping.destination') }}</th>
              <th class="table-th">{{ t('shipping.method') }}</th>
              <th class="table-th">{{ t('common.status') }}</th>
              <th class="table-th text-right">{{ t('common.actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loadingRoutes">
              <td colspan="5" class="table-td text-center py-10 text-slate-400">{{ t('common.loading') }}</td>
            </tr>
            <tr v-else-if="!routes.length">
              <td colspan="5" class="table-td text-center py-10 text-slate-400">{{ t('shipping.noRoutes') }}</td>
            </tr>
            <tr v-for="r in routes" :key="r.id" class="hover:bg-slate-50">
              <td class="table-td">{{ r.origin_country }}{{ r.origin_region ? ` · ${r.origin_region}` : '' }}</td>
              <td class="table-td">{{ r.dest_country }}{{ r.dest_region ? ` · ${r.dest_region}` : '' }}</td>
              <td class="table-td"><span class="badge badge-blue">{{ r.shipping_method }}</span></td>
              <td class="table-td">
                <span class="badge" :class="r.status === 'ACTIVE' ? 'badge-green' : 'badge-gray'">{{ statusLabel(r.status) }}</span>
              </td>
              <td class="table-td">
                <div class="flex justify-end gap-2">
                  <button class="btn-secondary" @click="fillRouteForm(r)">{{ t('common.edit') }}</button>
                  <button class="btn-secondary" @click="toggleRoute(r)">
                    {{ r.status === 'ACTIVE' ? t('common.disable') : t('common.enable') }}
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <form class="card p-4 space-y-3" @submit.prevent="saveRoute">
        <p class="text-sm font-semibold text-slate-900">
          {{ routeForm.id ? t('shipping.editRoute') : t('shipping.createRoute') }}
        </p>
        <div class="grid grid-cols-2 gap-3">
          <input v-model="routeForm.origin_country" class="input" :placeholder="t('shipping.originCountry')" required />
          <input v-model="routeForm.dest_country" class="input" :placeholder="t('shipping.destCountry')" required />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <input v-model="routeForm.origin_region" class="input" :placeholder="t('shipping.originRegion')" />
          <input v-model="routeForm.dest_region" class="input" :placeholder="t('shipping.destRegion')" />
        </div>
        <select v-model="routeForm.shipping_method" class="input" required>
          <option v-for="m in methods" :key="m.value" :value="m.value">{{ m.value }}</option>
        </select>
        <textarea v-model="routeForm.description" class="input min-h-20" :placeholder="t('shipping.description')"></textarea>
        <div class="flex gap-2">
          <button class="btn-primary flex-1" :disabled="savingRoute">
            {{ savingRoute ? t('common.saving') : t('common.save') }}
          </button>
          <button type="button" class="btn-secondary" @click="resetRouteForm">{{ t('common.reset') }}</button>
        </div>
      </form>
    </div>

    <div v-else class="grid grid-cols-1 xl:grid-cols-[1fr_380px] gap-6">
      <div class="space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div class="card p-4">
            <p class="text-xs text-slate-500">{{ t('shipping.totalRoutes') }}</p>
            <p class="text-xl font-semibold text-slate-900 mt-1">{{ stats.total_routes }}</p>
          </div>
          <div class="card p-4">
            <p class="text-xs text-slate-500">{{ t('shipping.activeRoutes') }}</p>
            <p class="text-xl font-semibold text-slate-900 mt-1">{{ stats.active_routes }}</p>
          </div>
          <div class="card p-4">
            <p class="text-xs text-slate-500">{{ t('shipping.totalRates') }}</p>
            <p class="text-xl font-semibold text-slate-900 mt-1">{{ stats.total_rates }}</p>
          </div>
          <div class="card p-4">
            <p class="text-xs text-slate-500">{{ t('shipping.activeRates') }}</p>
            <p class="text-xl font-semibold text-slate-900 mt-1">{{ stats.active_rates }}</p>
          </div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div class="card p-4">
            <p class="text-xs text-slate-500">{{ t('shipping.avgPricePerKg') }}</p>
            <p class="text-base font-semibold text-slate-900 mt-1">{{ fmtMinor(stats.avg_price_per_kg_minor, 'USD') }}</p>
          </div>
          <div class="card p-4">
            <p class="text-xs text-slate-500">{{ t('shipping.lastRouteUpdate') }}</p>
            <p class="text-sm font-semibold text-slate-900 mt-1">{{ fmtDatetime(stats.last_route_updated_at) }}</p>
          </div>
          <div class="card p-4">
            <p class="text-xs text-slate-500">{{ t('shipping.lastRateUpdate') }}</p>
            <p class="text-sm font-semibold text-slate-900 mt-1">{{ fmtDatetime(stats.last_rate_updated_at) }}</p>
          </div>
        </div>
        <div class="card p-4">
          <p class="text-xs text-slate-500 mb-2">{{ t('shipping.routesByMethod') }}</p>
          <div class="flex flex-wrap gap-2">
            <span v-for="(count, method) in stats.routes_by_method" :key="method" class="badge badge-blue">
              {{ method }}: {{ count }}
            </span>
            <span v-if="!Object.keys(stats.routes_by_method || {}).length" class="text-xs text-slate-400">{{ t('common.none') }}</span>
          </div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div class="card p-4">
            <p class="text-xs text-slate-500 mb-2">{{ t('shipping.topExpensive') }}</p>
            <div class="space-y-1 text-xs">
              <div v-for="item in stats.top_expensive_routes" :key="`exp-${item.route_id}`" class="flex justify-between gap-2">
                <span class="text-slate-600 truncate">{{ item.route_label }}</span>
                <span class="font-semibold text-slate-900">{{ fmtMinor(item.avg_price_per_kg_minor, 'USD') }}</span>
              </div>
              <div v-if="!stats.top_expensive_routes.length" class="text-slate-400">{{ t('common.none') }}</div>
            </div>
          </div>
          <div class="card p-4">
            <p class="text-xs text-slate-500 mb-2">{{ t('shipping.topCheapest') }}</p>
            <div class="space-y-1 text-xs">
              <div v-for="item in stats.top_cheapest_routes" :key="`cheap-${item.route_id}`" class="flex justify-between gap-2">
                <span class="text-slate-600 truncate">{{ item.route_label }}</span>
                <span class="font-semibold text-slate-900">{{ fmtMinor(item.avg_price_per_kg_minor, 'USD') }}</span>
              </div>
              <div v-if="!stats.top_cheapest_routes.length" class="text-slate-400">{{ t('common.none') }}</div>
            </div>
          </div>
          <div class="card p-4">
            <p class="text-xs text-slate-500 mb-2">{{ t('shipping.topSlowest') }}</p>
            <div class="space-y-1 text-xs">
              <div v-for="item in stats.top_slowest_routes" :key="`slow-${item.route_id}`" class="flex justify-between gap-2">
                <span class="text-slate-600 truncate">{{ item.route_label }}</span>
                <span class="font-semibold text-slate-900">{{ Number(item.avg_eta_max_days || 0).toFixed(1) }} d</span>
              </div>
              <div v-if="!stats.top_slowest_routes.length" class="text-slate-400">{{ t('common.none') }}</div>
            </div>
          </div>
        </div>

        <div class="card overflow-hidden">
        <div class="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
          <div>
            <p class="text-sm font-semibold text-slate-900">{{ t('shipping.ratesTitle') }}</p>
            <p class="text-xs text-slate-500">{{ t('shipping.ratesDesc') }}</p>
          </div>
          <div class="flex gap-2">
            <select v-model="selectedRouteId" class="input text-sm min-w-56" @change="loadRates">
              <option value="">{{ t('shipping.allRoutes') }}</option>
              <option v-for="r in routes" :key="r.id" :value="r.id">
                {{ r.origin_country }}→{{ r.dest_country }} · {{ r.shipping_method }}
              </option>
            </select>
            <button class="btn-secondary" @click="loadRates">{{ t('common.refresh') }}</button>
          </div>
        </div>
        <table class="w-full">
          <thead>
            <tr>
              <th class="table-th">{{ t('shipping.route') }}</th>
              <th class="table-th">{{ t('shipping.weightTier') }}</th>
              <th class="table-th">{{ t('shipping.pricePerKg') }}</th>
              <th class="table-th">{{ t('shipping.minCharge') }}</th>
              <th class="table-th">{{ t('shipping.eta') }}</th>
              <th class="table-th">{{ t('common.status') }}</th>
              <th class="table-th text-right">{{ t('common.actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loadingRates">
              <td colspan="7" class="table-td text-center py-10 text-slate-400">{{ t('common.loading') }}</td>
            </tr>
            <tr v-else-if="!rates.length">
              <td colspan="7" class="table-td text-center py-10 text-slate-400">{{ t('shipping.noRates') }}</td>
            </tr>
            <tr v-for="rate in rates" :key="rate.id" class="hover:bg-slate-50">
              <td class="table-td text-xs">{{ routeLabel(rate.route_id) }}</td>
              <td class="table-td">{{ rate.weight_min_kg }} - {{ rate.weight_max_kg }} kg</td>
              <td class="table-td">{{ fmtMinor(rate.price_per_kg_minor, rate.currency) }}</td>
              <td class="table-td">{{ fmtMinor(rate.min_charge_minor, rate.currency) }}</td>
              <td class="table-td">{{ rate.estimated_days_min }}-{{ rate.estimated_days_max }} d</td>
              <td class="table-td">
                <span class="badge" :class="rate.status === 'ACTIVE' ? 'badge-green' : 'badge-gray'">{{ statusLabel(rate.status) }}</span>
              </td>
              <td class="table-td">
                <div class="flex justify-end gap-2">
                  <button class="btn-secondary" @click="fillRateForm(rate)">{{ t('common.edit') }}</button>
                  <button class="btn-secondary" @click="toggleRate(rate)">
                    {{ rate.status === 'ACTIVE' ? t('common.disable') : t('common.enable') }}
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      </div>

      <form class="card p-4 space-y-3" @submit.prevent="saveRate">
        <p class="text-sm font-semibold text-slate-900">
          {{ rateForm.id ? t('shipping.editRate') : t('shipping.createRate') }}
        </p>
        <select v-model="rateForm.route_id" class="input" required>
          <option disabled value="">{{ t('shipping.selectRoute') }}</option>
          <option v-for="r in routes" :key="r.id" :value="r.id">
            {{ r.origin_country }}→{{ r.dest_country }} · {{ r.shipping_method }}
          </option>
        </select>
        <div class="grid grid-cols-2 gap-3">
          <input v-model.number="rateForm.weight_min_kg" class="input" type="number" min="0" step="0.01" :placeholder="t('shipping.weightMin')" required />
          <input v-model.number="rateForm.weight_max_kg" class="input" type="number" min="0" step="0.01" :placeholder="t('shipping.weightMax')" required />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <input v-model.number="rateForm.price_per_kg_minor" class="input" type="number" min="0" :placeholder="t('shipping.pricePerKgMinor')" required />
          <input v-model.number="rateForm.min_charge_minor" class="input" type="number" min="0" :placeholder="t('shipping.minChargeMinor')" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <input v-model.number="rateForm.estimated_days_min" class="input" type="number" min="1" :placeholder="t('shipping.etaMin')" required />
          <input v-model.number="rateForm.estimated_days_max" class="input" type="number" min="1" :placeholder="t('shipping.etaMax')" required />
        </div>
        <input v-model.number="rateForm.volume_factor" class="input" type="number" min="1" step="1" :placeholder="t('shipping.volumeFactor')" />
        <input v-model="rateForm.currency" class="input" placeholder="Currency (USD/PHP)" />
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <p class="text-xs font-semibold text-slate-600">{{ t('shipping.surcharges') }}</p>
            <button type="button" class="btn-secondary" @click="addSurchargeRow">{{ t('shipping.addSurcharge') }}</button>
          </div>
          <div v-if="!rateForm.surcharges.length" class="text-xs text-slate-400">{{ t('shipping.noSurcharge') }}</div>
          <div v-for="(row, idx) in rateForm.surcharges" :key="idx" class="grid grid-cols-[1fr_120px_36px] gap-2">
            <input v-model="row.name" class="input" :placeholder="t('shipping.surchargeName')" />
            <input v-model.number="row.amount_minor" class="input" type="number" min="0" :placeholder="t('shipping.surchargeAmount')" />
            <button type="button" class="btn-secondary px-0" @click="removeSurchargeRow(idx)">×</button>
          </div>
        </div>
        <textarea v-model="rateForm.notes" class="input min-h-20" :placeholder="t('shipping.notes')"></textarea>
        <div class="flex gap-2">
          <button class="btn-primary flex-1" :disabled="savingRate">
            {{ savingRate ? t('common.saving') : t('common.save') }}
          </button>
          <button type="button" class="btn-secondary" @click="resetRateForm">{{ t('common.reset') }}</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { api, fmtDatetime, fmtPrice } from '@/utils/api'

const { t } = useI18n()
const tab = ref('routes')
const tabs = computed(() => [
  { key: 'routes', label: t('shipping.routes') },
  { key: 'rates', label: t('shipping.rates') },
])

const methods = [
  { value: 'SEA_FREIGHT' },
  { value: 'AIR_FREIGHT' },
  { value: 'EXPRESS' },
  { value: 'LAND_FREIGHT' },
  { value: 'LOCAL_DELIVERY' },
  { value: 'SELF_PICKUP' },
]

const routes = ref([])
const rates = ref([])
const selectedRouteId = ref('')

const loadingRoutes = ref(false)
const loadingRates = ref(false)
const savingRoute = ref(false)
const savingRate = ref(false)
const stats = ref({
  total_routes: 0,
  active_routes: 0,
  inactive_routes: 0,
  total_rates: 0,
  active_rates: 0,
  inactive_rates: 0,
  avg_price_per_kg_minor: 0,
  last_route_updated_at: null,
  last_rate_updated_at: null,
  routes_by_method: {},
  top_expensive_routes: [],
  top_cheapest_routes: [],
  top_slowest_routes: [],
})

const routeForm = reactive({
  id: '',
  origin_country: 'PH',
  origin_region: '',
  dest_country: 'PH',
  dest_region: '',
  shipping_method: 'LOCAL_DELIVERY',
  description: '',
})

const rateForm = reactive({
  id: '',
  route_id: '',
  weight_min_kg: 0,
  weight_max_kg: 100,
  price_per_kg_minor: 0,
  currency: 'USD',
  min_charge_minor: 0,
  volume_factor: 5000,
  estimated_days_min: 1,
  estimated_days_max: 7,
  surcharges: [],
  notes: '',
})

function statusLabel(status) {
  return t(`status.${status}`)
}

function fmtMinor(minor, currency) {
  return fmtPrice(minor, currency)
}

function routeLabel(routeId) {
  const route = routes.value.find((x) => x.id === routeId)
  if (!route) return routeId
  return `${route.origin_country}→${route.dest_country} · ${route.shipping_method}`
}

function resetRouteForm() {
  routeForm.id = ''
  routeForm.origin_country = 'PH'
  routeForm.origin_region = ''
  routeForm.dest_country = 'PH'
  routeForm.dest_region = ''
  routeForm.shipping_method = 'LOCAL_DELIVERY'
  routeForm.description = ''
}

function resetRateForm() {
  rateForm.id = ''
  rateForm.route_id = selectedRouteId.value || ''
  rateForm.weight_min_kg = 0
  rateForm.weight_max_kg = 100
  rateForm.price_per_kg_minor = 0
  rateForm.currency = 'USD'
  rateForm.min_charge_minor = 0
  rateForm.volume_factor = 5000
  rateForm.estimated_days_min = 1
  rateForm.estimated_days_max = 7
  rateForm.surcharges = []
  rateForm.notes = ''
}

function addSurchargeRow() {
  rateForm.surcharges.push({ name: '', amount_minor: 0 })
}

function removeSurchargeRow(idx) {
  rateForm.surcharges.splice(idx, 1)
}

function surchargesToJson() {
  const cleaned = rateForm.surcharges.filter((x) => x.name && x.amount_minor >= 0)
  if (!cleaned.length) return null
  const result = {}
  for (const item of cleaned) result[item.name] = Number(item.amount_minor || 0)
  return result
}

async function loadRoutes() {
  loadingRoutes.value = true
  try {
    routes.value = await api.get('/admin/shipping/routes').then((r) => r.data)
  } catch {
    routes.value = []
  } finally {
    loadingRoutes.value = false
  }
}

async function loadRates() {
  loadingRates.value = true
  try {
    const params = selectedRouteId.value ? { route_id: selectedRouteId.value } : {}
    rates.value = await api.get('/admin/shipping/rates', { params }).then((r) => r.data)
  } catch {
    rates.value = []
  } finally {
    loadingRates.value = false
  }
}

async function loadStats() {
  try {
    stats.value = await api.get('/admin/shipping/statistics').then((r) => r.data)
  } catch {
    stats.value = {
      total_routes: 0,
      active_routes: 0,
      inactive_routes: 0,
      total_rates: 0,
      active_rates: 0,
      inactive_rates: 0,
      avg_price_per_kg_minor: 0,
      last_route_updated_at: null,
      last_rate_updated_at: null,
      routes_by_method: {},
      top_expensive_routes: [],
      top_cheapest_routes: [],
      top_slowest_routes: [],
    }
  }
}

function fillRouteForm(route) {
  routeForm.id = route.id
  routeForm.origin_country = route.origin_country
  routeForm.origin_region = route.origin_region || ''
  routeForm.dest_country = route.dest_country
  routeForm.dest_region = route.dest_region || ''
  routeForm.shipping_method = route.shipping_method
  routeForm.description = route.description || ''
}

async function saveRoute() {
  savingRoute.value = true
  try {
    const payload = {
      origin_country: routeForm.origin_country.toUpperCase(),
      origin_region: routeForm.origin_region || null,
      dest_country: routeForm.dest_country.toUpperCase(),
      dest_region: routeForm.dest_region || null,
      shipping_method: routeForm.shipping_method,
      description: routeForm.description || null,
    }
    if (routeForm.id) {
      await api.patch(`/admin/shipping/routes/${routeForm.id}`, payload)
    } else {
      await api.post('/admin/shipping/routes', payload)
    }
    resetRouteForm()
    await loadRoutes()
    await loadStats()
  } finally {
    savingRoute.value = false
  }
}

async function toggleRoute(route) {
  await api.patch(`/admin/shipping/routes/${route.id}`, {
    status: route.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE',
  })
  await loadRoutes()
  await loadStats()
}

function fillRateForm(rate) {
  rateForm.id = rate.id
  rateForm.route_id = rate.route_id
  rateForm.weight_min_kg = rate.weight_min_kg
  rateForm.weight_max_kg = rate.weight_max_kg
  rateForm.price_per_kg_minor = rate.price_per_kg_minor
  rateForm.currency = rate.currency
  rateForm.min_charge_minor = rate.min_charge_minor
  rateForm.volume_factor = rate.volume_factor
  rateForm.estimated_days_min = rate.estimated_days_min
  rateForm.estimated_days_max = rate.estimated_days_max
  rateForm.surcharges = Object.entries(rate.surcharges_json || {}).map(([name, amount_minor]) => ({ name, amount_minor }))
  rateForm.notes = rate.notes || ''
}

async function saveRate() {
  savingRate.value = true
  try {
    const payload = {
      route_id: rateForm.route_id,
      weight_min_kg: rateForm.weight_min_kg,
      weight_max_kg: rateForm.weight_max_kg,
      price_per_kg_minor: rateForm.price_per_kg_minor,
      currency: rateForm.currency,
      min_charge_minor: rateForm.min_charge_minor,
      volume_factor: rateForm.volume_factor,
      estimated_days_min: rateForm.estimated_days_min,
      estimated_days_max: rateForm.estimated_days_max,
      surcharges_json: surchargesToJson(),
      notes: rateForm.notes || null,
    }
    if (rateForm.id) {
      await api.patch(`/admin/shipping/rates/${rateForm.id}`, payload)
    } else {
      await api.post('/admin/shipping/rates', payload)
    }
    resetRateForm()
    await loadRates()
    await loadStats()
  } finally {
    savingRate.value = false
  }
}

async function toggleRate(rate) {
  await api.patch(`/admin/shipping/rates/${rate.id}`, {
    status: rate.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE',
  })
  await loadRates()
  await loadStats()
}

onMounted(async () => {
  await loadRoutes()
  await loadRates()
  await loadStats()
  resetRateForm()
})
</script>
