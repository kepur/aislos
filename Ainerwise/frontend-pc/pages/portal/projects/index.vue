<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-xl font-bold ws-title">{{ $t('portal.myProjects') }}</h1>
      <p class="text-sm ws-faint mt-1">{{ $t('pProj.subtitle') }}</p>
    </div>

    <div v-if="projects.length" class="space-y-4">
      <div
 v-for="project in paged"
        :key="project.id"
 class="portal-card hover:shadow-md cursor-pointer transition-all group"
        @click="$router.push(`/portal/projects/${project.id}`)"
      >
        <div class="flex items-start justify-between gap-4">
          <div>
            <h3 class="font-semibold ws-title group-hover:opacity-80 transition">{{ project.title }}</h3>
            <p class="text-sm ws-faint mt-1">{{ project.region || '-' }}</p>
          </div>
          <span :class="['text-xs font-semibold px-2.5 py-1 rounded-full', statusClass(project.status)]">
            {{ project.status?.replace(/_/g, ' ') }}
          </span>
        </div>

        <div class="mt-4">
          <div class="flex items-center gap-0.5">
            <div
 v-for="(step, i) in statusSteps"
              :key="step.key"
 class="h-1.5 flex-1 rounded-full transition-colors"
              :class="getStepIndex(project.status) >= i ? 'bg-gradient-to-r from-blue-500 to-indigo-500' : 'ws-soft'"
            />
          </div>
          <div class="flex justify-between mt-1.5 text-[10px] ws-faint font-medium uppercase tracking-wider">
            <span>{{ $t('pProj.planning') }}</span>
            <span>{{ $t('pProj.delivery') }}</span>
            <span>{{ $t('pProj.closed') }}</span>
          </div>
        </div>

        <div class="mt-3 flex flex-wrap items-center gap-4 text-xs ws-faint">
          <span v-if="project.start_date">{{ $t('pProj.start') }}: {{ project.start_date }}</span>
          <span v-if="project.expected_delivery_date">{{ $t('pProj.deliveryLabel') }}: {{ project.expected_delivery_date }}</span>
          <span>{{ $t('pProj.created') }}: {{ formatDay(project.created_at) }}</span>
        </div>
      </div>
    </div>

    <div v-else class="portal-card text-center py-12">
      <div class="text-4xl mb-3">🏗️</div>
      <p class="text-sm ws-faint">{{ loading ? $t('pProj.loading') : $t('pProj.noProjects') }}</p>
      <p v-if="!loading" class="text-xs ws-faint mt-1">{{ $t('pProj.projectsHint') }}</p>
    </div>
      <WorkspacePagination v-model:page="page" :page-size="pageSize" :total="projects.length" />

  </div>
</template>

<script setup lang="ts">

definePageMeta({ layout: 'procurement', middleware: 'auth' })

const { t } = useI18n()
const { formatDay } = useLocaleFormat()
const { apiFetch } = useApi()
const projects = ref<any[]>([])

// Client-side paging: these lists already hold the full filtered set, so the
// pager slices it rather than adding a round trip per page.
const page = ref(1)
const pageSize = 20
const paged = computed(() => projects.value.slice((page.value - 1) * pageSize, page.value * pageSize))
watch(() => projects.value.length, () => { page.value = 1 })

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
 if (['closed', 'handover'].includes(status)) return 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
 if (['planning', 'site_survey'].includes(status)) return 'bg-blue-500/15 ws-accent dark:text-blue-300'
 return 'bg-amber-500/15 text-amber-700 dark:text-amber-300'
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
