<template>
  <div v-if="project">
    <NuxtLink to="/portal/projects" class="text-sm text-primary-600 hover:underline">&larr; Back to My Projects</NuxtLink>

    <div class="mt-4 flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-900">{{ project.title }}</h1>
      <StatusBadge :status="project.status" />
    </div>

    <!-- Status Timeline -->
    <div class="mt-6 bg-white rounded-xl border p-6">
      <h2 class="font-semibold text-gray-900 mb-4">Project Progress</h2>
      <div class="flex items-center gap-1 overflow-x-auto pb-2">
        <div
          v-for="(step, i) in statusSteps"
          :key="step.key"
          class="flex items-center shrink-0"
        >
          <div class="flex flex-col items-center">
            <div
              class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold"
              :class="stepClass(step.key, i)"
            >
              <span v-if="currentStepIndex > i">&#10003;</span>
              <span v-else>{{ i + 1 }}</span>
            </div>
            <span class="text-xs mt-1 max-w-[72px] text-center leading-tight" :class="currentStepIndex >= i ? 'text-gray-900 font-medium' : 'text-gray-400'">
              {{ step.label }}
            </span>
          </div>
          <div v-if="i < statusSteps.length - 1" class="w-6 h-0.5 mt-[-16px]" :class="currentStepIndex > i ? 'bg-green-500' : 'bg-gray-200'" />
        </div>
      </div>
    </div>

    <div class="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Project Info -->
      <div class="bg-white rounded-xl border p-6">
        <h2 class="font-semibold text-gray-900 mb-4">Project Details</h2>
        <dl class="space-y-3 text-sm">
          <div class="flex justify-between">
            <dt class="text-gray-500">Region</dt>
            <dd class="font-medium">{{ project.region || '-' }}</dd>
          </div>
          <div class="flex justify-between">
            <dt class="text-gray-500">Start Date</dt>
            <dd class="font-medium">{{ project.start_date || 'Not scheduled' }}</dd>
          </div>
          <div class="flex justify-between">
            <dt class="text-gray-500">Expected Delivery</dt>
            <dd class="font-medium">{{ project.expected_delivery_date || 'Not scheduled' }}</dd>
          </div>
          <div class="flex justify-between">
            <dt class="text-gray-500">Created</dt>
            <dd class="font-medium">{{ new Date(project.created_at).toLocaleDateString() }}</dd>
          </div>
        </dl>
      </div>

      <!-- Team -->
      <div class="bg-white rounded-xl border p-6">
        <h2 class="font-semibold text-gray-900 mb-4">Project Team</h2>
        <div v-if="project.team_json?.length" class="space-y-2">
          <div v-for="(member, i) in project.team_json" :key="i" class="flex items-center gap-3 p-2 rounded-lg bg-gray-50">
            <div class="w-8 h-8 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-xs font-bold">
              {{ (member.name || '?').charAt(0).toUpperCase() }}
            </div>
            <div>
              <p class="text-sm font-medium text-gray-900">{{ member.name || '-' }}</p>
              <p class="text-xs text-gray-500">{{ member.role || '-' }}</p>
            </div>
          </div>
        </div>
        <p v-else class="text-sm text-gray-500">Team information will be available once the project starts.</p>
      </div>
    </div>
  </div>
  <div v-else class="text-center py-12 text-gray-500">Loading...</div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'portal', middleware: 'auth' })

const route = useRoute()
const { apiFetch } = useApi()
const project = ref<any>(null)

const statusSteps = [
  { key: 'planning', label: 'Planning' },
  { key: 'site_survey', label: 'Site Survey' },
  { key: 'quotation_confirmed', label: 'Quote OK' },
  { key: 'procurement', label: 'Procurement' },
  { key: 'delivery', label: 'Delivery' },
  { key: 'installation', label: 'Installation' },
  { key: 'testing', label: 'Testing' },
  { key: 'handover', label: 'Handover' },
  { key: 'maintenance', label: 'Maintenance' },
  { key: 'closed', label: 'Closed' },
]

const currentStepIndex = computed(() => {
  if (!project.value) return -1
  return statusSteps.findIndex(s => s.key === project.value.status)
})

function stepClass(key: string, index: number) {
  if (key === project.value?.status) return 'bg-primary-600 text-white'
  if (currentStepIndex.value > index) return 'bg-green-500 text-white'
  return 'bg-gray-200 text-gray-500'
}

onMounted(async () => {
  try {
    project.value = await apiFetch<any>(`/projects/${route.params.id}`)
  } catch {}
})
</script>
