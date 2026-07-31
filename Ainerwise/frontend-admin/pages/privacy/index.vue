<template>
  <div class="space-y-5">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div><h1 class="admin-page-title">Privacy Requests</h1><p class="mt-1 text-sm text-slate-500">Review data-subject requests. Deletion anonymizes access while retaining required business evidence.</p></div>
      <select v-model="statusFilter" class="input-field max-w-48" @change="load">
        <option value="">All statuses</option>
        <option value="requested">Requested</option>
        <option value="ready">Ready</option>
        <option value="completed">Completed</option>
        <option value="rejected">Rejected</option>
        <option value="cancelled">Cancelled</option>
      </select>
    </div>
    <p v-if="error" class="rounded-lg bg-red-50 p-3 text-sm text-red-700">{{ error }}</p>
    <div class="admin-panel overflow-x-auto">
      <table class="admin-table">
        <thead><tr><th>Type</th><th>User ID</th><th>Status</th><th>Requested</th><th>Reason</th><th>Actions</th></tr></thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td class="capitalize">{{ item.request_type }}</td>
            <td><code class="text-xs">{{ item.user_id }}</code></td>
            <td><StatusBadge :status="item.status" /></td>
            <td>{{ new Date(item.created_at).toLocaleString() }}</td>
            <td>{{ item.review_reason || '-' }}</td>
            <td>
              <div v-if="item.status === 'requested'" class="flex gap-2">
                <button class="text-xs text-red-600 hover:underline" :disabled="busy === item.id" @click="reject(item)">Reject</button>
                <button
                  v-if="item.request_type === 'delete'"
                  class="text-xs text-emerald-600 hover:underline"
                  :disabled="busy === item.id"
                  @click="complete(item)"
                >
                  Verify & anonymize
                </button>
              </div>
              <span v-else class="text-xs text-slate-400">No action</span>
            </td>
          </tr>
          <tr v-if="!items.length"><td colspan="6" class="py-8 text-center text-slate-500">No privacy requests.</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default', middleware: ['auth'] })
const { apiFetch } = useApi()
const items = ref<any[]>([])
const statusFilter = ref('requested')
const busy = ref('')
const error = ref('')
async function load(){try{error.value='';items.value=await apiFetch<any[]>(`/admin/privacy/requests${statusFilter.value?`?status=${statusFilter.value}`:''}`)}catch(e:any){error.value=e?.data?.detail||'Unable to load privacy requests'}}
async function reject(item:any){const reason=prompt('Rejection reason:');if(reason===null)return;busy.value=item.id;try{await apiFetch(`/admin/privacy/requests/${item.id}/reject`,{method:'POST',body:{reason}});await load()}finally{busy.value=''}}
async function complete(item:any){if(!confirm('Verify identity and anonymize this account? This disables login and revokes all Portal access.'))return;const reason=prompt('Verification / completion reason:')||'Identity verified';busy.value=item.id;try{await apiFetch(`/admin/privacy/requests/${item.id}/complete`,{method:'POST',body:{reason}});await load()}finally{busy.value=''}}
onMounted(load)
</script>
