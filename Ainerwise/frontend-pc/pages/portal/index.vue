<template>
  <div class="space-y-6">
    <!-- Hero. Deliberately not .portal-card: that class sets `background`,
 which wins over Tailwind's gradient background-image and left the
 white-on-white banner this page used to render. -->
    <section class="workspace-hero relative overflow-hidden rounded-2xl px-6 py-7 text-white lg:px-8">
      <div class="pointer-events-none absolute inset-0">
        <div class="absolute -right-16 -top-24 h-64 w-64 rounded-full bg-white/15 blur-3xl"></div>
        <div class="absolute -bottom-24 left-1/3 h-56 w-56 rounded-full bg-indigo-300/20 blur-3xl"></div>
      </div>
      <div class="relative flex flex-wrap items-center justify-between gap-6">
        <div class="min-w-0">
          <p class="text-xs font-bold uppercase tracking-[0.2em] text-blue-100">{{ $t('portal.home.eyebrow') }}</p>
          <h1 class="mt-2 text-2xl font-bold lg:text-3xl">{{ $t('portal.home.welcome', { name: userName }) }}</h1>
          <p class="mt-2 max-w-xl text-sm leading-6 text-blue-100">{{ $t('portal.home.subtitle') }}</p>
        </div>
        <div class="flex flex-col gap-3 sm:flex-row sm:items-center">
          <NuxtLink
 :to="localized('/submit-requirement')"
 class="inline-flex items-center justify-center gap-2 rounded-xl bg-white px-5 py-2.5 text-sm font-semibold text-blue-700 shadow-lg transition hover:bg-blue-50"
          >
            + {{ $t('nav.submitRequirement') }}
          </NuxtLink>
          <NuxtLink
 :to="localized('/portal/procurement')"
 class="inline-flex items-center justify-center gap-2 rounded-xl border border-white/40 px-5 py-2.5 text-sm font-semibold text-white backdrop-blur-sm transition hover:bg-white/15"
          >
            {{ $t('portal.home.goProcurement') }}
          </NuxtLink>
        </div>
      </div>
    </section>

    <div v-if="loadError" class="portal-card border-red-200 bg-red-50 text-sm text-red-700">
      {{ loadError }}
      <button class="ml-2 font-semibold underline" @click="loadDashboard">{{ $t('portal.home.retry') }}</button>
    </div>

    <!-- KPIs -->
    <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
      <NuxtLink
 v-for="stat in statCards"
        :key="stat.label"
        :to="localized(stat.to)"
 class="portal-card group !p-5 transition hover:-translate-y-0.5 hover:shadow-lg"
      >
        <div class="flex items-center gap-3">
          <div :class="['flex h-10 w-10 items-center justify-center rounded-xl text-lg', stat.bg]">{{ stat.emoji }}</div>
          <div class="min-w-0">
            <p class="text-2xl font-bold ws-title">{{ loading ? '…' : stat.value }}</p>
            <p class="truncate text-xs font-medium ws-faint">{{ stat.label }}</p>
          </div>
        </div>
        <p class="mt-3 text-xs ws-faint group-hover:ws-accent">{{ stat.hint }} &rarr;</p>
      </NuxtLink>
    </div>

    <div class="grid grid-cols-1 gap-6 lg:grid-cols-3 lg:items-start">
      <!-- Recent requirements -->
      <div class="portal-card lg:col-span-2">
        <div class="mb-4 flex items-center justify-between">
          <h2 class="text-sm font-bold ws-title">{{ $t('portal.home.recentRequirements') }}</h2>
          <NuxtLink :to="localized('/portal/leads')" class="text-xs font-semibold ws-accent hover:opacity-80">
            {{ $t('portal.home.viewAll') }} &rarr;
          </NuxtLink>
        </div>
        <div v-if="loading" class="py-8 text-center text-sm ws-faint">{{ $t('portal.home.loading') }}</div>
        <div v-else-if="recentLeads.length" class="space-y-3">
          <NuxtLink
 v-for="lead in recentLeads"
            :key="lead.id"
            :to="localized(`/portal/leads/${lead.id}`)"
 class="group flex items-center justify-between rounded-xl border ws-hairline p-3 transition hover:border-[color:var(--accent)] hover:bg-blue-50/40"
          >
            <div class="min-w-0">
              <span class="text-sm font-medium ws-title transition group-hover:opacity-80">
                {{ lead.project_type || $t('portal.home.requirement') }}
              </span>
              <span class="mt-0.5 block text-xs ws-faint">
                {{ formatDate(lead.created_at) }}
                <template v-if="lead.budget_range"> · {{ lead.budget_range }}</template>
              </span>
            </div>
            <span :class="['shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold', statusClass(lead.status)]">
              {{ lead.status }}
            </span>
          </NuxtLink>
        </div>
        <div v-else class="py-8 text-center">
          <div class="mb-2 text-3xl">📋</div>
          <p class="mb-3 text-sm ws-faint">{{ $t('portal.home.noRequirements') }}</p>
          <NuxtLink :to="localized('/submit-requirement')" class="inline-flex items-center text-sm font-semibold ws-accent hover:opacity-80">
            {{ $t('portal.home.submitFirst') }} &rarr;
          </NuxtLink>
        </div>
      </div>

      <div class="space-y-6">
        <!-- Projects in delivery -->
        <div class="portal-card">
          <div class="mb-4 flex items-center justify-between">
            <h2 class="text-sm font-bold ws-title">{{ $t('portal.home.inDelivery') }}</h2>
            <NuxtLink :to="localized('/portal/projects')" class="text-xs font-semibold ws-accent hover:opacity-80">
              {{ $t('portal.home.viewAll') }} &rarr;
            </NuxtLink>
          </div>
          <div v-if="recentProjects.length" class="space-y-3">
            <NuxtLink
 v-for="project in recentProjects"
              :key="project.id"
              :to="localized(`/portal/projects/${project.id}`)"
 class="group block rounded-xl border ws-hairline p-3 transition hover:border-[color:var(--accent)] hover:bg-blue-50/40"
            >
              <div class="flex items-center justify-between gap-2">
                <p class="truncate text-sm font-medium ws-title group-hover:opacity-80">
                  {{ project.name || project.title || $t('portal.home.project') }}
                </p>
                <span class="shrink-0 text-xs font-semibold ws-faint">{{ projectPercent(project) }}%</span>
              </div>
              <div class="mt-2 h-1.5 overflow-hidden rounded-full ws-soft">
                <div class="h-full rounded-full bg-gradient-to-r from-blue-500 to-indigo-500" :style="{ width: `${projectPercent(project)}%` }"></div>
              </div>
              <p class="mt-2 text-xs ws-faint">{{ project.status || $t('portal.home.inProgress') }}</p>
            </NuxtLink>
          </div>
          <p v-else class="py-4 text-center text-sm ws-faint">{{ $t('portal.home.noProjects') }}</p>
        </div>

        <!-- Open tickets -->
        <div class="portal-card">
          <div class="mb-4 flex items-center justify-between">
            <h2 class="text-sm font-bold ws-title">{{ $t('portal.home.support') }}</h2>
            <NuxtLink :to="localized('/portal/tickets')" class="text-xs font-semibold ws-accent hover:opacity-80">
              {{ $t('portal.home.viewAll') }} &rarr;
            </NuxtLink>
          </div>
          <ul v-if="recentTickets.length" class="divide-y ws-divide">
            <li v-for="ticket in recentTickets" :key="ticket.id" class="flex items-start gap-3 py-2.5">
              <div class="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-amber-50 text-xs">🎫</div>
              <div class="min-w-0">
                <p class="truncate text-sm font-medium ws-title">{{ ticket.subject || ticket.title || $t('portal.home.ticket') }}</p>
                <p class="truncate text-xs ws-faint">{{ ticket.status || '—' }}</p>
              </div>
            </li>
          </ul>
          <p v-else class="py-4 text-center text-sm ws-faint">{{ $t('portal.home.noTickets') }}</p>
        </div>
      </div>
    </div>

    <!-- Quick actions, full width so the row below the fold is not empty -->
    <div class="portal-card">
      <h2 class="mb-4 text-sm font-bold ws-title">{{ $t('portal.home.quickActions') }}</h2>
      <div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <NuxtLink
 v-for="action in quickActions"
          :key="action.to"
          :to="localized(action.to)"
 class="group flex items-center gap-3 rounded-xl border ws-hairline p-3.5 transition hover:border-[color:var(--accent)] hover:bg-blue-50/50"
        >
          <span class="text-xl">{{ action.emoji }}</span>
          <div class="min-w-0">
            <p class="truncate text-sm font-medium ws-muted group-hover:opacity-80">{{ action.label }}</p>
            <p class="truncate text-xs ws-faint">{{ action.hint }}</p>
          </div>
        </NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()
