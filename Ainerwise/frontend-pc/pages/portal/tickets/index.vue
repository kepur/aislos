<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold ws-title">{{ $t('portal.myTickets') }}</h1>
        <p class="text-sm ws-faint mt-1">{{ $t('pTickets.subtitle') }}</p>
      </div>
      <button @click="showCreateModal = true"
 class="inline-flex items-center gap-2 text-sm font-medium text-white bg-gradient-to-r from-blue-500 to-indigo-500 px-5 py-2.5 rounded-xl hover:shadow-lg hover:shadow-blue-500/20 transition-all">
        {{ $t('pTickets.create') }}
      </button>
    </div>

    <div v-if="error" class="portal-card border-red-200 bg-red-50 text-sm text-red-700">
      {{ error }} <button class="ml-2 font-semibold underline" @click="loadData">{{ $t('common.retry') }}</button>
    </div>
    <div class="portal-card p-0 overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="ws-sunken/80 border-b ws-hairline">
            <th class="text-left px-4 py-3 text-xs font-semibold ws-faint uppercase tracking-wider">{{ $t('pTickets.colTitle') }}</th>
            <th class="text-left px-4 py-3 text-xs font-semibold ws-faint uppercase tracking-wider">{{ $t('pTickets.colType') }}</th>
            <th class="text-left px-4 py-3 text-xs font-semibold ws-faint uppercase tracking-wider">{{ $t('pTickets.colPriority') }}</th>
            <th class="text-left px-4 py-3 text-xs font-semibold ws-faint uppercase tracking-wider">{{ $t('common.status') }}</th>
            <th class="text-left px-4 py-3 text-xs font-semibold ws-faint uppercase tracking-wider">{{ $t('pTickets.colCreated') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="ticket in paged" :key="ticket.id" class="border-b border-slate-50 hover:bg-blue-50/30 transition-colors">
            <td class="px-4 py-3 font-medium ws-title">{{ ticket.title }}</td>
            <td class="px-4 py-3 ws-muted">{{ ticket.issue_type || '-' }}</td>
            <td class="px-4 py-3">
              <span :class="['text-xs font-semibold px-2.5 py-1 rounded-full', priorityClass(ticket.priority)]">{{ ticket.priority }}</span>
            </td>
            <td class="px-4 py-3">
              <span :class="['text-xs font-semibold px-2.5 py-1 rounded-full', statusClass(ticket.status)]">{{ ticket.status }}</span>
            </td>
            <td class="px-4 py-3 ws-faint text-xs">{{ formatDay(ticket.created_at) }}</td>
          </tr>
          <tr v-if="loading && !tickets.length">
            <td colspan="5" class="px-4 py-12 text-center text-sm ws-faint">{{ $t('pTickets.loading') }}</td>
          </tr>
          <tr v-else-if="!tickets.length">
            <td colspan="5" class="px-4 py-12 text-center">
              <div class="text-3xl mb-2">🎫</div>
              <p class="text-sm ws-faint">{{ $t('common.noData') }}</p>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <Transition name="modal">
      <div v-if="showCreateModal" class="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4">
        <div class=" rounded-2xl shadow-2xl w-full max-w-lg p-6 space-y-5">
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-bold ws-title">{{ $t('pTickets.modalTitle') }}</h2>
            <button @click="showCreateModal = false" class="ws-faint hover:ws-muted p-1">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <form @submit.prevent="handleCreate" class="space-y-4">
            <div>
              <label class="block text-xs font-semibold ws-muted mb-1.5 uppercase tracking-wider">{{ $t('pTickets.titleLabel') }}</label>
              <input v-model="form.title" type="text" required class="portal-input" :placeholder="$t('pTickets.titlePh')" />
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-semibold ws-muted mb-1.5 uppercase tracking-wider">{{ $t('pTickets.issueType') }}</label>
                <select v-model="form.issue_type" class="portal-input">
                  <option value="">{{ $t('pTickets.selectType') }}</option>
                  <option value="technical">{{ $t('pTickets.typeTechnical') }}</option>
                  <option value="billing">{{ $t('pTickets.typeBilling') }}</option>
                  <option value="product">{{ $t('pTickets.typeProduct') }}</option>
                  <option value="service">{{ $t('pTickets.typeService') }}</option>
                  <option value="other">{{ $t('pTickets.typeOther') }}</option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-semibold ws-muted mb-1.5 uppercase tracking-wider">{{ $t('pTickets.colPriority') }}</label>
                <select v-model="form.priority" class="portal-input">
                  <option value="low">{{ $t('pTickets.prioLow') }}</option>
                  <option value="medium">{{ $t('pTickets.prioMedium') }}</option>
                  <option value="high">{{ $t('pTickets.prioHigh') }}</option>
                  <option value="critical">{{ $t('pTickets.prioCritical') }}</option>
                </select>
              </div>
            </div>
            <div>
              <label class="block text-xs font-semibold ws-muted mb-1.5 uppercase tracking-wider">{{ $t('pTickets.description') }}</label>
              <textarea v-model="form.description" rows="4" class="portal-input" :placeholder="$t('pTickets.descPh')" />
            </div>
            <div class="flex gap-3 pt-2">
              <button type="submit" :disabled="creating"
 class="text-sm font-medium text-white bg-gradient-to-r from-blue-500 to-indigo-500 px-6 py-2.5 rounded-xl hover:shadow-lg hover:shadow-blue-500/20 transition-all disabled:opacity-50">
                {{ creating ? $t('pTickets.creating') : $t('pTickets.create').replace('+ ','') }}
              </button>
              <button type="button" @click="showCreateModal = false"
 class="text-sm font-medium ws-muted ws-soft px-6 py-2.5 rounded-xl hover:bg-slate-200 transition">
                {{ $t('common.cancel') }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
      <WorkspacePagination v-model:page="page" :page-size="pageSize" :total="tickets.length" />

  </div>
</template>

<script setup lang="ts">

definePageMeta({ layout: 'procurement', middleware: 'auth' })

const { t } = useI18n()
const { formatDay } = useLocaleFormat()
const { apiFetch } = useApi()
const tickets = ref<any[]>([])

// Client-side paging: these lists already hold the full filtered set, so the
// pager slices it rather than adding a round trip per page.
const page = ref(1)
const pageSize = 20
const paged = computed(() => tickets.value.slice((page.value - 1) * pageSize, page.value * pageSize))
watch(() => tickets.value.length, () => { page.value = 1 })

const showCreateModal = ref(false)
const creating = ref(false)
const loading = ref(true)
const error = ref('')

const form = reactive({
 title: '',
 issue_type: '',
 priority: 'medium',
 description: '',
})

function statusClass(status: string) {
 const map: Record<string, string> = {
 open: 'bg-blue-500/15 ws-accent dark:text-blue-300',
 in_progress: 'bg-amber-500/15 text-amber-700 dark:text-amber-300',
 resolved: 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300',
 closed: 'ws-soft ws-muted',
  }
 return map[status] || 'ws-soft ws-muted'
}

function priorityClass(priority: string) {
 const map: Record<string, string> = {
 low: 'ws-soft ws-muted',
 medium: 'bg-blue-500/15 ws-accent dark:text-blue-300',
 high: 'bg-orange-50 text-orange-600',
 critical: 'bg-red-500/15 text-red-600 dark:text-red-300',
  }
 return map[priority] || 'ws-soft ws-muted'
}

onMounted(loadData)

async function loadData() {
 loading.value = true
 error.value = ''
 try {
 const res = await apiFetch<any>('/tickets/my')
 tickets.value = res.items || []
  } catch (e: any) {
 tickets.value = []
 error.value = e?.data?.detail || e?.message || t('pTickets.loadFailed')
  } finally {
 loading.value = false
  }
}

async function handleCreate() {
 creating.value = true
 error.value = ''
 try {
 const payload: Record<string, any> = { ...form }
 if (!payload.issue_type) delete payload.issue_type
 await apiFetch('/tickets', { method: 'POST', body: payload })
 showCreateModal.value = false
    Object.assign(form, { title: '', issue_type: '', priority: 'medium', description: '' })
 await loadData()
  } catch (e: any) {
 error.value = e?.data?.detail || e?.message || t('pTickets.createFailed')
  }
 finally { creating.value = false }
}
</script>

<style scoped>
.modal-enter-active, .modal-leave-active { transition: opacity 0.2s; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
</style>
