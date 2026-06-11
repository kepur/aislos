<template>
  <div v-if="solution">
    <NuxtLink to="/admin/solutions" class="text-sm text-primary-600 hover:underline">&larr; Back to Solutions</NuxtLink>
    <h1 class="text-2xl font-bold text-gray-900 mt-4 mb-6">Edit Solution</h1>

    <form class="max-w-3xl space-y-6" @submit.prevent="handleSubmit">
      <div class="bg-white rounded-xl border p-6 space-y-4">
        <h2 class="font-semibold text-gray-900">Basic Information</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Title *</label>
            <input v-model="form.title" type="text" required class="input-field" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Category</label>
            <select v-model="form.category" class="input-field">
              <option value="">Select category</option>
              <option value="hospitality">Hospitality</option>
              <option value="residential">Residential</option>
              <option value="commercial">Commercial</option>
              <option value="security">Security</option>
              <option value="energy">Energy</option>
              <option value="networking">Networking</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Sort Order</label>
            <input v-model.number="form.sort_order" type="number" class="input-field" />
          </div>
          <div class="flex items-end">
            <label class="flex items-center gap-2 text-sm">
              <input v-model="form.public_visible" type="checkbox" class="rounded border-gray-300" />
              Publicly Visible
            </label>
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
          <textarea v-model="form.description" rows="4" class="input-field" />
        </div>
      </div>

      <div class="bg-white rounded-xl border p-6 space-y-4">
        <h2 class="font-semibold text-gray-900">Details (comma-separated lists)</h2>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Target Scenarios</label>
          <input v-model="targetScenariosStr" type="text" class="input-field" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Pain Points</label>
          <input v-model="painPointsStr" type="text" class="input-field" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Delivery Flow Steps</label>
          <input v-model="deliveryFlowStr" type="text" class="input-field" />
        </div>
      </div>

      <div class="flex gap-3">
        <button type="submit" :disabled="loading" class="btn-primary text-sm">
          {{ loading ? 'Saving...' : 'Save Changes' }}
        </button>
        <NuxtLink to="/admin/solutions" class="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50">Cancel</NuxtLink>
      </div>
    </form>
  </div>
  <div v-else class="text-center py-12 text-gray-500">{{ $t('common.loading') }}</div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'admin' })

const route = useRoute()
const { apiFetch } = useApi()
const solution = ref<any>(null)
const loading = ref(false)

const form = reactive({
  title: '',
  category: '',
  description: '',
  public_visible: true,
  sort_order: 0,
})

const targetScenariosStr = ref('')
const painPointsStr = ref('')
const deliveryFlowStr = ref('')

onMounted(async () => {
  try {
    const sol = await apiFetch<any>(`/solutions/${route.params.id}`)
    solution.value = sol
    Object.assign(form, {
      title: sol.title || '',
      category: sol.category || '',
      description: sol.description || '',
      public_visible: sol.public_visible ?? true,
      sort_order: sol.sort_order || 0,
    })
    targetScenariosStr.value = (sol.target_scenarios_json || []).join(', ')
    painPointsStr.value = (sol.pain_points_json || []).join(', ')
    deliveryFlowStr.value = (sol.delivery_flow_json || []).join(', ')
  } catch {}
})

function splitCSV(str: string): string[] {
  return str.split(',').map(s => s.trim()).filter(Boolean)
}

async function handleSubmit() {
  loading.value = true
  try {
    const payload: Record<string, any> = {
      ...form,
      target_scenarios_json: splitCSV(targetScenariosStr.value),
      pain_points_json: splitCSV(painPointsStr.value),
      delivery_flow_json: splitCSV(deliveryFlowStr.value),
    }
    solution.value = await apiFetch<any>(`/solutions/${route.params.id}`, {
      method: 'PUT',
      body: payload,
    })
  } catch (e: any) {
    console.error('Update failed:', e)
  } finally {
    loading.value = false
  }
}
</script>
