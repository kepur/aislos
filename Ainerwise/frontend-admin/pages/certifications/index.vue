<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="admin-page-title">Certifications</h1>
      <button
        class="px-4 py-2 text-sm font-medium bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        @click="openCreate"
      >
        + Add Certification
      </button>
    </div>

    <!-- Filters -->
    <div class="flex gap-3 mb-4">
      <select v-model="ownerTypeFilter" class="text-sm border border-gray-300 rounded-lg px-3 py-2">
        <option value="">All Owner Types</option>
        <option value="company">Company</option>
        <option value="partner">Service Partner</option>
        <option value="platform">Platform</option>
      </select>
      <select v-model="statusFilter" class="text-sm border border-gray-300 rounded-lg px-3 py-2">
        <option value="">All Statuses</option>
        <option value="planned">Planned</option>
        <option value="in_progress">In Progress</option>
        <option value="obtained">Obtained</option>
        <option value="expired">Expired</option>
        <option value="revoked">Revoked</option>
      </select>
    </div>

    <!-- Table -->
    <div class="admin-panel">
      <table class="admin-table w-full text-sm">
        <thead class="bg-gray-50 text-left">
          <tr>
            <th class="px-4 py-3 font-medium text-gray-600">Certification</th>
            <th class="px-4 py-3 font-medium text-gray-600">Issuer</th>
            <th class="px-4 py-3 font-medium text-gray-600">Owner</th>
            <th class="px-4 py-3 font-medium text-gray-600">Status</th>
            <th class="px-4 py-3 font-medium text-gray-600">Expiry</th>
            <th class="px-4 py-3 font-medium text-gray-600">Public</th>
            <th class="px-4 py-3 font-medium text-gray-600 text-right">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y">
          <tr v-for="cert in items" :key="cert.id" class="hover:bg-gray-50">
            <td class="px-4 py-3 font-medium text-gray-900">{{ cert.certification_name }}</td>
            <td class="px-4 py-3 text-gray-600">{{ cert.issuer || '-' }}</td>
            <td class="px-4 py-3">
              <span class="px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-700">{{ cert.owner_type }}</span>
              <span class="text-xs text-gray-400 ml-1">{{ cert.owner_id?.slice(0, 8) }}</span>
            </td>
            <td class="px-4 py-3">
              <span class="px-2 py-0.5 text-xs font-medium rounded-full" :class="statusClass(cert.status)">
                {{ cert.status }}
              </span>
            </td>
            <td class="px-4 py-3 text-gray-600">
              <span v-if="cert.expiry_date" :class="isExpiringSoon(cert.expiry_date) ? 'text-red-600 font-medium' : ''">
                {{ cert.expiry_date }}
              </span>
              <span v-else class="text-gray-400">-</span>
            </td>
            <td class="px-4 py-3">
              <span v-if="cert.public_visible" class="text-green-600">Yes</span>
              <span v-else class="text-gray-400">No</span>
            </td>
            <td class="px-4 py-3 text-right space-x-2">
              <button class="text-xs text-primary-600 hover:underline" @click="openEdit(cert)">Edit</button>
              <button class="text-xs text-red-500 hover:underline" @click="deleteCert(cert.id)">Delete</button>
            </td>
          </tr>
          <tr v-if="!items.length">
            <td colspan="7" class="px-4 py-8 text-center text-gray-400">No certifications found.</td>
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

    <!-- Create/Edit Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="showModal = false">
      <div class="bg-white rounded-xl w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
        <h2 class="text-lg font-bold text-gray-900 mb-4">{{ editingCert ? 'Edit Certification' : 'Add Certification' }}</h2>
        <div class="space-y-3">
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Certification Name *</label>
            <input v-model="form.certification_name" type="text" class="w-full text-sm border border-gray-300 rounded-lg p-2" placeholder="e.g. KNX Partner" />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Owner Type *</label>
              <select v-model="form.owner_type" class="w-full text-sm border border-gray-300 rounded-lg p-2" :disabled="!!editingCert">
                <option value="company">Company</option>
                <option value="partner">Service Partner</option>
                <option value="platform">Platform</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Owner ID *</label>
              <input v-model="form.owner_id" type="text" class="w-full text-sm border border-gray-300 rounded-lg p-2" placeholder="UUID" :disabled="!!editingCert" />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Issuer</label>
              <input v-model="form.issuer" type="text" class="w-full text-sm border border-gray-300 rounded-lg p-2" placeholder="e.g. KNX Association" />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Country</label>
              <input v-model="form.country" type="text" class="w-full text-sm border border-gray-300 rounded-lg p-2" placeholder="e.g. Belgium" />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Status</label>
              <select v-model="form.status" class="w-full text-sm border border-gray-300 rounded-lg p-2">
                <option value="planned">Planned</option>
                <option value="in_progress">In Progress</option>
                <option value="obtained">Obtained</option>
                <option value="expired">Expired</option>
                <option value="revoked">Revoked</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Public Visible</label>
              <select v-model="form.public_visible" class="w-full text-sm border border-gray-300 rounded-lg p-2">
                <option :value="true">Yes</option>
                <option :value="false">No</option>
              </select>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Issue Date</label>
              <input v-model="form.issue_date" type="date" class="w-full text-sm border border-gray-300 rounded-lg p-2" />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Expiry Date</label>
              <input v-model="form.expiry_date" type="date" class="w-full text-sm border border-gray-300 rounded-lg p-2" />
            </div>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Certificate File URL</label>
            <input v-model="form.certificate_file_url" type="text" class="w-full text-sm border border-gray-300 rounded-lg p-2" placeholder="https://..." />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Notes</label>
            <textarea v-model="form.notes" rows="2" class="w-full text-sm border border-gray-300 rounded-lg p-2" />
          </div>
        </div>
        <div class="mt-4 flex justify-end gap-2">
          <button class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800" @click="showModal = false">Cancel</button>
          <button
            class="px-4 py-2 text-sm font-medium bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-60"
            :disabled="saving || !form.certification_name || !form.owner_id"
            @click="saveCert"
          >{{ saving ? 'Saving...' : 'Save' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { apiFetch } = useApi()
const items = ref<any[]>([])
const total = ref(0)
const page = ref(0)
const limit = 20
const ownerTypeFilter = ref('')
const statusFilter = ref('')
const showModal = ref(false)
const editingCert = ref<any>(null)
const saving = ref(false)

const defaultForm = () => ({
  certification_name: '',
  owner_type: 'platform',
  owner_id: '',
  issuer: '',
  country: '',
  status: 'planned',
  issue_date: '',
  expiry_date: '',
  certificate_file_url: '',
  public_visible: false,
  notes: '',
})

const form = reactive(defaultForm())

function statusClass(status: string) {
  const map: Record<string, string> = {
    planned: 'bg-gray-100 text-gray-700',
    in_progress: 'bg-blue-100 text-blue-700',
    obtained: 'bg-green-100 text-green-700',
    expired: 'bg-red-100 text-red-700',
    revoked: 'bg-red-100 text-red-700',
  }
  return map[status] || 'bg-gray-100 text-gray-700'
}

function isExpiringSoon(dateStr: string) {
  const d = new Date(dateStr)
  const now = new Date()
  const diff = (d.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)
  return diff < 60 && diff > -9999
}

async function load() {
  const params = new URLSearchParams()
  params.set('skip', String(page.value * limit))
  params.set('limit', String(limit))
  if (ownerTypeFilter.value) params.set('owner_type', ownerTypeFilter.value)
  if (statusFilter.value) params.set('status', statusFilter.value)
  try {
    const res = await apiFetch<any>(`/certifications?${params}`)
    items.value = res.items || []
    total.value = res.total || 0
  } catch {}
}

function openCreate() {
  editingCert.value = null
  Object.assign(form, defaultForm())
  showModal.value = true
}

function openEdit(cert: any) {
  editingCert.value = cert
  Object.assign(form, {
    certification_name: cert.certification_name || '',
    owner_type: cert.owner_type || 'platform',
    owner_id: cert.owner_id || '',
    issuer: cert.issuer || '',
    country: cert.country || '',
    status: cert.status || 'planned',
    issue_date: cert.issue_date || '',
    expiry_date: cert.expiry_date || '',
    certificate_file_url: cert.certificate_file_url || '',
    public_visible: cert.public_visible ?? false,
    notes: cert.notes || '',
  })
  showModal.value = true
}

async function saveCert() {
  saving.value = true
  try {
    const body: Record<string, any> = { ...form }
    if (!body.issue_date) delete body.issue_date
    if (!body.expiry_date) delete body.expiry_date
    if (!body.certificate_file_url) delete body.certificate_file_url

    if (editingCert.value) {
      delete body.owner_type
      delete body.owner_id
      await apiFetch(`/certifications/${editingCert.value.id}`, { method: 'PUT', body })
    } else {
      await apiFetch('/certifications', { method: 'POST', body })
    }
    showModal.value = false
    await load()
  } catch (e: any) {
    console.error('Save cert failed:', e)
  } finally {
    saving.value = false
  }
}

async function deleteCert(id: string) {
  if (!confirm('Delete this certification record?')) return
  try {
    await apiFetch(`/certifications/${id}`, { method: 'DELETE' })
    await load()
  } catch {}
}

watch([page, ownerTypeFilter, statusFilter], () => load())
onMounted(() => load())
</script>
