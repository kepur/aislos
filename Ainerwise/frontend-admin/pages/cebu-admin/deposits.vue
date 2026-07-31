<template>
  <div class="space-y-5">
    <div><h1 class="admin-page-title">Cebu Wallet Deposits</h1><p class="admin-page-desc">Finance review changes real wallet balances and writes audit events</p></div>
    <p v-if="error" class="text-sm text-red-400">{{ error }}</p>
    <div class="grid gap-3 md:grid-cols-2">
      <article v-for="row in items" :key="row.id" class="admin-panel p-4 text-sm">
        <div class="flex justify-between gap-3"><p class="font-semibold text-white">{{ row.amount_minor }} {{ row.currency }}</p><StatusBadge :status="row.status"/></div>
        <p class="mt-2 text-slate-400">Owner {{ row.owner_user_id }}</p><p class="text-slate-400">TX {{ row.tx_hash || '-' }}</p>
        <div v-if="pending(row.status)" class="mt-4 flex gap-2">
          <button class="btn-primary" @click="act(row,'verify')">Verify</button>
          <button class="btn-secondary" @click="act(row,'reject')">Reject</button>
        </div>
      </article>
    </div>
  </div>
</template>
<script setup lang="ts">
definePageMeta({layout:'default',middleware:['auth']})
const {apiFetch}=useApi();const items=ref<any[]>([]);const error=ref('');const pending=(s:string)=>['PENDING_TX','SUBMITTED','UNDER_REVIEW'].includes(s)
async function load(){items.value=(await apiFetch<any>('/admin/cebu-trade/deposits')).items}
async function act(row:any,action:string){const note=window.prompt(`Admin note for ${action}`)||undefined;try{await apiFetch(`/admin/cebu-trade/deposits/${row.id}/${action}`,{method:'POST',body:{admin_note:note}});await load()}catch(e:any){error.value=e?.data?.detail||e?.message}}
onMounted(()=>load().catch((e:any)=>error.value=e?.data?.detail||e?.message))
</script>
