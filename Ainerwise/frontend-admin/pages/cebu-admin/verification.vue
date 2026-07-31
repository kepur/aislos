<template>
  <div class="space-y-5">
    <div><h1 class="admin-page-title">Cebu KYC Verification Queue</h1><p class="admin-page-desc">Make real company verification decisions with reviewer notes</p></div>
    <p v-if="error" class="text-sm text-red-400">{{ error }}</p>
    <div class="grid gap-3">
      <article v-for="row in items" :key="row.id" class="admin-panel p-4 text-sm">
        <div class="flex justify-between gap-3"><p class="font-semibold text-white">Company {{ row.company_id }}</p><StatusBadge :status="row.status"/></div>
        <p class="mt-2 text-slate-400">{{ row.decision_reason || 'Awaiting decision' }}</p>
        <div v-if="['SUBMITTED','IN_REVIEW'].includes(row.status)" class="mt-4 flex flex-wrap gap-2"><button v-for="decision in decisions" :key="decision" class="btn-secondary" @click="decide(row,decision)">{{ decision }}</button></div>
      </article>
    </div>
  </div>
</template>
<script setup lang="ts">
definePageMeta({layout:'default',middleware:['auth']})
const {apiFetch}=useApi();const items=ref<any[]>([]);const error=ref('');const decisions=['APPROVE_BASIC','APPROVE_BUSINESS','REQUEST_MORE_INFO','REJECT','ESCALATE_TO_RISK']
async function load(){items.value=(await apiFetch<any>('/admin/kyc/verification/queue')).items}
async function decide(row:any,decision:string){const reason=window.prompt('Decision reason');if(!reason)return;try{await apiFetch(`/admin/kyc/verification/${row.id}/decide`,{method:'POST',body:{decision,decision_reason:reason,user_facing_note:reason}});await load()}catch(e:any){error.value=e?.data?.detail||e?.message}}
onMounted(()=>load().catch((e:any)=>error.value=e?.data?.detail||e?.message))
</script>
