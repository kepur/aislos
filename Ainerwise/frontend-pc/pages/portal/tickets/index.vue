<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold ws-title">{{ $t('portal.myTickets') }}</h1>
        <p class="text-sm ws-faint mt-1">Get help from our support team</p>
      </div>
      <button @click="showCreateModal = true"
 class="inline-flex items-center gap-2 text-sm font-medium text-white bg-gradient-to-r from-blue-500 to-indigo-500 px-5 py-2.5 rounded-xl hover:shadow-lg hover:shadow-blue-500/20 transition-all">
        + Create Ticket
      </button>
    </div>

    <div v-if="error" class="portal-card border-red-200 bg-red-50 text-sm text-red-700">
      {{ error }} <button class="ml-2 font-semibold underline" @click="loadData">Retry</button>
    </div>
    <div class="portal-card p-0 overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="ws-sunken/80 border-b ws-hairline">
            <th class="text-left px-4 py-3 text-xs font-semibold ws-faint uppercase tracking-wider">Title</th>
            <th class="text-left px-4 py-3 text-xs font-semibold ws-faint uppercase tracking-wider">Type</th>
            <th class="text-left px-4 py-3 text-xs font-semibold ws-faint uppercase tracking-wider">Priority</th>
            <th class="text-left px-4 py-3 text-xs font-semibold ws-faint uppercase tracking-wider">{{ $t('common.status') }}</th>
            <th class="text-left px-4 py-3 text-xs font-semibold ws-faint uppercase tracking-wider">Created</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="ticket in tickets" :key="ticket.id" class="border-b border-slate-50 hover:bg-blue-50/30 transition-colors">
            <td class="px-4 py-3 font-medium ws-title">{{ ticket.title }}</td>
            <td class="px-4 py-3 ws-muted">{{ ticket.issue_type || '-' }}</td>
            <td class="px-4 py-3">
              <span :class="['text-xs font-semibold px-2.5 py-1 rounded-full', priorityClass(ticket.priority)]">{{ ticket.priority }}</span>
            </td>
            <td class="px-4 py-3">
              <span :class="['text-xs font-semibold px-2.5 py-1 rounded-full', statusClass(ticket.status)]">{{ ticket.status }}</span>
            </td>
            <td class="px-4 py-3 ws-faint text-xs">{{ new Date(ticket.created_at).toLocaleDateString() }}</td>
          </tr>
          <tr v-if="loading && !tickets.length">
            <td colspan="5" class="px-4 py-12 text-center text-sm ws-faint">Loading tickets...</td>
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
            <h2 class="text-lg font-bold ws-title">Create Support Ticket</h2>
            <button @click="showCreateModal = false" class="ws-faint hover:ws-muted p-1">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <form @submit.prevent="handleCreate" class="space-y-4">
            <div>
              <label class="block text-xs font-semibold ws-muted mb-1.5 uppercase tracking-wider">Title *</label>
              <input v-model="form.title" type="text" required class="portal-input" placeholder="Brief description of the issue" />
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-semibold ws-muted mb-1.5 uppercase tracking-wider">Issue Type</label>
                <select v-model="form.issue_type" class="portal-input">
                  <option value="">Select type</option>
                  <option value="technical">Technical Issue</option>
                  <option value="billing">Billing</option>
                  <option value="product">Product Inquiry</option>
                  <option value="service">Service Request</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-semibold ws-muted mb-1.5 uppercase tracking-wider">Priority</label>
                <select v-model="form.priority" class="portal-input">
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
            </div>
            <div>
              <label class="block text-xs font-semibold ws-muted mb-1.5 uppercase tracking-wider">Description</label>
              <textarea v-model="form.description" rows="4" class="portal-input" placeholder="Detailed description..." />
            </div>
            <div class="flex gap-3 pt-2">
              <button type="submit" :disabled="creating"
 class="text-sm font-medium text-white bg-gradient-to-r from-blue-500 to-indigo-500 px-6 py-2.5 rounded-xl hover:shadow-lg hover:shadow-blue-500/20 transition-all disabled:opacity-50">
                {{ creating ? 'Creating...' : 'Create Ticket' }}
              </button>
              <button type="button" @click="showCreateModal = false"
 class="text-sm font-medium ws-muted ws-soft px-6 py-2.5 rounded-xl hover:bg-slate-200 transition">
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'procurement', middleware: 'auth' })

const { apiFetch } = useApi()
const tickets = ref<any[]>([])
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
 error.value = e?.data?.detail || e?.message || 'Unable to load tickets.'
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
 error.value = e?.data?.detail || e?.message || 'Unable to create ticket.'
  }
 finally { creating.value = false }
}
</script>

<style scoped>
.modal-enter-active, .modal-leave-active { transition: opacity 0.2s; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
</style>
