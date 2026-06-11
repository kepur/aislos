<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-6">{{ $t('admin.users') }}</h1>

    <!-- Filters -->
    <div class="flex gap-3 mb-4">
      <select v-model="roleFilter" class="text-sm border border-gray-300 rounded-lg px-3 py-1.5" @change="loadData">
        <option value="">All Roles</option>
        <option value="super_admin">Super Admin</option>
        <option value="admin">Admin</option>
        <option value="buyer">Buyer</option>
        <option value="vendor">Vendor</option>
        <option value="service_partner">Service Partner</option>
      </select>
    </div>

    <div class="bg-white rounded-xl border overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 border-b">
          <tr>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Name</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Email</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Role</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Active</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Joined</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">{{ $t('common.actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id" class="border-b hover:bg-gray-50">
            <td class="px-4 py-3 font-medium">{{ user.full_name || '-' }}</td>
            <td class="px-4 py-3">{{ user.email }}</td>
            <td class="px-4 py-3"><StatusBadge :status="user.role" /></td>
            <td class="px-4 py-3">
              <span :class="user.is_active ? 'text-green-600' : 'text-red-600'" class="text-xs font-medium">
                {{ user.is_active ? 'Active' : 'Inactive' }}
              </span>
            </td>
            <td class="px-4 py-3 text-gray-500">{{ new Date(user.created_at).toLocaleDateString() }}</td>
            <td class="px-4 py-3 flex gap-2">
              <button
                @click="toggleActive(user)"
                class="text-xs hover:underline"
                :class="user.is_active ? 'text-red-600' : 'text-green-600'"
              >
                {{ user.is_active ? 'Deactivate' : 'Activate' }}
              </button>
            </td>
          </tr>
          <tr v-if="!users.length">
            <td colspan="6" class="px-4 py-8 text-center text-gray-500">{{ $t('common.noData') }}</td>
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
definePageMeta({ layout: 'admin', middleware: 'admin' })

const { apiFetch } = useApi()
const users = ref<any[]>([])
const total = ref(0)
const skip = ref(0)
const roleFilter = ref('')

onMounted(loadData)

async function loadData() {
  try {
    let url = `/users?skip=${skip.value}&limit=20`
    if (roleFilter.value) url += `&role=${roleFilter.value}`
    const res = await apiFetch<any>(url)
    users.value = res.items || []
    total.value = res.total || 0
  } catch {}
}

function prevPage() { skip.value = Math.max(0, skip.value - 20); loadData() }
function nextPage() { skip.value += 20; loadData() }

async function toggleActive(user: any) {
  try {
    const updated = await apiFetch<any>(`/users/${user.id}/active?is_active=${!user.is_active}`, { method: 'PATCH' })
    const idx = users.value.findIndex(u => u.id === user.id)
    if (idx >= 0) users.value[idx] = updated
  } catch (e: any) { console.error(e) }
}
</script>
