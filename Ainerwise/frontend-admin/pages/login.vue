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
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: false })

const { login, isAdmin, clearAuth } = useAuth()
const { mode, portal } = usePortalMode()
const { availableForFrontend, loadAccess, switchAndNavigate } = usePortalManifest()
const form = reactive({ email: '', password: '' })
const error = ref('')
const loading = ref(false)
const preferredPortalByMode: Record<string, string> = {
  aislos: 'admin_executive',
  store: 'admin_commerce',
  marketing: 'marketing_pc',
  agent: 'admin_ai_supervisor',
}

onMounted(async () => {
  if (import.meta.client) {
    document.documentElement.classList.remove('theme-light')
    document.documentElement.classList.add('theme-dark')
    document.documentElement.dataset.adminTheme = 'dark'
    document.documentElement.style.colorScheme = 'dark'
  }
})

onBeforeUnmount(() => {
  if (import.meta.client) {
    const { initTheme } = useAdminTheme()
    initTheme()
  }
})

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await login(form.email, form.password)
    if (!isAdmin.value) {
      clearAuth()
      error.value = 'Access denied: Operations workbench account required'
      return
    }
    const accessLoaded = await loadAccess(true)
    const preferredKey = preferredPortalByMode[mode] || 'admin_executive'
    const preferred = availableForFrontend.value.find(item => item.portal_key === preferredKey)
      || availableForFrontend.value.find(item => item.portal_key === 'admin_executive')
      || availableForFrontend.value[0]
    if (!accessLoaded || !preferred) {
      clearAuth()
      error.value = 'Access denied: no operations workbench has been assigned'
      return
    }
    await switchAndNavigate(preferred.portal_key)
  } catch (e: any) {
    error.value = e?.data?.detail || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>
