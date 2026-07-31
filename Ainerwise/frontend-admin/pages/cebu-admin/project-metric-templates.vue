<template>
  <div class="space-y-5">
    <div>
      <h1 class="admin-page-title">Project Metric Templates</h1>
      <p class="admin-page-desc">Configure the questions and structured facts used by AI Project Forge.</p>
    </div>
    <p v-if="error" class="text-sm text-red-400">{{ error }}</p>
    <form class="admin-panel grid gap-3 p-4 md:grid-cols-4" @submit.prevent="create">
      <select v-model="form.project_type" class="input-field">
        <option v-for="type in projectTypes" :key="type">{{ type }}</option>
      </select>
      <input v-model.trim="form.key" required class="input-field" placeholder="metric key" />
      <input v-model.trim="form.label" required class="input-field" placeholder="Question label" />
      <select v-model="form.data_type" class="input-field">
        <option>text</option><option>number</option><option>boolean</option><option>select</option>
      </select>
      <input v-model.trim="form.prompt" class="input-field md:col-span-3" placeholder="AI extraction prompt" />
      <label class="flex items-center gap-2 text-sm text-slate-300"><input v-model="form.required" type="checkbox" /> Required</label>
      <button class="btn-primary md:col-span-4">Create metric template</button>
    </form>
    <div class="grid gap-3">
      <article v-for="row in items" :key="row.id" class="admin-panel p-4 text-sm">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p class="font-semibold text-white">{{ row.label }}</p>
            <p class="text-slate-400">{{ row.project_type }} · {{ row.key }} · {{ row.data_type }}</p>
          </div>
          <StatusBadge :status="row.active ? 'active' : 'inactive'" />
        </div>
        <p v-if="row.prompt" class="mt-2 text-slate-300">{{ row.prompt }}</p>
        <div class="mt-4 flex gap-2">
          <button class="btn-secondary" type="button" @click="editPrompt(row)">Edit prompt</button>
          <button class="btn-secondary" type="button" @click="toggle(row)">{{ row.active ? 'Deactivate' : 'Activate' }}</button>
        </div>
      </article>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default', middleware: ['auth'] })
const { apiFetch } = useApi()
const items = ref<any[]>([])
const error = ref('')
const projectTypes = ['GENERAL', 'CONSTRUCTION', 'RENOVATION', 'SOLAR', 'TECH_BUILD']
const form = reactive({ project_type: 'RENOVATION', key: '', label: '', data_type: 'text', prompt: '', required: false })
async function load() { items.value = (await apiFetch<any>('/admin/cebu/project-metric-templates')).items }
async function create() {
  try {
    await apiFetch('/admin/cebu/project-metric-templates', { method: 'POST', body: form })
    Object.assign(form, { project_type: 'RENOVATION', key: '', label: '', data_type: 'text', prompt: '', required: false })
    await load()
  } catch (e: any) { error.value = e?.data?.detail || e?.message }
}
async function editPrompt(row: any) {
  const prompt = window.prompt('AI extraction prompt', row.prompt || '')
  if (prompt === null) return
  try { await apiFetch(`/admin/cebu/project-metric-templates/${row.id}`, { method: 'PATCH', body: { prompt } }); await load() }
  catch (e: any) { error.value = e?.data?.detail || e?.message }
}
async function toggle(row: any) {
  try { await apiFetch(`/admin/cebu/project-metric-templates/${row.id}`, { method: 'PATCH', body: { active: !row.active } }); await load() }
  catch (e: any) { error.value = e?.data?.detail || e?.message }
}
onMounted(() => load().catch((e: any) => { error.value = e?.data?.detail || e?.message }))
</script>
