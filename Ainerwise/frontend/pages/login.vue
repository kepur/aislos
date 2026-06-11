<template>
  <div class="min-h-[80vh] flex items-center justify-center px-4">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <h1 class="text-2xl font-bold text-white">{{ $t('auth.login') }}</h1>
        <p class="mt-2 text-slate-400">{{ $t('brand') }}</p>
      </div>

      <form @submit.prevent="handleLogin" class="glass-panel p-8 space-y-5 border-primary-500/30 shadow-[0_0_30px_rgba(14,165,233,0.1)]">
        <div>
          <label class="block text-sm font-medium text-slate-300 mb-1">{{ $t('auth.email') }}</label>
          <input v-model="form.email" type="email" required class="input-field" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-300 mb-1">{{ $t('auth.password') }}</label>
          <input v-model="form.password" type="password" required class="input-field" />
        </div>
        <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
        <button type="submit" :disabled="loading" class="btn-primary w-full shadow-[0_0_15px_rgba(14,165,233,0.3)]">
          {{ loading ? $t('common.loading') : $t('auth.login') }}
        </button>
        <p class="text-center text-sm text-slate-400">
          {{ $t('auth.noAccount') }}
          <NuxtLink to="/register" class="text-primary-400 font-medium hover:underline">{{ $t('auth.register') }}</NuxtLink>
        </p>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'guest' })

const { login, isAdmin } = useAuth()
const form = reactive({ email: '', password: '' })
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await login(form.email, form.password)
    navigateTo(isAdmin.value ? '/admin' : '/portal')
  } catch (e: any) {
    error.value = e?.data?.detail || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>
