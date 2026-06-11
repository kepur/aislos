<template>
  <div>
    <!-- Header -->
    <header class="bg-white border-b border-slate-100 px-4 flex items-center justify-between sticky top-0 z-40" style="height: 56px; padding-top: var(--safe-area-top)">
      <div class="flex items-center gap-2">
        <NuxtLink to="/buyer/home" class="text-slate-500">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </NuxtLink>
        <h1 class="text-lg font-bold text-slate-900">{{ $t('project.title') }}</h1>
      </div>
      <button @click="showCreate = true" class="w-9 h-9 rounded-full bg-primary-600 text-white flex items-center justify-center active:bg-primary-700">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
        </svg>
      </button>
    </header>

    <div class="space-y-4 p-4 pb-24">
      <!-- AI Forge Banner -->
      <div class="rounded-2xl bg-gradient-to-r from-primary-600 to-purple-600 p-5 text-white shadow-card">
        <div class="flex items-center gap-2 mb-1">
          <span class="text-xl">🤖</span>
          <span class="text-xs font-semibold uppercase tracking-wider opacity-80">{{ $t('project.forge') }}</span>
        </div>
        <h2 class="text-lg font-bold leading-tight">{{ $t('project.banner_title') }}</h2>
        <p class="text-xs text-white/70 mt-2">{{ $t('project.banner_subtitle') }}</p>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="space-y-3">
        <div v-for="n in 3" :key="n" class="card">
          <div class="shimmer h-4 w-3/4 rounded mb-2"></div>
          <div class="shimmer h-3 w-1/2 rounded"></div>
        </div>
      </div>

      <!-- Empty -->
      <div v-if="!loading && projects.length === 0" class="text-center py-12">
        <div class="text-5xl mb-3">🏗️</div>
        <h3 class="text-base font-semibold text-slate-800">{{ $t('project.no_projects') }}</h3>
        <p class="text-sm text-slate-500 mt-1">{{ $t('project.create_first') }}</p>
      </div>

      <!-- Project Cards -->
      <NuxtLink
        v-for="project in projects"
        :key="project.id"
        :to="`/buyer/projects/${project.id}`"
        class="card block active:bg-slate-50 transition-colors"
      >
        <div class="flex items-start justify-between gap-2 mb-2">
          <div class="flex items-center gap-2">
            <span class="text-lg">{{ typeIcon(project.project_type) }}</span>
            <span :class="badgeClass(project.status)" class="text-[11px] px-2 py-0.5 rounded-full font-medium">
              {{ statusLabel(project.status) }}
            </span>
          </div>
          <svg class="w-4 h-4 text-slate-300 flex-shrink-0 mt-1" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </div>
        <h3 class="text-sm font-semibold text-slate-900 line-clamp-2">{{ project.title }}</h3>
        <p v-if="project.description" class="text-xs text-slate-500 mt-1 line-clamp-2">{{ project.description }}</p>
        <div class="flex items-center gap-3 mt-2 text-[11px] text-slate-400">
          <span v-if="project.city || project.country">📍 {{ [project.city, project.country].filter(Boolean).join(', ') }}</span>
          <span v-if="project.budget_max">💰 {{ formatCurrency(project.budget_max) }}</span>
          <span class="ml-auto">{{ timeAgo(project.created_at) }}</span>
        </div>
      </NuxtLink>
    </div>

    <!-- Create Modal (Full screen sheet) -->
    <Teleport to="body">
      <Transition name="sheet">
        <div v-if="showCreate" class="fixed inset-0 z-50 bg-white flex flex-col">
          <header class="flex items-center justify-between px-4 border-b border-slate-100" style="height: 56px; padding-top: var(--safe-area-top)">
            <button @click="showCreate = false" class="text-slate-500 text-sm font-medium">{{ $t('common.cancel') }}</button>
            <h2 class="font-bold text-slate-900">{{ $t('project.new_project') }}</h2>
            <button @click="createProject" :disabled="creating || !form.title.trim()" class="text-primary-600 text-sm font-semibold disabled:opacity-40">
              {{ creating ? '...' : $t('common.submit') }}
            </button>
          </header>

          <div class="flex-1 overflow-y-auto p-4 space-y-5 pb-12">
            <div>
              <label class="block text-xs font-semibold text-slate-500 mb-1">{{ $t('project.project_title') }} *</label>
              <input v-model="form.title" type="text" placeholder="e.g. 2-Storey House Construction" class="input-field" />
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-500 mb-1">{{ $t('project.project_type') }}</label>
              <select v-model="form.project_type" class="input-field">
                <option value="GENERAL">📦 {{ $t('project.type.GENERAL') }}</option>
                <option value="CONSTRUCTION">🏗️ {{ $t('project.type.CONSTRUCTION') }}</option>
                <option value="SOLAR">☀️ {{ $t('project.type.SOLAR') }}</option>
                <option value="TECH_BUILD">💻 {{ $t('project.type.TECH_BUILD') }}</option>
                <option value="RENOVATION">🔨 {{ $t('project.type.RENOVATION') }}</option>
              </select>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-semibold text-slate-500 mb-1">{{ $t('project.country') }}</label>
                <input v-model="form.country" type="text" placeholder="Philippines" class="input-field" />
              </div>
              <div>
                <label class="block text-xs font-semibold text-slate-500 mb-1">{{ $t('project.city') }}</label>
                <input v-model="form.city" type="text" placeholder="Cebu City" class="input-field" />
              </div>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-semibold text-slate-500 mb-1">{{ $t('project.area') }}</label>
                <input v-model.number="form.area_value" type="number" placeholder="150" class="input-field" />
              </div>
              <div>
                <label class="block text-xs font-semibold text-slate-500 mb-1">{{ $t('project.quality') }}</label>
                <select v-model="form.quality_preference" class="input-field">
                  <option value="NOT_SURE">🤷 {{ $t('project.quality_option.NOT_SURE') }}</option>
                  <option value="BUDGET">💰 {{ $t('project.quality_option.BUDGET') }}</option>
                  <option value="MID_RANGE">⚖️ {{ $t('project.quality_option.MID_RANGE') }}</option>
                  <option value="PREMIUM">✨ {{ $t('project.quality_option.PREMIUM') }}</option>
                </select>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-semibold text-slate-500 mb-1">{{ $t('project.budget_min') }}</label>
                <input v-model.number="form.budget_min" type="number" placeholder="500000" class="input-field" />
              </div>
              <div>
                <label class="block text-xs font-semibold text-slate-500 mb-1">{{ $t('project.budget_max') }}</label>
                <input v-model.number="form.budget_max" type="number" placeholder="2000000" class="input-field" />
              </div>
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-500 mb-1">{{ $t('project.description') }}</label>
              <textarea v-model="form.description" rows="4" :placeholder="$t('project.description_placeholder')" class="input-field"></textarea>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

