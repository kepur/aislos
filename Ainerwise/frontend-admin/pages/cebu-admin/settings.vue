<template>
  <div class="space-y-6">
    <div>
      <h1 class="admin-page-title">Cebu Platform Settings</h1>
      <p class="admin-page-desc">Audited non-secret policy settings and notification templates.</p>
    </div>
    <p v-if="error" class="text-sm text-red-400">{{ error }}</p>
    <p v-if="message" class="text-sm text-emerald-400">{{ message }}</p>

    <section class="admin-panel p-5">
      <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 class="font-semibold text-white">Platform policy settings</h2>
          <p class="text-sm text-slate-400">Secrets are rejected here and belong in Integrations.</p>
        </div>
        <button class="btn-secondary" type="button" @click="resetSetting">New setting</button>
      </div>
      <form class="grid gap-3 lg:grid-cols-2" @submit.prevent="saveSetting">
        <label class="text-sm text-slate-300">
          Key
          <input v-model.trim="settingForm.key" required class="input-field mt-1 w-full" placeholder="commerce.quote_expiry" />
        </label>
        <label class="text-sm text-slate-300">
          Description
          <input v-model.trim="settingForm.description" class="input-field mt-1 w-full" placeholder="What this policy controls" />
        </label>
        <label class="text-sm text-slate-300 lg:col-span-2">
          JSON value
          <textarea v-model="settingForm.value" required rows="5" class="input-field mt-1 w-full font-mono text-xs" placeholder='{"days": 7}' />
        </label>
        <div class="lg:col-span-2"><button class="btn-primary" :disabled="saving">Save audited setting</button></div>
      </form>
      <div class="mt-5 grid gap-3">
        <button
          v-for="row in settings"
          :key="row.id"
          type="button"
          class="rounded-lg border border-white/5 bg-slate-950/30 p-4 text-left hover:border-cyan-500/30"
          @click="editSetting(row)"
        >
          <span class="font-medium text-white">{{ row.key }}</span>
          <span class="mt-1 block text-sm text-slate-400">{{ row.description || 'No description' }}</span>
          <code class="mt-2 block overflow-x-auto text-xs text-cyan-300">{{ JSON.stringify(row.value_json) }}</code>
        </button>
      </div>
    </section>

    <section class="admin-panel p-5">
      <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 class="font-semibold text-white">Notification templates</h2>
          <p class="text-sm text-slate-400">Templates are scoped by key, channel and language.</p>
        </div>
        <button class="btn-secondary" type="button" @click="resetTemplate">New template</button>
      </div>
      <form class="grid gap-3 lg:grid-cols-3" @submit.prevent="saveTemplate">
        <label class="text-sm text-slate-300">
          Template key
          <input v-model.trim="templateForm.template_key" required class="input-field mt-1 w-full" placeholder="order-awarded" />
        </label>
        <label class="text-sm text-slate-300">
          Channel
          <select v-model="templateForm.channel" class="input-field mt-1 w-full">
            <option>EMAIL</option><option>SMS</option><option>IN_APP</option><option>PUSH</option>
          </select>
        </label>
        <label class="text-sm text-slate-300">
          Language
          <input v-model.trim="templateForm.language" required class="input-field mt-1 w-full" placeholder="en" />
        </label>
        <label class="text-sm text-slate-300 lg:col-span-3">
          Subject
          <input v-model.trim="templateForm.subject" class="input-field mt-1 w-full" placeholder="Optional subject" />
        </label>
        <label class="text-sm text-slate-300 lg:col-span-3">
          Body
          <textarea v-model="templateForm.body" required rows="6" class="input-field mt-1 w-full" placeholder="Order {{ order_id }} has been awarded." />
        </label>
        <label class="text-sm text-slate-300 lg:col-span-2">
          Variables hint
          <input v-model.trim="templateForm.variables_hint" class="input-field mt-1 w-full" placeholder="order_id, buyer_name" />
        </label>
        <label class="flex items-center gap-2 self-end pb-2 text-sm text-slate-300">
          <input v-model="templateForm.active" type="checkbox" /> Active
        </label>
        <div class="lg:col-span-3"><button class="btn-primary" :disabled="saving">Save template</button></div>
      </form>
      <div class="mt-5 grid gap-3 md:grid-cols-2">
        <button
          v-for="row in templates"
          :key="row.id"
          type="button"
          class="rounded-lg border border-white/5 bg-slate-950/30 p-4 text-left hover:border-cyan-500/30"
          @click="editTemplate(row)"
        >
          <span class="font-medium text-white">{{ row.template_key }}</span>
          <span class="ml-2 text-xs text-cyan-300">{{ row.channel }} / {{ row.language }}</span>
          <span class="mt-2 block text-sm text-slate-400">{{ row.subject || row.body }}</span>
          <StatusBadge class="mt-3" :status="row.active ? 'active' : 'inactive'" />
        </button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default', middleware: ['auth'] })
const { apiFetch } = useApi()
const settings = ref<any[]>([])
const templates = ref<any[]>([])
const error = ref('')
const message = ref('')
const saving = ref(false)
const settingForm = reactive({ key: '', description: '', value: '{\n  "days": 7\n}' })
const templateForm = reactive({
  template_key: '', channel: 'EMAIL', language: 'en', subject: '',
  body: '', variables_hint: '', active: true,
})

async function load() {
  const [settingResult, templateResult] = await Promise.all([
    apiFetch<any>('/admin/cebu/settings'),
    apiFetch<any>('/admin/cebu/notification-templates'),
  ])
  settings.value = settingResult.items
  templates.value = templateResult.items
}
function resetSetting() { Object.assign(settingForm, { key: '', description: '', value: '{\n  "days": 7\n}' }) }
function editSetting(row: any) {
  Object.assign(settingForm, {
    key: row.key, description: row.description || '', value: JSON.stringify(row.value_json, null, 2),
  })
}
function resetTemplate() {
  Object.assign(templateForm, {
    template_key: '', channel: 'EMAIL', language: 'en', subject: '',
    body: '', variables_hint: '', active: true,
  })
}
function editTemplate(row: any) {
  Object.assign(templateForm, {
    template_key: row.template_key, channel: row.channel, language: row.language,
    subject: row.subject || '', body: row.body, variables_hint: row.variables_hint || '',
    active: row.active,
  })
}
async function saveSetting() {
  error.value = ''; message.value = ''; saving.value = true
  try {
    const value_json = JSON.parse(settingForm.value)
    if (!value_json || Array.isArray(value_json) || typeof value_json !== 'object') throw new Error('JSON value must be an object.')
    await apiFetch(`/admin/cebu/settings/${encodeURIComponent(settingForm.key)}`, {
      method: 'PUT', body: { value_json, description: settingForm.description || null },
    })
    message.value = 'Setting saved and audited.'
    await load()
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Unable to save setting.'
  } finally { saving.value = false }
}
async function saveTemplate() {
  error.value = ''; message.value = ''; saving.value = true
  try {
    await apiFetch(`/admin/cebu/notification-templates/${encodeURIComponent(templateForm.template_key)}`, {
      method: 'PUT',
      body: {
        channel: templateForm.channel, language: templateForm.language,
        subject: templateForm.subject || null, body: templateForm.body,
        variables_hint: templateForm.variables_hint || null, active: templateForm.active,
      },
    })
    message.value = 'Notification template saved and audited.'
    await load()
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Unable to save template.'
  } finally { saving.value = false }
}
onMounted(() => load().catch((e: any) => { error.value = e?.data?.detail || e?.message }))
</script>
