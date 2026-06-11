<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between gap-4 flex-wrap">
      <div>
        <h1 class="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <UIcon name="i-heroicons-cpu-chip" class="h-7 w-7 text-indigo-600" />
          AI Project Forge
        </h1>
        <p class="text-sm text-slate-500 mt-1">
          Describe your project, upload documents — AI generates a structured procurement list.
        </p>
      </div>
      <UButton color="indigo" icon="i-heroicons-plus" size="lg" @click="showCreate = true">
        New Project
      </UButton>
    </div>

    <!-- Empty State -->
    <div v-if="!loading && projects.length === 0" class="bg-white rounded-3xl border border-slate-200 p-16 text-center">
      <div class="text-6xl mb-4">🏗️</div>
      <h3 class="text-xl font-semibold text-slate-900">No Projects Yet</h3>
      <p class="text-sm text-slate-500 mt-2 max-w-md mx-auto">
        Create your first project to let AI analyze your requirements and generate a smart procurement list.
      </p>
      <UButton color="indigo" icon="i-heroicons-plus" size="lg" class="mt-6" @click="showCreate = true">
        Create Your First Project
      </UButton>
    </div>

    <!-- Projects Grid -->
    <div v-if="projects.length > 0" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      <NuxtLink
        v-for="project in projects"
        :key="project.id"
        :to="`/buyer/projects/${project.id}`"
        class="group bg-white rounded-2xl border border-slate-200 p-5 hover:border-indigo-300 hover:shadow-lg transition-all duration-200"
      >
        <div class="flex items-start justify-between mb-3">
          <div class="flex items-center gap-2">
            <span class="text-xl">{{ projectTypeIcon(project.project_type) }}</span>
            <UBadge :color="statusColor(project.status)" variant="subtle" size="xs">
              {{ project.status.replace(/_/g, ' ') }}
            </UBadge>
          </div>
          <UIcon name="i-heroicons-arrow-right" class="w-4 h-4 text-slate-300 group-hover:text-indigo-500 transition-colors" />
        </div>
        <h3 class="text-base font-semibold text-slate-900 group-hover:text-indigo-700 line-clamp-2">
          {{ project.title }}
        </h3>
        <p v-if="project.description" class="text-xs text-slate-500 mt-1.5 line-clamp-2">
          {{ project.description }}
        </p>
        <div class="flex items-center gap-4 mt-4 text-xs text-slate-400">
          <span v-if="project.country || project.city" class="flex items-center gap-1">
            <UIcon name="i-heroicons-map-pin" class="w-3.5 h-3.5" />
            {{ [project.city, project.country].filter(Boolean).join(', ') }}
          </span>
          <span v-if="project.budget_max" class="flex items-center gap-1">
            <UIcon name="i-heroicons-banknotes" class="w-3.5 h-3.5" />
            {{ formatCurrency(project.budget_max, project.currency) }}
          </span>
          <span class="ml-auto text-[10px]">
            {{ timeAgo(project.created_at) }}
          </span>
        </div>
      </NuxtLink>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-16">
      <UIcon name="i-heroicons-arrow-path" class="w-8 h-8 text-indigo-400 animate-spin mx-auto" />
      <p class="text-sm text-slate-500 mt-3">Loading projects...</p>
    </div>

    <!-- Create Project Modal -->
    <UModal v-model="showCreate">
      <UCard class="sm:min-w-[480px]">
        <template #header>
          <h3 class="text-lg font-semibold text-slate-900">Create New Project</h3>
        </template>

        <div class="space-y-4">
          <UFormGroup label="Project Title" required>
            <UInput v-model="form.title" placeholder="e.g. 2-Storey Residential House Construction" size="lg" />
          </UFormGroup>

          <UFormGroup label="Project Type">
            <USelect v-model="form.project_type" :options="projectTypes" size="lg" />
          </UFormGroup>

          <div class="grid grid-cols-2 gap-4">
            <UFormGroup label="Country">
              <UInput v-model="form.country" placeholder="Philippines" />
            </UFormGroup>
            <UFormGroup label="City">
              <UInput v-model="form.city" placeholder="Cebu City" />
            </UFormGroup>
          </div>

          <div class="grid grid-cols-3 gap-4">
            <UFormGroup label="Area">
              <UInput v-model.number="form.area_value" type="number" placeholder="150" />
            </UFormGroup>
            <UFormGroup label="Unit">
              <USelect v-model="form.area_unit" :options="['sqm', 'sqft', 'm2', 'hectares']" />
            </UFormGroup>
            <UFormGroup label="Quality">
              <USelect v-model="form.quality_preference" :options="qualityOptions" />
            </UFormGroup>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <UFormGroup label="Budget Min">
              <UInput v-model.number="form.budget_min" type="number" placeholder="500000" />
            </UFormGroup>
            <UFormGroup label="Budget Max">
              <UInput v-model.number="form.budget_max" type="number" placeholder="2000000" />
            </UFormGroup>
          </div>

          <UFormGroup label="Description">
            <UTextarea
              v-model="form.description"
              :rows="4"
              placeholder="Describe your project in detail. Include materials needed, specifications, timeline, etc."
            />
          </UFormGroup>
        </div>

        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton variant="ghost" color="gray" @click="showCreate = false">Cancel</UButton>
            <UButton color="indigo" :loading="creating" @click="createProject">
              Create Project
            </UButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'buyer', middleware: ['buyer'] })

