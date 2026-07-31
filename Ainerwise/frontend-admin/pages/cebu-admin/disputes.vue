<template>
  <div class="space-y-5">
    <div><h1 class="admin-page-title">Cebu Disputes</h1><p class="admin-page-desc">Resolve real commerce disputes with an auditable reason</p></div>
    <p v-if="error" class="text-sm text-red-400">{{ error }}</p>
    <div class="grid gap-3">
      <article v-for="row in items" :key="row.id" class="admin-panel p-4 text-sm">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div><p class="font-semibold text-white">{{ row.reason_code }}</p><p class="text-slate-400">Order {{ row.commerce_order_id }} · opened by {{ row.opened_by_role }}</p><p class="mt-2 text-slate-300">{{ row.description || 'No description' }}</p></div>
          <StatusBadge :status="row.status" />
        </div>
        <div v-if="['open','under_review'].includes(row.status)" class="mt-4 flex flex-wrap gap-2">
          <button v-for="resolution in resolutions" :key="resolution" class="btn-secondary" @click="resolve(row, resolution)">{{ resolution }}</button>
        </div>
      </article>
    </div>
  </div>
</template>
<script setup lang="ts">
definePageMeta({layout:'default',middleware:['auth']})
const {apiFetch}=useApi();const items=ref<any[]>([]);const error=ref('');const resolutions=['resolved_buyer','resolved_supplier','closed']
async function load(){items.value=(await apiFetch<any>('/admin/cebu/disputes')).items}
async function resolve(row:any,resolution:string){const reason=window.prompt('Resolution reason is required');if(!reason)return;try{await apiFetch(`/admin/cebu/disputes/${row.id}/resolve`,{method:'POST',body:{resolution,reason}});await load()}catch(e:any){error.value=e?.data?.detail||e?.message}}
onMounted(()=>load().catch((e:any)=>error.value=e?.data?.detail||e?.message))
</script>
