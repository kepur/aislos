<template>
  <section class="space-y-5">
    <div><p class="text-xs font-bold uppercase tracking-wider text-blue-300">{{ $t('partner.commercialPipeline') }}</p><h1 class="mt-1 text-3xl font-bold text-white">{{ $t('partner.navRfqs') }}</h1></div>
    <div class="flex flex-wrap gap-2"><button v-for="tab in tabs" :key="tab.key" class="rounded-lg border px-4 py-2 text-sm" :class="active===tab.key?'border-blue-400/40 bg-blue-500/15 text-blue-200':'border-white/10 text-slate-400'" @click="active=tab.key">{{ tab.label }}</button></div>
    <p v-if="error" class="pc-card text-red-300">{{ error }}</p>
    <NuxtLink v-for="item in filtered" :key="item.id" :to="localized(`/partner/rfqs/${item.id}`)" class="pc-card grid gap-4 lg:grid-cols-[1fr_auto]">
      <div><div class="flex flex-wrap items-center gap-3"><h2 class="font-semibold text-white">{{ item.title }}</h2><span class="rounded-full bg-blue-500/10 px-2 py-1 text-xs uppercase text-blue-300">{{ item.trade }}</span></div><p class="mt-3 line-clamp-2 text-sm text-slate-400">{{ item.scope_json?.summary||$t('partner.noScopeSummary') }}</p><p class="mt-3 text-xs text-slate-500">{{ location(item) }} · {{ $t('partner.deadline') }} {{ date(item.bid_deadline) }}</p></div>
      <div class="text-right"><p class="text-xs uppercase text-slate-500">{{ label(item.invitation_status) }}</p><p v-if="item.bid" class="mt-2 text-lg font-bold text-emerald-300">{{ item.bid.currency }} {{ Number(item.bid.amount).toLocaleString() }}</p><p v-else class="mt-2 text-sm text-blue-300">{{ $t('partner.respondRequest') }}</p></div>
    </NuxtLink>
    <p v-if="!filtered.length&&!error" class="pc-card text-slate-500">{{ $t('partner.noRequestsView') }}</p>
  </section>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()
definePageMeta({layout:'partner-workspace',middleware:['auth']})
const {apiFetch}=useApi();const items=ref<any[]>([]);const active=ref('open');const error=ref('')
const tabs=computed(()=>[{key:'open',label:t('partner.tabOpen')},{key:'all',label:t('partner.tabAll')},{key:'bid_submitted',label:t('partner.tabBidSubmitted')},{key:'declined',label:t('partner.tabDeclined')}])
const filtered=computed(()=>active.value==='all'?items.value:active.value==='open'?items.value.filter(x=>['sent','viewed'].includes(x.invitation_status)):items.value.filter(x=>x.invitation_status===active.value))
const { t } = useI18n();const { formatDay } = useLocaleFormat();const label=(v:string)=>v?.replaceAll('_',' ')||t('partner.unknown');const date=(v:string)=>v?formatDay(v):t('partner.notSetLc');const location=(x:any)=>[x.scope_json?.city,x.scope_json?.country].filter(Boolean).join(', ')||t('partner.locationPending')
onMounted(async()=>{try{items.value=(await apiFetch<any>('/partner/rfqs?limit=100')).items||[]}catch(e:any){error.value=e?.data?.detail||e?.message}})
</script>
