<template>
  <div class="space-y-6">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="admin-page-title">Marketing Automation</h1>
        <p class="admin-page-desc">Turn campaigns, showroom visits, and website inquiries into reviewed follow-up actions.</p>
        <NuxtLink to="/marketing/integration" class="inline-block mt-2 text-sm text-cyan-400 hover:underline">
          → Marketing Media Integration (Briefs, Clients, Imported Assets)
        </NuxtLink>
      </div>
      <div class="flex gap-2">
        <button class="action-button" :disabled="weeklyReportBusy" @click="runWeeklyReport">
          {{ weeklyReportBusy ? 'Running report...' : 'Run Agent weekly report' }}
        </button>
        <button class="action-button" @click="openContactModal">+ Prospect</button>
        <button class="action-button primary" @click="openCampaignModal">+ Campaign</button>
      </div>
    </div>

    <div v-if="loadError" class="rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
      {{ loadError }}
    </div>

    <div v-if="weeklyReport" class="glass-panel p-5">
      <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p class="text-xs uppercase tracking-wider text-cyan-400">Marketing Agent · Preliminary Weekly Report</p>
          <p class="mt-2 text-sm text-slate-200">{{ weeklyReport.output?.summary }}</p>
          <p class="mt-1 text-xs text-slate-500">{{ formatDate(weeklyReport.created_at) }} · Human review required</p>
        </div>
        <NuxtLink to="/ai-reviews?target_type=marketing_weekly_report" class="action-button">Review report</NuxtLink>
      </div>
      <div class="mt-4 grid gap-3 sm:grid-cols-3 xl:grid-cols-6">
        <div v-for="(value, key) in weeklyReport.output?.metrics || {}" :key="key" class="rounded-lg bg-white/5 p-3">
          <p class="text-[10px] uppercase tracking-wide text-slate-500">{{ String(key).replace(/_/g, ' ') }}</p>
          <p class="mt-1 text-sm font-semibold text-white">{{ value }}</p>
        </div>
      </div>
    </div>

    <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-6">
      <div v-for="card in statCards" :key="card.label" class="glass-panel p-4">
        <p class="text-xs uppercase tracking-wider text-slate-500">{{ card.label }}</p>
        <p class="mt-2 text-2xl font-bold text-white">{{ card.value }}</p>
      </div>
    </div>

    <div class="glass-panel p-2 flex flex-wrap gap-2">
      <button
        v-for="item in tabs"
        :key="item.key"
        class="rounded-lg px-4 py-2 text-sm transition"
        :class="tab === item.key ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-400 hover:bg-white/5'"
        @click="tab = item.key"
      >
        {{ item.label }}
      </button>
    </div>

    <section v-if="tab === 'followups'" class="glass-panel p-6">
      <div class="mb-5 flex items-center justify-between">
        <div>
          <h2 class="text-lg font-bold text-white">Follow-up Approval Queue</h2>
          <p class="text-sm text-slate-400">Automated drafts stay here until a person approves or completes them.</p>
        </div>
        <select v-model="activityStatus" class="input-field max-w-48 bg-white/5 text-white" @change="loadActivities">
          <option value="" class="text-slate-900">All statuses</option>
          <option value="pending_approval" class="text-slate-900">Pending approval</option>
          <option value="scheduled" class="text-slate-900">Scheduled</option>
          <option value="completed" class="text-slate-900">Completed</option>
        </select>
      </div>
      <div class="table-shell">
        <table class="admin-table w-full text-sm">
          <thead><tr><th>Due</th><th>Type</th><th>Channel</th><th>Subject</th><th>Status</th><th></th></tr></thead>
          <tbody>
            <tr v-for="activity in activities" :key="activity.id">
              <td>{{ formatDate(activity.scheduled_at) }}</td>
              <td>{{ activity.activity_type }}</td>
              <td>{{ activity.channel }}</td>
              <td class="max-w-sm truncate">{{ activity.subject || '-' }}</td>
              <td><StatusBadge :status="activity.status" /></td>
              <td class="text-right"><button class="text-cyan-400 hover:underline" @click="reviewActivity(activity)">Review</button></td>
            </tr>
            <tr v-if="!activities.length"><td colspan="6" class="py-8 text-center text-slate-500">No follow-up tasks.</td></tr>
          </tbody>
        </table>
      </div>
    </section>

    <section v-else-if="tab === 'campaigns'" class="glass-panel p-6">
      <div class="mb-5">
        <h2 class="text-lg font-bold text-white">Campaigns & Attribution</h2>
        <p class="text-sm text-slate-400">Use campaign links for events, QR codes, partner referrals, social posts, and paid ads.</p>
      </div>
      <div class="table-shell">
        <table class="admin-table w-full text-sm">
          <thead><tr><th>Name</th><th>Channel</th><th>UTM Campaign</th><th>Status</th><th>Conversions</th><th></th></tr></thead>
          <tbody>
            <tr v-for="campaign in campaignPerformance" :key="campaign.id">
              <td class="font-medium text-white">{{ campaign.name }}</td>
              <td>{{ campaign.channel }}</td>
              <td class="font-mono text-xs">{{ campaign.utm_campaign }}</td>
              <td><StatusBadge :status="campaign.status" /></td>
              <td>{{ campaign.conversions }}</td>
              <td class="text-right whitespace-nowrap">
                <button class="text-cyan-400 hover:underline" @click="prepareCampaign(campaign)">Prepare drafts</button>
                <button class="ml-3 text-cyan-400 hover:underline" @click="copyCampaignLink(campaign)">Copy link</button>
              </td>
            </tr>
            <tr v-if="!campaignPerformance.length"><td colspan="6" class="py-8 text-center text-slate-500">Create the first campaign to start attributing leads.</td></tr>
          </tbody>
        </table>
      </div>
    </section>

    <section v-else class="glass-panel p-6">
      <div class="mb-5">
        <h2 class="text-lg font-bold text-white">Local Prospect Network</h2>
        <p class="text-sm text-slate-400">Architects, installers, hotels, restaurants, property managers, and showroom visitors.</p>
      </div>
      <div class="table-shell">
        <table class="admin-table w-full text-sm">
          <thead><tr><th>Contact</th><th>Company</th><th>Segment</th><th>Source</th><th>Consent</th><th>Next follow-up</th></tr></thead>
          <tbody>
            <tr v-for="contact in contacts" :key="contact.id">
              <td><p class="font-medium text-white">{{ contact.contact_name || '-' }}</p><p class="text-xs text-slate-500">{{ contact.email || contact.phone || '-' }}</p></td>
              <td>{{ contact.company_name || '-' }}</td>
              <td>{{ contact.segment || '-' }}</td>
              <td>{{ contact.source || '-' }}</td>
              <td><StatusBadge :status="contact.consent_status" /></td>
              <td>{{ formatDate(contact.next_follow_up_at) }}</td>
            </tr>
            <tr v-if="!contacts.length"><td colspan="6" class="py-8 text-center text-slate-500">No prospects yet.</td></tr>
          </tbody>
        </table>
      </div>
    </section>

    <div v-if="showCampaignModal" class="modal-backdrop" @click.self="showCampaignModal = false">
      <form class="modal-card" @submit.prevent="createCampaign">
        <h2 class="text-lg font-bold text-white">Create Campaign</h2>
        <div class="grid gap-4 sm:grid-cols-2">
          <label><span>Name</span><input v-model="campaignForm.name" class="input-field" required></label>
          <label><span>Channel</span><select v-model="campaignForm.channel" class="input-field" required><option v-for="v in channels" :key="v">{{ v }}</option></select></label>
          <label><span>Status</span><select v-model="campaignForm.status" class="input-field"><option value="draft">Draft</option><option value="active">Active</option><option value="paused">Paused</option></select></label>
          <label><span>UTM campaign</span><input v-model="campaignForm.utm_campaign" class="input-field" required></label>
          <label><span>UTM source</span><input v-model="campaignForm.utm_source" class="input-field"></label>
          <label><span>UTM medium</span><input v-model="campaignForm.utm_medium" class="input-field"></label>
          <label><span>Landing path</span><input v-model="campaignForm.landing_path" class="input-field" placeholder="/submit-requirement"></label>
          <label class="sm:col-span-2"><span>Objective</span><input v-model="campaignForm.objective" class="input-field" placeholder="Book a showroom consultation"></label>
          <label><span>Target segment</span><input v-model="campaignForm.segment" class="input-field" placeholder="hotel, architect, installer"></label>
          <label><span>Email subject</span><input v-model="campaignForm.subject" class="input-field" placeholder="Local smart-building update"></label>
          <label class="sm:col-span-2"><span>Draft body</span><textarea v-model="campaignForm.body" rows="4" class="input-field" placeholder="Hello {name}, ... {company}"></textarea></label>
        </div>
        <div class="modal-actions"><button type="button" class="action-button" @click="showCampaignModal = false">Cancel</button><button class="action-button primary">Create</button></div>
      </form>
    </div>

    <div v-if="showContactModal" class="modal-backdrop" @click.self="showContactModal = false">
      <form class="modal-card" @submit.prevent="createContact">
        <h2 class="text-lg font-bold text-white">Add Local Prospect</h2>
        <div class="grid gap-4 sm:grid-cols-2">
          <label><span>Name</span><input v-model="contactForm.contact_name" class="input-field"></label>
          <label><span>Company</span><input v-model="contactForm.company_name" class="input-field"></label>
          <label><span>Email</span><input v-model="contactForm.email" type="email" class="input-field"></label>
          <label><span>Phone</span><input v-model="contactForm.phone" class="input-field"></label>
          <label><span>Segment</span><input v-model="contactForm.segment" class="input-field" placeholder="architect, hotel, installer"></label>
          <label><span>Source</span><input v-model="contactForm.source" class="input-field" placeholder="showroom, event, referral"></label>
          <label class="sm:col-span-2"><span>Consent status</span><select v-model="contactForm.consent_status" class="input-field"><option value="unknown">Unknown</option><option value="inquiry_only">Inquiry only</option><option value="opted_in">Opted in</option><option value="unsubscribed">Unsubscribed</option></select></label>
        </div>
        <p class="text-xs text-amber-300">Promotional automation should only target contacts with the required consent.</p>
        <div class="modal-actions"><button type="button" class="action-button" @click="showContactModal = false">Cancel</button><button class="action-button primary">Add</button></div>
      </form>
    </div>

    <div v-if="selectedActivity" class="modal-backdrop" @click.self="selectedActivity = null">
      <div class="modal-card">
        <h2 class="text-lg font-bold text-white">Review Follow-up</h2>
        <input v-model="selectedActivity.subject" class="input-field">
        <textarea v-model="selectedActivity.content" rows="10" class="input-field"></textarea>
        <p class="text-xs text-amber-300">Review consent and context before sending. The system does not auto-send drafts.</p>
        <div class="modal-actions">
          <button class="action-button" @click="selectedActivity = null">Cancel</button>
          <button class="action-button" @click="saveActivity('scheduled')">Approve & schedule</button>
          <button class="action-button primary" @click="saveActivity('completed')">Mark completed</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })
