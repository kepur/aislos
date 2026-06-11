<template>
  <div class="min-h-[80vh] flex items-center justify-center px-4">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <h1 class="text-2xl font-bold text-white">{{ $t('auth.login') }}</h1>
        <p class="mt-2 text-slate-400">{{ $t('brand') }}</p>
      </div>

      <form @submit.prevent="handleLogin" class="glass-panel p-8 space-y-5 border-primary-500/30 shadow-[0_0_30px_rgba(14,165,233,0.1)]">
        <div v-if="demoMode.enabled" class="border border-emerald-400/30 bg-emerald-400/10 p-4">
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-xs font-bold uppercase tracking-wider text-emerald-300">Demo Mode On</p>
              <p class="mt-1 text-sm text-slate-300">Use the demo customer account to view portal features without registration.</p>
            </div>
            <span class="shrink-0 text-xs font-semibold text-emerald-200 border border-emerald-400/30 px-2 py-1">Customer</span>
          </div>
          <div class="mt-3 grid grid-cols-1 gap-2 text-xs text-slate-300">
            <div><span class="text-slate-500">Email:</span> {{ demoMode.buyer.email }}</div>
            <div><span class="text-slate-500">Password:</span> {{ demoMode.buyer.password }}</div>
          </div>
          <button type="button" class="mt-3 w-full border border-emerald-400/40 px-4 py-2 text-sm font-semibold text-emerald-100 hover:bg-emerald-400/10" @click="useDemoBuyer">
            Use Demo Customer
          </button>
        </div>
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
        <button v-if="demoMode.enabled" type="button" :disabled="loading" class="w-full border border-primary-500/40 text-primary-200 px-6 py-3 rounded-lg font-medium hover:bg-primary-500/10 transition" @click="loginDemoBuyer">
          {{ loading ? $t('common.loading') : 'Login as Demo Customer' }}
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

const { login, isAdmin, setDemoSession } = useAuth()
const { getDemoMode, defaultDemoMode } = useDemoMode()
const { mode, urls } = usePortalMode()
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
  goToPortalHome()
}

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await login(form.email, form.password)
    goToPortalHome()
  } catch (e: any) {
    error.value = e?.data?.detail || 'Login failed'
  } finally {
    loading.value = false
  }
}

function goToPortalHome() {
  if (isAdmin.value) return navigateTo(urls.admin, { external: true })
  if (mode === 'store') return navigateTo('/store/orders')
  if (mode === 'developer') return navigateTo('/developers/listings')
  return navigateTo(urls.customer, { external: true })
}
</script>
