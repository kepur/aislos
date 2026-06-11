<template>
  <div>
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Proposal Plans</h1>
        <p class="text-sm text-gray-500 mt-1">Four-tier smart building proposals with cost breakdown.</p>
      </div>
      <div class="flex gap-2">
        <select v-model="tierFilter" class="input-field max-w-40" @change="loadProposals">
          <option value="">All tiers</option>
          <option value="budget">Budget</option>
          <option value="standard">Standard</option>
          <option value="premium">Premium AI</option>
          <option value="future">Future Autonomous</option>
        </select>
        <button @click="openCreate" class="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700">
          + New Proposal
        </button>
      </div>
    </div>

    <div class="bg-white rounded-xl border overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 border-b">
          <tr>
            <th class="text-left px-4 py-3 font-medium text-gray-500">ID</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Tier</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Lead / Project</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Intelligence</th>
            <th class="text-right px-4 py-3 font-medium text-gray-500">Total Range</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Complexity</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Created</th>
            <th class="text-right px-4 py-3 font-medium text-gray-500">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in proposals" :key="p.id" class="border-b hover:bg-gray-50">
            <td class="px-4 py-3 font-mono text-xs text-gray-900">{{ p.id.slice(0, 8) }}</td>
            <td class="px-4 py-3">
              <span :class="tierBadge(p.tier)" class="px-2 py-0.5 rounded-full text-xs font-medium">{{ p.tier }}</span>
            </td>
            <td class="px-4 py-3">
              <NuxtLink v-if="p.lead_id" :to="`/admin/leads/${p.lead_id}`" class="text-primary-600 hover:underline text-xs">
                L-{{ p.lead_id.slice(0, 6) }}
              </NuxtLink>
              <NuxtLink v-if="p.project_id" :to="`/admin/projects/${p.project_id}`" class="text-blue-600 hover:underline text-xs ml-1">
                P-{{ p.project_id.slice(0, 6) }}
              </NuxtLink>
              <span v-if="!p.lead_id && !p.project_id" class="text-gray-400">-</span>
            </td>
            <td class="px-4 py-3 text-gray-700">
              <span v-if="p.intelligence_level_min">L{{ p.intelligence_level_min }}<span v-if="p.intelligence_level_max && p.intelligence_level_max !== p.intelligence_level_min">-L{{ p.intelligence_level_max }}</span></span>
              <span v-else class="text-gray-400">-</span>
            </td>
            <td class="px-4 py-3 text-right font-medium">
              {{ formatCurrency(p.total_min) }} - {{ formatCurrency(p.total_max) }}
              <span class="text-gray-400 text-xs ml-1">{{ p.currency }}</span>
            </td>
            <td class="px-4 py-3">
              <span v-if="p.complexity" :class="complexityColor(p.complexity)" class="text-xs font-medium">{{ p.complexity }}</span>
              <span v-else class="text-gray-400">-</span>
            </td>
            <td class="px-4 py-3 text-gray-500 whitespace-nowrap">{{ new Date(p.created_at).toLocaleDateString() }}</td>
            <td class="px-4 py-3 text-right">
              <div class="flex justify-end gap-1">
                <NuxtLink :to="`/admin/proposals/${p.id}`" class="px-2 py-1 text-xs font-medium rounded bg-blue-100 text-blue-700 hover:bg-blue-200">
                  BOM
                </NuxtLink>
                <button class="px-2 py-1 text-xs font-medium rounded bg-gray-100 text-gray-700 hover:bg-gray-200" @click="openEdit(p)">Edit</button>
                <button class="px-2 py-1 text-xs font-medium rounded bg-red-100 text-red-700 hover:bg-red-200" @click="deleteProposal(p.id)">Del</button>
              </div>
            </td>
          </tr>
          <tr v-if="!proposals.length">
            <td colspan="8" class="px-4 py-8 text-center text-gray-500">No proposal plans found.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <p v-if="total > proposals.length" class="text-xs text-gray-500 mt-3 text-right">
      Showing {{ proposals.length }} of {{ total }}
    </p>

    <!-- Create/Edit Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showModal = false">
      <div class="bg-white rounded-xl w-full max-w-2xl mx-4 p-6 max-h-[85vh] overflow-y-auto">
        <h2 class="text-lg font-bold text-gray-900 mb-4">{{ editId ? 'Edit' : 'Create' }} Proposal Plan</h2>
        <form class="space-y-4" @submit.prevent="saveProposal">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Tier *</label>
              <select v-model="form.tier" class="input-field" required>
                <option value="budget">Budget</option>
                <option value="standard">Standard</option>
                <option value="premium">Premium AI</option>
                <option value="future">Future Autonomous</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Currency</label>
              <input v-model="form.currency" type="text" class="input-field" placeholder="EUR" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Lead ID</label>
              <input v-model="form.lead_id" type="text" class="input-field" placeholder="UUID (optional)" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Project ID</label>
              <input v-model="form.project_id" type="text" class="input-field" placeholder="UUID (optional)" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Intelligence Min (L1-L6)</label>
              <input v-model.number="form.intelligence_level_min" type="number" min="1" max="6" class="input-field" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Intelligence Max (L1-L6)</label>
              <input v-model.number="form.intelligence_level_max" type="number" min="1" max="6" class="input-field" />
            </div>
          </div>

          <p class="text-xs font-semibold text-gray-500 uppercase tracking-wider border-b pb-1">Cost Estimates</p>
          <div class="grid grid-cols-3 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Device Cost</label>
              <input v-model.number="form.device_cost_estimate" type="number" step="0.01" class="input-field" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Design Fee</label>
              <input v-model.number="form.design_fee_estimate" type="number" step="0.01" class="input-field" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Installation Fee</label>
              <input v-model.number="form.installation_fee_estimate" type="number" step="0.01" class="input-field" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Platform Fee</label>
              <input v-model.number="form.platform_fee_estimate" type="number" step="0.01" class="input-field" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Maintenance Fee</label>
              <input v-model.number="form.maintenance_fee_estimate" type="number" step="0.01" class="input-field" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Spare Parts Reserve</label>
              <input v-model.number="form.spare_parts_reserve" type="number" step="0.01" class="input-field" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Total Min</label>
              <input v-model.number="form.total_min" type="number" step="0.01" class="input-field" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Total Max</label>
              <input v-model.number="form.total_max" type="number" step="0.01" class="input-field" />
            </div>
          </div>

          <div class="grid grid-cols-3 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Complexity</label>
              <select v-model="form.complexity" class="input-field">
                <option value="">-</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Risk Level</label>
              <select v-model="form.risk_level" class="input-field">
                <option value="">-</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>
            <div class="flex items-end">
              <label class="flex items-center gap-2 text-sm cursor-pointer mb-2">
                <input v-model="form.estimate_only" type="checkbox" class="rounded" />
                Estimate Only
              </label>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Recommended Next Step</label>
            <input v-model="form.recommended_next_step" type="text" class="input-field" placeholder="e.g. Schedule site survey" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Notes</label>
            <textarea v-model="form.notes" rows="2" class="input-field" placeholder="Internal notes..." />
          </div>

          <div class="flex justify-end gap-3 pt-2">
            <button type="button" class="px-4 py-2 text-sm border rounded-lg text-gray-600 hover:bg-gray-50" @click="showModal = false">Cancel</button>
            <button type="submit" class="px-4 py-2 text-sm font-medium bg-primary-600 text-white rounded-lg hover:bg-primary-700" :disabled="saving">
              {{ saving ? 'Saving...' : (editId ? 'Update' : 'Create') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'admin' })

