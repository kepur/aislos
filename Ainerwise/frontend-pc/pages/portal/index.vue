<template>
  <div class="space-y-6">
    <div class="portal-card bg-gradient-to-r from-blue-500 to-indigo-600 !border-0 text-white">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-xl font-bold">Welcome back, {{ userName }}</h1>
          <p class="text-blue-100 text-sm mt-1">Track your smart building projects and requirements</p>
        </div>
        <NuxtLink to="/submit-requirement"
          class="hidden sm:inline-flex items-center gap-2 bg-white/20 hover:bg-white/30 text-white text-sm font-medium px-5 py-2.5 rounded-xl backdrop-blur-sm transition">
          + {{ $t('nav.submitRequirement') }}
        </NuxtLink>
      </div>
    </div>

    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div v-for="stat in statCards" :key="stat.label" class="portal-card">
        <div class="flex items-center gap-3">
          <div :class="['w-10 h-10 rounded-xl flex items-center justify-center text-lg', stat.bg]">
            {{ stat.emoji }}
          </div>
          <div>
            <p class="text-2xl font-bold text-slate-800">{{ stat.value }}</p>
            <p class="text-xs text-slate-400 font-medium">{{ stat.label }}</p>
          </div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="portal-card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-sm font-bold text-slate-800">Recent Requirements</h2>
          <NuxtLink to="/portal/leads" class="text-xs font-semibold text-blue-500 hover:text-blue-600">View All &rarr;</NuxtLink>
        </div>
        <div v-if="recentLeads.length" class="space-y-3">
          <NuxtLink
            v-for="lead in recentLeads"
            :key="lead.id"
            :to="`/portal/leads/${lead.id}`"
            class="flex items-center justify-between p-3 rounded-xl hover:bg-slate-50 border border-slate-100 transition group"
          >
            <div>
              <span class="text-sm font-medium text-slate-700 group-hover:text-blue-600 transition">{{ lead.project_type || 'Requirement' }}</span>
              <span class="block text-xs text-slate-400 mt-0.5">{{ new Date(lead.created_at).toLocaleDateString() }}</span>
            </div>
            <span :class="['text-xs font-semibold px-2.5 py-1 rounded-full', statusClass(lead.status)]">
              {{ lead.status }}
            </span>
          </NuxtLink>
        </div>
        <div v-else class="text-center py-8">
          <div class="text-3xl mb-2">📋</div>
          <p class="text-sm text-slate-400 mb-3">No requirements submitted yet</p>
          <NuxtLink to="/submit-requirement" class="inline-flex items-center text-sm font-semibold text-blue-500 hover:text-blue-600">
            Submit your first requirement &rarr;
          </NuxtLink>
        </div>
      </div>

      <div class="space-y-4">
        <div class="portal-card">
          <h2 class="text-sm font-bold text-slate-800 mb-4">Quick Actions</h2>
          <div class="grid grid-cols-2 gap-3">
            <NuxtLink to="/submit-requirement" class="flex items-center gap-3 p-3 rounded-xl border border-slate-100 hover:border-blue-200 hover:bg-blue-50/50 transition group">
              <span class="text-xl">📝</span>
              <span class="text-sm font-medium text-slate-600 group-hover:text-blue-600">New Requirement</span>
            </NuxtLink>
            <NuxtLink to="/portal/quotes" class="flex items-center gap-3 p-3 rounded-xl border border-slate-100 hover:border-blue-200 hover:bg-blue-50/50 transition group">
              <span class="text-xl">💰</span>
              <span class="text-sm font-medium text-slate-600 group-hover:text-blue-600">View Quotes</span>
            </NuxtLink>
            <NuxtLink to="/portal/projects" class="flex items-center gap-3 p-3 rounded-xl border border-slate-100 hover:border-blue-200 hover:bg-blue-50/50 transition group">
              <span class="text-xl">🏗️</span>
              <span class="text-sm font-medium text-slate-600 group-hover:text-blue-600">My Projects</span>
            </NuxtLink>
            <NuxtLink to="/portal/tickets" class="flex items-center gap-3 p-3 rounded-xl border border-slate-100 hover:border-blue-200 hover:bg-blue-50/50 transition group">
              <span class="text-xl">🎫</span>
              <span class="text-sm font-medium text-slate-600 group-hover:text-blue-600">Support</span>
            </NuxtLink>
          </div>
        </div>

        <div class="portal-card">
          <h2 class="text-sm font-bold text-slate-800 mb-4">Project Progress</h2>
          <div v-if="stats.projects > 0" class="space-y-3">
            <div class="flex items-center justify-between text-sm">
              <span class="text-slate-500">Active projects</span>
              <span class="font-semibold text-slate-700">{{ stats.projects }}</span>
            </div>
            <div class="w-full bg-slate-100 rounded-full h-2">
              <div class="bg-gradient-to-r from-blue-500 to-indigo-500 h-2 rounded-full transition-all" style="width: 45%"></div>
            </div>
            <p class="text-xs text-slate-400">Overall completion estimate</p>
          </div>
          <div v-else class="text-center py-4">
            <p class="text-sm text-slate-400">No active projects yet</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'portal', middleware: 'auth' })

const { user } = useAuth()
const { apiFetch } = useApi()
const stats = reactive({ leads: 0, quotes: 0, projects: 0, tickets: 0 })
const recentLeads = ref<any[]>([])

const userName = computed(() => {
  if (user.value?.full_name) return user.value.full_name.split(' ')[0]
  return 'User'
})

const statCards = computed(() => [
  { label: 'Requirements', value: stats.leads, emoji: '📋', bg: 'bg-blue-50' },
  { label: 'Quotes', value: stats.quotes, emoji: '💰', bg: 'bg-emerald-50' },
  { label: 'Projects', value: stats.projects, emoji: '🏗️', bg: 'bg-indigo-50' },
  { label: 'Tickets', value: stats.tickets, emoji: '🎫', bg: 'bg-amber-50' },
])

function statusClass(status: string) {
  const map: Record<string, string> = {
    new: 'bg-blue-50 text-blue-600',
    in_progress: 'bg-amber-50 text-amber-600',
    qualified: 'bg-emerald-50 text-emerald-600',
    completed: 'bg-green-50 text-green-600',
    rejected: 'bg-red-50 text-red-600',
  }
  return map[status] || 'bg-slate-50 text-slate-600'
}

onMounted(async () => {
  try {
    const [leadsRes, quotesRes, projectsRes, ticketsRes] = await Promise.allSettled([
      apiFetch<any>('/leads/my?limit=5'),
      apiFetch<any>('/quotes/my?limit=5'),
      apiFetch<any>('/projects/my?limit=5'),
      apiFetch<any>('/tickets/my?limit=5'),
    ])
    if (leadsRes.status === 'fulfilled') {
      const data = leadsRes.value
      stats.leads = data.total || 0
      recentLeads.value = data.items || []
    }
    if (quotesRes.status === 'fulfilled') stats.quotes = quotesRes.value.total || 0
    if (projectsRes.status === 'fulfilled') stats.projects = projectsRes.value.total || 0
    if (ticketsRes.status === 'fulfilled') stats.tickets = ticketsRes.value.total || 0
  } catch {}
})
</script>
