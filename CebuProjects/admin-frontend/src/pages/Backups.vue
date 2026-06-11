<template>
  <div class="space-y-6">
    <div>
      <h2 class="text-xl font-bold text-slate-900">Backups</h2>
      <p class="text-sm text-slate-500">Manage automated backup schedules and download backup archives.</p>
    </div>

    <!-- Config -->
    <section class="card p-5 space-y-4 border-l-4 border-blue-400">
      <div class="flex items-center justify-between">
        <h3 class="font-bold text-slate-900 flex items-center gap-2"><span>⚙️</span> Backup Configuration</h3>
        <label class="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" v-model="config.enabled" class="rounded" />
          <span class="text-sm text-slate-700">Auto-backups enabled</span>
        </label>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="text-xs font-medium text-slate-600">Storage Path</label>
          <input v-model="config.backup_storage_path" class="input" placeholder="/var/backups/cebu" />
        </div>
        <div>
          <label class="text-xs font-medium text-slate-600">Default Retention (days)</label>
          <input v-model.number="config.backup_retention_days" type="number" min="1" class="input" />
        </div>
        <div>
          <label class="text-xs font-medium text-slate-600">Max Archives to Keep</label>
          <input v-model.number="config.backup_retention_count" type="number" min="1" class="input" />
        </div>
      </div>
      <div class="flex gap-2 justify-end">
        <button class="btn btn-primary text-sm" :disabled="savingConfig" @click="saveConfig">
          {{ savingConfig ? 'Saving…' : 'Save Config' }}
        </button>
      </div>
      <p v-if="configMsg" class="text-sm text-green-600">{{ configMsg }}</p>
    </section>

    <!-- Schedules -->
    <section class="card p-5 space-y-4">
      <div class="flex items-center justify-between">
        <h3 class="font-bold text-slate-900 flex items-center gap-2"><span>📅</span> Backup Schedules</h3>
        <button class="btn btn-primary text-xs" @click="showAddSchedule = !showAddSchedule">+ Add Schedule</button>
      </div>

      <!-- Add Schedule Form -->
      <div v-if="showAddSchedule" class="bg-slate-50 rounded-xl p-4 space-y-3 border border-slate-200">
        <h4 class="font-medium text-sm text-slate-800">New Schedule</h4>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label class="text-xs font-medium text-slate-600">Frequency</label>
            <select v-model="newSchedule.frequency" class="input">
              <option value="WEEKLY">Weekly</option>
              <option value="MONTHLY">Monthly</option>
              <option value="CUSTOM">Custom (cron)</option>
            </select>
          </div>
          <div v-if="newSchedule.frequency === 'WEEKLY'">
            <label class="text-xs font-medium text-slate-600">Day of Week (0=Sun)</label>
            <input v-model.number="newSchedule.day_of_week" type="number" min="0" max="6" class="input" />
          </div>
          <div v-if="newSchedule.frequency === 'MONTHLY'">
            <label class="text-xs font-medium text-slate-600">Day of Month</label>
            <input v-model.number="newSchedule.day_of_month" type="number" min="1" max="28" class="input" />
          </div>
          <div v-if="newSchedule.frequency === 'CUSTOM'">
            <label class="text-xs font-medium text-slate-600">Cron Expression</label>
            <input v-model="newSchedule.cron_expr" class="input" placeholder="0 2 * * 0" />
          </div>
          <div>
            <label class="text-xs font-medium text-slate-600">Hour (0-23)</label>
            <input v-model.number="newSchedule.hour" type="number" min="0" max="23" class="input" />
          </div>
          <div>
            <label class="text-xs font-medium text-slate-600">Minute (0-59)</label>
            <input v-model.number="newSchedule.minute" type="number" min="0" max="59" class="input" />
          </div>
          <div>
            <label class="text-xs font-medium text-slate-600">Retention (days)</label>
            <input v-model.number="newSchedule.retention_days" type="number" min="1" class="input" />
          </div>
          <div>
            <label class="text-xs font-medium text-slate-600">Keep (count)</label>
            <input v-model.number="newSchedule.retention_count" type="number" min="1" class="input" />
          </div>
        </div>
        <div class="flex gap-2 justify-end">
          <button class="btn btn-secondary text-xs" @click="showAddSchedule = false">Cancel</button>
          <button class="btn btn-primary text-xs" :disabled="addingSchedule" @click="addSchedule">
            {{ addingSchedule ? 'Creating…' : 'Create Schedule' }}
          </button>
        </div>
      </div>

      <!-- Schedule List -->
      <div v-if="schedulesLoading" class="space-y-2">
        <div v-for="n in 2" :key="n" class="h-10 bg-slate-100 rounded animate-pulse"></div>
      </div>
      <div v-else-if="!schedules.length" class="text-sm text-slate-400 text-center py-4">No schedules yet.</div>
      <div v-else class="space-y-2">
        <div v-for="s in schedules" :key="s.id" class="flex items-center gap-3 bg-slate-50 rounded-lg px-4 py-3">
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" :checked="s.enabled" @change="toggleSchedule(s)" class="rounded" />
            <span class="text-xs text-slate-500">Enabled</span>
          </label>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-slate-800">{{ s.frequency }}
              <span v-if="s.frequency==='WEEKLY'"> · Day {{ s.day_of_week }}</span>
              <span v-if="s.frequency==='MONTHLY'"> · {{ s.day_of_month }}th</span>
              <span v-if="s.cron_expr"> · <code class="text-xs">{{ s.cron_expr }}</code></span>
              &nbsp;@ {{ String(s.hour||0).padStart(2,'0') }}:{{ String(s.minute||0).padStart(2,'0') }}
            </p>
            <p class="text-xs text-slate-400">
              Retention: {{ s.retention_days || '—' }}d / {{ s.retention_count || '—' }} archives
              <span v-if="s.next_run_at"> · Next: {{ fmtDate(s.next_run_at) }}</span>
            </p>
          </div>
          <button class="text-red-500 text-xs hover:underline" @click="deleteSchedule(s)">Delete</button>
        </div>
      </div>
    </section>

    <!-- Backup Jobs -->
    <section class="card p-5 space-y-4">
      <div class="flex items-center justify-between">
        <h3 class="font-bold text-slate-900 flex items-center gap-2"><span>🗄️</span> Backup Jobs</h3>
        <div class="flex gap-2">
          <button class="btn btn-secondary text-xs" @click="loadJobs">↻ Refresh</button>
          <button class="btn btn-primary text-xs" :disabled="runningNow" @click="runNow">
            {{ runningNow ? 'Running…' : '▶ Run Now' }}
          </button>
        </div>
      </div>

      <div v-if="jobsLoading" class="space-y-2">
        <div v-for="n in 3" :key="n" class="h-10 bg-slate-100 rounded animate-pulse"></div>
      </div>
      <div v-else-if="!jobs.length" class="text-sm text-slate-400 text-center py-4">No backup jobs yet. Click "Run Now" to create one.</div>
      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="text-left text-xs text-slate-400 border-b border-slate-100">
              <th class="pb-2 pr-4">Status</th>
              <th class="pb-2 pr-4">Started</th>
              <th class="pb-2 pr-4">Finished</th>
              <th class="pb-2 pr-4">Size</th>
              <th class="pb-2">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="job in jobs" :key="job.id" class="border-b border-slate-50 hover:bg-slate-50">
              <td class="py-2 pr-4">
                <span :class="jobBadge(job.status)" class="badge">{{ job.status }}</span>
              </td>
              <td class="py-2 pr-4 text-slate-500 text-xs">{{ fmtDate(job.started_at || job.created_at) }}</td>
              <td class="py-2 pr-4 text-slate-500 text-xs">{{ job.finished_at ? fmtDate(job.finished_at) : '—' }}</td>
              <td class="py-2 pr-4 text-slate-500 text-xs">{{ fmtSize(job.archive_size_bytes) }}</td>
              <td class="py-2">
                <button v-if="job.status === 'SUCCESS'" class="text-xs text-primary-600 font-medium hover:underline" @click="downloadJob(job)">⬇ Download</button>
                <span v-else class="text-xs text-slate-300">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { api } from '@/utils/api'

