<template>
  <div class="space-y-5">
    <div><h1 class="admin-page-title">Cebu Payouts</h1><p class="admin-page-desc">Process supplier payouts through the Core finance workflow</p></div>
    <p v-if="error" class="text-sm text-red-400">{{ error }}</p>
    <div class="grid gap-3 md:grid-cols-2">
      <article v-for="row in items" :key="row.id" class="admin-panel p-4 text-sm">
        <div class="flex justify-between gap-3"><p class="font-semibold text-white">{{ row.amount_minor }} {{ row.currency }}</p><StatusBadge :status="row.status"/></div><p class="mt-2 text-slate-400">Company {{ row.company_id }} · Order {{ row.order_id }}</p>
        <div class="mt-4 flex flex-wrap gap-2"><button v-for="status in statuses" :key="status" class="btn-secondary" @click="process(row,status)">{{ status }}</button></div>
      </article>
    </div>
  </div>
</template>
<script setup lang="ts">
definePageMeta({layout:'default',middleware:['auth']})
const {apiFetch}=useApi();const items=ref<any[]>([]);const error=ref('');const statuses=['PROCESSING','PAID','FAILED','ON_HOLD']
async function load(){items.value=(await apiFetch<any>('/admin/cebu-trade/payouts')).items}
async function process(row:any,status:string){const ref=status==='PAID'?window.prompt('Provider reference'):undefined;const failure=status==='FAILED'?window.prompt('Failure reason'):undefined;if((status==='PAID'&&!ref)||(status==='FAILED'&&!failure))return;const q=new URLSearchParams({new_status:status});if(ref)q.set('provider_reference',ref);if(failure)q.set('failure_reason',failure);try{await apiFetch(`/admin/cebu-trade/payouts/${row.id}/process?${q}`,{method:'POST'});await load()}catch(e:any){error.value=e?.data?.detail||e?.message}}
onMounted(()=>load().catch((e:any)=>error.value=e?.data?.detail||e?.message))
</script>
