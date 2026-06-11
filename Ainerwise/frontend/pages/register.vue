<template>
  <div class="min-h-[80vh] flex items-center justify-center px-4 py-12">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <h1 class="text-2xl font-bold text-white">{{ $t('auth.register') }}</h1>
        <p class="mt-2 text-slate-400">{{ $t('brand') }}</p>
      </div>

      <form @submit.prevent="handleRegister" class="glass-panel p-8 space-y-4 border-primary-500/30 shadow-[0_0_30px_rgba(14,165,233,0.1)]">
        <div>
          <label class="block text-sm font-medium text-slate-300 mb-1">{{ $t('auth.email') }}</label>
          <input v-model="form.email" type="email" required class="input-field" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-300 mb-1">{{ $t('auth.password') }}</label>
          <input v-model="form.password" type="password" required minlength="6" class="input-field" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-300 mb-1">{{ $t('auth.fullName') }}</label>
          <input v-model="form.full_name" type="text" class="input-field" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-300 mb-1">{{ $t('auth.role') }}</label>
          <select v-model="form.role" class="input-field">
            <option value="buyer" class="bg-slate-900 text-white">{{ $t('auth.buyer') }}</option>
            <option value="vendor" class="bg-slate-900 text-white">{{ $t('auth.vendor') }}</option>
            <option value="service_partner" class="bg-slate-900 text-white">{{ $t('auth.servicePartner') }}</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-300 mb-1">{{ $t('auth.companyName') }}</label>
          <input v-model="form.company_name" type="text" class="input-field" />
        </div>
        <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
        <button type="submit" :disabled="loading" class="btn-primary w-full shadow-[0_0_15px_rgba(14,165,233,0.3)]">
          {{ loading ? $t('common.loading') : $t('auth.register') }}
        </button>
        <p class="text-center text-sm text-slate-400">
          {{ $t('auth.hasAccount') }}
          <NuxtLink to="/login" class="text-primary-400 font-medium hover:underline">{{ $t('auth.login') }}</NuxtLink>
        </p>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'guest' })

const { register, isAdmin } = useAuth()
const form = reactive({
  email: '',
  password: '',
  full_name: '',
  role: 'buyer',
  company_name: '',
})
const error = ref('')
const loading = ref(false)

async function handleRegister() {
  error.value = ''
  loading.value = true
  try {
    await register(form)
    navigateTo(isAdmin.value ? '/admin' : '/portal')
  } catch (e: any) {
    error.value = e?.data?.detail || 'Registration failed'
  } finally {
    loading.value = false
  }
}
</script>
