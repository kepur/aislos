<template>
  <div class="min-h-screen flex flex-col items-center justify-center px-6">
    <div class="w-full max-w-sm space-y-5">
      <div class="text-center">
        <h1 class="text-xl font-bold text-slate-800">{{ token ? 'Choose a new password' : 'Reset password' }}</h1>
        <p class="mt-2 text-sm text-slate-400">
          {{ token ? 'This one-time link expires after 30 minutes.' : 'We will email a one-time reset link if the account exists.' }}
        </p>
      </div>

      <form v-if="!token" class="space-y-4" @submit.prevent="requestReset">
        <input v-model="email" class="m-input" type="email" required placeholder="you@company.com" />
        <p v-if="message" class="text-sm text-emerald-600">{{ message }}</p>
        <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
        <button class="m-btn-primary" :disabled="loading">{{ loading ? 'Sending...' : 'Send reset link' }}</button>
      </form>

      <form v-else class="space-y-4" @submit.prevent="confirmReset">
        <input v-model="password" class="m-input" type="password" minlength="8" required placeholder="New password" />
        <input v-model="confirmPassword" class="m-input" type="password" minlength="8" required placeholder="Confirm new password" />
        <p v-if="message" class="text-sm text-emerald-600">{{ message }}</p>
        <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
        <button class="m-btn-primary" :disabled="loading">{{ loading ? 'Saving...' : 'Reset password' }}</button>
      </form>

      <NuxtLink to="/auth/login" class="block text-center text-sm font-semibold text-blue-500">Back to login</NuxtLink>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'auth' })
const route = useRoute()
const apiBase = useApiBase()
const token = computed(() => String(route.query.token || ''))
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const message = ref('')
const error = ref('')
const loading = ref(false)

async function requestReset() {
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

async function confirmReset() {
  error.value = ''
  if (password.value !== confirmPassword.value) {
    error.value = 'Passwords do not match.'
    return
  }
  loading.value = true
  try {
    const response = await $fetch<{ message: string }>(`${apiBase}/auth/reset-password`, {
      method: 'POST',
      body: { token: token.value, new_password: password.value },
    })
    message.value = response.message
  } catch (e: any) {
    error.value = e?.data?.detail || 'Unable to reset password.'
  } finally {
    loading.value = false
  }
}
</script>
