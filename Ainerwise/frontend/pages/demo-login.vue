<template>
  <div class="min-h-[80vh] bg-slate-950 text-white">
    <div class="container-main px-4 sm:px-6 lg:px-8 py-14">
      <div class="grid grid-cols-1 lg:grid-cols-[0.95fr_1.05fr] gap-10 items-center">
        <div>
          <p class="text-sm font-semibold uppercase tracking-wider text-emerald-300">Demo Buyer Access</p>
          <h1 class="mt-4 text-4xl sm:text-5xl font-bold leading-tight">Try AinerWise as a smart building buyer</h1>
          <p class="mt-5 text-slate-300 text-lg">
            Use the prefilled demo account to explore buyer workflows for AI assessment,
            preliminary proposals, quotes, tickets, and future BOM planning. Demo data is
            for product exploration only and cannot create real payments or contracts.
          </p>
          <div class="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div v-for="project in demoProjects" :key="project" class="border border-white/10 bg-white/5 p-4 text-sm text-slate-200">
              {{ project }}
            </div>
          </div>
        </div>

        <form class="bg-white text-gray-900 border p-8" @submit.prevent="handleDemoLogin">
          <h2 class="text-2xl font-bold">Login as Demo Buyer</h2>
          <p class="mt-2 text-sm text-gray-600">
            The credentials are intentionally visible for demo review.
          </p>

          <div class="mt-6 space-y-5">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input v-model="form.email" type="email" class="input-field" autocomplete="username" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input v-model="form.password" type="password" class="input-field" autocomplete="current-password" />
            </div>
          </div>

          <div class="mt-6 bg-amber-50 border border-amber-200 p-4 text-sm text-amber-900">
            AI estimates in demo projects are not final quotes. Final quote requires manual review,
            site survey, supplier confirmation, and signed contract.
          </div>

          <p v-if="error" class="mt-4 text-sm text-red-600">{{ error }}</p>

          <button type="submit" class="mt-6 btn-primary w-full" :disabled="loading">
            {{ loading ? 'Logging in...' : 'Login as Demo Buyer' }}
          </button>

          <p class="mt-4 text-xs text-gray-500">
            If login fails, run backend demo seed script:
            <code>python -m scripts.create_demo_buyer</code>
          </p>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'guest' })

const { login } = useAuth()
const loading = ref(false)
const error = ref('')
const form = reactive({
  email: 'demo@ainerwise.com',
  password: 'demo123',
})

const demoProjects = [
  'Future Smart Villa',
  'AI School Campus',
  'Smart Apartment Building',
  'Enterprise Office AI Brain',
  'Solar + Storage Energy Site',
  'Smart Hotel Room Control',
]

async function handleDemoLogin() {
  loading.value = true
  error.value = ''
  try {
    await login(form.email, form.password)
    navigateTo('/portal')
  } catch (e: any) {
    error.value = e?.data?.detail || 'Demo login failed. Create demo data first.'
  } finally {
    loading.value = false
  }
}
</script>
