<template>
  <section class="space-y-5">
    <div><p class="text-xs font-bold uppercase tracking-wider text-blue-300">{{ $t('partner.flexWorkforce') }}</p><h1 class="mt-1 text-3xl font-bold text-white">{{ $t('partner.navCrews') }}</h1><p class="mt-2 text-sm text-slate-400">{{ $t('partner.crewsDesc') }}</p></div>
    <form class="pc-card grid gap-3 md:grid-cols-[1fr_1fr_1fr_auto]" @submit.prevent="create">
      <select v-model="form.workspace_id" required class="input-field"><option value="">{{ $t('partner.workspacePh') }}</option><option v-for="item in memberships" :key="item.workspace_id" :value="item.workspace_id">{{ item.workspace_id }}</option></select>
      <input v-model.trim="form.name" required class="input-field" :placeholder="$t('partner.crewNamePh')">
      <input v-model.trim="form.trade" class="input-field" :placeholder="$t('partner.tradePh')">
      <button class="btn-primary py-2" :disabled="busy">{{ $t('partner.createCrew') }}</button>
    </form>
    <div v-for="crew in crews" :key="crew.id" class="pc-card">
      <div class="flex flex-wrap justify-between gap-3"><div><p class="text-lg font-semibold text-white">{{ crew.name }}</p><p class="mt-1 text-xs text-blue-300">{{ crew.trade || $t('partner.generalCrew') }}</p></div><span class="text-xs uppercase text-slate-400">{{ crew.status }}</span></div>
      <form class="mt-4 flex flex-wrap gap-3" @submit.prevent="addMember(crew)">
        <select v-model="members[crew.id].user_id" required class="input-field max-w-md"><option value="">{{ $t('partner.addWorker') }}</option><option v-for="worker in workers.filter(x => x.workspace_id === crew.workspace_id)" :key="worker.id" :value="worker.id">{{ worker.full_name || worker.email }}</option></select>
        <select v-model="members[crew.id].role_in_crew" class="input-field max-w-xs"><option value="worker">{{ $t('partner.roleWorker') }}</option><option value="lead">{{ $t('partner.roleLead') }}</option><option value="supervisor">{{ $t('partner.roleSupervisor') }}</option></select>
        <button class="btn-primary py-2" :disabled="busy">{{ $t('partner.addMember') }}</button>
      </form>
    </div>
    <p v-if="error" class="pc-card text-red-300">{{ error }}</p>
  </section>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'partner-workspace', middleware: ['auth'] })
const { apiFetch } = useApi()
const { memberships, loadAccess } = usePortalManifest()
const crews = ref<any[]>([])
const workers = ref<any[]>([])
const members = reactive<Record<string, { user_id: string; role_in_crew: string }>>({})
const form = reactive({ workspace_id: '', name: '', trade: '' })
const busy = ref(false)
const error = ref('')
async function load() {
  await loadAccess()
  const [crewData, workerData] = await Promise.all([apiFetch<any>('/partner/field-ops/crews'), apiFetch<any>('/partner/field-ops/workers')])
  crews.value = crewData.items || []
  workers.value = workerData.items || []
  form.workspace_id ||= memberships.value[0]?.workspace_id || ''
  for (const crew of crews.value) members[crew.id] ||= { user_id: '', role_in_crew: 'worker' }
}
async function create() {
  busy.value = true
  try {
    await apiFetch('/partner/field-ops/crews', { method: 'POST', body: { ...form, trade: form.trade || null } })
    form.name = ''
    form.trade = ''
    await load()
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message
  } finally {
    busy.value = false
  }
}
async function addMember(crew: any) {
  busy.value = true
  try {
    await apiFetch(`/partner/field-ops/crews/${crew.id}/members`, { method: 'POST', body: members[crew.id] })
    members[crew.id].user_id = ''
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message
  } finally {
    busy.value = false
  }
}
onMounted(() => load().catch((e: any) => error.value = e?.data?.detail || e?.message))
</script>

