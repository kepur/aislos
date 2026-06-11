<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Product Compatibility</h1>
        <p class="text-sm text-gray-500 mt-1">Protocol compatibility records for products.</p>
      </div>
      <button
        class="px-4 py-2 text-sm font-medium bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        @click="openCreate"
      >
        + Add Record
      </button>
    </div>

    <!-- Filters -->
    <div class="flex gap-3 mb-4">
      <input
        v-model="productIdFilter"
        type="text"
        class="text-sm border border-gray-300 rounded-lg px-3 py-2 w-64"
        placeholder="Filter by Product ID..."
      />
      <select v-model="protocolFilter" class="text-sm border border-gray-300 rounded-lg px-3 py-2">
        <option value="">All Protocols</option>
        <option value="KNX">KNX</option>
        <option value="DALI">DALI</option>
        <option value="BACnet">BACnet</option>
        <option value="Modbus">Modbus</option>
        <option value="Zigbee">Zigbee</option>
        <option value="Z-Wave">Z-Wave</option>
        <option value="Matter">Matter</option>
        <option value="EnOcean">EnOcean</option>
        <option value="0-10V">0-10V</option>
      </select>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-xl border overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 text-left">
          <tr>
            <th class="px-4 py-3 font-medium text-gray-600">Product</th>
            <th class="px-4 py-3 font-medium text-gray-600">Protocol</th>
            <th class="px-4 py-3 font-medium text-gray-600">Level</th>
            <th class="px-4 py-3 font-medium text-gray-600">Test Status</th>
            <th class="px-4 py-3 font-medium text-gray-600">Tested By</th>
            <th class="px-4 py-3 font-medium text-gray-600">Notes</th>
            <th class="px-4 py-3 font-medium text-gray-600 text-right">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y">
          <tr v-for="rec in items" :key="rec.id" class="hover:bg-gray-50">
            <td class="px-4 py-3 font-mono text-xs text-gray-600">{{ rec.product_id.slice(0, 8) }}...</td>
            <td class="px-4 py-3">
              <span class="px-2 py-0.5 text-xs font-medium rounded-full bg-indigo-100 text-indigo-700">{{ rec.protocol }}</span>
            </td>
            <td class="px-4 py-3">
              <span class="px-2 py-0.5 text-xs font-medium rounded-full" :class="levelClass(rec.compatibility_level)">
                {{ rec.compatibility_level }}
              </span>
            </td>
            <td class="px-4 py-3">
              <span v-if="rec.test_status" class="px-2 py-0.5 text-xs rounded-full" :class="testStatusClass(rec.test_status)">
                {{ rec.test_status }}
              </span>
              <span v-else class="text-gray-400 text-xs">-</span>
            </td>
            <td class="px-4 py-3 text-gray-600 text-xs">{{ rec.tested_by || '-' }}</td>
            <td class="px-4 py-3 text-gray-500 text-xs max-w-[200px] truncate" :title="rec.notes">{{ rec.notes || '-' }}</td>
            <td class="px-4 py-3 text-right space-x-2">
              <button class="text-xs text-primary-600 hover:underline" @click="openEdit(rec)">Edit</button>
              <button class="text-xs text-red-500 hover:underline" @click="deleteRecord(rec.id)">Delete</button>
            </td>
          </tr>
          <tr v-if="!items.length">
            <td colspan="7" class="px-4 py-8 text-center text-gray-400">No compatibility records found.</td>
          </tr>
        </tbody>
      </table>
    </div>

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
      <div class="bg-white rounded-xl w-full max-w-md p-6">
        <h2 class="text-lg font-bold text-gray-900 mb-4">{{ editingRec ? 'Edit Record' : 'Add Record' }}</h2>
        <div class="space-y-3">
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Product ID *</label>
            <input v-model="form.product_id" type="text" class="w-full text-sm border border-gray-300 rounded-lg p-2" placeholder="UUID" :disabled="!!editingRec" />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Protocol *</label>
              <select v-model="form.protocol" class="w-full text-sm border border-gray-300 rounded-lg p-2">
                <option value="">Select...</option>
                <option v-for="p in protocols" :key="p" :value="p">{{ p }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Compatibility Level</label>
              <select v-model="form.compatibility_level" class="w-full text-sm border border-gray-300 rounded-lg p-2">
                <option value="unknown">Unknown</option>
                <option value="full">Full</option>
                <option value="partial">Partial</option>
                <option value="gateway_required">Gateway Required</option>
                <option value="incompatible">Incompatible</option>
              </select>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Test Status</label>
              <select v-model="form.test_status" class="w-full text-sm border border-gray-300 rounded-lg p-2">
                <option value="">Not tested</option>
                <option value="passed">Passed</option>
                <option value="failed">Failed</option>
                <option value="in_progress">In Progress</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Tested By</label>
              <select v-model="form.tested_by" class="w-full text-sm border border-gray-300 rounded-lg p-2">
                <option value="">-</option>
                <option value="manufacturer">Manufacturer</option>
                <option value="platform">Platform</option>
                <option value="partner">Partner</option>
                <option value="third_party">Third Party</option>
              </select>
            </div>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Notes</label>
            <textarea v-model="form.notes" rows="2" class="w-full text-sm border border-gray-300 rounded-lg p-2" placeholder="Test details, limitations, etc." />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Test Artifact URL</label>
            <input v-model="form.test_artifact_url" type="text" class="w-full text-sm border border-gray-300 rounded-lg p-2" placeholder="https://..." />
          </div>
        </div>
        <div class="mt-4 flex justify-end gap-2">
          <button class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800" @click="showModal = false">Cancel</button>
          <button
            class="px-4 py-2 text-sm font-medium bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-60"
            :disabled="saving || !form.product_id || !form.protocol"
            @click="saveRecord"
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
const limit = 50
const productIdFilter = ref('')
const protocolFilter = ref('')
const showModal = ref(false)
const editingRec = ref<any>(null)
const saving = ref(false)

const protocols = ['KNX', 'DALI', 'BACnet', 'Modbus', 'Zigbee', 'Z-Wave', 'Matter', 'EnOcean', '0-10V', 'TCP/IP', 'RS485', 'LON']

const defaultForm = () => ({
  product_id: '',
  protocol: '',
  compatibility_level: 'unknown',
  test_status: '',
  tested_by: '',
  notes: '',
  test_artifact_url: '',
})

const form = reactive(defaultForm())

function levelClass(level: string) {
  const map: Record<string, string> = {
    full: 'bg-green-100 text-green-700',
    partial: 'bg-yellow-100 text-yellow-700',
    gateway_required: 'bg-blue-100 text-blue-700',
    incompatible: 'bg-red-100 text-red-700',
    unknown: 'bg-gray-100 text-gray-500',
  }
  return map[level] || 'bg-gray-100 text-gray-500'
}

function testStatusClass(status: string) {
  const map: Record<string, string> = {
    passed: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-700',
    in_progress: 'bg-blue-100 text-blue-700',
  }
  return map[status] || 'bg-gray-100 text-gray-500'
}

async function load() {
  const params = new URLSearchParams()
  params.set('skip', String(page.value * limit))
  params.set('limit', String(limit))
  if (productIdFilter.value) params.set('product_id', productIdFilter.value)
  if (protocolFilter.value) params.set('protocol', protocolFilter.value)
  try {
    const res = await apiFetch<any>(`/product-compatibility?${params}`)
    items.value = res.items || []
    total.value = res.total || 0
  } catch {}
}

function openCreate() {
  editingRec.value = null
  Object.assign(form, defaultForm())
  showModal.value = true
}

function openEdit(rec: any) {
  editingRec.value = rec
  Object.assign(form, {
    product_id: rec.product_id || '',
    protocol: rec.protocol || '',
    compatibility_level: rec.compatibility_level || 'unknown',
    test_status: rec.test_status || '',
    tested_by: rec.tested_by || '',
    notes: rec.notes || '',
    test_artifact_url: rec.test_artifact_url || '',
  })
  showModal.value = true
}

async function saveRecord() {
  saving.value = true
  try {
    const body: Record<string, any> = {
      protocol: form.protocol,
      compatibility_level: form.compatibility_level,
      tested_by: form.tested_by || null,
      test_status: form.test_status || null,
      notes: form.notes || null,
      test_artifact_url: form.test_artifact_url || null,
    }

    if (editingRec.value) {
      await apiFetch(`/product-compatibility/${editingRec.value.id}`, { method: 'PUT', body })
    } else {
      body.product_id = form.product_id
      await apiFetch('/product-compatibility', { method: 'POST', body })
    }
    showModal.value = false
    await load()
  } catch (e: any) {
    console.error('Save compat record failed:', e)
  } finally {
    saving.value = false
  }
}

async function deleteRecord(id: string) {
  if (!confirm('Delete this compatibility record?')) return
  try {
    await apiFetch(`/product-compatibility/${id}`, { method: 'DELETE' })
    await load()
  } catch {}
}

let debounceTimer: any
watch(productIdFilter, () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => load(), 300)
})
watch([page, protocolFilter], () => load())
onMounted(() => load())
</script>
