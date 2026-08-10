<template>
  <section class="space-y-6">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div><p class="text-xs font-bold uppercase tracking-wider text-blue-300">Partner Company</p><h1 class="mt-1 text-3xl font-bold text-white">Operations overview</h1><p class="mt-2 text-sm text-slate-400">Respond to opportunities, coordinate dispatched work and track delivery performance.</p></div>
      <NuxtLink :to="localized('/partner/rfqs')" class="btn-primary">Review open RFQs</NuxtLink>
    </div>
    <p v-if="error" class="pc-card text-red-300">{{ error }}</p>
    <template v-if="dashboard">
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <NuxtLink v-for="card in cards" :key="card.label" :to="card.to" class="pc-card block"><p class="text-xs uppercase tracking-wider text-slate-500">{{ card.label }}</p><p class="mt-3 text-3xl font-bold" :class="card.color">{{ card.value }}</p></NuxtLink>
      </div>
      <div class="grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">
        <div class="pc-card">
          <div class="flex items-center justify-between"><h2 class="text-lg font-semibold text-white">Recent requests</h2><NuxtLink :to="localized('/partner/rfqs')" class="text-sm text-blue-300">View all</NuxtLink></div>
          <NuxtLink v-for="item in recent" :key="item.id" :to="localized(`/partner/rfqs/${item.id}`)" class="mt-3 flex items-center justify-between gap-4 rounded-xl border border-white/5 p-4 hover:border-blue-400/30"><div><p class="font-semibold text-white">{{ item.title }}</p><p class="mt-1 text-xs uppercase text-blue-300">{{ item.trade }}</p></div><span class="text-xs text-slate-400">{{ label(item.invitation_status) }}</span></NuxtLink>
          <p v-if="!recent.length" class="mt-4 text-sm text-slate-500">No requests assigned yet.</p>
        </div>
        <div class="pc-card">
          <h2 class="text-lg font-semibold text-white">Company status</h2>
          <dl class="mt-4 space-y-3 text-sm"><div v-for="row in companyRows" :key="row.label" class="flex justify-between gap-4 border-b border-white/5 pb-3"><dt class="text-slate-500">{{ row.label }}</dt><dd class="text-right font-medium text-slate-200">{{ row.value }}</dd></div></dl>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()
definePageMeta({ layout: 'partner-workspace', middleware: ['auth'] })
const { apiFetch } = useApi(); const dashboard=ref<any>(); const recent=ref<any[]>([]); const packages=ref<any[]>([]); const error=ref('')
const label=(value:string)=>value?.replaceAll('_',' ')||'unknown'
const cards=computed(()=>dashboard.value?[
  {label:'Open RFQs',value:dashboard.value.counts.open,to:'/partner/rfqs',color:'text-blue-300'},
  {label:'Bids submitted',value:dashboard.value.counts.bid_submitted,to:'/partner/rfqs',color:'text-emerald-300'},
  {label:'Delivery packages',value:packages.value.length,to:'/partner/work-packages',color:'text-amber-300'},
  {label:'Composite score',value:dashboard.value.metric.composite_score??'—',to:'/partner/performance',color:'text-violet-300'},
]:[])
const companyRows=computed(()=>dashboard.value?[
  {label:'Verification',value:label(dashboard.value.partner.verification_status)},
  {label:'Availability',value:label(dashboard.value.partner.availability_status)},
  {label:'Partner type',value:label(dashboard.value.partner.partner_type)},
  {label:'Coverage',value:[dashboard.value.partner.city,dashboard.value.partner.country].filter(Boolean).join(', ')||'Not set'},
]:[])
onMounted(async()=>{try{const [summary,rfqs,work]=await Promise.all([apiFetch<any>('/partner/dashboard'),apiFetch<any>('/partner/rfqs?limit=5'),apiFetch<any>('/partner/field-ops/work-packages')]);dashboard.value=summary;recent.value=rfqs.items||[];packages.value=work.items||[]}catch(e:any){error.value=e?.data?.detail||e?.message}})
</script>