const { apiFetch } = useApi()

const dashboard = ref<any>({ counts: {}, campaigns: [] })
const activities = ref<any[]>([])
const contacts = ref<any[]>([])
const tab = ref('followups')
const activityStatus = ref('pending_approval')
const showCampaignModal = ref(false)
const showContactModal = ref(false)
const selectedActivity = ref<any>(null)
const loadError = ref('')
const weeklyReport = ref<any>(null)
const weeklyReportBusy = ref(false)
const tabs = [{ key: 'followups', label: 'Follow-ups' }, { key: 'campaigns', label: 'Campaigns' }, { key: 'contacts', label: 'Prospects' }]
const channels = ['showroom', 'event', 'referral', 'linkedin', 'instagram', 'google', 'email', 'partner']

const campaignForm = reactive({ name: '', channel: 'showroom', objective: '', status: 'draft', landing_path: '/submit-requirement', utm_source: 'showroom', utm_medium: 'offline', utm_campaign: '', segment: '', subject: '', body: '' })
const contactForm = reactive({ contact_name: '', company_name: '', email: '', phone: '', segment: '', source: '', consent_status: 'unknown', language: 'en', status: 'prospect' })
const campaignPerformance = computed(() => dashboard.value.campaigns || [])
const statCards = computed(() => [
  { label: 'Active campaigns', value: dashboard.value.counts?.active_campaigns ?? 0 },
  { label: 'Prospects', value: dashboard.value.counts?.contacts ?? 0 },
  { label: 'Awaiting review', value: dashboard.value.counts?.pending_approval ?? 0 },
  { label: 'Due now', value: dashboard.value.counts?.due_follow_ups ?? 0 },
  { label: 'Attributed leads', value: dashboard.value.counts?.attributed_leads ?? 0 },
  { label: 'Product inquiries', value: dashboard.value.counts?.attributed_inquiries ?? 0 },
])

