<template>
  <div class="min-h-screen flex flex-col items-center justify-center px-6">
    <!-- Back -->
    <NuxtLink to="/" class="self-start mb-6 inline-flex items-center gap-1 text-sm text-slate-400">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
      </svg>
      Back
    </NuxtLink>

    <div class="w-full max-w-sm">
      <!-- Logo -->
      <div class="text-center mb-8">
        <div class="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-xl shadow-blue-500/20 mb-4">
          <span class="text-2xl font-black text-white">A</span>
        </div>
        <h1 class="text-xl font-bold text-slate-800">{{ $t('auth.login') }}</h1>
        <p class="text-sm text-slate-400 mt-1">{{ portal.name }}</p>
      </div>

      <!-- Form -->
      <form @submit.prevent="handleLogin" class="space-y-4">
        <div v-if="demoMode.enabled" class="rounded-2xl border border-blue-100 bg-blue-50 p-4">
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-[10px] font-bold uppercase tracking-wider text-blue-500">Demo Mode On</p>
              <p class="mt-1 text-xs text-slate-500">Demo Customer is prefilled so visitors can explore all customer features.</p>
            </div>
            <span class="shrink-0 rounded-full bg-white px-2 py-1 text-[10px] font-bold text-blue-500">Customer</span>
          </div>
          <div class="mt-3 text-[11px] text-slate-500 space-y-1">
            <p>Email: <span class="font-semibold text-slate-700">{{ demoMode.buyer.email }}</span></p>
            <p>Password: <span class="font-semibold text-slate-700">{{ demoMode.buyer.password }}</span></p>
          </div>
          <button type="button" class="mt-3 w-full text-xs font-semibold text-blue-600 bg-white border border-blue-100 py-2.5 rounded-xl" @click="useDemoBuyer">
            Use Demo Customer
          </button>
        </div>
        <div>
          <label class="block text-xs font-semibold text-slate-500 mb-1.5">{{ $t('auth.email') }}</label>
          <input v-model="form.email" type="email" required
            class="w-full text-sm border border-slate-200 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-300 bg-white"
            placeholder="you@company.com" />
        </div>
        <div>
          <label class="block text-xs font-semibold text-slate-500 mb-1.5">{{ $t('auth.password') }}</label>
          <input v-model="form.password" type="password" required
            class="w-full text-sm border border-slate-200 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-300 bg-white" />
        </div>
        <p v-if="error" class="text-sm text-red-500 font-medium">{{ error }}</p>
        <button type="submit" :disabled="loading"
          class="w-full text-sm font-semibold text-white bg-gradient-to-r from-blue-500 to-indigo-500 py-3 rounded-xl shadow-md shadow-blue-500/20 disabled:opacity-50">
          {{ loading ? 'Logging in...' : $t('auth.login') }}
        </button>
        <button v-if="demoMode.enabled" type="button" :disabled="loading"
          class="w-full text-sm font-semibold text-blue-600 bg-white border border-blue-100 py-3 rounded-xl disabled:opacity-50"
          @click="loginDemoBuyer">
          {{ loading ? 'Logging in...' : 'Login as Demo Customer' }}
        </button>
      </form>

      <div class="mt-6 text-center">
        <p class="text-sm text-slate-400">
          Don't have an account?
          <NuxtLink to="/register" class="text-blue-500 font-semibold">Register</NuxtLink>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'auth', middleware: 'guest' })

const route = useRoute()
const { login, setDemoSession, user } = useAuth()
const { getDemoMode, defaultDemoMode } = useDemoMode()
const { mode, portal } = usePortalMode()
const form = reactive({ email: '', password: '' })
const demoMode = ref(defaultDemoMode)
const error = ref('')
const loading = ref(false)

onMounted(async () => {
  demoMode.value = await getDemoMode()
  if (demoMode.value.enabled && !form.email && !form.password) {
    useDemoBuyer()
  }
})

function useDemoBuyer() {
  form.email = demoMode.value.buyer.email
  form.password = demoMode.value.buyer.password
}

async function loginDemoBuyer() {
  useDemoBuyer()
  error.value = ''
  loading.value = true
  try {
    await login(form.email, form.password)
  } catch {
    setDemoSession('buyer', demoMode.value.buyer.email)
  } finally {
    loading.value = false
  }
  const redirect = route.query.redirect as string
  navigateTo(redirect || portal.home)
}

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await login(form.email, form.password)
    const redirect = route.query.redirect as string
    navigateTo(redirect || (mode === 'partner' ? '/partner' : '/'))
  } catch (e: any) {
    error.value = e?.data?.detail || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>
