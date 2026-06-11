<template>
  <div>
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-6">
      <div>
        <h1 class="admin-page-title">Knowledge Base</h1>
        <p class="admin-page-desc">Documents the AI consultant can cite: manuals, datasheets, FAQs, case studies. Upload → extract → chunk → embed.</p>
      </div>
      <select v-model="statusFilter" class="input-field max-w-44" @change="load">
        <option value="">All statuses</option>
        <option value="pending">Pending</option>
        <option value="embedded">Embedded</option>
        <option value="failed">Failed</option>
      </select>
    </div>

    <!-- Upload forms -->
    <div class="grid gap-4 md:grid-cols-2 mb-6">
      <div class="admin-panel p-4">
        <h2 class="font-medium text-gray-900 mb-3">Upload file (PDF / TXT / MD / HTML)</h2>
        <div class="space-y-2">
          <input ref="fileInput" type="file" accept=".pdf,.txt,.md,.html,.htm" class="text-sm" />
          <input v-model="fileTitle" placeholder="Title (defaults to filename)" class="input-field w-full" />
          <div class="flex gap-2">
            <select v-model="fileSourceType" class="input-field flex-1">
              <option value="manual">Manual</option>
              <option value="datasheet">Datasheet</option>
              <option value="case_study">Case study</option>
              <option value="installation_guide">Installation guide</option>
            </select>
            <select v-model="fileLang" class="input-field w-28">
              <option value="">Lang</option>
              <option value="en">EN</option>
              <option value="zh">ZH</option>
              <option value="sr">SR</option>
            </select>
          </div>
          <button class="btn-primary text-sm px-4 py-2" :disabled="uploading" @click="uploadFile">
            {{ uploading ? 'Uploading...' : 'Upload & ingest' }}
          </button>
        </div>
      </div>

      <div class="admin-panel p-4">
        <h2 class="font-medium text-gray-900 mb-3">Add text snippet (FAQ)</h2>
        <div class="space-y-2">
          <input v-model="textTitle" placeholder="Title" class="input-field w-full" />
          <textarea v-model="textContent" rows="4" placeholder="Content..." class="input-field w-full"></textarea>
          <button class="btn-primary text-sm px-4 py-2" :disabled="uploading || !textTitle || !textContent" @click="createText">
            Add & ingest
          </button>
        </div>
      </div>
    </div>

    <!-- Document list -->
    <div class="admin-panel">
      <table class="admin-table w-full text-sm">
        <thead>
          <tr>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Title</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Type</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Lang</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Status</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Chunks</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Updated</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="doc in documents" :key="doc.id" class="border-b">
            <td class="px-4 py-3">
              <p class="font-medium text-gray-900">{{ doc.title }}</p>
              <p v-if="doc.meta_json?.last_error" class="text-xs text-red-600">{{ doc.meta_json.last_error }}</p>
            </td>
            <td class="px-4 py-3 text-gray-600">{{ doc.source_type }}</td>
            <td class="px-4 py-3 text-gray-600">{{ doc.lang || '-' }}</td>
            <td class="px-4 py-3"><StatusBadge :status="doc.status" /></td>
            <td class="px-4 py-3 text-gray-600">{{ doc.chunk_count }}</td>
            <td class="px-4 py-3 text-gray-500 whitespace-nowrap">{{ new Date(doc.updated_at).toLocaleString() }}</td>
            <td class="px-4 py-3 whitespace-nowrap">
              <div class="flex gap-2">
                <button class="text-xs px-3 py-1.5 rounded border border-gray-300 hover:bg-gray-50" :disabled="busy" @click="reingest(doc)">Re-ingest</button>
                <button class="text-xs px-3 py-1.5 rounded border border-red-300 text-red-600 hover:bg-red-50" :disabled="busy" @click="remove(doc)">Delete</button>
              </div>
            </td>
          </tr>
          <tr v-if="!documents.length">
            <td colspan="7" class="px-4 py-8 text-center text-gray-500">No documents yet. Upload manuals or FAQs to power the AI consultant.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { apiFetch } = useApi()
const documents = ref<any[]>([])
const statusFilter = ref('')
const uploading = ref(false)
const busy = ref(false)

const fileInput = ref<HTMLInputElement | null>(null)
const fileTitle = ref('')
const fileSourceType = ref('manual')
const fileLang = ref('')
const textTitle = ref('')
const textContent = ref('')

async function load() {
  const params = statusFilter.value ? `?status=${statusFilter.value}` : ''
  try {
    const res = await apiFetch<any>(`/admin/knowledge/documents${params}`)
    documents.value = res.items || []
  } catch {
    documents.value = []
  }
}

async function uploadFile() {
  const file = fileInput.value?.files?.[0]
  if (!file) return
  uploading.value = true
  try {
    const form = new FormData()
    form.append('file', file)
    form.append('title', fileTitle.value)
    form.append('source_type', fileSourceType.value)
    form.append('lang', fileLang.value)
    await apiFetch('/admin/knowledge/documents', { method: 'POST', body: form })
    fileTitle.value = ''
    if (fileInput.value) fileInput.value.value = ''
    await load()
  } finally {
    uploading.value = false
  }
}

async function createText() {
  uploading.value = true
  try {
    await apiFetch('/admin/knowledge/documents/text', {
      method: 'POST',
      body: { title: textTitle.value, content: textContent.value, source_type: 'faq' },
    })
    textTitle.value = ''
    textContent.value = ''
    await load()
  } finally {
    uploading.value = false
  }
}

async function reingest(doc: any) {
  busy.value = true
  try {
    await apiFetch(`/admin/knowledge/documents/${doc.id}/reingest`, { method: 'POST' })
    await load()
  } finally {
    busy.value = false
  }
}

async function remove(doc: any) {
  if (!window.confirm(`Delete "${doc.title}" and all its chunks?`)) return
  busy.value = true
  try {
    await apiFetch(`/admin/knowledge/documents/${doc.id}`, { method: 'DELETE' })
    await load()
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>