definePageMeta({ layout: 'procurement', middleware: 'auth' })

const { t } = useI18n()
const { user } = useAuth()
const { apiFetch } = useApi()
const stats = reactive({ leads: 0, quotes: 0, projects: 0, tickets: 0 })
const recentLeads = ref<any[]>([])
const recentProjects = ref<any[]>([])
const recentTickets = ref<any[]>([])
const loading = ref(true)
const loadError = ref('')

const userName = computed(() => {
 if (user.value?.full_name) return user.value.full_name.split(' ')[0]
 return t('portal.home.fallbackName')
})

const statCards = computed(() => [
  { label: t('portal.home.kpiRequirements'), value: stats.leads, emoji: '📋', bg: 'bg-blue-50', to: '/portal/leads', hint: t('portal.home.kpiRequirementsHint') },
  { label: t('portal.home.kpiQuotes'), value: stats.quotes, emoji: '💰', bg: 'bg-emerald-50', to: '/portal/quotes', hint: t('portal.home.kpiQuotesHint') },
  { label: t('portal.home.kpiProjects'), value: stats.projects, emoji: '🏗️', bg: 'bg-indigo-50', to: '/portal/projects', hint: t('portal.home.kpiProjectsHint') },
  { label: t('portal.home.kpiTickets'), value: stats.tickets, emoji: '🎫', bg: 'bg-amber-50', to: '/portal/tickets', hint: t('portal.home.kpiTicketsHint') },
])

