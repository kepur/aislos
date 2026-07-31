<template>
  <div class="space-y-4 p-4">
    <h1 class="text-xl font-bold text-slate-800">Buyer profile</h1>
    <form v-if="loaded" class="m-card space-y-3" @submit.prevent="save">
      <input v-model="form.full_name" class="m-input" placeholder="Full name" />
      <input v-model="form.phone" class="m-input" placeholder="Phone" />
      <input v-model="form.company_name" class="m-input" :disabled="!canManageCompany" placeholder="Company name" />
      <input v-model="form.company_city" class="m-input" :disabled="!canManageCompany" placeholder="Company city" />
      <p v-if="!canManageCompany" class="text-xs text-slate-500">Company fields are managed by the customer owner.</p>
      <p v-if="message" class="text-xs text-emerald-600">{{ message }}</p>
      <p v-if="error" class="text-xs text-red-600">{{ error }}</p>
      <button class="m-btn-primary">Save profile</button>
    </form>
    <NuxtLink to="/profile/edit" class="m-card block text-sm font-semibold text-slate-700">Personal profile</NuxtLink>
    <NuxtLink to="/profile/company" class="m-card block text-sm font-semibold text-slate-700">Company profile</NuxtLink>
    <NuxtLink to="/profile/change-password" class="m-card block text-sm font-semibold text-slate-700">Change password</NuxtLink>
    <NuxtLink to="/settings/language" class="m-card block text-sm font-semibold text-slate-700">Language</NuxtLink>
    <NuxtLink to="/settings/notifications" class="m-card block text-sm font-semibold text-slate-700">Notification settings</NuxtLink>
    <NuxtLink to="/buyer/wallet" class="m-card block text-sm font-semibold text-slate-700">Payment ledger</NuxtLink>
    <NuxtLink to="/buyer/projects" class="m-card block text-sm font-semibold text-slate-700">AI procurement projects</NuxtLink>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: ['auth'] })

const api = useCommerce()
const loaded = ref(false)
const canManageCompany = ref(false)
const message = ref('')
const error = ref('')
const form = reactive({ full_name: '', phone: '', company_name: '', company_city: '' })

async function save() {
  try {
    const body = canManageCompany.value
      ? { ...form }
      : { full_name: form.full_name, phone: form.phone }
    await api.updateBuyerAccount(body)
    message.value = 'Profile saved.'
    error.value = ''
  } catch (cause: any) {
    error.value = cause?.data?.detail || cause?.message
  }
}

onMounted(async () => {
  try {
    const data = await api.getBuyerAccount()
    Object.assign(form, {
      full_name: data.user.full_name || '',
      phone: data.user.phone || '',
      company_name: data.company?.name || '',
      company_city: data.company?.city || '',
    })
    canManageCompany.value = data.permissions?.manage_company === true
    loaded.value = true
  } catch (cause: any) {
    error.value = cause?.data?.detail || cause?.message
  }
})
</script>
