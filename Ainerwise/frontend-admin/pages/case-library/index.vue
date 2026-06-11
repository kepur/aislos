<template>
  <div>
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-6">
      <div>
        <h1 class="admin-page-title">Case Library</h1>
        <p class="admin-page-desc">Structured delivered projects. Cases embed into the AI knowledge base; public ones feed the website.</p>
      </div>
    </div>

    <div class="admin-panel p-4 mb-6">
      <h2 class="font-medium text-gray-900 mb-3">New case</h2>
      <div class="grid gap-2 md:grid-cols-4">
        <input v-model="form.title" placeholder="Title" class="input-field md:col-span-2" />
        <select v-model="form.property_type" class="input-field">
          <option v-for="t in ['villa','apartment','office','hotel','factory','retail','other']" :key="t" :value="t">{{ t }}</option>
        </select>
        <input v-model.number="form.area_sqm" type="number" placeholder="Area m²" class="input-field" />
        <input v-model="form.country" placeholder="Country" class="input-field" />
        <input v-model="form.city" placeholder="City" class="input-field" />
        <input v-model.number="form.budget" type="number" placeholder="Budget €" class="input-field" />
        <input v-model.number="form.duration_days" type="number" placeholder="Duration days" class="input-field" />
        <textarea v-model="form.summary" rows="2" placeholder="Summary (embedded into knowledge base)" class="input-field md:col-span-4"></textarea>
        <textarea v-model="form.customer_feedback" rows="2" placeholder="Customer feedback" class="input-field md:col-span-4"></textarea>
      </div>
      <button class="btn-primary text-sm px-4 py-2 mt-3" :disabled="busy || !form.title" @click="create">Create & embed</button>
    </div>

    <div class="admin-panel">
      <table class="admin-table w-full text-sm">
        <thead>
          <tr>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Title</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Type / area</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Location</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Budget</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Public</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in cases" :key="c.id" class="border-b">
            <td class="px-4 py-3 font-medium text-gray-900">{{ c.title }}</td>
            <td class="px-4 py-3 text-gray-600">{{ c.property_type }} · {{ c.area_sqm ?? '?' }} m²</td>
            <td class="px-4 py-3 text-gray-600">{{ [c.city, c.country].filter(Boolean).join(', ') || '-' }}</td>
            <td class="px-4 py-3 text-gray-600">{{ c.budget ? `${c.budget} ${c.currency}` : '-' }}</td>
            <td class="px-4 py-3">
              <button
                class="text-xs px-2 py-1 rounded"
                :class="c.public_visible ? 'bg-emerald-50 text-emerald-700' : 'bg-gray-100 text-gray-500'"
                :disabled="busy"
                @click="togglePublic(c)"
              >{{ c.public_visible ? 'visible' : 'hidden' }}</button>
            </td>
            <td class="px-4 py-3">
              <button class="text-xs px-3 py-1.5 rounded border border-red-300 text-red-600 hover:bg-red-50" :disabled="busy" @click="remove(c)">Delete</button>
            </td>
          </tr>
          <tr v-if="!cases.length">
            <td colspan="6" class="px-4 py-8 text-center text-gray-500">No cases yet — every delivered project should become one.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { apiFetch } = useApi()
const cases = ref<any[]>([])
const busy = ref(false)
const blank = { title: '', property_type: 'villa', area_sqm: null, country: '', city: '', budget: null, duration_days: null, summary: '', customer_feedback: '' }
const form = ref<any>({ ...blank })

async function load() {
  const res = await apiFetch<any>('/admin/cases')
  cases.value = res.items || []
}

async function create() {
  busy.value = true
  try {
    await apiFetch('/admin/cases', { method: 'POST', body: form.value })
    form.value = { ...blank }
    await load()
  } finally {
    busy.value = false
  }
}

async function togglePublic(c: any) {
  busy.value = true
  try {
    await apiFetch(`/admin/cases/${c.id}`, { method: 'PATCH', body: { title: c.title, public_visible: !c.public_visible } })
    await load()
  } finally {
    busy.value = false
  }
}

async function remove(c: any) {
  if (!window.confirm(`Delete case "${c.title}"?`)) return
  busy.value = true
  try {
    await apiFetch(`/admin/cases/${c.id}`, { method: 'DELETE' })
    await load()
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>
