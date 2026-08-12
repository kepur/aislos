<template>
  <section class="space-y-5">
    <NuxtLink :to="localized('/partner/work-packages')" class="text-sm text-blue-300">&larr; {{ $t('partner.backPackages') }}</NuxtLink>
    <p v-if="error" class="pc-card text-red-300">{{ error }}</p>
    <template v-if="work">
      <div class="pc-card">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div><p class="text-xs uppercase tracking-wider text-blue-300">{{ $t('partner.workPackage') }}</p><h1 class="mt-2 text-3xl font-bold text-white">{{ work.title }}</h1><p class="mt-2 text-sm text-slate-400">{{ work.trade ? label(work.trade) : $t('partner.generalDelivery') }}</p></div>
          <span class="rounded-full bg-blue-500/10 px-3 py-1 text-xs uppercase text-blue-300">{{ label(work.status) }}</span>
        </div>
        <dl class="mt-5 grid gap-4 text-sm sm:grid-cols-3"><div><dt class="text-slate-500">{{ $t('pInstD.plannedStart') }}</dt><dd class="mt-1 text-white">{{ work.planned_start || $t('partner.notSet') }}</dd></div><div><dt class="text-slate-500">{{ $t('pInstD.plannedEnd') }}</dt><dd class="mt-1 text-white">{{ work.planned_end || $t('partner.notSet') }}</dd></div><div><dt class="text-slate-500">{{ $t('partner.fieldTasks') }}</dt><dd class="mt-1 text-white">{{ work.tasks.length }}</dd></div></dl>
      </div>

      <div v-for="task in work.tasks" :key="task.id" class="pc-card">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div><p class="text-xs uppercase text-blue-300">{{ label(task.task_type) }}</p><h2 class="mt-1 text-lg font-semibold text-white">{{ task.title }}</h2><p class="mt-2 text-xs text-slate-500">{{ task.required_skill || $t('partner.noSkill') }} · {{ $t('pInstD.evidenceRecords', { n: task.evidence_count }) }}</p></div>
          <span class="rounded-full bg-white/5 px-3 py-1 text-xs uppercase text-slate-300">{{ label(task.status) }}</span>
        </div>
        <div v-if="task.assignments.length" class="mt-4 space-y-2">
          <div v-for="assignment in task.assignments" :key="assignment.id" class="flex justify-between rounded-lg border border-white/5 px-3 py-2 text-sm"><span class="text-slate-300">{{ assignment.worker_name }}</span><span class="text-slate-500">{{ label(assignment.status) }}</span></div>
        </div>
        <form class="mt-4 grid gap-3 sm:grid-cols-[1fr_1fr_auto]" @submit.prevent="assign(task.id)">
          <select v-model="assignment[task.id].assignee_user_id" required class="input-field"><option value="">{{ $t('partner.selectWorker') }}</option><option v-for="worker in workersForPackage" :key="worker.id" :value="worker.id">{{ worker.full_name || worker.email }}</option></select>
          <select v-model="assignment[task.id].crew_id" class="input-field"><option value="">{{ $t('partner.noCrew') }}</option><option v-for="crew in crews" :key="crew.id" :value="crew.id">{{ crew.name }}</option></select>
          <button class="btn-primary py-2" :disabled="busy">{{ $t('partner.assign') }}</button>
        </form>
        <button class="mt-4 text-sm text-blue-300" @click="loadEvidence(task.id)">{{ $t('partner.viewEvidence') }}</button>
        <div v-if="evidence[task.id]" class="mt-3 grid gap-2 md:grid-cols-2">
          <div v-for="item in evidence[task.id]" :key="item.id" class="rounded-lg border border-white/5 p-3 text-xs"><p class="font-semibold uppercase text-blue-300">{{ item.evidence_type }}</p><pre class="mt-2 overflow-auto whitespace-pre-wrap text-slate-400">{{ JSON.stringify(item.payload_json, null, 2) }}</pre></div>
          <p v-if="!evidence[task.id].length" class="text-sm text-slate-500">{{ $t('partner.noEvidence') }}</p>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()
definePageMeta({ layout: 'partner-workspace', middleware: ['auth'] })
const route = useRoute()
const { apiFetch } = useApi()
const work = ref<any>()
const workers = ref<any[]>([])
const crews = ref<any[]>([])
const assignment = reactive<Record<string, { assignee_user_id: string; crew_id: string }>>({})
const evidence = reactive<Record<string, any[]>>({})
const error = ref('')
const busy = ref(false)
const { t } = useI18n()
const label = (value: string) => value?.replaceAll('_', ' ') || t('partner.unknown')
const workersForPackage = computed(() => workers.value.filter(worker => worker.workspace_id === work.value?.workspace_id))
async function load() {
  const [packageData, workerData, crewData] = await Promise.all([
    apiFetch<any>(`/partner/field-ops/work-packages/${route.params.id}`),
    apiFetch<any>('/partner/field-ops/workers'),
    apiFetch<any>('/partner/field-ops/crews'),
  ])
  work.value = packageData
  workers.value = workerData.items || []
  crews.value = (crewData.items || []).filter((crew: any) => crew.workspace_id === packageData.workspace_id)
  for (const task of packageData.tasks) {
    assignment[task.id] ||= { assignee_user_id: '', crew_id: '' }
  }
}
async function assign(taskId: string) {
  busy.value = true
  error.value = ''
  try {
    await apiFetch(`/partner/field-ops/tasks/${taskId}/assignments`, {
      method: 'POST',
      body: {
        assignee_user_id: assignment[taskId].assignee_user_id,
        crew_id: assignment[taskId].crew_id || null,
      },
    })
    await load()
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message
  } finally {
    busy.value = false
  }
}
async function loadEvidence(taskId: string) {
  try {
    evidence[taskId] = (await apiFetch<any>(`/partner/field-ops/tasks/${taskId}/evidence`)).items || []
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message
  }
}
onMounted(() => load().catch((e: any) => error.value = e?.data?.detail || e?.message))
</script>

