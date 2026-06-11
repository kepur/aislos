<template>
  <div>
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-6">
      <div>
        <h1 class="admin-page-title">RFQs</h1>
        <p class="admin-page-desc">Trade packages sent to partners for bidding. AI scores, you award.</p>
      </div>
      <select v-model="statusFilter" class="input-field max-w-44" @change="load">
        <option value="">All statuses</option>
        <option v-for="s in ['draft','bidding','evaluating','awarded','cancelled']" :key="s" :value="s">{{ s }}</option>
      </select>
    </div>

    <div class="admin-panel p-4 mb-6">
      <h2 class="font-medium text-gray-900 mb-3">New RFQ</h2>
      <div class="grid gap-2 md:grid-cols-4">
        <input v-model="form.title" placeholder="Title" class="input-field md:col-span-2" />
        <select v-model="form.trade" class="input-field">
          <option v-for="t in ['general','knx','electrical','solar','security','hvac','network']" :key="t" :value="t">{{ t }}</option>
        </select>
        <input v-model="form.lead_id" placeholder="Lead ID (optional)" class="input-field" />
        <input v-model="form.country" placeholder="Country" class="input-field" />
        <input v-model="form.city" placeholder="City" class="input-field" />
        <input v-model="form.summary" placeholder="Scope summary" class="input-field md:col-span-2" />
      </div>
      <button class="btn-primary text-sm px-4 py-2 mt-3" :disabled="busy || !form.title" @click="createRfq">Create RFQ</button>
    </div>

    <div class="admin-panel">
      <table class="admin-table w-full text-sm">
        <thead>
          <tr>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Title</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Trade</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Status</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Created</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="rfq in rfqs" :key="rfq.id" class="border-b">
            <td class="px-4 py-3 font-medium text-gray-900">{{ rfq.title }}</td>
            <td class="px-4 py-3 text-gray-600">{{ rfq.trade }}</td>
            <td class="px-4 py-3"><StatusBadge :status="rfq.status" /></td>
            <td class="px-4 py-3 text-gray-500 whitespace-nowrap">{{ new Date(rfq.created_at).toLocaleDateString() }}</td>
            <td class="px-4 py-3">
              <NuxtLink :to="`/rfqs/${rfq.id}`" class="text-primary-600 hover:underline text-xs">Open</NuxtLink>
            </td>
          </tr>
          <tr v-if="!rfqs.length">
            <td colspan="5" class="px-4 py-8 text-center text-gray-500">No RFQs yet.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { apiFetch } = useApi()
const rfqs = ref<any[]>([])
const statusFilter = ref('')
const busy = ref(false)
const form = ref<any>({ title: '', trade: 'general', lead_id: '', country: '', city: '', summary: '' })

async function load() {
  const params = statusFilter.value ? `?status=${statusFilter.value}` : ''
  try {
    const res = await apiFetch<any>(`/admin/rfqs${params}`)
    rfqs.value = res.items || []
  } catch {
    rfqs.value = []
  }
}

async function createRfq() {
  busy.value = true
  try {
    await apiFetch('/admin/rfqs', {
      method: 'POST',
      body: {
        title: form.value.title,
        trade: form.value.trade,
        lead_id: form.value.lead_id || null,
        scope_json: {
          country: form.value.country || null,
          city: form.value.city || null,
          summary: form.value.summary || null,
        },
      },
    })
    form.value = { title: '', trade: 'general', lead_id: '', country: '', city: '', summary: '' }
    await load()
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>
