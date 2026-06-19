<template>
  <div class="space-y-4">
    <div class="flex items-center gap-3 flex-wrap">
      <input v-model="search" type="search" placeholder="Search name or email…" class="input max-w-xs" />
      <select v-model="roleFilter" class="input w-40">
        <option value="">All roles</option>
        <option value="BUYER">Buyer</option>
        <option value="SUPPLIER_ADMIN">Supplier</option>
        <option value="ADMIN">Admin</option>
        <option value="SUPER_ADMIN">Super Admin</option>
      </select>
      <span class="ml-auto text-sm text-slate-500">{{ filtered.length }} users</span>
    </div>

    <div class="card overflow-hidden">
      <table class="w-full">
        <thead>
          <tr>
            <th class="table-th">User</th>
            <th class="table-th">Role</th>
            <th class="table-th">Status</th>
            <th class="table-th">Joined</th>
            <th class="table-th">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading"><td colspan="5" class="table-td text-center py-10 text-slate-400">Loading…</td></tr>
          <tr v-else-if="!filtered.length"><td colspan="5" class="table-td text-center py-10 text-slate-400">No users found</td></tr>
          <tr v-for="u in filtered" :key="u.id" class="hover:bg-slate-50">
            <td class="table-td">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 font-bold text-xs flex-shrink-0">
                  {{ (u.full_name || u.email).charAt(0).toUpperCase() }}
                </div>
                <div>
                  <p class="font-medium text-slate-900">{{ u.full_name || '—' }}</p>
                  <p class="text-xs text-slate-400">{{ u.email }}</p>
                </div>
              </div>
            </td>
            <td class="table-td"><span :class="roleBadge(u.role)" class="badge">{{ u.role }}</span></td>
            <td class="table-td"><span :class="u.status === 'ACTIVE' ? 'badge-green' : 'badge-red'" class="badge">{{ u.status }}</span></td>
            <td class="table-td text-slate-400">{{ fmtDate(u.created_at) }}</td>
            <td class="table-td">
              <div class="flex gap-2">
                <button v-if="u.status === 'ACTIVE'" class="btn btn-danger py-1 px-3 text-xs" @click="setStatus(u, 'SUSPENDED')">Suspend</button>
                <button v-else class="btn btn-success py-1 px-3 text-xs" @click="setStatus(u, 'ACTIVE')">Activate</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api, fmtDate } from '@/utils/api'

const loading = ref(true)
const users = ref([])
const search = ref('')
const roleFilter = ref('')

const filtered = computed(() =>
  users.value.filter(u => {
    const q = search.value.toLowerCase()
    return (!q || u.email.toLowerCase().includes(q) || (u.full_name||'').toLowerCase().includes(q))
      && (!roleFilter.value || u.role === roleFilter.value)
  })
)

function roleBadge(role) {
  if (['SUPER_ADMIN','ADMIN'].includes(role)) return 'badge-red'
  if (['SUPPLIER_ADMIN','SUPPLIER_AGENT'].includes(role)) return 'badge-amber'
  return 'badge-blue'
}

async function setStatus(user, status) {
  try {
    const { data } = await api.post(`/admin/users/${user.id}/status`, {
      status, reason_code: 'ADMIN_ACTION', reason_text: `Admin set to ${status}`, notify_user: false,
    })
    const idx = users.value.findIndex(u => u.id === data.id)
    if (idx >= 0) users.value[idx] = data
  } catch (e) {
    alert(e.response?.data?.detail || 'Action failed')
  }
}

onMounted(async () => {
  users.value = await api.get('/admin/users').then(r => r.data)
  loading.value = false
})
</script>
