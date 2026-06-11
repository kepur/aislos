<template>
  <div v-if="lead">
    <NuxtLink to="/portal/leads" class="text-sm text-primary-600 hover:underline">&larr; Back to My Requirements</NuxtLink>

    <div class="mt-4 flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-900">Requirement Detail</h1>
      <StatusBadge :status="lead.status" />
    </div>

    <div class="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="bg-white rounded-xl border p-6">
        <h2 class="font-semibold text-gray-900 mb-4">Project Information</h2>
        <dl class="space-y-3 text-sm">
          <div class="flex"><dt class="w-32 text-gray-500">Type</dt><dd class="font-medium">{{ lead.project_type || '-' }}</dd></div>
          <div class="flex"><dt class="w-32 text-gray-500">Country</dt><dd class="font-medium">{{ lead.country || '-' }}</dd></div>
          <div class="flex"><dt class="w-32 text-gray-500">Budget</dt><dd class="font-medium">{{ lead.budget_range || '-' }}</dd></div>
          <div class="flex"><dt class="w-32 text-gray-500">Systems</dt><dd class="font-medium">{{ lead.systems_needed_json?.join(', ') || '-' }}</dd></div>
          <div class="flex"><dt class="w-32 text-gray-500">Submitted</dt><dd>{{ new Date(lead.created_at).toLocaleString() }}</dd></div>
        </dl>
      </div>

      <div class="bg-white rounded-xl border p-6">
        <h2 class="font-semibold text-gray-900 mb-4">Status Tracking</h2>
        <div class="space-y-3">
          <div v-for="step in statusSteps" :key="step.status" class="flex items-center gap-3">
            <div :class="[
              'w-3 h-3 rounded-full',
              isStatusReached(step.status) ? 'bg-primary-600' : 'bg-gray-300'
            ]" />
            <span :class="isStatusReached(step.status) ? 'text-gray-900 font-medium' : 'text-gray-400'" class="text-sm">
              {{ step.label }}
            </span>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-xl border p-6 lg:col-span-2">
        <h2 class="font-semibold text-gray-900 mb-4">Description</h2>
        <p class="text-sm text-gray-600 whitespace-pre-wrap">{{ lead.description || 'No description provided.' }}</p>
      </div>
    </div>
  </div>
  <div v-else class="text-center py-12 text-gray-500">{{ $t('common.loading') }}</div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'portal', middleware: 'auth' })

const route = useRoute()
const { apiFetch } = useApi()
const lead = ref<any>(null)

const statusSteps = [
  { status: 'new', label: 'Submitted' },
  { status: 'contacted', label: 'Under Review' },
  { status: 'qualified', label: 'Qualified' },
  { status: 'quoting', label: 'Preparing Quote' },
  { status: 'won', label: 'Accepted' },
]

const statusOrder = statusSteps.map(s => s.status)

function isStatusReached(status: string): boolean {
  if (!lead.value) return false
  const currentIdx = statusOrder.indexOf(lead.value.status)
  const checkIdx = statusOrder.indexOf(status)
  // Special cases
  if (lead.value.status === 'ai_analyzing' || lead.value.status === 'ai_completed') {
    return checkIdx <= 1 // At least "contacted" level
  }
  return checkIdx <= currentIdx
}

onMounted(async () => {
  try {
    lead.value = await apiFetch<any>(`/leads/${route.params.id}`)
  } catch {}
})
</script>