const config = reactive({
  enabled: true,
  backup_storage_path: '',
  backup_retention_days: 30,
  backup_retention_count: 10,
})
const savingConfig = ref(false)
const configMsg = ref('')

const schedules = ref([])
const schedulesLoading = ref(true)
const showAddSchedule = ref(false)
const addingSchedule = ref(false)
const newSchedule = reactive({
  frequency: 'WEEKLY',
  day_of_week: 0,
  day_of_month: 1,
  cron_expr: '',
  hour: 2,
  minute: 0,
  retention_days: 30,
  retention_count: 10,
})

const jobs = ref([])
const jobsLoading = ref(true)
const runningNow = ref(false)

function fmtDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleString()
}
function fmtSize(bytes) {
  if (!bytes) return '—'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1048576).toFixed(1)} MB`
}
function jobBadge(s) {
  return { PENDING:'badge-gray', RUNNING:'badge-blue', SUCCESS:'badge-green', FAILED:'badge-red' }[s] || 'badge-gray'
}

async function loadConfig() {
  try {
    const { data } = await api.get('/admin/backups/config')
    Object.assign(config, data)
  } catch {}
}
async function saveConfig() {
  savingConfig.value = true
  configMsg.value = ''
  try {
    await api.put('/admin/backups/config', { ...config })
    configMsg.value = 'Saved!'
    setTimeout(() => configMsg.value = '', 3000)
  } catch (e) { alert(e.response?.data?.detail || 'Failed') }
  savingConfig.value = false
}

async function loadSchedules() {
  schedulesLoading.value = true
  try {
    const { data } = await api.get('/admin/backups/schedules')
    schedules.value = data
  } catch { schedules.value = [] }
  schedulesLoading.value = false
}
async function addSchedule() {
  addingSchedule.value = true
  try {
    const payload = { ...newSchedule }
    if (payload.frequency !== 'CUSTOM') delete payload.cron_expr
    if (payload.frequency !== 'WEEKLY') delete payload.day_of_week
    if (payload.frequency !== 'MONTHLY') delete payload.day_of_month
    const { data } = await api.post('/admin/backups/schedules', payload)
    schedules.value.push(data)
    showAddSchedule.value = false
    Object.assign(newSchedule, { frequency:'WEEKLY', day_of_week:0, day_of_month:1, cron_expr:'', hour:2, minute:0, retention_days:30, retention_count:10 })
  } catch (e) { alert(e.response?.data?.detail || 'Failed') }
  addingSchedule.value = false
}
async function toggleSchedule(s) {
  try {
    const { data } = await api.patch(`/admin/backups/schedules/${s.id}`, { enabled: !s.enabled })
    const idx = schedules.value.findIndex(x => x.id === s.id)
    if (idx >= 0) schedules.value[idx] = data
  } catch (e) { alert(e.response?.data?.detail || 'Failed') }
}
async function deleteSchedule(s) {
  if (!confirm(`Delete this ${s.frequency} schedule?`)) return
  try {
    await api.delete(`/admin/backups/schedules/${s.id}`)
    schedules.value = schedules.value.filter(x => x.id !== s.id)
  } catch (e) { alert(e.response?.data?.detail || 'Failed') }
}

async function loadJobs() {
  jobsLoading.value = true
  try {
    const { data } = await api.get('/admin/backups/jobs', { params: { limit: 50 } })
    jobs.value = data
  } catch { jobs.value = [] }
  jobsLoading.value = false
}
async function runNow() {
  runningNow.value = true
  try {
    const { data } = await api.post('/admin/backups/manual')
    jobs.value.unshift(data)
    alert(`Backup job created (ID: ${data.id}). Status: ${data.status}`)
  } catch (e) { alert(e.response?.data?.detail || 'Failed to trigger backup') }
  runningNow.value = false
}

async function downloadJob(job) {
  try {
    const token = localStorage.getItem('admin_token') || ''
    const apiBase = import.meta.env.VITE_ADMIN_API_BASE || '/api'
    const url = `${apiBase}/admin/backups/jobs/${job.id}/download`
    // Trigger download via a temporary anchor
    const res = await api.get(`/admin/backups/jobs/${job.id}/download`, { responseType: 'blob' })
    const blob = new Blob([res.data], { type: 'application/zip' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `backup-${job.id}.zip`
    a.click()
    URL.revokeObjectURL(a.href)
  } catch (e) { alert(e.response?.data?.detail || 'Download failed') }
}

onMounted(async () => {
  await Promise.all([loadConfig(), loadSchedules(), loadJobs()])
})
</script>
