<template>
  <div class="min-h-[80vh] bg-slate-950 text-white">
    <div class="container-main px-4 sm:px-6 lg:px-8 py-14">
      <div class="grid grid-cols-1 lg:grid-cols-[0.95fr_1.05fr] gap-10 items-center">
        <div>
          <p class="text-sm font-semibold uppercase tracking-wider text-emerald-300">Demo Customer Access</p>
          <h1 class="mt-4 text-4xl sm:text-5xl font-bold leading-tight text-white">Try AinerWise as a smart building customer</h1>
          <p class="mt-5 text-slate-300 text-lg">
            Use the prefilled demo account to explore customer workflows for AI assessment,
            preliminary proposals, quotes, tickets, and future BOM planning. Demo data is
            for product exploration only and cannot create real payments or contracts.
          </p>
          <div class="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div v-for="project in demoProjects" :key="project" class="pc-feature-card text-sm text-slate-200">
              {{ project }}
            </div>
          </div>
        </div>

        <form class="glass-panel p-8 space-y-5 border-primary-500/30" @submit.prevent="handleDemoLogin">
          <h2 class="text-2xl font-bold text-white">Login as Demo Customer</h2>
          <p class="text-sm text-slate-400">
            The credentials are intentionally visible for demo review. Signing in
            switches the current browser session to the Demo Customer account.
          </p>

          <div class="space-y-5">
            <div>
              <label class="block text-sm font-medium text-slate-300 mb-1">Email</label>
              <input v-model="form.email" type="email" class="input-field" autocomplete="username" />
            </div>
            <div>
              <label class="block text-sm font-medium text-slate-300 mb-1">Password</label>
              <input v-model="form.password" type="password" class="input-field" autocomplete="current-password" />
            </div>
          </div>

          <div class="pc-notice-amber">
            AI estimates in demo projects are not final quotes. Final quote requires manual review,
            site survey, supplier confirmation, and signed contract.
          </div>

          <p v-if="error" class="text-sm text-red-400">{{ error }}</p>

          <button type="submit" class="btn-primary w-full" :disabled="loading">
            {{ loading ? 'Logging in...' : 'Login as Demo Customer' }}
          </button>

          <p class="text-xs text-slate-500">
            You will continue in the independent Customer Project Portal.
          </p>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { login } = useAuth()
const { getDemoMode, defaultDemoMode } = useDemoMode()
const { urls } = usePortalMode()
const loading = ref(false)
const error = ref('')
const form = reactive({
  email: defaultDemoMode.buyer.email,
  password: defaultDemoMode.buyer.password,
})

const demoProjects = [
  'Future Smart Villa',
  'AI School Campus',
  'Smart Apartment Building',
  'Enterprise Office AI Brain',
  'Solar + Storage Energy Site',
  'Smart Hotel Room Control',
]

onMounted(async () => {
  const demoMode = await getDemoMode()
  if (!demoMode.enabled) {
    error.value = 'Demo mode is currently disabled.'
    return
  }
  form.email = demoMode.buyer.email
  form.password = demoMode.buyer.password
})

async function handleDemoLogin() {
  loading.value = true
  error.value = ''
  try {
    await login(form.email, form.password)
    await navigateTo(`${urls.customer}/dashboard`, { external: true })
  } catch (e: any) {
    error.value = e?.data?.detail || 'Demo login failed. Create demo data first.'
  } finally {
    loading.value = false
  }
}
</script>
