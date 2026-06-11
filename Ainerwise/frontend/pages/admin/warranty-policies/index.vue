<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Warranty Policies</h1>
      <button
        class="px-4 py-2 text-sm font-medium bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        @click="openCreate"
      >
        + Add Policy
      </button>
    </div>

    <!-- Filters -->
    <div class="flex gap-3 mb-4">
      <select v-model="regionFilter" class="text-sm border border-gray-300 rounded-lg px-3 py-2">
        <option value="">All Regions</option>
        <option value="Serbia">Serbia</option>
        <option value="Poland">Poland</option>
        <option value="New Zealand">New Zealand</option>
        <option value="Global">Global</option>
      </select>
      <label class="flex items-center gap-2 text-sm text-gray-600">
        <input v-model="activeOnly" type="checkbox" class="rounded" /> Active only
      </label>
    </div>

    <!-- Cards Grid -->
    <div v-if="items.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="policy in items" :key="policy.id" class="bg-white rounded-xl border p-5 hover:shadow-sm transition-shadow">
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-2">
            <span class="px-2 py-0.5 text-xs font-medium rounded-full" :class="policy.active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'">
              {{ policy.active ? 'Active' : 'Inactive' }}
            </span>
            <span v-if="policy.region" class="text-xs text-gray-500">{{ policy.region }}</span>
          </div>
          <div class="flex gap-2">
            <button class="text-xs text-primary-600 hover:underline" @click="openEdit(policy)">Edit</button>
            <button class="text-xs text-red-500 hover:underline" @click="deletePolicy(policy.id)">Delete</button>
          </div>
        </div>

        <div class="text-xs text-gray-500 mb-2">
          Product: <span class="font-mono">{{ policy.product_id?.slice(0, 8) || 'Any' }}</span>
          <span v-if="policy.supplier_id"> &middot; Supplier: <span class="font-mono">{{ policy.supplier_id.slice(0, 8) }}</span></span>
        </div>

        <div class="grid grid-cols-3 gap-2 text-center">
          <div class="rounded-lg bg-blue-50 p-2">
            <p class="text-lg font-bold text-blue-700">{{ policy.manufacturer_warranty_months ?? '-' }}</p>
            <p class="text-xs text-blue-600">Mfr (mo)</p>
          </div>
          <div class="rounded-lg bg-purple-50 p-2">
            <p class="text-lg font-bold text-purple-700">{{ policy.platform_support_months ?? '-' }}</p>
            <p class="text-xs text-purple-600">Platform (mo)</p>
          </div>
          <div class="rounded-lg bg-green-50 p-2">
            <p class="text-lg font-bold text-green-700">{{ policy.local_installation_warranty_months ?? '-' }}</p>
            <p class="text-xs text-green-600">Install (mo)</p>
          </div>
        </div>

        <div v-if="policy.exclusions_text" class="mt-3 text-xs text-gray-500 truncate" :title="policy.exclusions_text">
          Exclusions: {{ policy.exclusions_text }}
        </div>
      </div>
    </div>
    <div v-else class="bg-white rounded-xl border p-8 text-center text-gray-400">No warranty policies found.</div>

    <!-- Pagination -->
    <div v-if="total > limit" class="mt-4 flex justify-center gap-2">
      <button
        v-for="p in Math.ceil(total / limit)"
        :key="p"
        class="px-3 py-1 text-sm rounded-lg"
        :class="page === p - 1 ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
        @click="page = p - 1"
      >{{ p }}</button>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="showModal = false">
      <div class="bg-white rounded-xl w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
        <h2 class="text-lg font-bold text-gray-900 mb-4">{{ editingPolicy ? 'Edit Policy' : 'Add Policy' }}</h2>
        <div class="space-y-3">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Product ID</label>
              <input v-model="form.product_id" type="text" class="w-full text-sm border border-gray-300 rounded-lg p-2" placeholder="UUID (optional)" />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Supplier ID</label>
              <input v-model="form.supplier_id" type="text" class="w-full text-sm border border-gray-300 rounded-lg p-2" placeholder="UUID (optional)" />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Region</label>
              <input v-model="form.region" type="text" class="w-full text-sm border border-gray-300 rounded-lg p-2" placeholder="e.g. Serbia" />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Active</label>
              <select v-model="form.active" class="w-full text-sm border border-gray-300 rounded-lg p-2">
                <option :value="true">Yes</option>
                <option :value="false">No</option>
              </select>
            </div>
          </div>
          <div class="grid grid-cols-3 gap-3">
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Manufacturer (months)</label>
              <input v-model.number="form.manufacturer_warranty_months" type="number" class="w-full text-sm border border-gray-300 rounded-lg p-2" />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Platform (months)</label>
              <input v-model.number="form.platform_support_months" type="number" class="w-full text-sm border border-gray-300 rounded-lg p-2" />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Installation (months)</label>
              <input v-model.number="form.local_installation_warranty_months" type="number" class="w-full text-sm border border-gray-300 rounded-lg p-2" />
            </div>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Exclusions</label>
            <textarea v-model="form.exclusions_text" rows="2" class="w-full text-sm border border-gray-300 rounded-lg p-2" placeholder="e.g. Water damage, unauthorized modifications..." />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Spare Parts Policy (JSON)</label>
            <textarea v-model="form.spare_parts_json_str" rows="2" class="w-full text-sm border border-gray-300 rounded-lg p-2 font-mono text-xs" placeholder='{"coverage": "2 years", "shipping": "free"}' />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Response SLA (JSON)</label>
            <textarea v-model="form.response_sla_json_str" rows="2" class="w-full text-sm border border-gray-300 rounded-lg p-2 font-mono text-xs" placeholder='{"critical": "4h", "normal": "24h"}' />
          </div>
        </div>
        <div class="mt-4 flex justify-end gap-2">
          <button class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800" @click="showModal = false">Cancel</button>
          <button
            class="px-4 py-2 text-sm font-medium bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-60"
            :disabled="saving"
            @click="savePolicy"
          >{{ saving ? 'Saving...' : 'Save' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'admin' })

