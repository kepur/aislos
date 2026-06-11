<template>
  <div class="min-h-[80vh] flex items-center justify-center bg-slate-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 space-y-8">
      <div>
        <h2 class="text-center text-3xl font-extrabold text-slate-900 tracking-tight">
          Welcome back to {{ $config.public.appName }}
        </h2>
        <p class="mt-2 text-center text-sm text-slate-600">
          Or
          <NuxtLink to="/register-role" class="font-medium text-indigo-600 hover:text-indigo-500 transition-colors">
            create a new account
          </NuxtLink>
        </p>
      </div>
      
      <form class="mt-8 space-y-6" @submit.prevent="handleLogin">
        <div v-if="authStore.isDemoMode" class="rounded-xl border border-amber-200 bg-amber-50 p-4">
          <div class="mb-3 flex items-center justify-between gap-3">
            <div>
              <p class="text-sm font-semibold text-amber-900">Demo Mode</p>
              <p class="text-xs text-amber-700">Use one of these accounts to preview buyer or supplier workflows.</p>
            </div>
            <UBadge color="amber" variant="subtle">Enabled</UBadge>
          </div>
          <div class="grid gap-2">
            <button
              v-for="acc in demoAccounts"
              :key="acc.email"
              type="button"
              class="flex items-center justify-between gap-3 rounded-lg border border-amber-100 bg-white px-3 py-2.5 text-left text-sm transition hover:bg-amber-50"
              @click="fillDemo(acc)"
            >
              <span>
                <span class="block font-semibold text-slate-800">{{ acc.label }}</span>
                <span class="block font-mono text-xs text-slate-500">{{ acc.email }}</span>
              </span>
              <span class="rounded-md bg-slate-100 px-2 py-1 font-mono text-xs text-slate-600">{{ acc.password }}</span>
            </button>
          </div>
          <p class="mt-2 text-xs text-amber-700">Click an account to fill email and password.</p>
        </div>

        <div class="space-y-4">
          <!-- Email / Phone -->
          <div class="space-y-1">
            <label class="block text-sm font-medium text-slate-700">Email or Phone Number</label>
            <div class="relative">
              <span class="absolute inset-y-0 left-3 flex items-center pointer-events-none">
                <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </span>
              <input
                v-model="form.identifier"
                type="text"
                placeholder="Enter email or phone"
                autocomplete="username"
                class="w-full rounded-lg border border-slate-200 bg-white pl-9 pr-4 py-3 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200"
              />
            </div>
          </div>

          <!-- Password -->
          <div class="space-y-1">
            <label class="block text-sm font-medium text-slate-700">Password</label>
            <div class="relative">
              <span class="absolute inset-y-0 left-3 flex items-center pointer-events-none">
                <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </span>
              <input
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="Enter your password"
                autocomplete="current-password"
                class="w-full rounded-lg border border-slate-200 bg-white pl-9 pr-10 py-3 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200"
              />
              <!-- Toggle show/hide password -->
              <button type="button" @click="showPassword = !showPassword"
                class="absolute inset-y-0 right-3 flex items-center text-slate-400 hover:text-slate-600">
                <svg v-if="!showPassword" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        <div class="flex items-center justify-between">
          <label class="flex items-center gap-2 cursor-pointer select-none">
            <input
              v-model="form.rememberMe"
              type="checkbox"
              class="w-4 h-4 rounded border-slate-300 text-indigo-600 accent-indigo-600 cursor-pointer"
            />
            <span class="text-sm text-slate-700">Remember me</span>
          </label>

          <NuxtLink to="/forgot-password" class="text-sm font-medium text-indigo-600 hover:text-indigo-500">
            Forgot your password?
          </NuxtLink>
        </div>

        <div>
          <UButton type="submit" color="indigo" block size="xl" class="w-full justify-center font-semibold shadow-md">
            {{ loading ? 'Signing in...' : 'Sign in' }}
          </UButton>
          <p v-if="error" class="text-sm text-red-600 text-center mt-3">{{ error }}</p>
        </div>
      </form>

      <div class="mt-6">
        <div class="relative">
          <div class="absolute inset-0 flex items-center">
            <div class="w-full border-t border-slate-200"></div>
          </div>
          <div class="relative flex justify-center text-sm">
            <span class="px-2 bg-white text-slate-500">
              Or continue with
            </span>
          </div>
        </div>

        <div class="mt-6 grid grid-cols-1 gap-3">
          <UButton color="white" variant="solid" block size="lg" class="border border-slate-200 text-slate-700 hover:bg-slate-50">
            <template #leading>
              <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
              </svg>
            </template>
            Sign in with Google
          </UButton>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

definePageMeta({
  middleware: 'guest'
})

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const form = ref({
  identifier: '',
  password: '',
  rememberMe: false
})
const loading = ref(false)
const error = ref('')
const showPassword = ref(false)
const demoAccounts = [
  { label: 'Demo Buyer', email: 'buyer@demo.procureping', password: '123' },
  { label: 'Demo Supplier', email: 'supplier@demo.procureping', password: '123' },
]

function fillDemo(acc: { email: string; password: string }) {
  form.value.identifier = acc.email
  form.value.password = acc.password
}

onMounted(async () => {
  await authStore.fetchSystemMode()
})

const handleLogin = async () => {
  if (loading.value) return
  loading.value = true
  error.value = ''
  try {
    await authStore.login(form.value.identifier, form.value.password)
    
    // Check for return_url param first
    const returnUrl = typeof route.query.return_url === 'string' ? route.query.return_url : ''
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : ''
    
    if (returnUrl) {
      return navigateTo(returnUrl)
    }

    // If redirecting to a page that doesn't match the role, force dashboard
    if (redirect && redirect !== '/') {
      const isSupplierPath = redirect.startsWith('/supplier') || redirect === '/register-supplier'
      const isBuyerPath = redirect.startsWith('/buyer') || redirect === '/register-buyer'
      
      if (authStore.isBuyer && isSupplierPath) return navigateTo('/buyer/dashboard')
      if (authStore.isSupplier && isBuyerPath) return navigateTo('/supplier/dashboard')
      
      return navigateTo(redirect)
    }

    if (authStore.isSupplier) return navigateTo('/supplier/dashboard')
    if (authStore.isAdmin) return navigateTo('/admin/dashboard')
    return navigateTo('/buyer/dashboard')
  } catch (e: any) {
    error.value = e?.data?.detail || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>
