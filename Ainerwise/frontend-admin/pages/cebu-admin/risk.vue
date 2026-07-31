<template>
  <div class="space-y-5">
    <div><h1 class="admin-page-title">Cebu Risk Flags</h1><p class="admin-page-desc">Create, investigate and close auditable risk cases.</p></div>
    <p v-if="error" class="text-sm text-red-400">{{ error }}</p>
    <form class="admin-panel grid gap-3 p-4 md:grid-cols-5" @submit.prevent="create">
      <input v-model="form.subject_type" required class="input-field" placeholder="Subject type"/>
      <input v-model="form.subject_id" required class="input-field" placeholder="Subject UUID"/>
      <input v-model="form.reason_code" required class="input-field" placeholder="Reason code"/>
      <select v-model="form.severity" class="input-field"><option v-for="s in severities" :key="s">{{ s }}</option></select>
      <button class="btn-primary">Create flag</button>
    </form>
    <div class="grid gap-3">
      <article v-for="row in items" :key="row.id" class="admin-panel p-4 text-sm">
        <div class="flex justify-between gap-3"><p class="font-semibold text-white">{{ row.reason_code }}</p><StatusBadge :status="row.status"/></div>
        <p class="mt-2 text-slate-400">{{ row.subject_type }} · {{ row.subject_id }} · {{ row.severity }}</p>
        <button v-if="row.status==='open'" class="btn-secondary mt-4" @click="act(row)">Record action</button>
      </article>
    </div>
  </div>
</template>
<script setup lang="ts">
definePageMeta({layout:'default',middleware:['auth']})
const {apiFetch}=useApi();const items=ref<any[]>([]);const error=ref('');const severities=['low','medium','high','critical']
const form=reactive({subject_type:'commerce_order',subject_id:'',reason_code:'manual_review',severity:'medium'})
async function load(){items.value=(await apiFetch<any>('/admin/cebu/risk-flags?status=')).items}
async function create(){try{await apiFetch('/admin/cebu/risk-flags',{method:'POST',body:form});form.subject_id='';await load()}catch(e:any){error.value=e?.data?.detail||e?.message}}
async function act(row:any){const action_taken=window.prompt('Action taken');if(!action_taken)return;const status=window.prompt('New status: resolved or dismissed','resolved');if(!status)return;try{await apiFetch(`/admin/cebu/risk-flags/${row.id}/action`,{method:'POST',body:{status,action_taken}});await load()}catch(e:any){error.value=e?.data?.detail||e?.message}}
onMounted(()=>load().catch((e:any)=>error.value=e?.data?.detail||e?.message))
</script>
