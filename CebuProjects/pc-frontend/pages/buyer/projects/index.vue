<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="bg-white rounded-2xl border border-slate-200 p-5 flex items-center justify-between gap-4 flex-wrap">
      <div class="min-w-0">
        <h1 class="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <UIcon name="i-heroicons-cpu-chip" class="h-7 w-7 text-indigo-600 flex-shrink-0" />
          {{ appStore.t('buyer.projects.forgeTitle') }}
        </h1>
        <p class="text-sm text-slate-500 mt-1">
          {{ appStore.t('buyer.projects.forgeSubtitle') }}
        </p>
      </div>
      <UButton color="indigo" icon="i-heroicons-plus" class="flex-shrink-0" @click="openCreateModal">
        {{ appStore.t('buyer.projects.new') }}
      </UButton>
    </div>

    <!-- Empty State -->
    <div v-if="!loading && projects.length === 0" class="bg-white rounded-3xl border border-slate-200 p-16 text-center">
      <div class="text-6xl mb-4">🏗️</div>
      <h3 class="text-xl font-semibold text-slate-900">{{ appStore.t('buyer.projects.emptyTitle') }}</h3>
      <p class="text-sm text-slate-500 mt-2 max-w-md mx-auto">
        {{ appStore.t('buyer.projects.emptyDesc') }}
      </p>
      <UButton color="indigo" icon="i-heroicons-plus" size="lg" class="mt-6" @click="openCreateModal">
        {{ appStore.t('buyer.projects.createFirst') }}
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
      <p class="text-sm text-slate-500 mt-3">{{ appStore.t('buyer.projects.loading') }}</p>
    </div>

    <!-- Create Project Modal -->
    <UModal v-model="showCreate">
      <UCard class="sm:min-w-[480px]">
        <template #header>
          <h3 class="text-lg font-semibold text-slate-900">{{ appStore.t('buyer.projects.createTitle') }}</h3>
        </template>

        <div class="space-y-4">
          <UFormGroup :label="appStore.t('buyer.projects.fieldTitle')" required>
            <UInput v-model="form.title" :placeholder="appStore.t('buyer.projects.phTitle')" size="lg" />
          </UFormGroup>

          <UFormGroup :label="appStore.t('buyer.projects.fieldType')">
            <USelect v-model="form.project_type" :options="projectTypes" size="lg" />
          </UFormGroup>

          <div class="grid grid-cols-2 gap-4">
            <UFormGroup :label="appStore.t('buyer.projects.fieldCountry')">
              <select
                v-model="form.country"
                class="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 shadow-sm outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
              >
                <option v-for="region in regionOptions" :key="region.code" :value="region.code">
                  {{ region.name }} ({{ region.code }})
                </option>
              </select>
            </UFormGroup>
            <UFormGroup :label="appStore.t('buyer.projects.fieldCity')">
              <UInput v-model="form.city" :placeholder="selectedRegion?.defaultCity || 'Belgrade'" />
            </UFormGroup>
          </div>

          <div class="grid grid-cols-3 gap-4">
            <UFormGroup :label="appStore.t('buyer.projects.fieldArea')">
              <UInput v-model.number="form.area_value" type="number" placeholder="150" />
            </UFormGroup>
            <UFormGroup :label="appStore.t('buyer.projects.fieldUnit')">
              <USelect v-model="form.area_unit" :options="['sqm', 'sqft', 'm2', 'hectares']" />
            </UFormGroup>
            <UFormGroup :label="appStore.t('buyer.projects.fieldQuality')">
              <USelect v-model="form.quality_preference" :options="qualityOptions" />
            </UFormGroup>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <UFormGroup :label="appStore.t('buyer.projects.fieldBudgetMin')">
              <UInput v-model.number="form.budget_min" type="number" placeholder="500000" />
            </UFormGroup>
            <UFormGroup :label="appStore.t('buyer.projects.fieldBudgetMax')">
              <UInput v-model.number="form.budget_max" type="number" placeholder="2000000" />
            </UFormGroup>
          </div>

          <UFormGroup :label="appStore.t('buyer.projects.fieldCurrency')">
            <USelect
              v-model="form.currency"
              :options="appStore.currencyOptions"
              option-attribute="label"
              value-attribute="code"
            />
            <p class="mt-1 text-xs text-slate-500">
              {{ currencyPolicyHint }}
            </p>
          </UFormGroup>

          <UFormGroup :label="appStore.t('buyer.projects.fieldDescription')">
            <UTextarea
              v-model="form.description"
              :rows="4"
              :placeholder="appStore.t('buyer.projects.phDescription')"
            />
          </UFormGroup>
        </div>

        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton variant="ghost" color="gray" @click="showCreate = false">{{ appStore.t('buyer.projects.cancel') }}</UButton>
            <UButton color="indigo" :loading="creating" @click="createProject">
              {{ appStore.t('buyer.projects.create') }}
            </UButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import { FALLBACK_PAYMENT_POLICIES, currencyOptionLabel, formatMoneyMinor, localeForLanguage } from '~/utils/currencyPolicy'

