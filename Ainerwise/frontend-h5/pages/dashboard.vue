<template>
  <div class="px-4 py-4">
    <div v-if="!isLoggedIn" class="text-center py-16">
      <div class="text-4xl mb-3">📊</div>
      <p class="text-sm text-slate-500">{{ $t('dash.loginRequired') }}</p>
      <NuxtLink to="/login?redirect=/dashboard" class="inline-block mt-4 text-sm font-semibold bg-blue-500 text-white px-8 py-3 rounded-full">{{ $t('nav.login') }}</NuxtLink>
    </div>

    <template v-else>
      <div class="flex items-end justify-between gap-2 mb-3">
        <div>
          <h1 class="text-lg font-bold text-slate-800">{{ $t('dash.title') }}</h1>
          <p class="text-xs text-slate-400">{{ $t('dash.subtitle') }}</p>
        </div>
      </div>

      <!-- Stat cards -->
      <div class="grid grid-cols-4 gap-2 mb-4">
        <NuxtLink to="/projects" class="bg-white rounded-2xl p-3 text-center border border-slate-100 shadow-sm active:bg-slate-50">
          <p class="text-xl font-bold text-blue-600">{{ stats.projects }}</p>
          <p class="text-[10px] text-slate-400 font-medium">{{ $t('dash.projects') }}</p>
        </NuxtLink>
        <div class="bg-white rounded-2xl p-3 text-center border border-slate-100 shadow-sm">
          <p class="text-xl font-bold text-slate-800">{{ stats.leads }}</p>
          <p class="text-[10px] text-slate-400 font-medium">{{ $t('dash.leads') }}</p>
        </div>
        <div class="bg-white rounded-2xl p-3 text-center border border-slate-100 shadow-sm">
          <p class="text-xl font-bold text-emerald-600">{{ stats.quotes }}</p>
          <p class="text-[10px] text-slate-400 font-medium">{{ $t('dash.quotes') }}</p>
        </div>
        <div class="bg-white rounded-2xl p-3 text-center border border-slate-100 shadow-sm">
          <p class="text-xl font-bold text-amber-600">{{ stats.tickets }}</p>
          <p class="text-[10px] text-slate-400 font-medium">{{ $t('dash.tickets') }}</p>
        </div>
      </div>

      <NuxtLink to="/submit-requirement" class="block text-center text-sm font-semibold bg-gradient-to-r from-blue-500 to-indigo-500 text-white py-3 rounded-2xl shadow-md shadow-blue-500/20 mb-4">
        {{ $t('dash.newAssessment') }}
      </NuxtLink>

      <!-- Recent Projects -->
      <Section :title="$t('dash.recentProjects')" to="/projects" :empty="!projects.length">
        <NuxtLink v-for="p in projects.slice(0, 3)" :key="p.id" :to="`/projects/${p.id}`" class="block rounded-xl bg-slate-50 p-3 active:bg-slate-100">
          <div class="flex items-center justify-between gap-2">
            <p class="text-xs font-semibold text-slate-700 truncate">{{ p.title }}</p>
            <span :class="['text-[10px] font-semibold px-2 py-0.5 rounded-full flex-shrink-0', statusClass(p.status)]">{{ (p.status || '').replace(/_/g,' ') }}</span>
          </div>
        </NuxtLink>
      </Section>

      <!-- Recent Leads -->
      <Section :title="$t('dash.recentLeads')" :empty="!leads.length">
        <div v-for="l in leads.slice(0, 3)" :key="l.id" class="rounded-xl bg-slate-50 p-3">
          <div class="flex items-center justify-between gap-2">
            <p class="text-xs font-semibold text-slate-700 truncate">{{ l.project_type || '—' }}</p>
            <span :class="['text-[10px] font-semibold px-2 py-0.5 rounded-full flex-shrink-0', statusClass(l.status)]">{{ (l.status || '').replace(/_/g,' ') }}</span>
          </div>
          <p v-if="l.solution_line" class="mt-0.5 text-[11px] text-slate-400">{{ l.solution_line }}<template v-if="l.estimated_arr"> · ARR €{{ Math.round(l.estimated_arr).toLocaleString() }}</template></p>
        </div>
      </Section>

      <!-- Quotes -->
      <Section :title="$t('dash.myQuotes')" :empty="!quotes.length">
        <div v-for="q in quotes.slice(0, 3)" :key="q.id" class="rounded-xl bg-slate-50 p-3 flex items-center justify-between gap-2">
          <p class="text-xs font-semibold text-slate-700">{{ q.currency || 'EUR' }} {{ Number(q.total || 0).toLocaleString() }}</p>
          <span :class="['text-[10px] font-semibold px-2 py-0.5 rounded-full', statusClass(q.status)]">{{ (q.status || '').replace(/_/g,' ') }}</span>
        </div>
      </Section>

      <!-- Tickets -->
      <Section :title="$t('dash.myTickets')" :empty="!tickets.length">
        <div v-for="tk in tickets.slice(0, 3)" :key="tk.id" class="rounded-xl bg-slate-50 p-3">
          <div class="flex items-center justify-between gap-2">
            <p class="text-xs font-semibold text-slate-700 truncate">{{ tk.title }}</p>
            <span :class="['text-[10px] font-semibold px-2 py-0.5 rounded-full flex-shrink-0', statusClass(tk.status)]">{{ (tk.status || '').replace(/_/g,' ') }}</span>
          </div>
        </div>
      </Section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { h } from 'vue'