definePageMeta({ layout: 'buyer', middleware: ['buyer'] })
const { t } = useI18n({ useScope: 'global' })
useHead({ title: t('project.title') })

const authStore = useAuthStore()
const config = useRuntimeConfig()

const loading = ref(true)
const creating = ref(false)
const showCreate = ref(false)
const projects = ref<any[]>([])

const form = reactive({
  title: '',
  project_type: 'GENERAL',
  country: 'Philippines',
  city: '',
  area_value: null as number | null,
  budget_min: null as number | null,
  budget_max: null as number | null,
  quality_preference: 'NOT_SURE',
  description: '',
})

function typeIcon(type: string) {
  return { CONSTRUCTION: '🏗️', SOLAR: '☀️', TECH_BUILD: '💻', RENOVATION: '🔨', GENERAL: '📦' }[type] || '📦'
}

function badgeClass(status: string) {
  const map: Record<string, string> = {
    DRAFT: 'badge-gray', COLLECTING_INFO: 'badge-primary', ANALYZING: 'badge-warning',
    AI_ANALYZED: 'badge-success', READY_FOR_SOURCING: 'badge-primary',
    SOURCING: 'badge-primary', ORDERING: 'badge-warning', COMPLETED: 'badge-success', CANCELED: 'badge-danger',
  }
  return map[status] || 'badge-gray'
}

function statusLabel(status: string) {
  return t(`project.status.${status}`)
}

function formatCurrency(amount: number) {
  return `₱${(amount || 0).toLocaleString('en-PH', { maximumFractionDigits: 0 })}`
}

function timeAgo(dateStr: string) {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h`
  return `${Math.floor(hrs / 24)}d`
}

async function loadProjects() {
  loading.value = true
  try {
    projects.value = await $fetch<any[]>(`${config.public.apiBase}/buyer/projects`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    })
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

async function createProject() {
  if (!form.title.trim()) return
  creating.value = true
  try {
    const body: any = { title: form.title, project_type: form.project_type }
    if (form.country) body.country = form.country
    if (form.city) body.city = form.city
    if (form.area_value) body.area_value = form.area_value
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
  } catch (e: any) { console.error(e) }
  finally { creating.value = false }
}

onMounted(loadProjects)
</script>

<style scoped>
.input-field {
  width: 100%;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 12px 14px;
  font-size: 14px;
  background: white;
  outline: none;
  transition: border-color 0.15s;
}
.input-field:focus {
  border-color: #6366f1;
}
.sheet-enter-active, .sheet-leave-active {
  transition: transform 0.25s ease;
}
.sheet-enter-from, .sheet-leave-to {
  transform: translateY(100%);
}
</style>
