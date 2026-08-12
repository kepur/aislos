<template>
  <section class="mx-auto max-w-3xl space-y-5">
    <h1 class="text-2xl font-bold text-white">{{ $t('supSet.title') }}</h1>
    <form v-if="loaded" class="pc-card grid gap-3 md:grid-cols-2" @submit.prevent="save">
      <input v-model="form.full_name" class="input-field" :placeholder="$t('supSet.yourName')" />
      <input v-model="form.phone" class="input-field" :placeholder="$t('supSet.phone')" />
      <input v-model="form.company_name" class="input-field" :disabled="!canManageCompany" required :placeholder="$t('supSet.company')" />
      <input v-model="form.company_website" class="input-field" :disabled="!canManageCompany" :placeholder="$t('supSet.website')" />
      <input v-model="form.company_country" class="input-field" :disabled="!canManageCompany" :placeholder="$t('supSet.country')" />
      <input v-model="form.company_city" class="input-field" :disabled="!canManageCompany" :placeholder="$t('supSet.city')" />
      <textarea v-model="form.company_description" class="input-field md:col-span-2" :disabled="!canManageCompany" :placeholder="$t('supSet.description')" />
      <p v-if="!canManageCompany" class="text-sm text-slate-400 md:col-span-2">
        {{ $t('supSet.ownerNote') }}
      </p>
      <button class="btn-primary md:col-span-2">{{ $t('supSet.saveSettings') }}</button>
      <p v-if="message" class="text-emerald-300 md:col-span-2">{{ message }}</p>
      <p v-if="error" class="text-red-300 md:col-span-2">{{ error }}</p>
    </form>
    <div class="grid gap-3 md:grid-cols-3">
      <NuxtLink :to="localized('/supplier/team')" class="btn-secondary text-center">{{ $t('supNav.team') }}</NuxtLink>
      <NuxtLink :to="localized('/supplier/triggers')" class="btn-secondary text-center">{{ $t('supSet.alertRules') }}</NuxtLink>
      <NuxtLink :to="localized('/forgot-password')" class="btn-secondary text-center">{{ $t('supSet.accountRecovery') }}</NuxtLink>
    </div>
  </section>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()
const { t } = useI18n()
definePageMeta({ layout: 'procurement', middleware: ['auth'] })

const api = useCommerce()
const loaded = ref(false)
const canManageCompany = ref(false)
const message = ref('')
const error = ref('')
const form = reactive({
  full_name: '',
  phone: '',
  company_name: '',
  company_website: '',
  company_country: '',
  company_city: '',
  company_description: '',
})

async function save() {
  try {
    const body = canManageCompany.value
      ? { ...form }
      : { full_name: form.full_name, phone: form.phone }
    await api.updateSupplierAccount(body)
    message.value = t('supSet.saved')
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
      company_website: account.company?.website || '',
      company_country: account.company?.country || '',
      company_city: account.company?.city || '',
      company_description: account.company?.description || '',
    })
    canManageCompany.value = account.permissions?.manage_company === true
    loaded.value = true
  } catch (cause: any) {
    error.value = cause?.data?.detail || cause?.message
  }
})
</script>
