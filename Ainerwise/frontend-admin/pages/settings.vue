<template>
  <div>
    <h1 class="admin-page-title mb-6">{{ $t('admin.settings') }}</h1>
    <div class="grid grid-cols-1 xl:grid-cols-[1fr_0.8fr] gap-6">
      <div class="admin-card">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h2 class="admin-section-title">Demo Mode</h2>
            <p class="mt-1 text-sm text-gray-500">
              When enabled, PC/H5/Admin login pages show prefilled demo credentials and one-click demo access.
            </p>
          </div>
          <button
            type="button"
            class="relative inline-flex h-7 w-12 shrink-0 items-center rounded-full transition"
            :class="demoMode.enabled ? 'bg-emerald-500' : 'bg-gray-300'"
            :disabled="loading"
            @click="toggleDemoMode"
          >
            <span
              class="inline-block h-5 w-5 transform rounded-full bg-white shadow transition"
              :class="demoMode.enabled ? 'translate-x-6' : 'translate-x-1'"
            ></span>
          </button>
        </div>

        <div class="mt-5 rounded-lg border p-4" :class="demoMode.enabled ? 'border-emerald-200 bg-emerald-50' : 'border-gray-200 bg-gray-50'">
          <p class="text-sm font-semibold" :class="demoMode.enabled ? 'text-emerald-700' : 'text-gray-600'">
            {{ demoMode.enabled ? 'Demo mode is enabled by default.' : 'Demo mode is currently disabled.' }}
          </p>
          <p class="mt-1 text-xs text-gray-500">
            This switch is served by backend API. Environment default is enabled; production can override it with DEMO_MODE_ENABLED=false.
          </p>
        </div>

        <p v-if="error" class="mt-3 text-sm text-red-600">{{ error }}</p>
      </div>

      <div class="admin-card">
        <h2 class="admin-section-title">Demo Accounts</h2>
        <div class="mt-4 space-y-3 text-sm">
          <div class="rounded-lg border p-4">
            <p class="admin-section-title">{{ demoMode.buyer.label }}</p>
            <p class="mt-1 text-gray-500">Email: {{ demoMode.buyer.email }}</p>
            <p class="text-gray-500">Password: {{ demoMode.buyer.password }}</p>
          </div>
          <div v-if="demoMode.admin" class="rounded-lg border p-4">
            <p class="admin-section-title">{{ demoMode.admin.label }}</p>
            <p class="mt-1 text-gray-500">Email: {{ demoMode.admin.email }}</p>
            <p class="text-gray-500">Password: {{ demoMode.admin.password }}</p>
          </div>
        </div>
      </div>

      <IntegrationSettings />
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { getDemoMode, updateDemoMode, defaultDemoMode } = useDemoMode()
const demoMode = ref(defaultDemoMode)
const loading = ref(false)
const error = ref('')

onMounted(async () => {
  demoMode.value = await getDemoMode(true)
})

async function toggleDemoMode() {
  loading.value = true
  error.value = ''
  try {
    demoMode.value = await updateDemoMode(!demoMode.value.enabled)
  } catch (e: any) {
    error.value = e?.data?.detail || 'Failed to update demo mode'
  } finally {
    loading.value = false
  }
}
</script>
