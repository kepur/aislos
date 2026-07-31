<template>
  <section class="mx-auto max-w-3xl space-y-5">
    <div><p class="text-xs uppercase tracking-wider text-indigo-400">Buyer account</p><h1 class="mt-1 text-2xl font-bold text-white">Company profile</h1></div>
    <form v-if="loaded" class="pc-card grid gap-4 md:grid-cols-2" @submit.prevent="save">
      <div><label class="mb-1 block text-sm text-slate-400">Company name</label><input v-model="form.company_name" class="input-field" :disabled="!canManageCompany" /></div>
      <div><label class="mb-1 block text-sm text-slate-400">Website</label><input v-model="form.company_website" class="input-field" :disabled="!canManageCompany" /></div>
      <div><label class="mb-1 block text-sm text-slate-400">Country</label><input v-model="form.company_country" class="input-field" :disabled="!canManageCompany" /></div>
      <div><label class="mb-1 block text-sm text-slate-400">City</label><input v-model="form.company_city" class="input-field" :disabled="!canManageCompany" /></div>
      <div class="md:col-span-2"><label class="mb-1 block text-sm text-slate-400">Address</label><input v-model="form.company_address" class="input-field" :disabled="!canManageCompany" /></div>
      <div class="md:col-span-2"><label class="mb-1 block text-sm text-slate-400">Description</label><textarea v-model="form.company_description" rows="4" class="input-field" :disabled="!canManageCompany" /></div>
      <p v-if="!canManageCompany" class="text-sm text-slate-400 md:col-span-2">Only the customer company owner can edit this profile.</p>
      <p v-if="message" class="text-sm text-emerald-300">{{ message }}</p>
      <p v-if="error" class="text-sm text-red-300">{{ error }}</p>
      <button v-if="canManageCompany" class="btn-primary md:col-span-2">Save company profile</button>
    </form>
  </section>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'procurement', middleware: ['auth'], alias: ['/buyer/company-profile'] })

const api = useCommerce()
const loaded = ref(false)
const canManageCompany = ref(false)
const message = ref('')
const error = ref('')
const form = reactive({ company_name: '', company_website: '', company_country: '', company_city: '', company_address: '', company_description: '' })

async function load() {
  const data = await api.getBuyerAccount()
  Object.assign(form, {
    company_name: data.company?.name || '',
    company_website: data.company?.website || '',
    company_country: data.company?.country || '',
    company_city: data.company?.city || '',
    company_address: data.company?.address || '',
    company_description: data.company?.description || '',
  })
  canManageCompany.value = data.permissions?.manage_company === true
  loaded.value = true
}

async function save() {
  try {
    await api.updateBuyerAccount(form)
    message.value = 'Company profile saved.'
    error.value = ''
  } catch (cause: any) {
    error.value = cause?.data?.detail || cause?.message
  }
}

onMounted(async () => {
  try {
    await load()
  } catch (cause: any) {
    error.value = cause?.data?.detail || cause?.message
  }
})
</script>
