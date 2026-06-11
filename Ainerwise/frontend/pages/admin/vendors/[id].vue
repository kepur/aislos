<template>
  <div v-if="vendor">
    <NuxtLink to="/admin/vendors" class="text-sm text-primary-600 hover:underline">&larr; Back to Vendors</NuxtLink>

    <div class="mt-4 flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-900">{{ vendor.name }}</h1>
      <StatusBadge :status="vendor.verification_status" />
    </div>

    <div class="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2 space-y-6">
        <!-- Company Info -->
        <div class="bg-white rounded-xl border p-6">
          <h2 class="font-semibold text-gray-900 mb-4">Company Information</h2>
          <dl class="grid grid-cols-2 gap-3 text-sm">
            <div><dt class="text-gray-500">Name</dt><dd class="font-medium">{{ vendor.name }}</dd></div>
            <div><dt class="text-gray-500">Type</dt><dd class="font-medium">{{ vendor.type }}</dd></div>
            <div><dt class="text-gray-500">Country</dt><dd class="font-medium">{{ vendor.country || '-' }}</dd></div>
            <div><dt class="text-gray-500">City</dt><dd class="font-medium">{{ vendor.city || '-' }}</dd></div>
            <div class="col-span-2"><dt class="text-gray-500">Address</dt><dd class="font-medium">{{ vendor.address || '-' }}</dd></div>
            <div class="col-span-2"><dt class="text-gray-500">Website</dt><dd class="font-medium"><a v-if="vendor.website" :href="vendor.website" target="_blank" class="text-primary-600 hover:underline">{{ vendor.website }}</a><span v-else>-</span></dd></div>
          </dl>
        </div>

        <!-- Contact Info -->
        <div class="bg-white rounded-xl border p-6">
          <h2 class="font-semibold text-gray-900 mb-4">Contact Information</h2>
          <dl class="grid grid-cols-2 gap-3 text-sm" v-if="vendor.contact_info">
            <div v-for="(value, key) in vendor.contact_info" :key="key">
              <dt class="text-gray-500 capitalize">{{ key }}</dt>
              <dd class="font-medium">{{ value }}</dd>
            </div>
          </dl>
          <p v-else class="text-sm text-gray-500">No contact information available.</p>
        </div>

        <!-- Description -->
        <div class="bg-white rounded-xl border p-6">
          <h2 class="font-semibold text-gray-900 mb-4">Description</h2>
          <p class="text-sm text-gray-600 whitespace-pre-wrap">{{ vendor.description || 'No description provided.' }}</p>
        </div>
      </div>

      <!-- Right column -->
      <div class="space-y-6">
        <StatusWorkflow
          :current-status="vendor.verification_status"
          entity="vendor"
          :loading="statusLoading"
          @transition="handleStatusChange"
        />

        <div class="bg-white rounded-xl border p-6">
          <h2 class="font-semibold text-gray-900 mb-4">Details</h2>
          <dl class="text-xs space-y-2">
            <div class="flex justify-between"><dt class="text-gray-500">ID</dt><dd class="font-mono">{{ vendor.id.slice(0, 8) }}...</dd></div>
            <div class="flex justify-between"><dt class="text-gray-500">Created</dt><dd>{{ new Date(vendor.created_at).toLocaleString() }}</dd></div>
          </dl>
        </div>
      </div>
    </div>
  </div>
  <div v-else class="text-center py-12 text-gray-500">{{ $t('common.loading') }}</div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'admin' })

const route = useRoute()
const { apiFetch } = useApi()
const vendor = ref<any>(null)
const statusLoading = ref(false)

onMounted(async () => {
  try {
    vendor.value = await apiFetch<any>(`/vendors/${route.params.id}`)
  } catch {}
})

async function handleStatusChange(newStatus: string) {
  statusLoading.value = true
  try {
    vendor.value = await apiFetch<any>(`/vendors/${route.params.id}/status`, {
      method: 'PATCH',
      body: { verification_status: newStatus },
    })
  } catch (e: any) {
    console.error('Status change failed:', e)
  } finally {
    statusLoading.value = false
  }
}
</script>