definePageMeta({ layout: 'buyer', middleware: ['buyer'] })

const authStore = useAuthStore()
const appStore = useAppStore()
const config = useRuntimeConfig()

const loading = ref(true)
const creating = ref(false)
const showCreate = ref(false)
const projects = ref<any[]>([])

type RegionOption = {
  code: string
  name: string
  defaultCity?: string
}

const projectTypes = computed(() => [
  { label: `🏠 ${appStore.t('buyer.projects.typeGeneral')}`, value: 'GENERAL' },
  { label: `🏗️ ${appStore.t('buyer.projects.typeConstruction')}`, value: 'CONSTRUCTION' },
  { label: `☀️ ${appStore.t('buyer.projects.typeSolar')}`, value: 'SOLAR' },
  { label: `💻 ${appStore.t('buyer.projects.typeTech')}`, value: 'TECH_BUILD' },
  { label: `🔨 ${appStore.t('buyer.projects.typeRenovation')}`, value: 'RENOVATION' },
])
const qualityOptions = computed(() => [
  { label: `🤷 ${appStore.t('buyer.projects.qualityNotSure')}`, value: 'NOT_SURE' },
  { label: `💰 ${appStore.t('buyer.projects.qualityBudget')}`, value: 'BUDGET' },
  { label: `⚖️ ${appStore.t('buyer.projects.qualityMid')}`, value: 'MID_RANGE' },
  { label: `✨ ${appStore.t('buyer.projects.qualityPremium')}`, value: 'PREMIUM' },
])

const form = reactive({
  title: '',
  project_type: 'GENERAL',
  country: '',
  city: '',
  area_value: null as number | null,
  area_unit: 'sqm',
  budget_min: null as number | null,
  budget_max: null as number | null,
  currency: 'EUR',
  quality_preference: 'NOT_SURE',
  description: '',
})

const fallbackDefaultCities: Record<string, string> = {
  RS: 'Belgrade',
  PL: 'Warsaw',
  PH: 'Cebu City',
  BA: 'Sarajevo',
  RO: 'Bucharest',
}

const fallbackRegions: RegionOption[] = Object.values(FALLBACK_PAYMENT_POLICIES).map((policy) => ({
  code: policy.country_code,
  name: policy.country_name,
  defaultCity: fallbackDefaultCities[policy.country_code],
}))

const regionOptions = computed<RegionOption[]>(() => {
  const regions = (authStore.systemMode as any)?.regions
  if (Array.isArray(regions) && regions.length) {
    return regions
      .map((region: any) => ({
        code: String(region.code || '').toUpperCase(),
        name: String(region.name || region.label || region.code || '').trim(),
        defaultCity: region.default_city || region.city || undefined,
      }))
      .filter((region: RegionOption) => region.code && region.name)
  }
  return fallbackRegions
})

const selectedRegion = computed(() => regionOptions.value.find(region => region.code === form.country))
const dateLocale = computed(() => localeForLanguage(appStore.language, form.currency || appStore.currency))
const currencyPolicyHint = computed(() => {
  const policy = appStore.paymentPolicy
  const local = policy.local_currency_alias ? `${policy.local_currency} / ${policy.local_currency_alias}` : policy.local_currency
  if (appStore.language === 'ZH') {
    return `${policy.country_name || form.country}: 结算币 ${currencyOptionLabel(form.currency)}；本地参考币 ${local}。`
  }
  return `${policy.country_name || form.country}: settlement ${currencyOptionLabel(form.currency)}; local reference ${local}.`
})

function ensureDefaultRegion() {
  if (!form.country && regionOptions.value.length) {
    form.country = regionOptions.value[0].code
  }
  if (!form.currency) {
    form.currency = appStore.currency || 'EUR'
  }
}

async function openCreateModal() {
  showCreate.value = true
  if (!authStore.systemMode) {
    await authStore.fetchSystemMode()
  }
  ensureDefaultRegion()
}

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

function formatCurrency(amount: number, currency = appStore.currency || 'EUR') {
  return formatMoneyMinor(Number(amount || 0) * 100, currency, localeForLanguage(appStore.language, currency))
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
    body.currency = form.currency || appStore.currency || 'EUR'
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

watch(regionOptions, ensureDefaultRegion, { immediate: true })
watch(() => form.country, async (country) => {
  if (!country) return
  await appStore.setRegionCountry(country)
  form.currency = appStore.currency || appStore.defaultSettlementCurrency || 'EUR'
})

onMounted(async () => {
  if (!authStore.systemMode) {
    await authStore.fetchSystemMode()
  }
  ensureDefaultRegion()
  form.currency = appStore.currency || 'EUR'
  await loadProjects()
})
</script>
