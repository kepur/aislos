<template>
  <section class="container-main section-padding">
    <form class="pc-card mx-auto max-w-md space-y-4" @submit.prevent="submit">
      <p class="pc-kicker">{{ $t('authP.recovery') }}</p>
      <h1 class="text-2xl font-bold text-white">{{ $t('authP.resetTitle') }}</h1>
      <p class="text-sm text-slate-400">{{ $t('authP.resetDesc') }}</p>
      <input v-model="email" class="input-field" type="email" required :placeholder="$t('authP.emailPh')" />
      <p v-if="message" class="text-sm text-emerald-300">{{ message }}</p>
      <p v-if="error" class="text-sm text-red-300">{{ error }}</p>
      <button class="btn-primary w-full" :disabled="loading">{{ loading ? $t('authP.sending') : $t('authP.sendLink') }}</button>
    </form>
  </section>
</template>

<script setup lang="ts">
const { t } = useI18n()
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
    error.value = e?.data?.detail || t('authP.resetFailed')
  } finally {
    loading.value = false
  }
}
</script>
