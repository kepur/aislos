<template>
  <div class="min-h-[80vh] bg-slate-950 text-white">
    <div class="container-main px-4 sm:px-6 lg:px-8 py-14">
      <div class="grid grid-cols-1 lg:grid-cols-[0.95fr_1.05fr] gap-10 items-center">
        <div>
          <p class="text-sm font-semibold uppercase tracking-wider text-emerald-300">{{ $t('authP.demoAccess') }}</p>
          <h1 class="mt-4 text-4xl sm:text-5xl font-bold leading-tight text-white">{{ $t('authP.tryTitle') }}</h1>
          <p class="mt-5 text-slate-300 text-lg">{{ $t('authP.tryDesc') }}</p>
          <div class="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div v-for="project in demoProjects" :key="project" class="pc-feature-card text-sm text-slate-200">
              {{ $t(project) }}
            </div>
          </div>
        </div>

        <form class="glass-panel p-8 space-y-5 border-primary-500/30" @submit.prevent="handleDemoLogin">
          <h2 class="text-2xl font-bold text-white">{{ $t('auth.demo.loginAs') }}</h2>
          <p class="text-sm text-slate-400">{{ $t('authP.credsVisible') }}</p>

          <div class="space-y-5">
            <div>
              <label class="block text-sm font-medium text-slate-300 mb-1">{{ $t('auth.email') }}</label>
              <input v-model="form.email" type="email" class="input-field" autocomplete="username" />
            </div>
            <div>
              <label class="block text-sm font-medium text-slate-300 mb-1">{{ $t('auth.password') }}</label>
              <input v-model="form.password" type="password" class="input-field" autocomplete="current-password" />
            </div>
          </div>

          <div class="pc-notice-amber">{{ $t('authP.aiEstimate') }}</div>

          <p v-if="error" class="text-sm text-red-400">{{ error }}</p>

          <button type="submit" class="btn-primary w-full" :disabled="loading">
            {{ loading ? $t('authP.loggingIn') : $t('auth.demo.loginAs') }}
          </button>

          <p class="text-xs text-slate-500">{{ $t('authP.continuePortal') }}</p>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { t } = useI18n()
const { login } = useAuth()
const { getDemoMode, defaultDemoMode } = useDemoMode()
const loading = ref(false)
const error = ref('')
const form = reactive({
  email: '',
  password: '',
})

const demoProjects = ['authP.projVilla','authP.projSchool','authP.projApartment','authP.projOffice','authP.projSolar','authP.projHotel']

onMounted(async () => {
  const demoMode = await getDemoMode()
  if (!demoMode.enabled || !demoMode.buyer) {
    error.value = t('authP.demoDisabled')
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
    await navigateTo('/portal')
  } catch (e: any) {
    error.value = e?.data?.detail || t('authP.demoFailed')
  } finally {
    loading.value = false
  }
}
</script>
