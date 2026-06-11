<template>
  <div v-if="plan">
    <NuxtLink to="/admin/proposals" class="text-sm text-primary-600 hover:underline">&larr; Back to Proposals</NuxtLink>

    <!-- Proposal Header -->
    <div class="mt-4 flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">
          Proposal — <span :class="tierColor(plan.tier)" class="capitalize">{{ plan.tier }}</span>
        </h1>
        <p class="text-sm text-gray-500 mt-1">
          ID: {{ plan.id.slice(0, 8) }}
          <span v-if="plan.estimate_only" class="ml-2 px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded-full text-xs font-medium">Estimate Only</span>
        </p>
      </div>
      <div class="flex gap-2 items-center">
        <span class="text-lg font-bold text-gray-900">
          {{ formatCurrency(plan.total_min) }} - {{ formatCurrency(plan.total_max) }} {{ plan.currency }}
        </span>
      </div>
    </div>

    <!-- Summary Cards -->
    <div class="mt-6 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
      <div class="bg-white rounded-lg border p-3 text-center">
        <p class="text-xs text-gray-500">Devices</p>
        <p class="text-lg font-bold text-gray-900">{{ formatCurrency(plan.device_cost_estimate) }}</p>
      </div>
      <div class="bg-white rounded-lg border p-3 text-center">
        <p class="text-xs text-gray-500">Design</p>
        <p class="text-lg font-bold text-gray-900">{{ formatCurrency(plan.design_fee_estimate) }}</p>
      </div>
      <div class="bg-white rounded-lg border p-3 text-center">
        <p class="text-xs text-gray-500">Installation</p>
        <p class="text-lg font-bold text-gray-900">{{ formatCurrency(plan.installation_fee_estimate) }}</p>
      </div>
      <div class="bg-white rounded-lg border p-3 text-center">
        <p class="text-xs text-gray-500">Platform</p>
        <p class="text-lg font-bold text-gray-900">{{ formatCurrency(plan.platform_fee_estimate) }}</p>
      </div>
      <div class="bg-white rounded-lg border p-3 text-center">
        <p class="text-xs text-gray-500">Maintenance</p>
        <p class="text-lg font-bold text-gray-900">{{ formatCurrency(plan.maintenance_fee_estimate) }}</p>
      </div>
      <div class="bg-white rounded-lg border p-3 text-center">
        <p class="text-xs text-gray-500">Spare Parts</p>
        <p class="text-lg font-bold text-gray-900">{{ formatCurrency(plan.spare_parts_reserve) }}</p>
      </div>
    </div>

    <!-- BOM Section -->
    <div class="mt-8">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-bold text-gray-900">Bill of Materials (BOM)</h2>
        <div class="flex gap-2">
          <span class="text-sm text-gray-500">{{ bomItems.length }} items &middot; BOM Total: <strong>{{ formatCurrency(bomTotal) }} {{ plan.currency }}</strong></span>
          <button @click="openAddItem" class="px-3 py-1.5 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700">
            + Add Item
          </button>
        </div>
      </div>

      <div class="bg-white rounded-xl border overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 border-b">
            <tr>
              <th class="text-left px-3 py-2 font-medium text-gray-500 w-8">#</th>
              <th class="text-left px-3 py-2 font-medium text-gray-500">Name</th>
              <th class="text-left px-3 py-2 font-medium text-gray-500">Category</th>
              <th class="text-left px-3 py-2 font-medium text-gray-500">Brand</th>
              <th class="text-right px-3 py-2 font-medium text-gray-500">Qty</th>
              <th class="text-right px-3 py-2 font-medium text-gray-500">Unit Price</th>
              <th class="text-right px-3 py-2 font-medium text-gray-500">Device</th>
              <th class="text-right px-3 py-2 font-medium text-gray-500">Install</th>
              <th class="text-right px-3 py-2 font-medium text-gray-500">Service</th>
              <th class="text-center px-3 py-2 font-medium text-gray-500">Flags</th>
              <th class="text-right px-3 py-2 font-medium text-gray-500">Total</th>
              <th class="text-right px-3 py-2 font-medium text-gray-500 w-20">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, idx) in bomItems" :key="item.id" class="border-b hover:bg-gray-50" :class="item.already_owned ? 'bg-green-50/50' : ''">
              <td class="px-3 py-2 text-gray-400">{{ idx + 1 }}</td>
              <td class="px-3 py-2 font-medium text-gray-900">
                {{ item.name }}
                <p v-if="item.notes" class="text-xs text-gray-400 truncate max-w-[200px]">{{ item.notes }}</p>
              </td>
              <td class="px-3 py-2 text-gray-600">{{ item.category || '-' }}</td>
              <td class="px-3 py-2 text-gray-600">{{ item.brand || '-' }}</td>
              <td class="px-3 py-2 text-right">{{ item.qty }}</td>
              <td class="px-3 py-2 text-right">{{ item.unit_price.toFixed(2) }}</td>
              <td class="px-3 py-2 text-right">{{ item.device_cost.toFixed(2) }}</td>
              <td class="px-3 py-2 text-right">{{ item.installation_cost.toFixed(2) }}</td>
              <td class="px-3 py-2 text-right">{{ item.service_fee.toFixed(2) }}</td>
              <td class="px-3 py-2 text-center">
                <div class="flex justify-center gap-1">
                  <span v-if="item.already_owned" class="px-1.5 py-0.5 bg-green-100 text-green-700 rounded text-[10px] font-medium" title="Already owned">Own</span>
                  <span v-if="item.need_ainerwise_supply" class="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-[10px] font-medium" title="Ainerwise supply">Sup</span>
                  <span v-if="item.need_installation" class="px-1.5 py-0.5 bg-purple-100 text-purple-700 rounded text-[10px] font-medium" title="Needs installation">Ins</span>
                  <span v-if="item.design_only" class="px-1.5 py-0.5 bg-amber-100 text-amber-700 rounded text-[10px] font-medium" title="Design only">Des</span>
                </div>
              </td>
              <td class="px-3 py-2 text-right font-medium">{{ item.total.toFixed(2) }}</td>
              <td class="px-3 py-2 text-right">
                <div class="flex justify-end gap-1">
                  <button class="px-1.5 py-0.5 text-xs rounded bg-gray-100 text-gray-700 hover:bg-gray-200" @click="openEditItem(item)">Edit</button>
                  <button class="px-1.5 py-0.5 text-xs rounded bg-red-100 text-red-700 hover:bg-red-200" @click="deleteItem(item.id)">Del</button>
                </div>
              </td>
            </tr>
            <tr v-if="!bomItems.length">
              <td colspan="12" class="px-4 py-8 text-center text-gray-500">No BOM items yet. Click "+ Add Item" to begin building the bill of materials.</td>
            </tr>
          </tbody>
          <tfoot v-if="bomItems.length" class="bg-gray-50 border-t-2">
            <tr class="font-bold">
              <td colspan="4" class="px-3 py-2 text-right text-gray-700">Totals</td>
              <td class="px-3 py-2 text-right">{{ totalQty }}</td>
              <td class="px-3 py-2"></td>
              <td class="px-3 py-2 text-right">{{ totalDevice.toFixed(2) }}</td>
              <td class="px-3 py-2 text-right">{{ totalInstall.toFixed(2) }}</td>
              <td class="px-3 py-2 text-right">{{ totalService.toFixed(2) }}</td>
              <td class="px-3 py-2"></td>
              <td class="px-3 py-2 text-right text-primary-700">{{ bomTotal.toFixed(2) }}</td>
              <td class="px-3 py-2"></td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>

    <!-- Add/Edit BOM Item Modal -->
    <div v-if="showItemModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showItemModal = false">
      <div class="bg-white rounded-xl w-full max-w-2xl mx-4 p-6 max-h-[85vh] overflow-y-auto">
        <h2 class="text-lg font-bold text-gray-900 mb-4">{{ editItemId ? 'Edit' : 'Add' }} BOM Item</h2>
        <form class="space-y-4" @submit.prevent="saveItem">
          <div class="grid grid-cols-2 gap-4">
            <div class="col-span-2">
              <label class="block text-sm font-medium text-gray-700 mb-1">Name *</label>
              <input v-model="itemForm.name" type="text" class="input-field" required placeholder="e.g. KNX Dimming Actuator 4ch" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Category</label>
              <select v-model="itemForm.category" class="input-field">
                <option value="">-</option>
                <option value="lighting">Lighting</option>
                <option value="hvac">HVAC</option>
                <option value="security">Security</option>
                <option value="shading">Shading</option>
                <option value="energy">Energy</option>
                <option value="sensor">Sensor</option>
                <option value="controller">Controller</option>
                <option value="network">Network</option>
                <option value="interface">Interface</option>
                <option value="software">Software</option>
                <option value="service">Service</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Brand</label>
              <input v-model="itemForm.brand" type="text" class="input-field" placeholder="e.g. ABB, Schneider" />
            </div>
          </div>

          <div class="grid grid-cols-4 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Qty</label>
              <input v-model.number="itemForm.qty" type="number" min="1" class="input-field" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Unit Price</label>
              <input v-model.number="itemForm.unit_price" type="number" step="0.01" class="input-field" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Device Cost</label>
              <input v-model.number="itemForm.device_cost" type="number" step="0.01" class="input-field" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Total</label>
              <input v-model.number="itemForm.total" type="number" step="0.01" class="input-field" />
            </div>
          </div>

          <div class="grid grid-cols-3 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Installation Cost</label>
              <input v-model.number="itemForm.installation_cost" type="number" step="0.01" class="input-field" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Service Fee</label>
              <input v-model.number="itemForm.service_fee" type="number" step="0.01" class="input-field" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Maintenance Years</label>
              <input v-model.number="itemForm.maintenance_years" type="number" min="0" class="input-field" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Product ID (optional)</label>
              <input v-model="itemForm.product_id" type="text" class="input-field" placeholder="Link to catalog product" />
            </div>
            <div class="flex items-end gap-4 pb-1">
              <label class="flex items-center gap-1.5 text-sm cursor-pointer">
                <input v-model="itemForm.already_owned" type="checkbox" class="rounded" /> Owned
              </label>
              <label class="flex items-center gap-1.5 text-sm cursor-pointer">
                <input v-model="itemForm.need_ainerwise_supply" type="checkbox" class="rounded" /> Supply
              </label>
              <label class="flex items-center gap-1.5 text-sm cursor-pointer">
                <input v-model="itemForm.need_installation" type="checkbox" class="rounded" /> Install
              </label>
              <label class="flex items-center gap-1.5 text-sm cursor-pointer">
                <input v-model="itemForm.design_only" type="checkbox" class="rounded" /> Design
              </label>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Notes</label>
            <textarea v-model="itemForm.notes" rows="2" class="input-field" placeholder="Item notes..." />
          </div>

          <div class="flex justify-end gap-3 pt-2">
            <button type="button" class="px-4 py-2 text-sm border rounded-lg text-gray-600 hover:bg-gray-50" @click="showItemModal = false">Cancel</button>
            <button type="submit" class="px-4 py-2 text-sm font-medium bg-primary-600 text-white rounded-lg hover:bg-primary-700" :disabled="savingItem">
              {{ savingItem ? 'Saving...' : (editItemId ? 'Update' : 'Add Item') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>

  <div v-else class="flex items-center justify-center py-20">
    <p class="text-gray-500">Loading proposal...</p>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'admin' })

