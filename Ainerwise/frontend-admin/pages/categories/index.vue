<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="admin-page-title">{{ $t('admin.categories') }}</h1>
      <button @click="showCreateModal = true" class="btn-primary text-sm">{{ $t('common.create') }}</button>
    </div>

    <div class="admin-panel">
      <table class="admin-table w-full text-sm">
        <thead>
          <tr>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Name</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Slug</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Parent</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Icon</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Order</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">{{ $t('common.actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="cat in categories" :key="cat.id" class="border-b">
            <td class="px-4 py-3 font-medium">
              <span v-if="cat.parent_id" class="text-gray-400 mr-1">&nbsp;&nbsp;└</span>
              {{ cat.name }}
            </td>
            <td class="px-4 py-3 text-gray-500 font-mono text-xs">{{ cat.slug }}</td>
            <td class="px-4 py-3">{{ getParentName(cat.parent_id) }}</td>
            <td class="px-4 py-3">{{ cat.icon || '-' }}</td>
            <td class="px-4 py-3">{{ cat.sort_order }}</td>
            <td class="px-4 py-3">
              <button @click="startEdit(cat)" class="text-primary-600 hover:underline text-xs">{{ $t('common.edit') }}</button>
            </td>
          </tr>
          <tr v-if="!categories.length">
            <td colspan="6" class="px-4 py-8 text-center text-gray-500">{{ $t('common.noData') }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showCreateModal || editingCat" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-xl w-full max-w-md p-6 space-y-4">
        <h2 class="text-lg font-semibold">{{ editingCat ? 'Edit' : 'Create' }} Category</h2>
        <form @submit.prevent="editingCat ? handleUpdate() : handleCreate()" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Name *</label>
            <input v-model="form.name" type="text" required class="input-field" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Slug *</label>
            <input v-model="form.slug" type="text" required class="input-field" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Parent Category</label>
            <select v-model="form.parent_id" class="input-field">
              <option value="">None (root)</option>
              <option v-for="c in rootCategories" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Icon</label>
              <input v-model="form.icon" type="text" class="input-field" placeholder="mdi-lightbulb" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Sort Order</label>
              <input v-model.number="form.sort_order" type="number" class="input-field" />
            </div>
          </div>
          <div class="flex gap-3 pt-2">
            <button type="submit" :disabled="saving" class="btn-primary text-sm">
              {{ saving ? 'Saving...' : (editingCat ? 'Save' : 'Create') }}
            </button>
            <button type="button" @click="closeModal" class="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { apiFetch } = useApi()
const categories = ref<any[]>([])
const showCreateModal = ref(false)
const editingCat = ref<any>(null)
const saving = ref(false)

const form = reactive({
  name: '',
  slug: '',
  parent_id: '',
  icon: '',
  sort_order: 0,
})

const rootCategories = computed(() => categories.value.filter(c => !c.parent_id))

onMounted(loadData)

async function loadData() {
  try {
    const res = await apiFetch<any>('/product-categories')
    categories.value = res.items || res || []
  } catch {}
}

function getParentName(parentId: string | null): string {
  if (!parentId) return '-'
  const parent = categories.value.find(c => c.id === parentId)
  return parent?.name || '-'
}

function closeModal() {
  showCreateModal.value = false
  editingCat.value = null
  Object.assign(form, { name: '', slug: '', parent_id: '', icon: '', sort_order: 0 })
}

function startEdit(cat: any) {
  editingCat.value = cat
  Object.assign(form, {
    name: cat.name || '',
    slug: cat.slug || '',
    parent_id: cat.parent_id || '',
    icon: cat.icon || '',
    sort_order: cat.sort_order || 0,
  })
}

async function handleCreate() {
  saving.value = true
  try {
    const payload: Record<string, any> = { ...form }
    if (!payload.parent_id) delete payload.parent_id
    if (!payload.icon) delete payload.icon
    await apiFetch('/product-categories', { method: 'POST', body: payload })
    closeModal()
    await loadData()
  } catch (e: any) { console.error(e) }
  finally { saving.value = false }
}

async function handleUpdate() {
  saving.value = true
  try {
    const payload: Record<string, any> = { ...form }
    if (!payload.parent_id) payload.parent_id = null
    if (!payload.icon) payload.icon = null
    await apiFetch(`/product-categories/${editingCat.value.id}`, { method: 'PUT', body: payload })
    closeModal()
    await loadData()
  } catch (e: any) { console.error(e) }
  finally { saving.value = false }
}
</script>
