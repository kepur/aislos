<template>
  <div class="space-y-5">
    <div><h1 class="admin-page-title">Cebu Commerce Orders</h1><p class="admin-page-desc">Manage lifecycle status and auditable operational holds.</p></div>
    <p v-if="error" class="text-sm text-red-400">{{ error }}</p>
    <div class="grid gap-3">
      <article v-for="row in items" :key="row.id" class="admin-panel p-4 text-sm">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div><p class="font-semibold text-white">{{ row.total_minor }} {{ row.currency }}</p><p class="text-slate-400">Order {{ row.id }}</p></div>
          <StatusBadge :status="row.admin_hold ? 'held' : row.status"/>
        </div>
        <p v-if="row.admin_hold_reason" class="mt-2 text-amber-300">{{ row.admin_hold_reason }}</p>
        <div class="mt-4 flex flex-wrap gap-2">
          <select class="input-field min-w-36" :value="row.status" @change="changeStatus(row, ($event.target as HTMLSelectElement).value)">
            <option v-for="status in statuses" :key="status" :value="status">{{ status }}</option>
          </select>
          <button v-if="!row.admin_hold" class="btn-secondary" @click="hold(row)">Hold</button>
          <button v-else class="btn-primary" @click="release(row)">Release hold</button>
        </div>
      </article>
    </div>
  </div>
</template>
<script setup lang="ts">
definePageMeta({layout:'default',middleware:['auth']})
const {apiFetch}=useApi();const items=ref<any[]>([]);const error=ref('');const statuses=['pending','confirmed','in_delivery','completed','disputed','cancelled']
async function load(){items.value=(await apiFetch<any>('/admin/cebu/orders')).items}
async function changeStatus(row:any,status:string){const reason=window.prompt('Status change reason')||undefined;try{await apiFetch(`/admin/cebu/orders/${row.id}/status`,{method:'PATCH',body:{status,reason}});await load()}catch(e:any){error.value=e?.data?.detail||e?.message;await load()}}
async function hold(row:any){const reason=window.prompt('Hold reason');if(!reason)return;try{await apiFetch(`/admin/cebu/orders/${row.id}/hold`,{method:'POST',body:{reason}});await load()}catch(e:any){error.value=e?.data?.detail||e?.message}}
async function release(row:any){const reason=window.prompt('Release reason');if(!reason)return;try{await apiFetch(`/admin/cebu/orders/${row.id}/release-hold`,{method:'POST',body:{reason}});await load()}catch(e:any){error.value=e?.data?.detail||e?.message}}
onMounted(()=>load().catch((e:any)=>error.value=e?.data?.detail||e?.message))
</script>
