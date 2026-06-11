<template>
  <div>
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Service Partners</h1>
        <p class="text-sm text-gray-500 mt-1">Manage local installation and maintenance partners.</p>
      </div>
      <div class="flex gap-2">
        <select v-model="statusFilter" class="input-field max-w-44" @change="loadPartners">
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="verified">Verified</option>
          <option value="suspended">Suspended</option>
        </select>
        <button @click="showCreate = true" class="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700">
          + Add Partner
        </button>
      </div>
    </div>

    <div class="bg-white rounded-xl border overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 border-b">
          <tr>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Partner</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Type</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Location</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Skills</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Status</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Availability</th>
            <th class="text-right px-4 py-3 font-medium text-gray-500">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="partner in partners"
            :key="partner.id"
            class="border-b hover:bg-gray-50 cursor-pointer"
            @click="openDetail(partner)"
          >
            <td class="px-4 py-3">
              <p class="font-medium text-gray-900">{{ partner.id.slice(0, 8) }}</p>
              <p class="text-xs text-gray-500">{{ partner.hourly_rate ? `${partner.hourly_rate} EUR/hr` : '-' }}</p>
            </td>
            <td class="px-4 py-3 text-gray-600">{{ partner.partner_type }}</td>
            <td class="px-4 py-3 text-gray-600">
              {{ [partner.city, partner.country].filter(Boolean).join(', ') || '-' }}
              <span v-if="partner.service_radius_km" class="text-xs text-gray-400 ml-1">({{ partner.service_radius_km }}km)</span>
            </td>
            <td class="px-4 py-3">
              <div class="flex flex-wrap gap-1">
                <span
                  v-for="skill in (partner.skills_json || []).slice(0, 3)"
                  :key="skill"
                  class="px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-600"
                >{{ skill }}</span>
                <span v-if="(partner.skills_json || []).length > 3" class="text-xs text-gray-400">+{{ partner.skills_json.length - 3 }}</span>
              </div>
            </td>
            <td class="px-4 py-3"><StatusBadge :status="partner.verification_status" /></td>
            <td class="px-4 py-3"><StatusBadge :status="partner.availability_status" /></td>
            <td class="px-4 py-3 text-right">
              <button
                v-if="partner.verification_status === 'pending'"
                class="px-2 py-1 text-xs font-medium rounded bg-green-100 text-green-700 hover:bg-green-200 mr-1"
                @click.stop="updateStatus(partner.id, 'verified')"
              >
                Verify
              </button>
              <button
                v-if="partner.verification_status === 'verified'"
                class="px-2 py-1 text-xs font-medium rounded bg-yellow-100 text-yellow-700 hover:bg-yellow-200"
                @click.stop="updateStatus(partner.id, 'suspended')"
              >
                Suspend
              </button>
              <button
                v-if="partner.verification_status === 'suspended'"
                class="px-2 py-1 text-xs font-medium rounded bg-blue-100 text-blue-700 hover:bg-blue-200"
                @click.stop="updateStatus(partner.id, 'verified')"
              >
                Reactivate
              </button>
            </td>
          </tr>
          <tr v-if="!partners.length">
            <td colspan="7" class="px-4 py-8 text-center text-gray-500">No service partners found.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create Modal -->
    <div v-if="showCreate" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showCreate = false">
      <div class="bg-white rounded-xl w-full max-w-lg mx-4 p-6 max-h-[80vh] overflow-y-auto">
        <h2 class="text-lg font-bold text-gray-900 mb-4">Add Service Partner</h2>
        <form class="space-y-4" @submit.prevent="createPartner">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Partner Type *</label>
            <select v-model="createForm.partner_type" class="input-field" required>
              <option value="">Select type</option>
              <option value="installer">Installer</option>
              <option value="electrician">Electrician</option>
              <option value="network_engineer">Network Engineer</option>
              <option value="knx_programmer">KNX Programmer</option>
              <option value="maintenance">Maintenance</option>
              <option value="general_contractor">General Contractor</option>
            </select>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Country</label>
              <input v-model="createForm.country" type="text" class="input-field" placeholder="e.g. Serbia" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">City</label>
              <input v-model="createForm.city" type="text" class="input-field" placeholder="e.g. Belgrade" />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Hourly Rate (EUR)</label>
              <input v-model.number="createForm.hourly_rate" type="number" step="0.01" class="input-field" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Service Radius (km)</label>
              <input v-model.number="createForm.service_radius_km" type="number" class="input-field" />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Skills (comma separated)</label>
            <input v-model="skillsText" type="text" class="input-field" placeholder="e.g. KNX, DALI, CCTV, network" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Languages (comma separated)</label>
            <input v-model="languagesText" type="text" class="input-field" placeholder="e.g. English, Serbian" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Notes</label>
            <textarea v-model="createForm.notes_internal" rows="3" class="input-field" placeholder="Internal notes..." />
          </div>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" class="px-4 py-2 text-sm border rounded-lg text-gray-600 hover:bg-gray-50" @click="showCreate = false">Cancel</button>
            <button type="submit" class="px-4 py-2 text-sm font-medium bg-primary-600 text-white rounded-lg hover:bg-primary-700" :disabled="saving">
              {{ saving ? 'Saving...' : 'Add Partner' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Detail Modal -->
    <div v-if="selectedPartner" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="selectedPartner = null">
      <div class="bg-white rounded-xl w-full max-w-lg mx-4 p-6 max-h-[80vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-bold text-gray-900">Partner Detail</h2>
          <button @click="selectedPartner = null" class="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
        </div>
        <dl class="space-y-3 text-sm">
          <div class="flex justify-between"><dt class="text-gray-500">ID</dt><dd class="font-mono text-xs">{{ selectedPartner.id }}</dd></div>
          <div class="flex justify-between"><dt class="text-gray-500">Type</dt><dd class="font-medium">{{ selectedPartner.partner_type }}</dd></div>
          <div class="flex justify-between"><dt class="text-gray-500">Location</dt><dd>{{ [selectedPartner.city, selectedPartner.country].filter(Boolean).join(', ') || '-' }}</dd></div>
          <div class="flex justify-between"><dt class="text-gray-500">Radius</dt><dd>{{ selectedPartner.service_radius_km ? `${selectedPartner.service_radius_km} km` : '-' }}</dd></div>
          <div class="flex justify-between"><dt class="text-gray-500">Hourly Rate</dt><dd>{{ selectedPartner.hourly_rate ? `${selectedPartner.hourly_rate} EUR` : '-' }}</dd></div>
          <div class="flex justify-between"><dt class="text-gray-500">Day Rate</dt><dd>{{ selectedPartner.day_rate ? `${selectedPartner.day_rate} EUR` : '-' }}</dd></div>
          <div class="flex justify-between"><dt class="text-gray-500">Verification</dt><dd><StatusBadge :status="selectedPartner.verification_status" /></dd></div>
          <div class="flex justify-between"><dt class="text-gray-500">Availability</dt><dd><StatusBadge :status="selectedPartner.availability_status" /></dd></div>
          <div v-if="selectedPartner.skills_json?.length">
            <dt class="text-gray-500 mb-1">Skills</dt>
            <dd class="flex flex-wrap gap-1">
              <span v-for="s in selectedPartner.skills_json" :key="s" class="px-2 py-0.5 text-xs rounded-full bg-primary-50 text-primary-700">{{ s }}</span>
            </dd>
          </div>
          <div v-if="selectedPartner.languages_json?.length">
            <dt class="text-gray-500 mb-1">Languages</dt>
            <dd>{{ selectedPartner.languages_json.join(', ') }}</dd>
          </div>
          <div v-if="selectedPartner.certifications_json?.length">
            <dt class="text-gray-500 mb-1">Certifications</dt>
            <dd>{{ selectedPartner.certifications_json.join(', ') }}</dd>
          </div>
          <div v-if="selectedPartner.notes_internal">
            <dt class="text-gray-500 mb-1">Internal Notes</dt>
            <dd class="text-gray-700 whitespace-pre-wrap">{{ selectedPartner.notes_internal }}</dd>
          </div>
        </dl>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'admin' })

