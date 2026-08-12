<template>
  <section class="space-y-5">
    <div v-if="project" class="pc-card">
      <p class="text-xs uppercase tracking-wider text-indigo-400">{{ $t('bProj.sharedWorkspace') }}</p>
      <div class="mt-2 flex flex-wrap items-start justify-between gap-4"><div><h1 class="text-2xl font-bold text-white">{{ project.title }}</h1><p class="mt-2 text-sm text-slate-400">{{ project.description || $t('bProj.descFallback2') }}</p></div><span class="rounded-full bg-slate-800 px-3 py-1 text-xs text-indigo-300">{{ project.status }}</span></div>
    </div>

    <div v-if="metrics" class="pc-card">
      <div class="flex items-center justify-between"><div><h2 class="text-lg font-semibold text-white">{{ $t('bProj.reqFacts') }}</h2><p class="text-sm text-slate-400">{{ $t('bProj.requiredGaps', { n: metrics.missing_required.length }) }}</p></div></div>
      <div class="mt-4 grid gap-3 md:grid-cols-2">
        <button v-for="template in metrics.templates" :key="template.id" class="rounded-xl border border-slate-700 p-3 text-left hover:border-indigo-400/50" @click="editMetric(template)">
          <div class="flex justify-between gap-2"><span class="font-medium text-white">{{ template.label }}</span><span v-if="template.required" class="text-xs text-indigo-300">{{ $t('bProj.required') }}</span></div>
          <p class="mt-1 text-sm text-slate-400">{{ metricValue(template.key) }}</p>
        </button>
      </div>
    </div>

    <div class="pc-card">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div><h2 class="text-lg font-semibold text-white">{{ $t('bProj.boqTitle') }}</h2><p class="text-sm text-slate-400">{{ report?.current_version ? $t('bProj.version', { v: report.current_version.version_number, status: report.current_version.status }) : $t('bProj.notGenerated') }}</p></div>
        <div class="flex flex-wrap gap-2">
          <button class="btn-secondary" @click="estimate">{{ $t('bProj.estimate') }}</button>
          <button class="btn-secondary" @click="recalculate">{{ $t('bProj.newVersion') }}</button>
          <button class="btn-primary" @click="freeze">{{ $t('bProj.freezeBoq') }}</button>
        </div>
      </div>
      <div v-if="report?.rows?.length" class="mt-4 overflow-x-auto">
        <table class="w-full text-left text-sm">
          <thead class="text-slate-500"><tr><th class="p-2">{{ $t('bProj.colItem') }}</th><th class="p-2">{{ $t('bProj.colQty') }}</th><th class="p-2">{{ $t('bProj.colTier') }}</th><th class="p-2">{{ $t('bProj.colSelected') }}</th></tr></thead>
          <tbody>
            <tr v-for="row in report.rows" :key="row.id" class="border-t border-slate-800">
              <td class="p-2 text-white">{{ row.name }}</td>
              <td class="p-2 text-slate-300">{{ row.qty }} {{ row.unit }}</td>
              <td class="p-2"><select :value="row.selected_tier" :disabled="report.current_version.status==='FROZEN'" class="rounded bg-slate-900 p-2 text-slate-200" @change="setTier(row,$event)"><option>BUDGET</option><option>MID_RANGE</option><option>PREMIUM</option></select></td>
              <td class="p-2"><input type="checkbox" :checked="row.selected_for_purchase" :disabled="report.current_version.status==='FROZEN'" @change="toggleRow(row,$event)"></td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else class="mt-4 text-sm text-slate-500">{{ $t('bProj.addLineItems') }}</p>
      <div v-if="versions.length" class="mt-4 border-t border-slate-800 pt-3 text-xs text-slate-500">{{ $t('bProj.versionsPrefix', { list: versions.map(v=>`${v.version_number} ${v.status}`).join(' · ') }) }}</div>
    </div>
    <p v-if="message" class="pc-card text-emerald-300">{{ message }}</p><p v-if="error" class="pc-card text-red-300">{{ error }}</p>
  </section>
</template>
<script setup lang="ts">
const { t } = useI18n()
definePageMeta({ layout: 'procurement', middleware: ['auth'], alias: ['/buyer/projects/:id'] })
const route=useRoute();const {apiFetch}=useApi();const base=`/buyer/projects/${route.params.id}`;const project=ref<any>();const metrics=ref<any>();const report=ref<any>();const versions=ref<any[]>([]);const error=ref('');const message=ref('')
function metricValue(key:string){const row=metrics.value?.values?.find((v:any)=>v.key===key);return row?.value_json?.value??row?.value_json?.value_text??t('bProj.clickToEnter')}
async function load(){error.value='';[project.value,metrics.value,report.value]=await Promise.all([apiFetch(base),apiFetch(`${base}/metrics`),apiFetch(`${base}/report`)]);versions.value=(await apiFetch<any>(`${base}/report/versions`)).items}
async function editMetric(template:any){const raw=window.prompt(template.prompt||template.label,String(metricValue(template.key)===t('bProj.clickToEnter')?'':metricValue(template.key)));if(raw===null)return;const value=Number.isFinite(Number(raw))&&raw.trim()!==''?Number(raw):raw;metrics.value=await apiFetch(`${base}/metrics`,{method:'PATCH',body:{metrics:[{key:template.key,label:template.label,value}]}})}
async function estimate(){await act(t('bProj.pricesEstimated'),()=>apiFetch(`${base}/price-estimate`,{method:'POST'}));await recalculate()}
async function recalculate(){report.value=await apiFetch(`${base}/report/recalculate`,{method:'POST'});versions.value=(await apiFetch<any>(`${base}/report/versions`)).items;message.value=t('bProj.newVersionCreated')}
async function freeze(){report.value=await apiFetch(`${base}/report/freeze`,{method:'POST'});versions.value=(await apiFetch<any>(`${base}/report/versions`)).items;message.value=t('bProj.boqFrozen')}
async function setTier(row:any,event:any){await patchRow(row,{selected_tier:event.target.value})}
async function toggleRow(row:any,event:any){await patchRow(row,{selected_for_purchase:event.target.checked})}
async function patchRow(row:any,body:any){report.value=await apiFetch(`${base}/report/rows/${row.id}`,{method:'PATCH',body})}
async function act(text:string,fn:()=>Promise<any>){try{error.value='';await fn();message.value=text}catch(e:any){error.value=e?.data?.detail||e?.message}}
onMounted(()=>load().catch((e:any)=>error.value=e?.data?.detail||e?.message))
</script>
