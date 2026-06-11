<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="admin-page-title">{{ $t('admin.servicePackages') }}</h1>
      <button @click="showCreateModal = true" class="btn-primary text-sm">{{ $t('common.create') }}</button>
    </div>

    <div class="admin-panel">
      <table class="admin-table w-full text-sm">
        <thead>
          <tr>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Name</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Duration</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Price</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Visible</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Order</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">{{ $t('common.actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="pkg in packages" :key="pkg.id" class="border-b">
            <td class="px-4 py-3 font-medium">{{ pkg.name }}</td>
            <td class="px-4 py-3">{{ pkg.years }} years</td>
            <td class="px-4 py-3">{{ pkg.price_monthly ? `€${pkg.price_monthly}/mo` : '-' }}</td>
            <td class="px-4 py-3"><StatusBadge :status="pkg.public_visible ? 'active' : 'draft'" :label="pkg.public_visible ? 'Yes' : 'No'" /></td>
            <td class="px-4 py-3">{{ pkg.sort_order }}</td>
            <td class="px-4 py-3 flex gap-2">
              <button @click="startEdit(pkg)" class="text-primary-600 hover:underline text-xs">{{ $t('common.edit') }}</button>
              <button @click="handleDelete(pkg.id)" class="text-red-600 hover:underline text-xs">{{ $t('common.delete') }}</button>
            </td>
          </tr>
          <tr v-if="!packages.length">
            <td colspan="6" class="px-4 py-8 text-center text-gray-500">{{ $t('common.noData') }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showCreateModal || editingPkg" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-xl w-full max-w-lg p-6 space-y-4">
        <h2 class="text-lg font-semibold">{{ editingPkg ? 'Edit' : 'Create' }} Service Package</h2>
        <form @submit.prevent="editingPkg ? handleUpdate() : handleCreate()" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Name *</label>
            <input v-model="form.name" type="text" required class="input-field" />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Duration (years)</label>
              <input v-model.number="form.years" type="number" min="1" class="input-field" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Price Monthly (EUR)</label>
              <input v-model.number="form.price_monthly" type="number" step="0.01" class="input-field" />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea v-model="form.description" rows="3" class="input-field" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Included Services (one per line)</label>
            <textarea v-model="includedStr" rows="4" class="input-field" placeholder="24/7 Remote Support&#10;Firmware Updates&#10;Annual On-site Visit" />
          </div>
          <div class="grid grid-cols-3 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">SLA Level</label>
              <input v-model="form.sla_level" type="text" class="input-field" placeholder="Standard" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Response Time</label>
              <input v-model="form.response_time" type="text" class="input-field" placeholder="48h" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Sort Order</label>
              <input v-model.number="form.sort_order" type="number" class="input-field" />
            </div>
          </div>
          <label class="flex items-center gap-2 text-sm">
            <input v-model="form.public_visible" type="checkbox" class="rounded border-gray-300" />
            Publicly visible
          </label>
          <div class="flex gap-3 pt-2">
            <button type="submit" :disabled="saving" class="btn-primary text-sm">
              {{ saving ? 'Saving...' : (editingPkg ? 'Save' : 'Create') }}
            </button>
            <button type="button" @click="closeModal" class="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { apiFetch } = useApi()
const packages = ref<any[]>([])
const showCreateModal = ref(false)
const editingPkg = ref<any>(null)
const saving = ref(false)
const includedStr = ref('')

const form = reactive({
  name: '',
  years: 1,
  price_monthly: null as number | null,
  description: '',
  sla_level: '',
  response_time: '',
  sort_order: 0,
  public_visible: true,
})

onMounted(loadData)

async function loadData() {
  try {
    const res = await apiFetch<any>('/service-packages')
    packages.value = res.items || res || []
  } catch {}
}

function resetForm() {
  Object.assign(form, { name: '', years: 1, price_monthly: null, description: '', sla_level: '', response_time: '', sort_order: 0, public_visible: true })
  includedStr.value = ''
}

function closeModal() {
  showCreateModal.value = false
  editingPkg.value = null
  resetForm()
}

function startEdit(pkg: any) {
  editingPkg.value = pkg
  Object.assign(form, {
    name: pkg.name || '',
    years: pkg.years || 1,
    price_monthly: pkg.price_monthly,
    description: pkg.description || '',
    sla_level: pkg.sla_level || '',
    response_time: pkg.response_time || '',
    sort_order: pkg.sort_order || 0,
    public_visible: pkg.public_visible ?? true,
  })
  includedStr.value = (pkg.included_services_json || []).join('\n')
}

async function handleCreate() {
  saving.value = true
  try {
    const payload: Record<string, any> = { ...form, included_services_json: includedStr.value.split('\n').map(s => s.trim()).filter(Boolean) }
    await apiFetch('/service-packages', { method: 'POST', body: payload })
    closeModal()
    await loadData()
  } catch (e: any) { console.error(e) }
  finally { saving.value = false }
}

async function handleUpdate() {
  saving.value = true
  try {
    const payload: Record<string, any> = { ...form, included_services_json: includedStr.value.split('\n').map(s => s.trim()).filter(Boolean) }
    await apiFetch(`/service-packages/${editingPkg.value.id}`, { method: 'PUT', body: payload })
    closeModal()
    await loadData()
  } catch (e: any) { console.error(e) }
  finally { saving.value = false }
}

async function handleDelete(id: string) {
  if (!confirm('Delete this service package?')) return
  try {
    await apiFetch(`/service-packages/${id}`, { method: 'DELETE' })
    await loadData()
  } catch (e: any) { console.error(e) }
}
</script>
