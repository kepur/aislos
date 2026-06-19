<template>
  <div class="space-y-6">
    <div class="grid grid-cols-1 xl:grid-cols-[1fr_360px] gap-6">
      <div class="card overflow-hidden">
        <div class="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
          <div>
            <p class="text-sm font-semibold text-slate-900">{{ t('regions.panelTitle') }}</p>
            <p class="text-xs text-slate-500">{{ t('regions.desc') }}</p>
          </div>
          <button class="btn-secondary" @click="load">{{ t('common.refresh') }}</button>
        </div>
        <table class="w-full">
          <thead>
            <tr>
              <th class="table-th">{{ t('regions.region') }}</th>
              <th class="table-th">{{ t('regions.type') }}</th>
              <th class="table-th">{{ t('regions.center') }}</th>
              <th class="table-th">{{ t('regions.radius') }}</th>
              <th class="table-th">{{ t('common.status') }}</th>
              <th class="table-th text-right">{{ t('common.actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="6" class="table-td text-center py-10 text-slate-400">{{ t('common.loading') }}</td>
            </tr>
            <tr v-else-if="!regions.length">
              <td colspan="6" class="table-td text-center py-10 text-slate-400">{{ t('regions.noRegions') }}</td>
            </tr>
            <tr v-for="r in regions" :key="r.id" class="hover:bg-slate-50">
              <td class="table-td">
                <p class="font-semibold text-slate-900">{{ r.name }}</p>
                <p class="text-xs text-slate-400">{{ r.slug }} · {{ r.city || r.country }}</p>
              </td>
              <td class="table-td">{{ r.region_type }}</td>
              <td class="table-td text-xs">{{ fmtCoord(r.center_lat, r.center_lng) }}</td>
              <td class="table-td">{{ r.default_radius_km }} km</td>
              <td class="table-td"><span class="badge" :class="r.status === 'ACTIVE' ? 'badge-green' : 'badge-gray'">{{ statusLabel(r.status) }}</span></td>
              <td class="table-td">
                <div class="flex justify-end gap-2">
                  <button class="btn-secondary" @click="fillEstimate(r)">{{ t('regions.estimate') }}</button>
                  <button class="btn-secondary" @click="toggleRegion(r)">{{ r.status === 'ACTIVE' ? t('common.disable') : t('common.enable') }}</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="space-y-6">
        <form class="card p-4 space-y-3" @submit.prevent="createRegion">
          <p class="text-sm font-semibold text-slate-900">{{ t('regions.create') }}</p>
          <input v-model="form.name" class="input" :placeholder="t('regions.namePlaceholder')" required />
          <input v-model="form.slug" class="input" placeholder="slug" required />
          <div class="grid grid-cols-2 gap-3">
            <input v-model="form.country" class="input" :placeholder="t('regions.country')" required />
            <input v-model="form.city" class="input" :placeholder="t('regions.city')" />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <input v-model.number="form.center_lat" class="input" type="number" step="0.000001" placeholder="Lat" />
            <input v-model.number="form.center_lng" class="input" type="number" step="0.000001" placeholder="Lng" />
          </div>
          <input v-model.number="form.default_radius_km" class="input" type="number" min="1" max="500" :placeholder="t('regions.defaultRadius')" />
          <textarea v-model="form.notes" class="input min-h-20" :placeholder="t('regions.notes')"></textarea>
          <button class="btn-primary w-full" :disabled="saving">{{ saving ? t('common.saving') : t('regions.create') }}</button>
        </form>

        <form class="card p-4 space-y-3" @submit.prevent="estimate">
          <p class="text-sm font-semibold text-slate-900">{{ t('regions.coverageEstimate') }}</p>
          <div class="grid grid-cols-2 gap-3">
            <input v-model.number="estimateForm.lat" class="input" type="number" step="0.000001" placeholder="Lat" required />
            <input v-model.number="estimateForm.lng" class="input" type="number" step="0.000001" placeholder="Lng" required />
          </div>
          <input v-model.number="estimateForm.radius_km" class="input" type="number" min="1" max="500" :placeholder="t('regions.radiusKm')" />
          <button class="btn-secondary w-full" :disabled="estimating">{{ estimating ? t('regions.estimating') : t('regions.estimateSuppliers') }}</button>
          <div v-if="coverage" class="rounded-xl bg-slate-50 border border-slate-100 p-3 text-sm">
            <p class="font-semibold text-slate-900">{{ coverage.matching_companies }} {{ t('regions.companies') }} · {{ coverage.matching_branches }} {{ t('regions.branches') }}</p>
            <p class="text-xs text-slate-500 mt-1">{{ t('regions.activeRegions') }}: {{ coverage.active_regions.join(', ') || t('common.none') }}</p>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { api } from '@/utils/api'

const { t } = useI18n()
const loading = ref(true)
const saving = ref(false)
const estimating = ref(false)
const regions = ref([])
const coverage = ref(null)

const form = reactive({
  name: '',
  slug: '',
  country: 'Philippines',
  city: 'Cebu',
  region_type: 'CITY',
  center_lat: null,
  center_lng: null,
  default_radius_km: 15,
  status: 'ACTIVE',
  notes: '',
})

const estimateForm = reactive({
  lat: 10.3157,
  lng: 123.8854,
  radius_km: 15,
})

function fmtCoord(lat, lng) {
  if (!lat || !lng) return '—'
  return `${Number(lat).toFixed(4)}, ${Number(lng).toFixed(4)}`
}

function statusLabel(status) {
  return t(`status.${status}`)
}

async function load() {
  loading.value = true
  try {
    regions.value = await api.get('/admin/regions').then(r => r.data)
  } catch {
    regions.value = []
  } finally {
    loading.value = false
  }
}

async function createRegion() {
  saving.value = true
  try {
    await api.post('/admin/regions', form)
    form.name = ''
    form.slug = ''
    form.notes = ''
    await load()
  } finally {
    saving.value = false
  }
}

async function toggleRegion(region) {
  await api.patch(`/admin/regions/${region.id}`, {
    status: region.status === 'ACTIVE' ? 'DISABLED' : 'ACTIVE',
  })
  await load()
}

function fillEstimate(region) {
  estimateForm.lat = region.center_lat || estimateForm.lat
  estimateForm.lng = region.center_lng || estimateForm.lng
  estimateForm.radius_km = region.default_radius_km || estimateForm.radius_km
}

async function estimate() {
  estimating.value = true
  try {
    coverage.value = await api.get('/maps/coverage/estimate', { params: estimateForm }).then(r => r.data)
  } finally {
    estimating.value = false
  }
}

onMounted(load)
</script>