const authStore = useAuthStore()
const config = useRuntimeConfig()

const loading = ref(true)
const creating = ref(false)
const showCreate = ref(false)
const projects = ref<any[]>([])

const projectTypes = [
  { label: '🏠 General', value: 'GENERAL' },
  { label: '🏗️ Construction', value: 'CONSTRUCTION' },
  { label: '☀️ Solar', value: 'SOLAR' },
  { label: '💻 Tech Build', value: 'TECH_BUILD' },
  { label: '🔨 Renovation', value: 'RENOVATION' },
]
const qualityOptions = [
  { label: '🤷 Not Sure', value: 'NOT_SURE' },
  { label: '💰 Budget', value: 'BUDGET' },
  { label: '⚖️ Mid-Range', value: 'MID_RANGE' },
  { label: '✨ Premium', value: 'PREMIUM' },
]

const form = reactive({
  title: '',
  project_type: 'GENERAL',
  country: 'Philippines',
  city: '',
  area_value: null as number | null,
  area_unit: 'sqm',
  budget_min: null as number | null,
  budget_max: null as number | null,
  quality_preference: 'NOT_SURE',
  description: '',
})

function projectTypeIcon(type: string) {
  const map: Record<string, string> = {
    CONSTRUCTION: '🏗️', SOLAR: '☀️', TECH_BUILD: '💻',
    RENOVATION: '🔨', GENERAL: '📦',
  }
  return map[type] || '📦'
}

function statusColor(status: string) {
  const map: Record<string, string> = {
    DRAFT: 'gray', COLLECTING_INFO: 'blue', ANALYZING: 'yellow',
    AI_ANALYZED: 'green', READY_FOR_SOURCING: 'indigo',
    SOURCING: 'purple', ORDERING: 'orange', COMPLETED: 'green', CANCELED: 'red',
  }
  return map[status] || 'gray'
}

function formatCurrency(amount: number, currency = 'PHP') {
  try {
    return new Intl.NumberFormat('en-PH', { style: 'currency', currency, maximumFractionDigits: 0 }).format(amount)
  } catch { return `${amount} ${currency}` }
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

async function loadProjects() {
  loading.value = true
  try {
    projects.value = await $fetch<any[]>(`${config.public.apiBase}/buyer/projects`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    })
  } catch (e) {
    console.error('Failed to load projects:', e)
  } finally {
    loading.value = false
  }
}

async function createProject() {
  if (!form.title.trim()) return
  creating.value = true
  try {
    const body: any = { title: form.title, project_type: form.project_type }
    if (form.country) body.country = form.country
    if (form.city) body.city = form.city
    if (form.area_value) body.area_value = form.area_value
    if (form.area_unit) body.area_unit = form.area_unit
    if (form.budget_min) body.budget_min = form.budget_min
    if (form.budget_max) body.budget_max = form.budget_max
    if (form.quality_preference) body.quality_preference = form.quality_preference
    if (form.description) body.description = form.description

    const project = await $fetch<any>(`${config.public.apiBase}/buyer/projects`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
      body,
    })
    showCreate.value = false
    navigateTo(`/buyer/projects/${project.id}`)
  } catch (e: any) {
    console.error('Failed to create project:', e)
  } finally {
    creating.value = false
  }
}

onMounted(loadProjects)
</script>