const route = useRoute()
const { apiFetch } = useApi()

const planId = route.params.id as string
const plan = ref<any>(null)
const bomItems = ref<any[]>([])
const showItemModal = ref(false)
const savingItem = ref(false)
const editItemId = ref<string | null>(null)

const defaultItemForm = () => ({
  name: '',
  category: '',
  brand: '',
  qty: 1,
  unit_price: 0,
  device_cost: 0,
  installation_cost: 0,
  service_fee: 0,
  maintenance_years: null as number | null,
  total: 0,
  product_id: '',
  already_owned: false,
  need_ainerwise_supply: true,
  need_installation: true,
  design_only: false,
  notes: '',
})
const itemForm = reactive(defaultItemForm())

const bomTotal = computed(() => bomItems.value.reduce((s, i) => s + (i.total || 0), 0))
const totalQty = computed(() => bomItems.value.reduce((s, i) => s + (i.qty || 0), 0))
const totalDevice = computed(() => bomItems.value.reduce((s, i) => s + (i.device_cost || 0), 0))
const totalInstall = computed(() => bomItems.value.reduce((s, i) => s + (i.installation_cost || 0), 0))
const totalService = computed(() => bomItems.value.reduce((s, i) => s + (i.service_fee || 0), 0))

function tierColor(t: string) {
  const m: Record<string, string> = {
    budget: 'text-gray-700',
    standard: 'text-blue-700',
    premium: 'text-purple-700',
    future: 'text-amber-700',
  }
  return m[t] || 'text-gray-700'
}

