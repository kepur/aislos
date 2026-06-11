<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-6">{{ $t('admin.vendors') }}</h1>
    <div class="bg-white rounded-xl border overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 border-b">
          <tr>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Company</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Country</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">{{ $t('common.status') }}</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Date</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">{{ $t('common.actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="vendor in vendors" :key="vendor.id" class="border-b hover:bg-gray-50">
            <td class="px-4 py-3 font-medium">{{ vendor.name }}</td>
            <td class="px-4 py-3">{{ vendor.country || '-' }}</td>
            <td class="px-4 py-3"><StatusBadge :status="vendor.verification_status" /></td>
            <td class="px-4 py-3 text-gray-500">{{ new Date(vendor.created_at).toLocaleDateString() }}</td>
            <td class="px-4 py-3">
              <NuxtLink :to="`/admin/vendors/${vendor.id}`" class="text-primary-600 hover:underline text-xs">{{ $t('common.viewDetails') }}</NuxtLink>
            </td>
          </tr>
          <tr v-if="!vendors.length">
            <td colspan="5" class="px-4 py-8 text-center text-gray-500">{{ $t('common.noData') }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'admin' })

const { apiFetch } = useApi()
const vendors = ref<any[]>([])

onMounted(async () => {
  try {
    const res = await apiFetch<any>('/vendors')
    vendors.value = res.items || res || []
  } catch {}
})
</script>
