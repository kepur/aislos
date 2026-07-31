<template>
  <div class="space-y-4 p-4">
    <h1 class="text-xl font-bold text-slate-800">Edit profile</h1>
    <form v-if="loaded" class="m-card space-y-3" @submit.prevent="save">
      <input v-model="form.full_name" class="m-input" required placeholder="Full name" />
      <input :value="account?.user?.email" class="m-input bg-slate-50 text-slate-400" disabled />
      <input v-model="form.phone" class="m-input" placeholder="Phone" />
      <input v-model="form.country" class="m-input" placeholder="Country" />
      <p v-if="message" class="text-xs text-emerald-600">{{ message }}</p>
      <p v-if="error" class="text-xs text-red-600">{{ error }}</p>
      <button class="m-btn-primary" :disabled="saving">{{ saving ? 'Saving...' : 'Save changes' }}</button>
    </form>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: ['auth'] })
const api = useCommerce()
const account = ref<any>(null)
const loaded = ref(false)
const saving = ref(false)
const message = ref('')
const error = ref('')
const form = reactive({ full_name: '', phone: '', country: '' })
async function save() {
  saving.value = true
  error.value = ''
  try {
    account.value = await api.updateBuyerAccount(form)
    message.value = 'Profile saved.'
  } catch (e: any) {
    error.value = e?.data?.detail || 'Unable to save profile.'
  } finally {
    saving.value = false
  }
}
onMounted(async () => {
  try {
    account.value = await api.getBuyerAccount()
    Object.assign(form, {
      full_name: account.value.user.full_name || '',
      phone: account.value.user.phone || '',
      country: account.value.user.country || '',
    })
    loaded.value = true
  } catch (e: any) {
    error.value = e?.data?.detail || 'Unable to load profile.'
  }
})
</script>
