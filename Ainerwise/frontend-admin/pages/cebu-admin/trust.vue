<template>
  <div class="space-y-5">
    <div><h1 class="admin-page-title">Cebu Trust Profiles</h1><p class="admin-page-desc">Audited manual adjustments are bounded to a 0–100 score</p></div>
    <p v-if="error" class="text-sm text-red-400">{{ error }}</p>
    <div class="grid gap-3 md:grid-cols-2">
      <article v-for="row in items" :key="row.id" class="admin-panel p-4 text-sm">
        <div class="flex justify-between gap-3"><p class="font-semibold text-white">Company {{ row.company_id }}</p><p class="text-2xl font-bold text-cyan-300">{{ row.trust_score }}</p></div>
        <p class="mt-2 text-slate-400">{{ row.completed_orders }} completed · {{ row.dispute_count }} disputes</p>
        <div class="mt-4 flex gap-2">
          <button class="btn-secondary" @click="adjust(row)">Adjust score</button>
          <button class="btn-secondary" @click="loadEvents(row)">History</button>
        </div>
        <div v-if="selectedId===row.id" class="mt-4 space-y-2 border-t border-slate-700 pt-3">
          <p v-if="events.length===0" class="text-slate-500">No score events yet.</p>
          <div v-for="event in events" :key="event.id" class="rounded-lg bg-slate-900/60 p-2">
            <div class="flex justify-between"><span class="text-cyan-300">{{ event.event_type }}</span><span :class="event.score_delta>=0?'text-emerald-300':'text-red-300'">{{ event.score_delta>=0?'+':'' }}{{ event.score_delta }}</span></div>
            <p class="mt-1 text-slate-400">{{ event.before_score }} → {{ event.after_score }} · {{ event.reason || 'No reason' }}</p>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>
<script setup lang="ts">
definePageMeta({layout:'default',middleware:['auth']})
const {apiFetch}=useApi();const items=ref<any[]>([]);const events=ref<any[]>([]);const selectedId=ref('');const error=ref('')
async function load(){items.value=(await apiFetch<any>('/admin/cebu/trade')).trust_profiles.items}
async function loadEvents(row:any){selectedId.value=row.id;events.value=(await apiFetch<any>(`/admin/cebu/trust-profiles/${row.id}/events`)).items}
async function adjust(row:any){const delta=window.prompt('Score delta (-100 to 100)');if(delta===null)return;const reason=window.prompt('Reason is required');if(!reason)return;try{await apiFetch(`/admin/cebu/trust-profiles/${row.id}/adjust`,{method:'POST',body:{delta:Number(delta),reason}});await load();if(selectedId.value===row.id)await loadEvents(row)}catch(e:any){error.value=e?.data?.detail||e?.message}}
onMounted(()=>load().catch((e:any)=>error.value=e?.data?.detail||e?.message))
</script>