const { apiFetch } = useApi()
const proposals = ref<any[]>([])
const total = ref(0)
const tierFilter = ref('')
const showModal = ref(false)
const saving = ref(false)
const editId = ref<string | null>(null)

const defaultForm = () => ({
  tier: 'standard',
  lead_id: '',
  project_id: '',
  intelligence_level_min: null as number | null,
  intelligence_level_max: null as number | null,
  device_cost_estimate: 0,
  design_fee_estimate: 0,
  installation_fee_estimate: 0,
  platform_fee_estimate: 0,
  maintenance_fee_estimate: 0,
  spare_parts_reserve: 0,
  total_min: 0,
  total_max: 0,
  currency: 'EUR',
  complexity: '',
  risk_level: '',
  recommended_next_step: '',
  estimate_only: true,
  notes: '',
})
const form = reactive(defaultForm())

function tierBadge(tier: string) {
  const m: Record<string, string> = {
    budget: 'bg-gray-100 text-gray-700',
    standard: 'bg-blue-100 text-blue-700',
    premium: 'bg-purple-100 text-purple-700',
    future: 'bg-amber-100 text-amber-700',
  }
  return m[tier] || 'bg-gray-100 text-gray-700'
}

function complexityColor(c: string) {
  const m: Record<string, string> = { low: 'text-green-600', medium: 'text-yellow-600', high: 'text-red-600' }
  return m[c] || 'text-gray-600'
}

