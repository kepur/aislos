<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-xl font-bold text-slate-800">{{ $t('portal.myProjects') }}</h1>
      <p class="text-sm text-slate-400 mt-1">Track your smart building projects</p>
    </div>

    <div v-if="projects.length" class="space-y-4">
      <div
        v-for="project in projects"
        :key="project.id"
        class="portal-card hover:shadow-md cursor-pointer transition-all group"
        @click="$router.push(`/portal/projects/${project.id}`)"
      >
        <div class="flex items-start justify-between gap-4">
          <div>
            <h3 class="font-semibold text-slate-800 group-hover:text-blue-600 transition">{{ project.title }}</h3>
            <p class="text-sm text-slate-400 mt-1">{{ project.region || '-' }}</p>
          </div>
          <span :class="['text-xs font-semibold px-2.5 py-1 rounded-full', statusClass(project.status)]">
            {{ project.status?.replace(/_/g, ' ') }}
          </span>
        </div>

        <!-- Progress bar -->
        <div class="mt-4">
          <div class="flex items-center gap-0.5">
            <div
              v-for="(step, i) in statusSteps"
              :key="step.key"
              class="h-1.5 flex-1 rounded-full transition-colors"
              :class="getStepIndex(project.status) >= i ? 'bg-gradient-to-r from-blue-500 to-indigo-500' : 'bg-slate-100'"
            />
          </div>
          <div class="flex justify-between mt-1.5 text-[10px] text-slate-400 font-medium uppercase tracking-wider">
            <span>Planning</span>
            <span>Delivery</span>
            <span>Closed</span>
          </div>
        </div>

        <div class="mt-3 flex flex-wrap items-center gap-4 text-xs text-slate-400">
          <span v-if="project.start_date" class="flex items-center gap-1">📅 Start: {{ project.start_date }}</span>
          <span v-if="project.expected_delivery_date" class="flex items-center gap-1">🎯 Delivery: {{ project.expected_delivery_date }}</span>
          <span>Created: {{ new Date(project.created_at).toLocaleDateString() }}</span>
        </div>
      </div>
    </div>

    <div v-else class="portal-card text-center py-12">
      <div class="text-4xl mb-3">🏗️</div>
      <p class="text-sm text-slate-400">{{ loading ? 'Loading projects...' : 'No active projects yet' }}</p>
      <p v-if="!loading" class="text-xs text-slate-300 mt-1">Projects appear here once a quote is accepted</p>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'portal', middleware: 'auth' })

const { apiFetch } = useApi()
const projects = ref<any[]>([])
const loading = ref(true)

const statusSteps = [
  { key: 'planning' }, { key: 'site_survey' }, { key: 'quotation_confirmed' },
  { key: 'procurement' }, { key: 'delivery' }, { key: 'installation' },
  { key: 'testing' }, { key: 'handover' }, { key: 'maintenance' }, { key: 'closed' },
]

function getStepIndex(status: string) {
  return statusSteps.findIndex(s => s.key === status)
}

function statusClass(status: string) {
  if (['closed', 'handover'].includes(status)) return 'bg-emerald-50 text-emerald-600'
  if (['planning', 'site_survey'].includes(status)) return 'bg-blue-50 text-blue-600'
  return 'bg-amber-50 text-amber-600'
}

onMounted(async () => {
  try {
    const res = await apiFetch<any>('/projects/my')
    projects.value = res.items || []
  } catch {
    projects.value = []
  } finally {
    loading.value = false
  }
})
</script>
