<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="admin-page-title">Regions</h1>
        <p class="admin-page-desc">Manage operating regions, currencies, and tax rules.</p>
      </div>
      <button @click="openCreateModal" class="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700">
        + Add Region
      </button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="region in regions"
        :key="region.id"
        class="bg-white rounded-xl border p-5 hover:shadow-sm transition-shadow"
      >
        <div class="flex items-start justify-between mb-3">
          <div>
            <h3 class="admin-section-title">{{ region.name }}</h3>
            <p class="text-xs text-gray-500 font-mono">{{ region.code }}</p>
          </div>
          <span
            class="px-2 py-0.5 text-xs font-medium rounded-full"
            :class="region.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'"
          >{{ region.is_active ? 'Active' : 'Inactive' }}</span>
        </div>
        <dl class="text-sm space-y-1.5">
          <div class="flex justify-between">
            <dt class="text-gray-500">Currency</dt>
            <dd class="font-medium">{{ region.currency_code }}</dd>
          </div>
          <div class="flex justify-between">
            <dt class="text-gray-500">Timezone</dt>
            <dd>{{ region.timezone || '-' }}</dd>
          </div>
          <div v-if="region.language_codes_json?.length">
            <dt class="text-gray-500 mb-1">Languages</dt>
            <dd class="flex flex-wrap gap-1">
              <span v-for="lang in region.language_codes_json" :key="lang" class="px-2 py-0.5 text-xs rounded-full bg-blue-50 text-blue-700">{{ lang }}</span>
            </dd>
          </div>
          <div v-if="region.tax_rules_json">
            <dt class="text-gray-500 mb-1">Tax Rules</dt>
            <dd class="text-xs text-gray-600">{{ summarizeTax(region.tax_rules_json) }}</dd>
          </div>
        </dl>
        <div class="mt-3 pt-3 border-t flex gap-2">
          <button @click="openEditModal(region)" class="text-xs text-primary-600 hover:underline">Edit</button>
          <button
            @click="toggleActive(region)"
            class="text-xs"
            :class="region.is_active ? 'text-yellow-600 hover:underline' : 'text-green-600 hover:underline'"
          >{{ region.is_active ? 'Deactivate' : 'Activate' }}</button>
        </div>
      </div>
    </div>

    <div v-if="!regions.length" class="bg-white rounded-xl border p-8 text-center">
      <p class="text-gray-500">No regions configured. Add your first region to get started.</p>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showModal = false">
      <div class="bg-white rounded-xl w-full max-w-md mx-4 p-6">
        <h2 class="text-lg font-bold text-gray-900 mb-4">{{ editing ? 'Edit Region' : 'Add Region' }}</h2>
        <form class="space-y-4" @submit.prevent="saveRegion">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Code *</label>
              <input v-model="form.code" type="text" class="input-field" placeholder="e.g. RS" required :disabled="!!editing" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Name *</label>
              <input v-model="form.name" type="text" class="input-field" placeholder="e.g. Serbia" required />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Currency Code</label>
              <input v-model="form.currency_code" type="text" class="input-field" placeholder="EUR" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Timezone</label>
              <input v-model="form.timezone" type="text" class="input-field" placeholder="Europe/Belgrade" />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Languages (comma separated)</label>
            <input v-model="languagesText" type="text" class="input-field" placeholder="en, sr, zh" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">VAT Rate (%)</label>
            <input v-model.number="vatRate" type="number" step="0.1" class="input-field" placeholder="20" />
          </div>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" class="px-4 py-2 text-sm border rounded-lg text-gray-600 hover:bg-gray-50" @click="showModal = false">Cancel</button>
            <button type="submit" class="px-4 py-2 text-sm font-medium bg-primary-600 text-white rounded-lg hover:bg-primary-700" :disabled="saving">
              {{ saving ? 'Saving...' : 'Save' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { apiFetch } = useApi()
const regions = ref<any[]>([])
const showModal = ref(false)
const editing = ref<any>(null)
const saving = ref(false)
const languagesText = ref('')
const vatRate = ref<number | null>(null)

const form = reactive({
  code: '',
  name: '',
  currency_code: 'EUR',
  timezone: '',
})

function summarizeTax(rules: any) {
  if (!rules) return '-'
  if (rules.vat_rate !== undefined) return `VAT ${rules.vat_rate}%`
  return JSON.stringify(rules)
}

function openCreateModal() {
  editing.value = null
  Object.assign(form, { code: '', name: '', currency_code: 'EUR', timezone: '' })
  languagesText.value = ''
  vatRate.value = null
  showModal.value = true
}

function openEditModal(region: any) {
  editing.value = region
  Object.assign(form, {
    code: region.code,
    name: region.name,
    currency_code: region.currency_code,
    timezone: region.timezone || '',
  })
  languagesText.value = (region.language_codes_json || []).join(', ')
  vatRate.value = region.tax_rules_json?.vat_rate ?? null
  showModal.value = true
}

async function saveRegion() {
  saving.value = true
  try {
    const body: any = {
      name: form.name,
      currency_code: form.currency_code || 'EUR',
    }
    if (form.timezone) body.timezone = form.timezone
    if (languagesText.value.trim()) {
      body.language_codes_json = languagesText.value.split(',').map((s: string) => s.trim()).filter(Boolean)
    }
    if (vatRate.value !== null) {
      body.tax_rules_json = { vat_rate: vatRate.value }
    }

    if (editing.value) {
      await apiFetch(`/regions/${editing.value.id}`, { method: 'PUT', body })
    } else {
      body.code = form.code
      await apiFetch('/regions', { method: 'POST', body })
    }
    showModal.value = false
    await loadRegions()
  } catch (e: any) {
    console.error('Save region failed:', e)
  } finally {
    saving.value = false
  }
}

async function toggleActive(region: any) {
  try {
    await apiFetch(`/regions/${region.id}`, {
      method: 'PUT',
      body: { is_active: !region.is_active },
    })
    await loadRegions()
  } catch (e: any) {
    console.error('Toggle active failed:', e)
  }
}

async function loadRegions() {
  try {
    const res = await apiFetch<any>('/regions?limit=50')
    regions.value = res.items || []
  } catch {
    regions.value = []
  }
}

onMounted(loadRegions)
</script>
