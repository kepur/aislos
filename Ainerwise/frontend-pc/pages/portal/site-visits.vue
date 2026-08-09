<template>
  <section class="space-y-6">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold ws-title">{{ $t('siteVisit.title') }}</h1>
        <p class="mt-1 text-sm ws-muted">{{ $t('siteVisit.subtitle') }}</p>
      </div>
      <NuxtLink to="/portal/installations" class="text-sm ws-accent hover:opacity-80">
        {{ $t('siteVisit.viewInstallations') }} →
      </NuxtLink>
    </div>

    <p v-if="message" class="pc-card text-sm text-emerald-600 dark:text-emerald-300">{{ message }}</p>
    <p v-if="error" class="pc-card text-sm text-red-400">{{ error }}</p>

    <div class="grid gap-6 lg:grid-cols-[1.15fr_1fr] lg:items-start">
      <!-- Request form. A site visit is an on_site_request ticket; the crew
           dispatch side already consumes those through field ops. -->
      <form class="pc-card space-y-4" @submit.prevent="submit">
        <div>
          <h2 class="text-lg font-medium ws-title">{{ $t('siteVisit.formTitle') }}</h2>
          <p class="mt-1 text-sm ws-muted">{{ $t('siteVisit.formHint') }}</p>
        </div>

        <div>
          <label class="mb-1 block text-sm ws-muted">{{ $t('siteVisit.fieldProject') }}</label>
          <select v-model="form.project_id" class="input-field">
            <option value="">{{ $t('siteVisit.projectAny') }}</option>
            <option v-for="project in projects" :key="project.id" :value="project.id">
              {{ project.name || project.title || project.id }}
            </option>
          </select>
        </div>

        <div>
          <label class="mb-1 block text-sm ws-muted">{{ $t('siteVisit.fieldPurpose') }}</label>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="purpose in purposes"
              :key="purpose.key"
              type="button"
              class="ws-chip !px-3 !py-1.5"
              :class="{ 'ws-chip-active': form.purpose === purpose.key }"
              @click="form.purpose = purpose.key"
            >{{ purpose.label }}</button>
          </div>
        </div>

        <div class="grid gap-4 sm:grid-cols-2">
          <div>
            <label class="mb-1 block text-sm ws-muted">{{ $t('siteVisit.fieldDate') }}</label>
            <input v-model="form.preferred_date" type="date" class="input-field" :min="today" />
          </div>
          <div>
            <label class="mb-1 block text-sm ws-muted">{{ $t('siteVisit.fieldWindow') }}</label>
            <select v-model="form.window" class="input-field">
              <option value="morning">{{ $t('siteVisit.windowMorning') }}</option>
              <option value="afternoon">{{ $t('siteVisit.windowAfternoon') }}</option>
              <option value="allday">{{ $t('siteVisit.windowAllDay') }}</option>
            </select>
          </div>
        </div>

        <div>
          <label class="mb-1 block text-sm ws-muted">{{ $t('siteVisit.fieldNotes') }}</label>
          <textarea
            v-model.trim="form.notes"
            rows="4"
            class="input-field"
            :placeholder="$t('siteVisit.notesPlaceholder')"
          ></textarea>
        </div>

        <div class="flex items-center justify-between border-t ws-hairline pt-4">
          <p class="text-xs ws-faint">{{ $t('siteVisit.dispatchNote') }}</p>
          <button class="btn-primary" :disabled="submitting || !form.notes">
            {{ submitting ? $t('siteVisit.submitting') : $t('siteVisit.submit') }}
          </button>
        </div>
      </form>

      <!-- Existing visit requests -->
      <div class="pc-card">
        <div class="mb-4 flex items-center justify-between">
          <h2 class="text-lg font-medium ws-title">{{ $t('siteVisit.existing') }}</h2>
          <NuxtLink to="/portal/tickets" class="text-xs ws-accent hover:opacity-80">
            {{ $t('siteVisit.allTickets') }} →
          </NuxtLink>
        </div>
        <div v-if="loading" class="py-8 text-center text-sm ws-muted">{{ $t('siteVisit.loading') }}</div>
        <ul v-else-if="visits.length" class="divide-y ws-divide">
          <li v-for="visit in visits" :key="visit.id" class="flex items-start gap-3 py-3">
            <div class="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ws-soft text-sm">🔧</div>
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-medium ws-title">{{ visit.title }}</p>
              <p class="truncate text-xs ws-faint">{{ formatDate(visit.created_at) }}</p>
            </div>
            <span :class="['shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold', statusTone(visit.status)]">
              {{ visit.status }}
            </span>
          </li>
        </ul>
        <p v-else class="py-8 text-center text-sm ws-muted">{{ $t('siteVisit.noVisits') }}</p>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'procurement', middleware: 'auth' })

const { t } = useI18n()
const { apiFetch } = useApi()

const projects = ref<any[]>([])
const visits = ref<any[]>([])
const loading = ref(true)
const submitting = ref(false)
const message = ref('')
const error = ref('')

const today = new Date().toISOString().slice(0, 10)
const form = reactive({
  project_id: '',
  purpose: 'survey',
  preferred_date: '',
  window: 'morning',
  notes: '',
})

const purposes = computed(() => [
  { key: 'survey', label: t('siteVisit.purposeSurvey') },
  { key: 'installation', label: t('siteVisit.purposeInstall') },
  { key: 'maintenance', label: t('siteVisit.purposeMaintenance') },
  { key: 'inspection', label: t('siteVisit.purposeInspection') },
])

function statusTone(status?: string) {
  const s = String(status || '').toLowerCase()
  if (s.includes('open') || s.includes('new')) return 'bg-blue-500/15 text-blue-600 dark:text-blue-300'
  if (s.includes('progress') || s.includes('scheduled')) return 'bg-amber-500/15 text-amber-700 dark:text-amber-300'
  if (s.includes('done') || s.includes('closed') || s.includes('resolved')) return 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
  return 'ws-soft ws-muted'
}

function formatDate(value?: string) {
  if (!value) return '—'
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? '—' : parsed.toLocaleDateString()
}

async function load() {
  loading.value = true
  const [projectRes, ticketRes] = await Promise.allSettled([
    apiFetch<any>('/projects/my?limit=50'),
    apiFetch<any>('/tickets/my?limit=50'),
  ])
  if (projectRes.status === 'fulfilled') projects.value = projectRes.value.items || []
  if (ticketRes.status === 'fulfilled') {
    visits.value = (ticketRes.value.items || []).filter(
      (item: any) => String(item.issue_type || '') === 'on_site_request',
    )
  }
  loading.value = false
}

async function submit() {
  submitting.value = true
  message.value = ''
  error.value = ''
  const purposeLabel = purposes.value.find(p => p.key === form.purpose)?.label || form.purpose
  try {
    await apiFetch('/tickets', {
      method: 'POST',
      body: {
        issue_type: 'on_site_request',
        priority: 'medium',
        title: t('siteVisit.ticketTitle', { purpose: purposeLabel }),
        description: [
          `${t('siteVisit.fieldPurpose')}: ${purposeLabel}`,
          form.preferred_date ? `${t('siteVisit.fieldDate')}: ${form.preferred_date} (${form.window})` : '',
          form.notes,
        ]
          .filter(Boolean)
          .join('\n'),
        ...(form.project_id ? { project_id: form.project_id } : {}),
      },
    })
    message.value = t('siteVisit.submitted')
    form.notes = ''
    form.preferred_date = ''
    await load()
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || t('siteVisit.submitFailed')
  } finally {
    submitting.value = false
  }
}

onMounted(load)
</script>
