<template>
  <div>
    <NuxtLink to="/admin/projects" class="text-sm text-primary-600 hover:underline">&larr; Back to Projects</NuxtLink>
    <h1 class="mt-4 text-2xl font-bold text-gray-900 mb-6">Create Project</h1>

    <form class="max-w-2xl space-y-6" @submit.prevent="submit">
      <div class="bg-white rounded-xl border p-6 space-y-4">
        <h2 class="font-semibold text-gray-900">Basic Information</h2>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Title *</label>
          <input v-model="form.title" type="text" class="input-field" placeholder="e.g. Smart Hotel Belgrade Phase 1" required />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Region</label>
            <input v-model="form.region" type="text" class="input-field" placeholder="e.g. Serbia" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Lead ID (optional)</label>
            <input v-model="form.lead_id" type="text" class="input-field" placeholder="UUID of linked lead" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
            <input v-model="form.start_date" type="date" class="input-field" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Expected Delivery</label>
            <input v-model="form.expected_delivery_date" type="date" class="input-field" />
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Buyer Company ID (optional)</label>
          <input v-model="form.buyer_company_id" type="text" class="input-field" placeholder="UUID of buyer company" />
        </div>
      </div>

      <div class="bg-white rounded-xl border p-6 space-y-4">
        <h2 class="font-semibold text-gray-900">Notes</h2>
        <textarea v-model="form.notes" rows="4" class="input-field" placeholder="Initial project notes..." />
      </div>

      <div class="flex justify-end gap-3">
        <NuxtLink to="/admin/projects" class="px-4 py-2 text-sm border rounded-lg text-gray-600 hover:bg-gray-50">
          Cancel
        </NuxtLink>
        <button
          type="submit"
          class="px-6 py-2 text-sm font-medium bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-60"
          :disabled="saving"
        >
          {{ saving ? 'Creating...' : 'Create Project' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'admin' })

const router = useRouter()
const { apiFetch } = useApi()
const saving = ref(false)
const form = reactive({
  title: '',
  region: '',
  lead_id: '',
  buyer_company_id: '',
  start_date: '',
  expected_delivery_date: '',
  notes: '',
})

async function submit() {
  saving.value = true
  try {
    const body: any = { title: form.title }
    if (form.region) body.region = form.region
    if (form.lead_id) body.lead_id = form.lead_id
    if (form.buyer_company_id) body.buyer_company_id = form.buyer_company_id
    if (form.start_date) body.start_date = form.start_date
    if (form.expected_delivery_date) body.expected_delivery_date = form.expected_delivery_date
    if (form.notes) body.notes = form.notes

    const project = await apiFetch<any>('/projects', { method: 'POST', body })
    router.push(`/admin/projects/${project.id}`)
  } catch (e: any) {
    console.error('Create project failed:', e)
    alert('Failed to create project. Check console for details.')
  } finally {
    saving.value = false
  }
}
</script>
