<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold ws-title">{{ $t('portal.myLeads') }}</h1>
        <p class="text-sm ws-faint mt-1">Track your submitted requirements</p>
      </div>
      <NuxtLink to="/submit-requirement"
 class="inline-flex items-center gap-2 text-sm font-medium text-white bg-gradient-to-r from-blue-500 to-indigo-500 px-5 py-2.5 rounded-xl hover:shadow-lg hover:shadow-blue-500/20 transition-all">
        + New Requirement
      </NuxtLink>
    </div>

    <div v-if="error" class="portal-card border-red-200 bg-red-50 text-sm text-red-700">
      {{ error }} <button class="ml-2 font-semibold underline" @click="loadData">Retry</button>
    </div>
    <div class="portal-card p-0 overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="ws-sunken/80 border-b ws-hairline">
            <th class="text-left px-4 py-3 text-xs font-semibold ws-faint uppercase tracking-wider">Project Type</th>
            <th class="text-left px-4 py-3 text-xs font-semibold ws-faint uppercase tracking-wider">Country</th>
            <th class="text-left px-4 py-3 text-xs font-semibold ws-faint uppercase tracking-wider">Budget</th>
            <th class="text-left px-4 py-3 text-xs font-semibold ws-faint uppercase tracking-wider">{{ $t('common.status') }}</th>
            <th class="text-left px-4 py-3 text-xs font-semibold ws-faint uppercase tracking-wider">Submitted</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="lead in paged" :key="lead.id"
 class="border-b border-slate-50 hover:bg-blue-50/30 cursor-pointer transition-colors"
              @click="navigateTo(`/portal/leads/${lead.id}`)">
            <td class="px-4 py-3 font-medium ws-title">{{ lead.project_type || '-' }}</td>
            <td class="px-4 py-3 ws-muted">{{ lead.country || '-' }}</td>
            <td class="px-4 py-3 ws-muted">{{ lead.budget_range || '-' }}</td>
            <td class="px-4 py-3">
              <span :class="['text-xs font-semibold px-2.5 py-1 rounded-full', statusClass(lead.status)]">{{ lead.status }}</span>
            </td>
            <td class="px-4 py-3 ws-faint text-xs">{{ new Date(lead.created_at).toLocaleDateString() }}</td>
          </tr>
          <tr v-if="loading && !leads.length">
            <td colspan="5" class="px-4 py-12 text-center text-sm ws-faint">Loading requirements...</td>
          </tr>
          <tr v-else-if="!leads.length">
            <td colspan="5" class="px-4 py-12 text-center">
              <div class="text-3xl mb-2">📋</div>
              <p class="ws-faint text-sm">{{ $t('common.noData') }}</p>
              <NuxtLink to="/submit-requirement" class="inline-block mt-2 text-sm font-semibold ws-accent hover:opacity-80">Submit your first requirement &rarr;</NuxtLink>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
      <WorkspacePagination v-model:page="page" :page-size="pageSize" :total="leads.length" />

  </div>
</template>

<script setup lang="ts">

definePageMeta({ layout: 'procurement', middleware: 'auth' })

const { apiFetch } = useApi()
const leads = ref<any[]>([])

// Client-side paging: these lists already hold the full filtered set, so the
// pager slices it rather than adding a round trip per page.
const page = ref(1)
const pageSize = 20
const paged = computed(() => leads.value.slice((page.value - 1) * pageSize, page.value * pageSize))
watch(() => leads.value.length, () => { page.value = 1 })

const loading = ref(true)
const error = ref('')

function statusClass(status: string) {
 const map: Record<string, string> = {
 new: 'bg-blue-500/15 ws-accent dark:text-blue-300',
 in_progress: 'bg-amber-500/15 text-amber-700 dark:text-amber-300',
 qualified: 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300',
 completed: 'bg-green-500/15 text-green-700 dark:text-green-300',
 rejected: 'bg-red-500/15 text-red-600 dark:text-red-300',
  }
 return map[status] || 'ws-soft ws-muted'
}

async function loadData() {
 loading.value = true
 error.value = ''
 try {
 const res = await apiFetch<any>('/leads/my')
 leads.value = res.items || []
  } catch (e: any) {
 leads.value = []
 error.value = e?.data?.detail || e?.message || 'Unable to load requirements.'
  } finally {
 loading.value = false
  }
}

onMounted(loadData)
</script>
