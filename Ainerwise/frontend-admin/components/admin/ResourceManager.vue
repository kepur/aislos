<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="admin-page-title">{{ title }}</h1>
        <p class="admin-page-desc">{{ description }}</p>
      </div>
      <button @click="openCreate" class="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700">
        + {{ t('common.new') }}
      </button>
    </div>

    <div class="bg-white rounded-xl border overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 text-gray-500">
          <tr>
            <th v-for="col in columns" :key="col.key" class="text-left font-medium px-4 py-2.5">{{ col.label }}</th>
            <th class="px-4 py-2.5 w-28"></th>
          </tr>
        </thead>
        <tbody class="divide-y">
          <tr v-for="row in items" :key="row.id" class="hover:bg-gray-50">
            <td v-for="col in columns" :key="col.key" class="px-4 py-2.5 text-gray-700 align-top">
              {{ render(col, row) }}
            </td>
            <td class="px-4 py-2.5 text-right whitespace-nowrap">
              <button @click="openEdit(row)" class="text-xs text-primary-600 hover:underline mr-3">{{ t('common.edit') }}</button>
              <button @click="remove(row)" class="text-xs text-red-600 hover:underline">{{ t('common.delete') }}</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="!items.length" class="p-8 text-center text-gray-500">{{ emptyText || t('common.noData') }}</div>
    </div>

    <!-- Create / Edit Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="showModal = false">
      <div class="bg-white rounded-xl w-full max-w-lg max-h-[90vh] overflow-y-auto p-6">
        <h2 class="text-lg font-bold text-gray-900 mb-4">{{ editing ? t('common.edit') : t('common.new') }} — {{ title }}</h2>
        <form class="grid grid-cols-2 gap-4" @submit.prevent="save">
          <div v-for="field in fields" :key="field.key" :class="field.full ? 'col-span-2' : 'col-span-2 sm:col-span-1'">
            <label class="block text-sm font-medium text-gray-700 mb-1">{{ field.label }}</label>

            <select v-if="field.type === 'select'" v-model="form[field.key]" class="input-field">
              <option value="">—</option>
              <option v-for="opt in normalizeOptions(field.options)" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>

            <label v-else-if="field.type === 'checkbox'" class="flex items-center gap-2 mt-1.5 text-sm text-gray-600">
              <input type="checkbox" v-model="form[field.key]" class="rounded" />
              {{ field.hint || 'Yes' }}
            </label>

            <textarea v-else-if="field.type === 'textarea'" v-model="form[field.key]" rows="2" class="input-field" :placeholder="field.placeholder || ''"></textarea>

            <input v-else :type="field.type === 'number' ? 'number' : field.type === 'date' ? 'date' : 'text'"
              v-model="form[field.key]" :step="field.step" class="input-field" :placeholder="field.placeholder || ''" />
          </div>

          <p v-if="error" class="col-span-2 text-sm text-red-500">{{ error }}</p>

          <div class="col-span-2 flex justify-end gap-3 pt-2">
            <button type="button" class="px-4 py-2 text-sm border rounded-lg text-gray-600 hover:bg-gray-50" @click="showModal = false">{{ t('common.cancel') }}</button>
            <button type="submit" class="px-4 py-2 text-sm font-medium bg-primary-600 text-white rounded-lg hover:bg-primary-700" :disabled="saving">
              {{ saving ? t('common.saving') : t('common.save') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Column { key: string; label: string; format?: (val: any, row: any) => string }
interface Field {
  key: string; label: string
  type?: 'text' | 'number' | 'date' | 'select' | 'checkbox' | 'textarea'
  options?: any[]; step?: string; placeholder?: string; hint?: string; full?: boolean
}

const props = defineProps<{
  title: string
  description?: string
  endpoint: string
  columns: Column[]
  fields: Field[]
  emptyText?: string
}>()

const { apiFetch } = useApi()
const { t } = useI18n({ useScope: 'global' })
const items = ref<any[]>([])
const showModal = ref(false)
const editing = ref<any>(null)
const saving = ref(false)
const error = ref('')
const form = reactive<Record<string, any>>({})

function normalizeOptions(options: any[] = []) {
  return options.map((o) => (typeof o === 'string' ? { value: o, label: o } : o))
}

function render(col: Column, row: any) {
  const val = row[col.key]
  if (col.format) return col.format(val, row)
  if (val === null || val === undefined || val === '') return '—'
  if (typeof val === 'boolean') return val ? 'Yes' : 'No'
  if (typeof val === 'object') return Array.isArray(val) ? val.join(', ') : JSON.stringify(val)
  return String(val)
}

function blankForm() {
  for (const f of props.fields) form[f.key] = f.type === 'checkbox' ? false : ''
}

function openCreate() {
  editing.value = null
  error.value = ''
  blankForm()
  showModal.value = true
}

function openEdit(row: any) {
  editing.value = row
  error.value = ''
  for (const f of props.fields) {
    const v = row[f.key]
    form[f.key] = f.type === 'checkbox' ? !!v : v ?? ''
  }
  showModal.value = true
}

function buildBody() {
  const body: Record<string, any> = {}
  for (const f of props.fields) {
    const v = form[f.key]
    if (f.type === 'checkbox') {
      body[f.key] = !!v
    } else if (v === '' || v === null || v === undefined) {
      continue
    } else if (f.type === 'number') {
      body[f.key] = Number(v)
    } else {
      body[f.key] = v
    }
  }
  return body
}

async function save() {
  saving.value = true
  error.value = ''
  try {
    const body = buildBody()
    if (editing.value) {
      await apiFetch(`${props.endpoint}/${editing.value.id}`, { method: 'PUT', body })
    } else {
      await apiFetch(props.endpoint, { method: 'POST', body })
    }
    showModal.value = false
    await load()
  } catch (e: any) {
    error.value = e?.data?.detail ? JSON.stringify(e.data.detail) : 'Save failed'
  } finally {
    saving.value = false
  }
}

async function remove(row: any) {
  if (!confirm(t('common.confirmDelete'))) return
  try {
    await apiFetch(`${props.endpoint}/${row.id}`, { method: 'DELETE' })
    await load()
  } catch (e) {
    console.error('Delete failed', e)
  }
}

async function load() {
  try {
    const res = await apiFetch<any>(`${props.endpoint}?limit=100`)
    items.value = res.items || []
  } catch {
    items.value = []
  }
}

onMounted(load)
</script>
