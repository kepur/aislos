<template>
  <div class="space-y-5">
    <div><h1 class="admin-page-title">Cebu Companies</h1><p class="admin-page-desc">Verification and operational status are separate controls.</p></div>
    <p v-if="error" class="text-sm text-red-400">{{ error }}</p>
    <div class="admin-panel overflow-x-auto">
      <table class="admin-table min-w-full text-sm">
        <thead><tr><th>Name</th><th>Type</th><th>Country</th><th>Verification</th><th>Operational status</th></tr></thead>
        <tbody>
          <tr v-for="row in items" :key="row.id">
            <td>{{ row.name }}</td><td><StatusBadge :status="row.type"/></td><td>{{ row.country || '-' }}</td>
            <td>
              <select class="input-field min-w-32" :value="row.verification_status" @change="verification(row, ($event.target as HTMLSelectElement).value)">
                <option v-for="status in verificationStatuses" :key="status" :value="status">{{ status }}</option>
              </select>
            </td>
            <td>
              <select class="input-field min-w-32" :value="row.operational_status" @change="operation(row, ($event.target as HTMLSelectElement).value)">
                <option v-for="status in operationStatuses" :key="status" :value="status">{{ status }}</option>
              </select>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
<script setup lang="ts">
definePageMeta({layout:'default',middleware:['auth']})
const {apiFetch}=useApi();const items=ref<any[]>([]);const error=ref('')
const verificationStatuses=['pending','review','verified','rejected','suspended'];const operationStatuses=['pending','active','restricted','suspended']
async function load(){items.value=(await apiFetch<any>('/admin/cebu/companies')).items}
async function verification(row:any,status:string){const reason=window.prompt('Verification reason')||undefined;try{await apiFetch(`/admin/cebu/companies/${row.id}/verification`,{method:'PATCH',body:{verification_status:status,reason}});await load()}catch(e:any){error.value=e?.data?.detail||e?.message;await load()}}
async function operation(row:any,status:string){const reason=window.prompt('Operational status reason');if(!reason){await load();return}try{await apiFetch(`/admin/cebu/companies/${row.id}/status`,{method:'PATCH',body:{status,reason}});await load()}catch(e:any){error.value=e?.data?.detail||e?.message;await load()}}
onMounted(()=>load().catch((e:any)=>error.value=e?.data?.detail||e?.message))
</script>
