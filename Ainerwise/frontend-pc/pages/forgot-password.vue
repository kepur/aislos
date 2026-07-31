<template>
  <section class="container-main section-padding">
    <form class="pc-card mx-auto max-w-md space-y-4" @submit.prevent="submit">
      <p class="pc-kicker">Account recovery</p>
      <h1 class="text-2xl font-bold text-white">Reset password</h1>
      <p class="text-sm text-slate-400">We will email a one-time reset link if the account exists.</p>
      <input v-model="email" class="input-field" type="email" required placeholder="you@company.com" />
      <p v-if="message" class="text-sm text-emerald-300">{{ message }}</p>
      <p v-if="error" class="text-sm text-red-300">{{ error }}</p>
      <button class="btn-primary w-full" :disabled="loading">{{ loading ? 'Sending...' : 'Send reset link' }}</button>
    </form>
  </section>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'guest' })
const apiBase = useApiBase()
const email = ref('')
const message = ref('')
const error = ref('')
const loading = ref(false)
async function submit() {
  loading.value = true
  error.value = ''
  try {
    const response = await $fetch<{ message: string }>(`${apiBase}/auth/request-password-reset`, {
      method: 'POST',
      body: { email: email.value },
    })
    message.value = response.message
  } catch (e: any) {
    error.value = e?.data?.detail || 'Unable to request password reset.'
  } finally {
    loading.value = false
  }
}
</script>