function formatCurrency(v: number) {
  return v ? v.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 }) : '0'
}

async function loadPlan() {
  try {
    plan.value = await apiFetch<any>(`/proposals/${planId}`)
  } catch {
    plan.value = null
  }
}

async function loadBom() {
  try {
    const res = await apiFetch<any>(`/proposals/${planId}/bom`)
    bomItems.value = res.items || []
  } catch {
    bomItems.value = []
  }
}

function openAddItem() {
  editItemId.value = null
  Object.assign(itemForm, defaultItemForm())
  showItemModal.value = true
}

function openEditItem(item: any) {
  editItemId.value = item.id
  Object.assign(itemForm, {
    name: item.name,
    category: item.category || '',
    brand: item.brand || '',
    qty: item.qty,
    unit_price: item.unit_price,
    device_cost: item.device_cost,
    installation_cost: item.installation_cost,
    service_fee: item.service_fee,
    maintenance_years: item.maintenance_years,
    total: item.total,
    product_id: item.product_id || '',
    already_owned: item.already_owned,
    need_ainerwise_supply: item.need_ainerwise_supply,
    need_installation: item.need_installation,
    design_only: item.design_only,
    notes: item.notes || '',
  })
  showItemModal.value = true
}

async function saveItem() {
  savingItem.value = true
  try {
    const body: any = { ...itemForm }
    if (!body.category) body.category = null
    if (!body.brand) body.brand = null
    if (!body.product_id) body.product_id = null
    if (!body.notes) body.notes = null
    body.proposal_plan_id = planId

    if (editItemId.value) {
      await apiFetch(`/proposals/${planId}/bom/${editItemId.value}`, { method: 'PUT', body })
    } else {
      await apiFetch(`/proposals/${planId}/bom`, { method: 'POST', body })
    }
    showItemModal.value = false
    await loadBom()
  } catch (e: any) {
    console.error('Save BOM item failed:', e)
  } finally {
    savingItem.value = false
  }
}

async function deleteItem(itemId: string) {
  if (!confirm('Remove this BOM item?')) return
  try {
    await apiFetch(`/proposals/${planId}/bom/${itemId}`, { method: 'DELETE' })
    await loadBom()
  } catch (e: any) {
    console.error('Delete BOM item failed:', e)
  }
}

onMounted(async () => {
  await Promise.all([loadPlan(), loadBom()])
})
</script>
