<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-slate-800">{{ $t('portal.myLeads') }}</h1>
        <p class="text-sm text-slate-400 mt-1">Track your submitted requirements</p>
      </div>
      <NuxtLink to="/submit-requirement"
        class="inline-flex items-center gap-2 text-sm font-medium text-white bg-gradient-to-r from-blue-500 to-indigo-500 px-5 py-2.5 rounded-xl hover:shadow-lg hover:shadow-blue-500/20 transition-all">
        + New Requirement
      </NuxtLink>
    </div>

    <div class="portal-card p-0 overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="bg-slate-50/80 border-b border-slate-100">
            <th class="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Project Type</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Country</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Budget</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">{{ $t('common.status') }}</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Submitted</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="lead in leads" :key="lead.id"
              class="border-b border-slate-50 hover:bg-blue-50/30 cursor-pointer transition-colors"
              @click="navigateTo(`/portal/leads/${lead.id}`)">
            <td class="px-4 py-3 font-medium text-slate-700">{{ lead.project_type || '-' }}</td>
            <td class="px-4 py-3 text-slate-500">{{ lead.country || '-' }}</td>
            <td class="px-4 py-3 text-slate-500">{{ lead.budget_range || '-' }}</td>
            <td class="px-4 py-3">
              <span :class="['text-xs font-semibold px-2.5 py-1 rounded-full', statusClass(lead.status)]">{{ lead.status }}</span>
            </td>
            <td class="px-4 py-3 text-slate-400 text-xs">{{ new Date(lead.created_at).toLocaleDateString() }}</td>
          </tr>
          <tr v-if="!leads.length">
            <td colspan="5" class="px-4 py-12 text-center">
              <div class="text-3xl mb-2">📋</div>
              <p class="text-slate-400 text-sm">{{ $t('common.noData') }}</p>
              <NuxtLink to="/submit-requirement" class="inline-block mt-2 text-sm font-semibold text-blue-500 hover:text-blue-600">Submit your first requirement &rarr;</NuxtLink>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'portal', middleware: 'auth' })

const { apiFetch } = useApi()
const leads = ref<any[]>([])

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
    const res = await apiFetch<any>('/leads/my')
    leads.value = res.items || []
  } catch {}
})
</script>
