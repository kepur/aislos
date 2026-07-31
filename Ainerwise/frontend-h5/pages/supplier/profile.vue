<template>
  <div class="space-y-4 p-4">
    <h1 class="text-xl font-bold text-slate-800">Supplier profile</h1>
    <form v-if="loaded" class="m-card space-y-3" @submit.prevent="save">
      <input v-model="form.full_name" class="m-input" placeholder="Your name" />
      <input v-model="form.phone" class="m-input" placeholder="Phone" />
      <input v-model="form.company_name" class="m-input" :disabled="!canManageCompany" required placeholder="Company" />
      <input v-model="form.company_city" class="m-input" :disabled="!canManageCompany" placeholder="City" />
      <input v-model="form.company_website" class="m-input" :disabled="!canManageCompany" placeholder="Website" />
      <p v-if="!canManageCompany" class="text-xs text-slate-500">
        Company profile fields are managed by the supplier owner.
      </p>
      <button class="m-btn-primary">Save profile</button>
      <p v-if="message" class="text-xs text-emerald-600">{{ message }}</p>
      <p v-if="error" class="text-xs text-red-600">{{ error }}</p>
    </form>
    <NuxtLink to="/supplier/team" class="m-card block text-sm font-semibold">Team access</NuxtLink>
    <NuxtLink to="/supplier/triggers" class="m-card block text-sm font-semibold">Matching rules</NuxtLink>
    <NuxtLink to="/settings/notifications" class="m-card block text-sm font-semibold">Notification settings</NuxtLink>
    <NuxtLink to="/profile/change-password" class="m-card block text-sm font-semibold">Change password</NuxtLink>
    <NuxtLink to="/supplier/wallet" class="m-card block text-sm font-semibold">Wallet and payouts</NuxtLink>
    <NuxtLink to="/supplier/ads" class="m-card block text-sm font-semibold">Advertising</NuxtLink>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: ['auth'] })

const api = useCommerce()
const loaded = ref(false)
const canManageCompany = ref(false)
const message = ref('')
const error = ref('')
const form = reactive({ full_name: '', phone: '', company_name: '', company_city: '', company_website: '' })

async function save() {
  try {
    const body = canManageCompany.value
      ? { ...form }
      : { full_name: form.full_name, phone: form.phone }
    await api.updateSupplierAccount(body)
    message.value = 'Profile saved.'
    error.value = ''
  } catch (cause: any) {
    error.value = cause?.data?.detail || cause?.message
  }
}

onMounted(async () => {
  try {
    const account = await api.getSupplierAccount()
    Object.assign(form, {
      full_name: account.user.full_name || '',
      phone: account.user.phone || '',
      company_name: account.company?.name || '',
      company_city: account.company?.city || '',
      company_website: account.company?.website || '',
    })
    canManageCompany.value = account.permissions?.manage_company === true
    loaded.value = true
  } catch (cause: any) {
    error.value = cause?.data?.detail || cause?.message
  }
})
</script>
