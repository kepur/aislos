<template>
  <div>
    <div class="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div>
        <p :class="['text-xs font-bold uppercase tracking-wider', brand.accentText]">
          {{ brandLabel }}
        </p>
        <h1 class="mt-1 text-2xl font-bold text-white">{{ $t('procurement.title') }}</h1>
        <p class="mt-2 max-w-2xl text-sm text-slate-400">{{ $t('procurement.subtitle') }}</p>
      </div>
      <button
        type="button"
        class="rounded-lg bg-gradient-to-r px-4 py-2 text-sm font-semibold text-white shadow-lg"
        :class="brand.accent"
        @click="showCreate = true"
      >
        {{ $t('procurement.newProject') }}
      </button>
    </div>

    <div v-if="loading" class="pc-card text-sm text-slate-400">{{ $t('common.loading') }}</div>
    <div v-else-if="error" class="pc-card text-sm text-red-400">{{ error }}</div>
    <div v-else class="space-y-3">
      <NuxtLink
        v-for="project in projects"
        :key="project.id"
        :to="`/procurement/projects/${project.id}`"
        class="pc-card block hover:border-white/20 transition"
      >
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 class="font-semibold text-white">{{ project.title }}</h2>
            <p class="mt-1 text-xs text-slate-500">
              {{ project.project_type }} · {{ project.country || project.region || '—' }}
            </p>
          </div>
          <span class="rounded-full bg-white/10 px-3 py-1 text-xs font-medium text-slate-300">
            {{ project.status.replace(/_/g, ' ') }}
          </span>
        </div>
      </NuxtLink>
      <p v-if="!projects.length" class="pc-card text-sm text-slate-400">
        {{ $t('procurement.emptyProjects') }}
      </p>
    </div>

    <div v-if="showCreate" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <form class="pc-card w-full max-w-lg space-y-4" @submit.prevent="createNew">
        <h2 class="text-lg font-bold text-white">{{ $t('procurement.newProject') }}</h2>
        <div>
          <label class="mb-1 block text-sm text-slate-400">{{ $t('procurement.fields.title') }}</label>
          <input v-model="form.title" required class="input-field" />
        </div>
        <div>
          <label class="mb-1 block text-sm text-slate-400">{{ $t('procurement.fields.type') }}</label>
          <select v-model="form.project_type" class="input-field">
            <option v-for="type in allowedTypes" :key="type" :value="type">{{ type }}</option>
          </select>
        </div>
        <div>
          <label class="mb-1 block text-sm text-slate-400">{{ $t('procurement.fields.country') }}</label>
          <input v-model="form.country" class="input-field" />
        </div>
        <p v-if="createError" class="text-sm text-red-400">{{ createError }}</p>
        <div class="flex justify-end gap-2">
          <button type="button" class="btn-secondary" @click="showCreate = false">{{ $t('common.cancel') }}</button>
          <button type="submit" class="btn-primary" :disabled="creating">{{ $t('common.save') }}</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PortalPolicy, ProcurementProject } from '~/composables/useProcurement'

definePageMeta({
  layout: 'procurement',
  middleware: ['auth'],
})

const { t } = useI18n()
const procurement = useProcurement()
const policy = useState<PortalPolicy | null>('procurement-portal-policy', () => null)
const { brand, portalKey } = useProcurementBrand(policy)

const brandLabel = computed(() =>
  portalKey.value === 'cebu' ? t('procurement.brands.cebu') : t('procurement.brands.aislos'),
)

const projects = ref<ProcurementProject[]>([])
const loading = ref(true)
const error = ref('')
const showCreate = ref(false)
const creating = ref(false)
const createError = ref('')

const form = reactive({
  title: '',
  project_type: 'villa_smart_home',
  country: 'PH',
})

const allowedTypes = computed(
  () => policy.value?.allowed_project_types || ['villa_smart_home'],
)

async function load() {
  loading.value = true
  error.value = ''
  try {
    policy.value = await procurement.fetchPortalPolicy()
    const data = await procurement.listProjects()
    projects.value = data.items
    if (!form.project_type && allowedTypes.value.length) {
      form.project_type = allowedTypes.value[0]
    }
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Failed to load'
  } finally {
    loading.value = false
  }
}

async function createNew() {
  creating.value = true
  createError.value = ''
  try {
    const project = await procurement.createProject({ ...form })
    await navigateTo(`/procurement/projects/${project.id}`)
  } catch (e: any) {
    createError.value = e?.data?.detail || e?.message || 'Create failed'
  } finally {
    creating.value = false
  }
}

onMounted(load)
</script>
