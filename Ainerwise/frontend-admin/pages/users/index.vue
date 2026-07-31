<template>
  <div>
    <h1 class="admin-page-title mb-6">{{ $t('admin.users') }}</h1>

    <!-- Filters -->
    <div class="flex gap-3 mb-4">
      <select v-model="roleFilter" class="text-sm border border-gray-300 rounded-lg px-3 py-1.5" @change="loadData">
        <option value="">All Roles</option>
        <option v-for="role in roles" :key="role" :value="role">{{ roleLabel(role) }}</option>
      </select>
      <button class="px-3 py-1.5 text-sm border rounded-lg hover:bg-gray-50" :disabled="loading" @click="loadData">
        {{ loading ? 'Loading...' : 'Refresh' }}
      </button>
    </div>

    <p v-if="error" class="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{{ error }}</p>

    <div class="admin-panel">
      <table class="admin-table w-full text-sm">
        <thead>
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
          <tr v-for="user in users" :key="user.id" class="border-b">
            <td class="px-4 py-3 font-medium">{{ user.full_name || '-' }}</td>
            <td class="px-4 py-3">{{ user.email }}</td>
            <td class="px-4 py-3">
              <select
                class="rounded-lg border border-gray-300 px-2 py-1 text-xs"
                :value="user.role"
                :disabled="busyId === user.id || user.id === currentUser?.id || !canManageRole(user)"
                @change="changeRole(user, ($event.target as HTMLSelectElement).value)"
              >
                <option v-for="role in assignableRoles(user)" :key="role" :value="role">{{ roleLabel(role) }}</option>
              </select>
            </td>
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
                :disabled="busyId === user.id || (user.id === currentUser?.id && user.is_active) || !canManageRole(user)"
              >
                {{ busyId === user.id ? 'Saving...' : user.is_active ? 'Deactivate' : 'Activate' }}
              </button>
            </td>
          </tr>
          <tr v-if="loading && !users.length">
            <td colspan="6" class="px-4 py-8 text-center text-gray-500">Loading users...</td>
          </tr>
          <tr v-else-if="!users.length">
            <td colspan="6" class="px-4 py-8 text-center text-gray-500">{{ error ? 'Users could not be loaded.' : $t('common.noData') }}</td>
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
const { user: currentUser } = useAuth()
const users = ref<any[]>([])
const total = ref(0)
const skip = ref(0)
const roleFilter = ref('')
const loading = ref(false)
const busyId = ref('')
const error = ref('')
const roles = [
  'super_admin', 'admin', 'sales_manager', 'project_manager', 'finance', 'marketing_operator',
  'buyer', 'customer_user', 'vendor', 'developer', 'service_partner', 'partner_worker',
  'maintenance_worker',
]

onMounted(loadData)

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    let url = `/users?skip=${skip.value}&limit=20`
    if (roleFilter.value) url += `&role=${roleFilter.value}`
    const res = await apiFetch<any>(url)
    users.value = res.items || []
    total.value = res.total || 0
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Unable to load users'
  } finally {
    loading.value = false
  }
}

function prevPage() { skip.value = Math.max(0, skip.value - 20); loadData() }
function nextPage() { skip.value += 20; loadData() }
function roleLabel(role: string) { return role.split('_').map(part => part[0].toUpperCase() + part.slice(1)).join(' ') }
function canManageRole(target: any) { return target.role !== 'super_admin' || currentUser.value?.role === 'super_admin' }
function assignableRoles(target: any) {
  return currentUser.value?.role === 'super_admin' || target.role === 'super_admin'
    ? roles
    : roles.filter(role => role !== 'super_admin')
}

async function changeRole(target: any, role: string) {
  if (role === target.role) return
  busyId.value = target.id
  error.value = ''
  try {
    const updated = await apiFetch<any>(`/users/${target.id}/role?role=${encodeURIComponent(role)}`, { method: 'PATCH' })
    const idx = users.value.findIndex(item => item.id === target.id)
    if (idx >= 0) users.value[idx] = updated
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Unable to change role'
    await loadData()
  } finally {
    busyId.value = ''
  }
}

async function toggleActive(user: any) {
  busyId.value = user.id
  error.value = ''
  try {
    const updated = await apiFetch<any>(`/users/${user.id}/active?is_active=${!user.is_active}`, { method: 'PATCH' })
    const idx = users.value.findIndex(u => u.id === user.id)
    if (idx >= 0) users.value[idx] = updated
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Unable to update account'
  } finally {
    busyId.value = ''
  }
}
</script>
