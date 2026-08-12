<template>
  <section class="space-y-5">
    <NuxtLink :to="localized('/partner/rfqs')" class="text-sm text-blue-300">&larr; {{ $t('partner.backRfqs') }}</NuxtLink>
    <p v-if="error" class="pc-card text-red-300">{{ error }}</p>
    <template v-if="rfq">
      <div class="pc-card"><div class="flex flex-wrap justify-between gap-4"><div><p class="text-xs uppercase tracking-wider text-blue-300">{{ rfq.trade }}</p><h1 class="mt-2 text-3xl font-bold text-white">{{ rfq.title }}</h1></div><div class="text-right"><p class="text-xs uppercase text-slate-500">{{ label(rfq.invitation_status) }}</p><p class="mt-2 text-sm text-slate-300">{{ $t('partner.deadlineLabel') }} {{ date(rfq.bid_deadline) }}</p></div></div><p class="mt-5 whitespace-pre-line text-sm leading-7 text-slate-300">{{ rfq.scope_json?.summary||$t('partner.noScopeSummary') }}</p></div>
      <div class="grid gap-5 lg:grid-cols-2">
        <div class="pc-card"><h2 class="font-semibold text-white">{{ $t('partner.scopeFacts') }}</h2><dl class="mt-4 space-y-3 text-sm"><div v-for="item in scope" :key="item.key" class="border-b border-white/5 pb-3"><dt class="text-xs uppercase text-slate-500">{{ label(item.key) }}</dt><dd class="mt-1 text-slate-200">{{ item.value }}</dd></div></dl></div>
        <div v-if="rfq.bid" class="pc-card"><p class="text-xs uppercase tracking-wider text-emerald-300">{{ $t('partner.yourBid') }}</p><p class="mt-3 text-3xl font-bold text-white">{{ rfq.bid.currency }} {{ Number(rfq.bid.amount).toLocaleString() }}</p><p class="mt-2 text-sm text-slate-400">{{ rfq.bid.lead_time_days??'—' }} {{ $t('prod.days') }} · {{ label(rfq.bid.status) }}</p><p class="mt-4 whitespace-pre-line text-sm text-slate-300">{{ rfq.bid.notes||$t('partner.noNotes') }}</p></div>
        <form v-else-if="canRespond" class="pc-card space-y-4" @submit.prevent="submit"><h2 class="font-semibold text-white">{{ $t('partner.submitBid') }}</h2><div class="grid gap-3 sm:grid-cols-2"><input v-model.number="form.amount" required min="0.01" step="0.01" type="number" class="input-field" :placeholder="$t('partner.amountPh')"><input v-model="form.currency" required maxlength="10" class="input-field" :placeholder="$t('partner.currencyPh')"></div><input v-model.number="form.lead_time_days" required min="0" type="number" class="input-field" :placeholder="$t('partner.leadTimePh')"><textarea v-model="form.notes" rows="5" class="input-field" :placeholder="$t('partner.notesPh')"/><div class="flex gap-3"><button class="btn-primary" :disabled="saving">{{ $t('partner.submitBidBtn') }}</button><button type="button" class="btn-secondary" :disabled="saving" @click="decline">{{ $t('portal.approvals.decline') }}</button></div></form>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()
definePageMeta({layout:'partner-workspace',middleware:['auth']})
const route=useRoute();const {apiFetch}=useApi();const rfq=ref<any>();const error=ref('');const saving=ref(false);const form=reactive({amount:null as number|null,currency:'EUR',lead_time_days:null as number|null,notes:''})
const { t } = useI18n();const { formatDay } = useLocaleFormat();const label=(v:string)=>v?.replaceAll('_',' ')||t('partner.unknown');const date=(v:string)=>v?formatDay(v):t('partner.notSetLc');const canRespond=computed(()=>rfq.value&&['sent','viewed'].includes(rfq.value.invitation_status)&&!['awarded','cancelled'].includes(rfq.value.status));const scope=computed(()=>Object.entries(rfq.value?.scope_json||{}).filter(([k,v])=>k!=='summary'&&v!==null&&v!=='').map(([key,value])=>({key,value:typeof value==='object'?JSON.stringify(value):String(value)})))
async function load(){rfq.value=await apiFetch(`/partner/rfqs/${route.params.id}`);form.currency=rfq.value.currency||'EUR'}async function submit(){saving.value=true;try{await apiFetch(`/partner/rfqs/${route.params.id}/bids`,{method:'POST',body:form});await load()}catch(e:any){error.value=e?.data?.detail||e?.message}finally{saving.value=false}}async function decline(){saving.value=true;try{await apiFetch(`/partner/rfqs/${route.params.id}/decline`,{method:'POST'});await load()}catch(e:any){error.value=e?.data?.detail||e?.message}finally{saving.value=false}}
onMounted(()=>load().catch((e:any)=>error.value=e?.data?.detail||e?.message))
</script>
