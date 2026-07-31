<template>
  <div class="space-y-5">
    <div><h1 class="admin-page-title">Cebu Escrow</h1><p class="admin-page-desc">Capture, release and refund real escrow records with finance audit</p></div>
    <p v-if="error" class="text-sm text-red-400">{{ error }}</p>
    <div class="grid gap-3 md:grid-cols-2">
      <article v-for="row in items" :key="row.id" class="admin-panel p-4 text-sm">
        <div class="flex justify-between gap-3"><p class="font-semibold text-white">Order {{ row.order_id }}</p><StatusBadge :status="row.status"/></div>
        <p class="mt-2 text-slate-400">Authorized {{ row.auth_amount_minor }} · Captured {{ row.captured_amount_minor }} · Released {{ row.released_amount_minor }} · Refunded {{ row.refunded_amount_minor }}</p>
        <div class="mt-4 flex flex-wrap gap-2">
          <button v-if="row.status==='AUTH_HELD'" class="btn-secondary" @click="act(row,'capture')">Capture</button>
          <button v-if="['AUTH_HELD','CAPTURED'].includes(row.status)" class="btn-primary" @click="act(row,'release')">Release</button>
          <button v-if="['AUTH_HELD','CAPTURED','RELEASED','PARTIALLY_REFUNDED'].includes(row.status)" class="btn-secondary" @click="act(row,'refund',true)">Refund</button>
        </div>
      </article>
    </div>
  </div>
</template>
<script setup lang="ts">
definePageMeta({layout:'default',middleware:['auth']})
const {apiFetch}=useApi();const items=ref<any[]>([]);const error=ref('')
async function load(){items.value=(await apiFetch<any>('/admin/cebu/trade')).escrow.items}
async function act(row:any,action:string,reasonRequired=false){const amountText=window.prompt('Amount minor (blank = maximum)');if(amountText===null)return;const reason=reasonRequired?window.prompt('Reason is required'):undefined;if(reasonRequired&&!reason)return;try{await apiFetch(`/admin/cebu-trade/escrow/${row.id}/${action}`,{method:'POST',body:{amount_minor:amountText?Number(amountText):null,reason}});await load()}catch(e:any){error.value=e?.data?.detail||e?.message}}
onMounted(()=>load().catch((e:any)=>error.value=e?.data?.detail||e?.message))
</script>