function formatDate(value?: string) {
  return value ? new Date(value).toLocaleString() : '-'
}
function openCampaignModal() {
  campaignForm.utm_campaign = `local-${new Date().toISOString().slice(0, 10)}`
  showCampaignModal.value = true
}
function openContactModal() { showContactModal.value = true }
function reviewActivity(activity: any) { selectedActivity.value = { ...activity } }

async function loadDashboard() { dashboard.value = await apiFetch<any>('/marketing/dashboard') }
async function loadActivities() {
  const query = activityStatus.value ? `?status=${activityStatus.value}&limit=100` : '?limit=100'
  const res = await apiFetch<any>(`/marketing/activities${query}`)
  activities.value = res.items || []
}
async function loadContacts() {
  const res = await apiFetch<any>('/marketing/contacts?limit=100')
  contacts.value = res.items || []
}
async function loadWeeklyReport() {
  const res = await apiFetch<any>('/admin/marketing/weekly-report/latest')
  weeklyReport.value = res.report
}
async function refresh() {
  loadError.value = ''
  try {
    await Promise.all([loadDashboard(), loadActivities(), loadContacts(), loadWeeklyReport()])
  } catch {
    loadError.value = 'Marketing API is unavailable. Start the backend to load campaigns and follow-up tasks.'
  }
}
async function runWeeklyReport() {
  weeklyReportBusy.value = true
  loadError.value = ''
  try {
    const report = await apiFetch<any>('/admin/marketing/weekly-report/run', { method: 'POST' })
    weeklyReport.value = { ...report, created_at: new Date().toISOString() }
  } catch (e: any) {
    loadError.value = e?.data?.detail || 'Marketing Agent weekly report could not run.'
  } finally {
    weeklyReportBusy.value = false
  }
}
async function createCampaign() {
  const { segment, subject, body, ...campaign } = campaignForm
  await apiFetch('/marketing/campaigns', {
    method: 'POST',
    body: {
      ...campaign,
      audience_json: segment ? { segments: [segment] } : null,
      content_json: subject || body ? { subject, body } : null,
    },
  })
  showCampaignModal.value = false
  await refresh()
}
async function createContact() {
  await apiFetch('/marketing/contacts', { method: 'POST', body: contactForm })
  showContactModal.value = false
  await refresh()
}
async function saveActivity(status: string) {
  await apiFetch(`/marketing/activities/${selectedActivity.value.id}`, {
    method: 'PUT',
    body: { subject: selectedActivity.value.subject, content: selectedActivity.value.content, status },
  })
  selectedActivity.value = null
  await refresh()
}
async function copyCampaignLink(campaign: any) {
  const full = await apiFetch<any>(`/marketing/campaigns/${campaign.id}`)
  const params = new URLSearchParams({ utm_campaign: full.utm_campaign })
  if (full.utm_source) params.set('utm_source', full.utm_source)
  if (full.utm_medium) params.set('utm_medium', full.utm_medium)
  const origin = window.location.origin.replace(':4097', ':4099')
  await navigator.clipboard.writeText(`${origin}${full.landing_path || '/submit-requirement'}?${params}`)
}
async function prepareCampaign(campaign: any) {
  const result = await apiFetch<any>(`/marketing/campaigns/${campaign.id}/prepare`, { method: 'POST' })
  alert(`Prepared ${result.created} drafts for ${result.eligible} opted-in contacts.`)
  tab.value = 'followups'
  await refresh()
}

onMounted(refresh)
</script>

<style scoped>
.action-button { @apply rounded-lg border border-white/10 px-4 py-2 text-sm text-slate-300 transition hover:bg-white/10; }
.action-button.primary { @apply border-cyan-500/40 bg-cyan-500/20 text-cyan-200 hover:bg-cyan-500/30; }
.table-shell { @apply overflow-x-auto rounded-xl border border-white/10; }
.admin-table th { @apply bg-white/5 px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500; }
.admin-table td { @apply border-t border-white/10 px-4 py-3 text-slate-300; }
.modal-backdrop { @apply fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm; }
.modal-card { @apply w-full max-w-2xl space-y-5 rounded-2xl border border-white/10 bg-slate-900 p-6 shadow-2xl; }
.modal-card label span { @apply mb-1 block text-xs font-medium text-slate-400; }
.modal-actions { @apply flex justify-end gap-2; }
</style>