definePageMeta({ middleware: 'auth' })

const { isLoggedIn } = useAuth()
const { apiFetch } = useApi()

const projects = ref<any[]>([])
const leads = ref<any[]>([])
const quotes = ref<any[]>([])
const tickets = ref<any[]>([])
const stats = reactive({ projects: 0, leads: 0, quotes: 0, tickets: 0 })

function statusClass(status: string) {
  if (['closed', 'handover', 'resolved', 'accepted', 'won', 'converted'].includes(status)) return 'bg-emerald-50 text-emerald-600'
  if (['planning', 'site_survey', 'open', 'new', 'draft'].includes(status)) return 'bg-blue-50 text-blue-600'
  return 'bg-amber-50 text-amber-600'
}

// Tiny section wrapper component (title + "view all" + empty state).
const { t } = useI18n({ useScope: 'global' })
const Section = (props: any, { slots }: any) => h('div', { class: 'bg-white rounded-2xl p-4 border border-slate-100 shadow-sm mb-3' }, [
  h('div', { class: 'flex items-center justify-between mb-2' }, [
    h('h2', { class: 'text-sm font-bold text-slate-800' }, props.title),
    props.to ? h(resolveComponent('NuxtLink'), { to: props.to, class: 'text-[11px] text-blue-500 font-medium' }, () => t('dash.viewAll')) : null,
  ]),
  props.empty ? h('p', { class: 'text-[11px] text-slate-400 py-2' }, t('dash.none')) : h('div', { class: 'space-y-2' }, slots.default?.()),
])

onMounted(async () => {
  if (!isLoggedIn.value) return
  const [p, l, q, tk] = await Promise.allSettled([
    apiFetch<any>('/projects/my'),
    apiFetch<any>('/leads/my'),
    apiFetch<any>('/quotes/my'),
    apiFetch<any>('/tickets/my'),
  ])
  const items = (r: any) => (r.status === 'fulfilled' ? (r.value.items || []) : [])
  const total = (r: any, arr: any[]) => (r.status === 'fulfilled' ? (r.value.total ?? arr.length) : 0)
  projects.value = items(p); stats.projects = total(p, projects.value)
  leads.value = items(l); stats.leads = total(l, leads.value)
  quotes.value = items(q); stats.quotes = total(q, quotes.value)
  tickets.value = items(tk); stats.tickets = total(tk, tickets.value)
})
</script>
