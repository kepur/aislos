<template>
  <div>
    <div class="mb-6">
      <h1 class="admin-page-title">Document Center</h1>
      <p class="admin-page-desc">Templates with &#123;&#123;variables&#125;&#125; → rendered documents → final PDF. Contracts, acceptance and maintenance reports.</p>
    </div>

    <div class="grid gap-4 md:grid-cols-2 mb-6">
      <div class="admin-panel p-4">
        <h2 class="font-medium text-gray-900 mb-3">New template</h2>
        <div class="space-y-2">
          <div class="flex gap-2">
            <input v-model="tplForm.name" placeholder="Template name" class="input-field flex-1" />
            <select v-model="tplForm.kind" class="input-field w-48">
              <option v-for="k in ['contract','proposal','acceptance_report','maintenance_report','installation_report']" :key="k" :value="k">{{ k }}</option>
            </select>
          </div>
          <textarea v-model="tplForm.body_md" rows="5" placeholder="# Acceptance Report&#10;Project: {{project_title}}&#10;Customer: {{customer_name}}&#10;..." class="input-field w-full font-mono text-xs"></textarea>
          <button class="btn-primary text-sm px-4 py-2" :disabled="busy || !tplForm.name || !tplForm.body_md" @click="createTemplate">Save template</button>
        </div>
      </div>

      <div class="admin-panel p-4">
        <h2 class="font-medium text-gray-900 mb-3">Generate document</h2>
        <div class="space-y-2">
          <select v-model="genForm.template_id" class="input-field w-full">
            <option value="">Select template…</option>
            <option v-for="t in templates" :key="t.id" :value="t.id">{{ t.kind }} — {{ t.name }}</option>
          </select>
          <input v-model="genForm.title" placeholder="Document title" class="input-field w-full" />
          <textarea v-model="genForm.variablesText" rows="3" placeholder='Variables JSON, e.g. {"project_title": "Belgrade villa", "customer_name": "Marko"}' class="input-field w-full font-mono text-xs"></textarea>
          <button class="btn-primary text-sm px-4 py-2" :disabled="busy || !genForm.template_id || !genForm.title" @click="generate">Render</button>
        </div>
      </div>
    </div>

    <div class="admin-panel">
      <h2 class="font-medium text-gray-900 px-4 pt-4">Documents</h2>
      <table class="admin-table w-full text-sm mt-2">
        <thead>
          <tr>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Title</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Kind</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Status</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Created</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="d in documents" :key="d.id" class="border-b">
            <td class="px-4 py-3 font-medium text-gray-900">{{ d.title }}</td>
            <td class="px-4 py-3 text-gray-600">{{ d.kind }}</td>
            <td class="px-4 py-3"><StatusBadge :status="d.status" /></td>
            <td class="px-4 py-3 text-gray-500 whitespace-nowrap">{{ new Date(d.created_at).toLocaleDateString() }}</td>
            <td class="px-4 py-3 whitespace-nowrap">
              <div class="flex gap-2">
                <button v-if="d.status === 'draft'" class="btn-primary text-xs px-3 py-1.5" :disabled="busy" @click="finalize(d)">Finalize PDF</button>
                <button v-if="['final','sent_for_signature'].includes(d.status)" class="text-xs px-3 py-1.5 rounded border border-emerald-300 text-emerald-700 hover:bg-emerald-50" :disabled="busy" @click="sendForSignature(d)">Send for signature</button>
                <button v-if="d.pdf_minio_key" class="text-xs px-3 py-1.5 rounded border border-gray-300 hover:bg-gray-50" @click="openPdf(d)">PDF</button>
              </div>
            </td>
          </tr>
          <tr v-if="!documents.length"><td colspan="5" class="px-4 py-8 text-center text-gray-500">No documents yet.</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { apiFetch } = useApi()
const templates = ref<any[]>([])
const documents = ref<any[]>([])
const busy = ref(false)
const tplForm = ref<any>({ name: '', kind: 'acceptance_report', body_md: '' })
const genForm = ref<any>({ template_id: '', title: '', variablesText: '{}' })

async function load() {
  templates.value = (await apiFetch<any>('/admin/documents/templates')).items || []
  documents.value = (await apiFetch<any>('/admin/documents')).items || []
}

async function createTemplate() {
  busy.value = true
  try {
    await apiFetch('/admin/documents/templates', { method: 'POST', body: tplForm.value })
    tplForm.value = { name: '', kind: 'acceptance_report', body_md: '' }
    await load()
  } finally {
    busy.value = false
  }
}

async function generate() {
  busy.value = true
  try {
    let variables = {}
    try { variables = JSON.parse(genForm.value.variablesText || '{}') } catch { /* keep empty */ }
    await apiFetch('/admin/documents/generate', {
      method: 'POST',
      body: { template_id: genForm.value.template_id, title: genForm.value.title, variables },
    })
    genForm.value.title = ''
    await load()
  } finally {
    busy.value = false
  }
}

async function finalize(d: any) {
  busy.value = true
  try {
    const res = await apiFetch<any>(`/admin/documents/${d.id}/finalize`, { method: 'POST' })
    if (res.pdf_url) window.open(res.pdf_url, '_blank')
    await load()
  } finally {
    busy.value = false
  }
}

async function openPdf(d: any) {
  const res = await apiFetch<any>(`/admin/documents/${d.id}/pdf-url`)
  if (res.pdf_url) window.open(res.pdf_url, '_blank')
}

async function sendForSignature(d: any) {
  const name = window.prompt('Signer full name:')
  if (!name) return
  const email = window.prompt('Signer email (optional, sends the link automatically):') || null
  busy.value = true
  try {
    const res = await apiFetch<any>(`/admin/documents/${d.id}/send-for-signature`, {
      method: 'POST',
      body: { signer_name: name, signer_email: email },
    })
    window.prompt('Signing link (copy & share):', res.signing_url)
    await load()
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>
