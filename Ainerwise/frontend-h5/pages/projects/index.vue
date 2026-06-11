<template>
  <div class="px-4 py-4">
    <!-- Not logged in -->
    <div v-if="!isLoggedIn" class="text-center py-16">
      <div class="w-20 h-20 mx-auto rounded-full bg-blue-50 flex items-center justify-center mb-4">
        <svg class="w-10 h-10 text-blue-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
        </svg>
      </div>
      <h2 class="text-lg font-bold text-slate-800">Login Required</h2>
      <p class="text-sm text-slate-400 mt-2">Login to view and manage your smart building projects</p>
      <NuxtLink to="/login?redirect=/projects"
        class="inline-block mt-5 text-sm font-semibold bg-blue-500 text-white px-8 py-3 rounded-full shadow-md shadow-blue-500/20">
        Login
      </NuxtLink>
    </div>

    <!-- Logged in -->
    <template v-else>
      <div class="flex items-center justify-between mb-4">
        <div>
          <h1 class="text-lg font-bold text-slate-800">My Projects</h1>
          <p class="text-xs text-slate-400">Track your active smart building projects</p>
        </div>
        <NuxtLink to="/submit-requirement"
          class="text-xs font-semibold bg-blue-500 text-white px-4 py-2 rounded-full shadow-sm">
          + New
        </NuxtLink>
      </div>

      <!-- Stats -->
      <div class="grid grid-cols-3 gap-2 mb-4">
        <div class="bg-white rounded-xl p-3 text-center border border-slate-100 shadow-sm">
          <p class="text-xl font-bold text-slate-800">{{ stats.total }}</p>
          <p class="text-[10px] text-slate-400 font-medium">Total</p>
        </div>
        <div class="bg-white rounded-xl p-3 text-center border border-slate-100 shadow-sm">
          <p class="text-xl font-bold text-blue-500">{{ stats.active }}</p>
          <p class="text-[10px] text-slate-400 font-medium">Active</p>
        </div>
        <div class="bg-white rounded-xl p-3 text-center border border-slate-100 shadow-sm">
          <p class="text-xl font-bold text-emerald-500">{{ stats.completed }}</p>
          <p class="text-[10px] text-slate-400 font-medium">Done</p>
        </div>
      </div>

      <!-- Project list -->
      <div class="space-y-3">
        <NuxtLink
          v-for="project in projects"
          :key="project.id"
          :to="`/projects/${project.id}`"
          class="block bg-white rounded-xl p-4 border border-slate-100 shadow-sm active:bg-slate-50 transition"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1 min-w-0">
              <h3 class="text-sm font-semibold text-slate-800 truncate">{{ project.title || project.name || project.project_type }}</h3>
              <p class="text-xs text-slate-400 mt-1">{{ project.region || '' }} &middot; {{ new Date(project.created_at).toLocaleDateString() }}</p>
            </div>
            <span :class="['text-[10px] font-semibold px-2.5 py-1 rounded-full flex-shrink-0 ml-2', statusClass(project.status)]">
              {{ project.status?.replace(/_/g, ' ') }}
            </span>
          </div>
          <!-- Progress bar -->
          <div class="mt-3 flex items-center gap-0.5">
            <div
              v-for="(step, i) in statusSteps"
              :key="step"
              class="h-1 flex-1 rounded-full"
              :class="getStepIndex(project.status) >= i ? 'bg-blue-500' : 'bg-slate-100'"
            />
          </div>
        </NuxtLink>
      </div>

      <div v-if="!projects.length && !loading" class="text-center py-12 text-slate-400">
        <div class="text-3xl mb-2">🏗️</div>
        <p class="text-sm">No projects yet</p>
        <NuxtLink to="/submit-requirement" class="inline-block mt-3 text-xs font-semibold text-blue-500">
          Submit your first requirement &rarr;
        </NuxtLink>
      </div>

      <div v-if="loading" class="text-center py-12 text-slate-400">
        <p class="text-sm">Loading...</p>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
const { isLoggedIn } = useAuth()
const { apiFetch } = useApi()
const projects = ref<any[]>([])
const loading = ref(true)
const stats = reactive({ total: 0, active: 0, completed: 0 })

const statusSteps = ['planning', 'site_survey', 'quotation_confirmed', 'procurement', 'delivery', 'installation', 'testing', 'handover', 'maintenance', 'closed']

function getStepIndex(status: string) {
  return statusSteps.indexOf(status)
}

function statusClass(status: string) {
  if (['closed', 'handover'].includes(status)) return 'bg-emerald-50 text-emerald-600'
  if (['planning', 'site_survey'].includes(status)) return 'bg-blue-50 text-blue-600'
  return 'bg-amber-50 text-amber-600'
}

onMounted(async () => {
  if (!isLoggedIn.value) { loading.value = false; return }
  try {
    const res = await apiFetch<any>('/projects/my')
    projects.value = res.items || []
    stats.total = res.total || projects.value.length
    stats.active = projects.value.filter((p: any) => !['closed', 'handover', 'maintenance'].includes(p.status)).length
    stats.completed = projects.value.filter((p: any) => ['closed', 'handover'].includes(p.status)).length
  } catch {
    projects.value = []
  } finally {
    loading.value = false
  }
})
</script>
