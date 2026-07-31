<template>
  <div class="space-y-5">
    <div><h1 class="admin-page-title">Cebu Ad Campaigns</h1><p class="admin-page-desc">Approve, reject or pause supplier marketplace campaigns</p></div>
    <p v-if="error" class="text-sm text-red-400">{{ error }}</p>
    <div class="grid gap-3 md:grid-cols-2">
      <article v-for="row in items" :key="row.id" class="admin-panel p-4 text-sm">
        <div class="flex justify-between gap-3"><p class="font-semibold text-white">{{ row.title }}</p><StatusBadge :status="row.status"/></div>
        <p class="mt-2 text-slate-400">{{ row.placement }} · {{ row.spent_minor }}/{{ row.budget_minor }} {{ row.currency }}</p>
        <div class="mt-4 flex flex-wrap gap-2">
          <button class="btn-primary" @click="act(row,'ACTIVE')">Approve</button>
          <button class="btn-secondary" @click="act(row,'REJECTED',true)">Reject</button>
          <button class="btn-secondary" @click="act(row,'PAUSED',true)">Pause</button>
        </div>
      </article>
    </div>
  </div>
</template>
<script setup lang="ts">
definePageMeta({layout:'default',middleware:['auth']})
const {apiFetch}=useApi();const items=ref<any[]>([]);const error=ref('')
async function load(){items.value=(await apiFetch<any>('/admin/cebu-trade/ads/campaigns')).items}
async function act(row:any,status:string,ask=false){const reason=ask?window.prompt('Reason'):undefined;if(ask&&!reason)return;try{await apiFetch(`/admin/cebu-trade/ads/campaigns/${row.id}/status`,{method:'PATCH',body:{status,rejection_reason:reason}});await load()}catch(e:any){error.value=e?.data?.detail||e?.message}}
onMounted(()=>load().catch((e:any)=>error.value=e?.data?.detail||e?.message))
</script>
