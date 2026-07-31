<template>
  <div class="space-y-4 p-4">
    <h1 class="text-xl font-bold text-slate-800">Company profile</h1>
    <form v-if="loaded" class="m-card space-y-3" @submit.prevent="save">
      <input v-model="form.company_name" class="m-input" required placeholder="Company name" />
      <input v-model="form.company_country" class="m-input" placeholder="Country" />
      <input v-model="form.company_city" class="m-input" placeholder="City" />
      <input v-model="form.company_address" class="m-input" placeholder="Business address" />
      <input v-model="form.company_website" class="m-input" placeholder="Website" />
      <textarea v-model="form.company_description" class="m-input min-h-24" placeholder="Company description" />
      <p v-if="message" class="text-xs text-emerald-600">{{ message }}</p>
      <p v-if="error" class="text-xs text-red-600">{{ error }}</p>
      <button class="m-btn-primary" :disabled="saving">{{ saving ? 'Saving...' : 'Save company profile' }}</button>
    </form>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: ['auth'] })
const api = useCommerce()
const loaded = ref(false)
const saving = ref(false)
const message = ref('')
const error = ref('')
const form = reactive({
  company_name: '',
  company_country: '',
  company_city: '',
  company_address: '',
  company_website: '',
  company_description: '',
})
async function save() {
  saving.value = true
  error.value = ''
  try {
    await api.updateBuyerAccount(form)
    message.value = 'Company profile saved.'
  } catch (e: any) {
    error.value = e?.data?.detail || 'Unable to save company profile.'
  } finally {
    saving.value = false
  }
}
onMounted(async () => {
  try {
    const data = await api.getBuyerAccount()
    Object.assign(form, {
      company_name: data.company?.name || '',
      company_country: data.company?.country || '',
      company_city: data.company?.city || '',
      company_address: data.company?.address || '',
      company_website: data.company?.website || '',
      company_description: data.company?.description || '',
    })
    loaded.value = true
  } catch (e: any) {
    error.value = e?.data?.detail || 'Unable to load company profile.'
  }
})
</script>