function formatCurrency(v: number) {
  return v ? v.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 }) : '0'
}

async function loadProposals() {
  const params = tierFilter.value ? `?tier=${tierFilter.value}` : ''
  try {
    const res = await apiFetch<any>(`/proposals${params}`)
    proposals.value = res.items || []
    total.value = res.total || 0
  } catch {
    proposals.value = []
  }
}

function openCreate() {
  editId.value = null
  Object.assign(form, defaultForm())
  showModal.value = true
}

function openEdit(p: any) {
  editId.value = p.id
  Object.assign(form, {
    tier: p.tier,
    lead_id: p.lead_id || '',
    project_id: p.project_id || '',
    intelligence_level_min: p.intelligence_level_min,
    intelligence_level_max: p.intelligence_level_max,
    device_cost_estimate: p.device_cost_estimate,
    design_fee_estimate: p.design_fee_estimate,
    installation_fee_estimate: p.installation_fee_estimate,
    platform_fee_estimate: p.platform_fee_estimate,
    maintenance_fee_estimate: p.maintenance_fee_estimate,
    spare_parts_reserve: p.spare_parts_reserve,
    total_min: p.total_min,
    total_max: p.total_max,
    currency: p.currency,
    complexity: p.complexity || '',
    risk_level: p.risk_level || '',
    recommended_next_step: p.recommended_next_step || '',
    estimate_only: p.estimate_only,
    notes: p.notes || '',
  })
  showModal.value = true
}

async function saveProposal() {
  saving.value = true
  try {
    const body: any = { ...form }
    if (!body.lead_id) delete body.lead_id
    if (!body.project_id) delete body.project_id
    if (!body.complexity) body.complexity = null
    if (!body.risk_level) body.risk_level = null
    if (!body.recommended_next_step) body.recommended_next_step = null
    if (!body.notes) body.notes = null

    if (editId.value) {
      await apiFetch(`/proposals/${editId.value}`, { method: 'PUT', body })
    } else {
      await apiFetch('/proposals', { method: 'POST', body })
    }
    showModal.value = false
    await loadProposals()
  } catch (e: any) {
    console.error('Save proposal failed:', e)
  } finally {
    saving.value = false
  }
}

async function deleteProposal(id: string) {
  if (!confirm('Delete this proposal plan and all its BOM items?')) return
  try {
    await apiFetch(`/proposals/${id}`, { method: 'DELETE' })
    await loadProposals()
  } catch (e: any) {
    console.error('Delete failed:', e)
  }
}

onMounted(loadProposals)
</script>