const { apiFetch } = useApi()
const partners = ref<any[]>([])
const statusFilter = ref('')
const showCreate = ref(false)
const selectedPartner = ref<any>(null)
const saving = ref(false)
const skillsText = ref('')
const languagesText = ref('')

const createForm = reactive({
  partner_type: '',
  country: '',
  city: '',
  hourly_rate: null as number | null,
  service_radius_km: null as number | null,
  notes_internal: '',
})

async function loadPartners() {
  const params = new URLSearchParams()
  if (statusFilter.value) params.set('verification_status', statusFilter.value)
  try {
    const res = await apiFetch<any>(`/service-partners?${params.toString()}`)
    partners.value = res.items || []
  } catch {
    partners.value = []
  }
}

function openDetail(partner: any) {
  selectedPartner.value = partner
}

async function createPartner() {
  saving.value = true
  try {
    const body: any = { partner_type: createForm.partner_type }
    if (createForm.country) body.country = createForm.country
    if (createForm.city) body.city = createForm.city
    if (createForm.hourly_rate) body.hourly_rate = createForm.hourly_rate
    if (createForm.service_radius_km) body.service_radius_km = createForm.service_radius_km
    if (createForm.notes_internal) body.notes_internal = createForm.notes_internal
    if (skillsText.value.trim()) body.skills_json = skillsText.value.split(',').map((s: string) => s.trim()).filter(Boolean)
    if (languagesText.value.trim()) body.languages_json = languagesText.value.split(',').map((s: string) => s.trim()).filter(Boolean)

    await apiFetch('/service-partners', { method: 'POST', body })
    showCreate.value = false
    Object.assign(createForm, { partner_type: '', country: '', city: '', hourly_rate: null, service_radius_km: null, notes_internal: '' })
    skillsText.value = ''
    languagesText.value = ''
    await loadPartners()
  } catch (e: any) {
    console.error('Create partner failed:', e)
  } finally {
    saving.value = false
  }
}

async function updateStatus(id: string, newStatus: string) {
  try {
    await apiFetch(`/service-partners/${id}/status`, {
      method: 'PATCH',
      body: { verification_status: newStatus },
    })
    await loadPartners()
  } catch (e: any) {
    console.error('Status update failed:', e)
  }
}

onMounted(loadPartners)
</script>
