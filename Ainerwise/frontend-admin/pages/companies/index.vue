<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="admin-page-title">{{ $t('admin.companies') }}</h1>
    </div>

    <div class="flex gap-3 mb-4">
      <select v-model="typeFilter" class="text-sm border border-gray-300 rounded-lg px-3 py-1.5" @change="loadData">
        <option value="">All Types</option>
        <option value="buyer">Buyer</option>
        <option value="vendor">Vendor</option>
        <option value="service_partner">Service Partner</option>
      </select>
    </div>

    <div class="admin-panel">
      <table class="admin-table w-full text-sm">
        <thead>
          <tr>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Name</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Type</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Country</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">{{ $t('common.status') }}</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Created</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="company in companies" :key="company.id" class="border-b">
            <td class="px-4 py-3 font-medium">{{ company.name }}</td>
            <td class="px-4 py-3"><StatusBadge :status="company.type" /></td>
            <td class="px-4 py-3">{{ company.country || '-' }}</td>
            <td class="px-4 py-3"><StatusBadge :status="company.verification_status" /></td>
            <td class="px-4 py-3 text-gray-500">{{ new Date(company.created_at).toLocaleDateString() }}</td>
          </tr>
          <tr v-if="!companies.length">
            <td colspan="5" class="px-4 py-8 text-center text-gray-500">{{ $t('common.noData') }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="total > 20" class="mt-4 flex justify-center gap-2">
      <button @click="prevPage" :disabled="skip === 0" class="px-3 py-1 text-sm border rounded hover:bg-gray-50 disabled:opacity-50">Previous</button>
      <span class="px-3 py-1 text-sm text-gray-600">{{ skip + 1 }}-{{ Math.min(skip + 20, total) }} of {{ total }}</span>
      <button @click="nextPage" :disabled="skip + 20 >= total" class="px-3 py-1 text-sm border rounded hover:bg-gray-50 disabled:opacity-50">Next</button>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { apiFetch } = useApi()
const companies = ref<any[]>([])
const total = ref(0)
const skip = ref(0)
const typeFilter = ref('')

onMounted(loadData)

async function loadData() {
  try {
    let url = `/companies?skip=${skip.value}&limit=20`
    if (typeFilter.value) url += `&type=${typeFilter.value}`
    const res = await apiFetch<any>(url)
    companies.value = res.items || []
    total.value = res.total || 0
  } catch {}
}

function prevPage() { skip.value = Math.max(0, skip.value - 20); loadData() }
function nextPage() { skip.value += 20; loadData() }
</script>