const { apiFetch } = useApi()
const items = ref<any[]>([])
const total = ref(0)
const page = ref(0)
const limit = 20
const regionFilter = ref('')
const activeOnly = ref(false)
const showModal = ref(false)
const editingPolicy = ref<any>(null)
const saving = ref(false)

const defaultForm = () => ({
  product_id: '',
  supplier_id: '',
  region: '',
  active: true,
  manufacturer_warranty_months: null as number | null,
  platform_support_months: null as number | null,
  local_installation_warranty_months: null as number | null,
  exclusions_text: '',
  spare_parts_json_str: '',
  response_sla_json_str: '',
})

const form = reactive(defaultForm())

async function load() {
  const params = new URLSearchParams()
  params.set('skip', String(page.value * limit))
  params.set('limit', String(limit))
  if (regionFilter.value) params.set('region', regionFilter.value)
  if (activeOnly.value) params.set('active_only', 'true')
  try {
    const res = await apiFetch<any>(`/warranty-policies?${params}`)
    items.value = res.items || []
    total.value = res.total || 0
  } catch {}
}

function openCreate() {
  editingPolicy.value = null
  Object.assign(form, defaultForm())
  showModal.value = true
}

function openEdit(policy: any) {
  editingPolicy.value = policy
  Object.assign(form, {
    product_id: policy.product_id || '',
    supplier_id: policy.supplier_id || '',
    region: policy.region || '',
    active: policy.active ?? true,
    manufacturer_warranty_months: policy.manufacturer_warranty_months,
    platform_support_months: policy.platform_support_months,
    local_installation_warranty_months: policy.local_installation_warranty_months,
    exclusions_text: policy.exclusions_text || '',
    spare_parts_json_str: policy.spare_parts_policy_json ? JSON.stringify(policy.spare_parts_policy_json) : '',
    response_sla_json_str: policy.response_sla_json ? JSON.stringify(policy.response_sla_json) : '',
  })
  showModal.value = true
}

function tryParseJson(str: string): any {
  if (!str.trim()) return null
  try { return JSON.parse(str) } catch { return null }
}

async function savePolicy() {
  saving.value = true
  try {
    const body: Record<string, any> = {
      region: form.region || null,
      active: form.active,
      manufacturer_warranty_months: form.manufacturer_warranty_months,
      platform_support_months: form.platform_support_months,
      local_installation_warranty_months: form.local_installation_warranty_months,
      exclusions_text: form.exclusions_text || null,
      spare_parts_policy_json: tryParseJson(form.spare_parts_json_str),
      response_sla_json: tryParseJson(form.response_sla_json_str),
    }
    if (form.product_id) body.product_id = form.product_id
    if (form.supplier_id) body.supplier_id = form.supplier_id

    if (editingPolicy.value) {
      await apiFetch(`/warranty-policies/${editingPolicy.value.id}`, { method: 'PUT', body })
    } else {
      await apiFetch('/warranty-policies', { method: 'POST', body })
    }
    showModal.value = false
    await load()
  } catch (e: any) {
    console.error('Save policy failed:', e)
  } finally {
    saving.value = false
  }
}

async function deletePolicy(id: string) {
  if (!confirm('Delete this warranty policy?')) return
  try {
    await apiFetch(`/warranty-policies/${id}`, { method: 'DELETE' })
    await load()
  } catch {}
}

watch([page, regionFilter, activeOnly], () => load())
onMounted(() => load())
</script>
