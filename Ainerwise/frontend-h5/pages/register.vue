<template>
  <div class="min-h-screen flex flex-col items-center justify-center px-6">
    <NuxtLink to="/" class="self-start mb-6 inline-flex items-center gap-1 text-sm text-slate-400">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
      </svg>
      Back
    </NuxtLink>

    <div class="w-full max-w-sm">
      <div class="text-center mb-8">
        <div class="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-xl shadow-blue-500/20 mb-4">
          <span class="text-2xl font-black text-white">A</span>
        </div>
        <h1 class="text-xl font-bold text-slate-800">Create Account</h1>
        <p class="text-sm text-slate-400 mt-1">Join AinerWise Smart Building Platform</p>
      </div>

      <form @submit.prevent="handleRegister" class="space-y-4">
        <div>
          <label class="block text-xs font-semibold text-slate-500 mb-1.5">Full Name</label>
          <input v-model="form.full_name" type="text" required
            class="w-full text-sm border border-slate-200 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-300 bg-white" />
        </div>
        <div>
          <label class="block text-xs font-semibold text-slate-500 mb-1.5">{{ $t('auth.email') }}</label>
          <input v-model="form.email" type="email" required
            class="w-full text-sm border border-slate-200 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-300 bg-white"
            placeholder="you@company.com" />
        </div>
        <div>
          <label class="block text-xs font-semibold text-slate-500 mb-1.5">{{ $t('auth.password') }}</label>
          <input v-model="form.password" type="password" required minlength="8"
            class="w-full text-sm border border-slate-200 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-300 bg-white" />
        </div>
        <div>
          <label class="block text-xs font-semibold text-slate-500 mb-1.5">Company (optional)</label>
          <input v-model="form.company_name" type="text"
            class="w-full text-sm border border-slate-200 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-300 bg-white" />
        </div>
        <div>
          <label class="block text-xs font-semibold text-slate-500 mb-1.5">{{ $t('auth.role') }}</label>
          <select v-model="form.role"
            class="w-full text-sm border border-slate-200 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-300 bg-white">
            <option value="buyer">{{ $t('auth.buyer') }}</option>
            <option value="service_partner">{{ $t('auth.servicePartner') }}</option>
          </select>
          <p v-if="form.role === 'service_partner'" class="mt-1.5 text-[11px] leading-relaxed text-slate-400">
            {{ $t('partner.registrationNote') }}
          </p>
        </div>
        <p v-if="error" class="text-sm text-red-500 font-medium">{{ error }}</p>
        <button type="submit" :disabled="loading"
          class="w-full text-sm font-semibold text-white bg-gradient-to-r from-blue-500 to-indigo-500 py-3 rounded-xl shadow-md shadow-blue-500/20 disabled:opacity-50">
          {{ loading ? 'Creating...' : 'Create Account' }}
        </button>
      </form>

      <div class="mt-6 text-center">
        <p class="text-sm text-slate-400">
          Already have an account?
          <NuxtLink to="/login" class="text-blue-500 font-semibold">Login</NuxtLink>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'auth', middleware: 'guest' })

const { register, user } = useAuth()
const form = reactive({ full_name: '', email: '', password: '', company_name: '', role: 'buyer' })
const error = ref('')
const loading = ref(false)

async function handleRegister() {
  error.value = ''
  loading.value = true
  try {
    await register(form)
    navigateTo(user.value?.role === 'service_partner' ? '/partner' : '/')
  } catch (e: any) {
    error.value = e?.data?.detail || 'Registration failed'
  } finally {
    loading.value = false
  }
}
</script>
