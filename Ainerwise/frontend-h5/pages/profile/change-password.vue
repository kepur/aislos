<template>
  <div class="space-y-4 p-4">
    <h1 class="text-xl font-bold text-slate-800">Change password</h1>
    <form class="m-card space-y-3" @submit.prevent="save">
      <input v-model="form.current_password" class="m-input" type="password" required placeholder="Current password" />
      <input v-model="form.new_password" class="m-input" type="password" minlength="8" required placeholder="New password" />
      <input v-model="confirmPassword" class="m-input" type="password" minlength="8" required placeholder="Confirm new password" />
      <p v-if="message" class="text-xs text-emerald-600">{{ message }}</p>
      <p v-if="error" class="text-xs text-red-600">{{ error }}</p>
      <button class="m-btn-primary" :disabled="saving">{{ saving ? 'Saving...' : 'Change password' }}</button>
    </form>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: ['auth'] })
const { apiFetch } = useApi()
const saving = ref(false)
const confirmPassword = ref('')
const message = ref('')
const error = ref('')
const form = reactive({ current_password: '', new_password: '' })
async function save() {
  error.value = ''
  if (form.new_password !== confirmPassword.value) {
    error.value = 'Passwords do not match.'
    return
  }
  saving.value = true
  try {
    const response = await apiFetch<{ message: string }>('/auth/change-password', { method: 'PUT', body: form })
    message.value = response.message
    form.current_password = ''
    form.new_password = ''
    confirmPassword.value = ''
  } catch (e: any) {
    error.value = e?.data?.detail || 'Unable to change password.'
  } finally {
    saving.value = false
  }
}
</script>