const quickActions = computed(() => [
  { to: '/submit-requirement', emoji: '📝', label: t('portal.home.actionNewRequirement'), hint: t('portal.home.actionNewRequirementHint') },
  { to: '/portal/approvals', emoji: '✅', label: t('portal.home.actionApprovals'), hint: t('portal.home.actionApprovalsHint') },
  { to: '/portal/assets', emoji: '🧰', label: t('portal.home.actionAssets'), hint: t('portal.home.actionAssetsHint') },
  { to: '/portal/installations', emoji: '🔧', label: t('portal.home.actionInstallations'), hint: t('portal.home.actionInstallationsHint') },
])

function statusClass(status: string) {
 const map: Record<string, string> = {
 new: 'bg-blue-500/15 ws-accent dark:text-blue-300',
 in_progress: 'bg-amber-500/15 text-amber-700 dark:text-amber-300',
 matched: 'bg-indigo-500/15 text-indigo-600 dark:text-indigo-300',
 qualified: 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300',
 completed: 'bg-green-500/15 text-green-700 dark:text-green-300',
 rejected: 'bg-red-500/15 text-red-600 dark:text-red-300',
  }
 return map[status] || 'ws-soft ws-muted'
}

function formatDate(value?: string) {
 if (!value) return '—'
 const parsed = new Date(value)
 return Number.isNaN(parsed.getTime()) ? '—' : parsed.toLocaleDateString()
}

// Projects expose progress under a few different field names depending on how
// far through delivery they are; fall back to a status-derived estimate.
function projectPercent(project: any) {
 const raw = project.progress_percent ?? project.progress ?? project.completion_percent
 if (raw != null && !Number.isNaN(Number(raw))) return Math.max(0, Math.min(100, Math.round(Number(raw))))
 const status = String(project.status || '').toLowerCase()
 if (status.includes('complete') || status.includes('closed')) return 100
 if (status.includes('install') || status.includes('deliver')) return 70
 if (status.includes('progress') || status.includes('active')) return 45
 return 15
}

async function loadDashboard() {
 loading.value = true
 loadError.value = ''
 const results = await Promise.allSettled([
 apiFetch<any>('/leads/my?limit=5'),
 apiFetch<any>('/quotes/my?limit=5'),
 apiFetch<any>('/projects/my?limit=5'),
 apiFetch<any>('/tickets/my?limit=5'),
  ])
 const [leadsRes, quotesRes, projectsRes, ticketsRes] = results
 if (leadsRes.status === 'fulfilled') {
 stats.leads = leadsRes.value.total || 0
 recentLeads.value = leadsRes.value.items || []
  } else {
 stats.leads = 0
 recentLeads.value = []
  }
 stats.quotes = quotesRes.status === 'fulfilled' ? quotesRes.value.total || 0 : 0
 if (projectsRes.status === 'fulfilled') {
 stats.projects = projectsRes.value.total || 0
 recentProjects.value = (projectsRes.value.items || []).slice(0, 3)
  }
 if (ticketsRes.status === 'fulfilled') {
 stats.tickets = ticketsRes.value.total || 0
 recentTickets.value = (ticketsRes.value.items || []).slice(0, 4)
  }
 const failed = results.filter(result => result.status === 'rejected').length
 if (failed) loadError.value = t('portal.home.partialError', { count: failed })
 loading.value = false
}

onMounted(loadDashboard)
</script>

<style scoped>
.workspace-hero {
 background: linear-gradient(120deg, #2563eb 0%, #4f46e5 55%, #6366f1 100%);
 box-shadow: 0 16px 40px rgba(37, 99, 235, 0.22);
}
</style>
