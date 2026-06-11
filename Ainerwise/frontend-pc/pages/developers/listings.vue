<template>
  <div class="section-padding">
    <div class="container-main max-w-6xl">
      <div class="mb-8">
        <p class="text-xs font-bold tracking-[0.25em] text-primary-400 uppercase">Developer Console</p>
        <h1 class="mt-2 text-3xl font-bold text-white">Submit an Agent for review</h1>
        <p class="mt-2 text-slate-400">Requested scopes are a review request only. Approval and installation grant no data access.</p>
      </div>
      <div class="grid gap-8 lg:grid-cols-[420px_1fr]">
        <form class="glass-panel p-5 space-y-4" @submit.prevent="submit">
          <input v-model="form.name" required class="input-field" placeholder="Agent name" />
          <input v-model="form.role_title" class="input-field" placeholder="Role title, e.g. KNX Design Specialist" />
          <input v-model="form.version" required class="input-field" placeholder="Version" />
          <textarea v-model="form.description" rows="4" class="input-field" placeholder="What this Agent does"></textarea>
          <input v-model="workflowsText" required class="input-field" placeholder="Workflows, comma separated" />
          <input v-model="scopesText" class="input-field" placeholder="Requested scopes, comma separated" />
          <input v-model.number="form.price_monthly" min="0" type="number" class="input-field" placeholder="Monthly price EUR" />
          <button class="btn-primary w-full" :disabled="submitting">{{ submitting ? 'Submitting...' : 'Submit for human review' }}</button>
          <p v-if="error" class="text-sm text-red-300">{{ error }}</p>
        </form>
        <div>
          <h2 class="text-lg font-semibold text-white mb-4">My listings</h2>
          <div class="space-y-4">
            <article v-for="listing in listings" :key="listing.id" class="glass-panel p-5">
              <div class="flex flex-wrap items-start justify-between gap-3">
                <div><h3 class="font-semibold text-white">{{ listing.name }}</h3><p class="text-xs text-slate-400">v{{ listing.version }} · {{ listing.slug }}</p></div>
                <span class="rounded-full border border-primary-400/30 px-3 py-1 text-xs text-primary-300">{{ listing.status }}</span>
              </div>
              <p v-if="listing.review_notes" class="mt-3 text-sm text-amber-200">Review: {{ listing.review_notes }}</p>
              <p class="mt-3 text-xs text-slate-500">Requested scopes: {{ listing.requested_scopes.join(', ') || 'none' }}</p>
            </article>
            <p v-if="!listings.length" class="glass-panel p-8 text-center text-slate-400">No submitted Agents yet.</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth' })
const { apiFetch } = useApi()
const listings = ref<any[]>([])
const workflowsText = ref('')
const scopesText = ref('')
const submitting = ref(false)
const error = ref('')
const form = reactive<any>({ name: '', role_title: '', version: '1.0.0', description: '', price_monthly: null, currency: 'EUR' })
async function load() {
  const res = await apiFetch<any>('/developer/listings/my')
  listings.value = res.items || []
}
async function submit() {
  submitting.value = true
  error.value = ''
  try {
    await apiFetch('/developer/listings', {
      method: 'POST',
      body: {
        ...form,
        workflows: workflowsText.value.split(',').map((v) => v.trim()).filter(Boolean),
        requested_scopes: scopesText.value.split(',').map((v) => v.trim()).filter(Boolean),
      },
    })
    form.name = ''; form.role_title = ''; form.description = ''; form.price_monthly = null
    workflowsText.value = ''; scopesText.value = ''
    await load()
  } catch (e: any) {
    error.value = e?.data?.detail || 'Submission failed'
  } finally {
    submitting.value = false
  }
}
onMounted(load)
</script>
