<template>
  <div class="space-y-5">
    <div>
      <h1 class="admin-page-title">Cebu Staff</h1>
      <p class="admin-page-desc">Invite internal operators and synchronize their logical Portal grants.</p>
    </div>
    <p v-if="error" class="text-sm text-red-400">{{ error }}</p>
    <form class="admin-panel grid gap-3 p-4 md:grid-cols-4" @submit.prevent="invite">
      <input v-model="form.email" required type="email" class="input-field" placeholder="Staff email" />
      <input v-model="form.full_name" class="input-field" placeholder="Full name" />
      <select v-model="form.role" class="input-field">
        <option v-for="role in roles" :key="role" :value="role">{{ role }}</option>
      </select>
      <button class="btn-primary">Invite staff</button>
    </form>
    <div class="admin-panel overflow-x-auto">
      <table class="admin-table min-w-full text-sm">
        <thead><tr><th>Email</th><th>Name</th><th>Role</th><th>Active</th><th>Created</th></tr></thead>
        <tbody>
          <tr v-for="row in items" :key="row.id">
            <td>{{ row.email }}</td>
            <td>{{ row.full_name || '-' }}</td>
            <td>
              <select class="input-field min-w-40" :value="row.role" @change="changeRole(row, ($event.target as HTMLSelectElement).value)">
                <option v-for="role in roles" :key="role" :value="role">{{ role }}</option>
              </select>
            </td>
            <td>
              <select class="input-field min-w-28" :value="row.is_active ? 'active' : 'disabled'" @change="changeActive(row, ($event.target as HTMLSelectElement).value)">
                <option value="active">active</option>
                <option value="disabled">disabled</option>
              </select>
            </td>
            <td>{{ row.created_at || '-' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default', middleware: ['auth'] })
const { apiFetch } = useApi()
const roles = ['admin', 'super_admin', 'sales_manager', 'project_manager', 'finance', 'marketing_operator']
const form = reactive({ email: '', full_name: '', role: 'finance' })
const items = ref<any[]>([])
const error = ref('')
async function load(){items.value=(await apiFetch<any>('/admin/cebu/staff')).items}
async function invite(){try{await apiFetch('/admin/cebu/staff/invite',{method:'POST',body:form});form.email='';form.full_name='';await load()}catch(e:any){error.value=e?.data?.detail||e?.message}}
async function changeRole(row:any,role:string){const reason=window.prompt('Reason for role change');if(!reason){await load();return}try{await apiFetch(`/admin/cebu/staff/${row.id}/role`,{method:'PUT',body:{role,reason}});await load()}catch(e:any){error.value=e?.data?.detail||e?.message;await load()}}
async function changeActive(row:any,status:string){try{await apiFetch(`/admin/cebu/users/${row.id}/active`,{method:'PATCH',body:{status,reason:'Cebu staff status update'}});await load()}catch(e:any){error.value=e?.data?.detail||e?.message;await load()}}
onMounted(()=>load().catch((e:any)=>error.value=e?.data?.detail||e?.message))
</script>
