<template><div class="space-y-4 p-4">
  <div v-if="project" class="m-card"><p class="text-[10px] uppercase tracking-wider text-indigo-500">AinerWise project workspace</p><h1 class="mt-2 text-lg font-bold text-slate-800">{{ project.title }}</h1><p class="mt-2 text-sm text-slate-500">{{ project.description }}</p><span class="mt-3 inline-flex rounded-full bg-indigo-50 px-3 py-1 text-xs text-indigo-600">{{ project.status }}</span></div>
  <div v-if="metrics" class="m-card"><div class="flex justify-between"><h2 class="font-semibold text-slate-800">Requirement facts</h2><span class="text-xs text-indigo-500">{{ metrics.missing_required.length }} gaps</span></div><button v-for="item in metrics.templates" :key="item.id" class="mt-2 w-full rounded-xl bg-slate-50 p-3 text-left" @click="editMetric(item)"><p class="text-sm font-medium text-slate-700">{{ item.label }}</p><p class="mt-1 text-xs text-slate-400">{{ metricValue(item.key) }}</p></button></div>
  <div class="m-card">
    <div class="flex justify-between gap-3">
      <div><h2 class="font-semibold text-slate-800">BOQ</h2><p class="text-xs text-slate-400">{{ report?.current_version ? `V${report.current_version.version_number} ${report.current_version.status}` : 'Not generated' }}</p></div>
      <button class="rounded-lg bg-indigo-500 px-3 py-2 text-xs font-semibold text-white" @click="freeze">Freeze</button>
    </div>
    <div class="mt-3 grid grid-cols-2 gap-2">
      <button class="rounded-lg bg-slate-100 p-2 text-xs text-slate-600" @click="estimate">Estimate prices</button>
      <button class="rounded-lg bg-slate-100 p-2 text-xs text-slate-600" @click="recalculate">New version</button>
    </div>
    <div v-for="row in report?.rows||[]" :key="row.id" class="mt-3 rounded-xl border border-slate-100 p-3">
      <div class="flex justify-between gap-2">
        <p class="text-sm font-medium text-slate-700">{{ row.name }}</p>
        <input type="checkbox" :checked="row.selected_for_purchase" :disabled="report.current_version.status==='FROZEN'" @change="toggleRow(row,$event)">
      </div>
      <p class="mt-1 text-xs text-slate-400">{{ row.qty }} {{ row.unit }}</p>
      <select :value="row.selected_tier" :disabled="report.current_version.status==='FROZEN'" class="mt-2 w-full rounded-lg bg-slate-50 p-2 text-xs" @change="setTier(row,$event)"><option>BUDGET</option><option>MID_RANGE</option><option>PREMIUM</option></select>
    </div>
  </div>
  <p v-if="message" class="m-card text-sm text-emerald-600">{{ message }}</p><p v-if="error" class="m-card text-sm text-red-600">{{ error }}</p>
</div></template>
<script setup lang="ts">
definePageMeta({middleware:['auth']});const route=useRoute();const {apiFetch}=useApi();const base=`/buyer/projects/${route.params.id}`;const project=ref<any>();const metrics=ref<any>();const report=ref<any>();const error=ref('');const message=ref('')
function metricValue(key:string){const row=metrics.value?.values?.find((v:any)=>v.key===key);return row?.value_json?.value??'Tap to enter'}
async function load(){[project.value,metrics.value,report.value]=await Promise.all([apiFetch(base),apiFetch(`${base}/metrics`),apiFetch(`${base}/report`)])}
async function editMetric(item:any){const raw=window.prompt(item.prompt||item.label,String(metricValue(item.key)==='Tap to enter'?'':metricValue(item.key)));if(raw===null)return;const value=Number.isFinite(Number(raw))&&raw.trim()!==''?Number(raw):raw;metrics.value=await apiFetch(`${base}/metrics`,{method:'PATCH',body:{metrics:[{key:item.key,label:item.label,value}]}})}
async function estimate(){await apiFetch(`${base}/price-estimate`,{method:'POST'});await recalculate();message.value='Prices estimated'}
async function recalculate(){report.value=await apiFetch(`${base}/report/recalculate`,{method:'POST'});message.value='New BOQ version created'}
async function freeze(){try{report.value=await apiFetch(`${base}/report/freeze`,{method:'POST'});message.value='BOQ frozen and audited'}catch(e:any){error.value=e?.data?.detail||e?.message}}
async function setTier(row:any,event:any){report.value=await apiFetch(`${base}/report/rows/${row.id}`,{method:'PATCH',body:{selected_tier:event.target.value}})}
async function toggleRow(row:any,event:any){report.value=await apiFetch(`${base}/report/rows/${row.id}`,{method:'PATCH',body:{selected_for_purchase:event.target.checked}})}
onMounted(()=>load().catch((e:any)=>error.value=e?.data?.detail||e?.message))
</script>
