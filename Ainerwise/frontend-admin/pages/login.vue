<template>
  <div class="admin-login-page min-h-screen flex items-center justify-center px-4">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <div class="login-logo mx-auto mb-4">
          <span class="text-2xl font-black text-white">A</span>
        </div>
        <h1 class="login-title">{{ portal.name }}</h1>
        <p class="login-subtitle">Independent portal · Shared Ainerwise Core</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-card space-y-5">
        <div v-if="demoMode.enabled && demoMode.admin" class="login-demo-box">
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-xs font-bold uppercase tracking-wider text-cyan-300">Demo Mode On</p>
              <p class="mt-1 text-sm text-slate-300">Use Demo Admin to explore {{ portal.name }}.</p>
            </div>
            <span class="login-demo-badge">Admin</span>
          </div>
          <div class="mt-3 space-y-1 text-xs text-slate-300">
            <p>Email: <span class="font-semibold text-white">{{ demoMode.admin.email }}</span></p>
            <p>Password: <span class="font-semibold text-white">{{ demoMode.admin.password }}</span></p>
          </div>
          <button type="button" class="login-btn-secondary mt-3" @click="useDemoAdmin">
            Use Demo Admin
          </button>
        </div>
        <div>
          <label class="login-label">Email</label>
          <input v-model="form.email" type="email" required class="login-input" placeholder="admin@ainerwise.com" />
        </div>
        <div>
          <label class="login-label">Password</label>
          <input v-model="form.password" type="password" required class="login-input" />
        </div>
        <p v-if="error" class="text-sm text-red-400 font-medium">{{ error }}</p>
        <button type="submit" :disabled="loading" class="login-btn-primary">
          {{ loading ? 'Authenticating...' : 'Sign In' }}
        </button>
        <button
          v-if="demoMode.enabled && demoMode.admin"
          type="button"
          :disabled="loading"
          class="login-btn-secondary"
          @click="loginDemoAdmin"
        >
          {{ loading ? 'Authenticating...' : 'Login as Demo Admin' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: false })

const { login, isAdmin, setDemoSession } = useAuth()
const { getDemoMode, defaultDemoMode } = useDemoMode()
const { portal } = usePortalMode()
const form = reactive({ email: '', password: '' })
const demoMode = ref(defaultDemoMode)
const error = ref('')
const loading = ref(false)

onMounted(async () => {
  if (import.meta.client) {
    document.documentElement.classList.remove('theme-light')
  }
  demoMode.value = await getDemoMode(false)
  if (demoMode.value.enabled && demoMode.value.admin && !form.email && !form.password) {
    useDemoAdmin()
  }
})

onBeforeUnmount(() => {
  if (import.meta.client) {
    const { initTheme } = useAdminTheme()
    initTheme()
  }
})

function useDemoAdmin() {
  if (!demoMode.value.admin) return
  form.email = demoMode.value.admin.email
  form.password = demoMode.value.admin.password
}

async function loginDemoAdmin() {
  useDemoAdmin()
  if (!demoMode.value.admin) return
  error.value = ''
  loading.value = true
  try {
    await login(form.email, form.password)
    if (!isAdmin.value) {
      error.value = 'Access denied: Admin account required'
      return
    }
  } catch {
    setDemoSession('super_admin', demoMode.value.admin.email)
  } finally {
    loading.value = false
  }
  navigateTo(portal.home)
}

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await login(form.email, form.password)
    if (!isAdmin.value) {
      error.value = 'Access denied: Admin account required'
      return
    }
    navigateTo(portal.home)
  } catch (e: any) {
    error.value = e?.data?.detail || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>
