<template>
  <div v-if="agent">
    <NuxtLink to="/agents" class="text-xs text-gray-500 hover:underline">← AI Employees</NuxtLink>
    <div class="flex items-center justify-between mt-1 mb-6">
      <div>
        <h1 class="admin-page-title">{{ agent.name }}</h1>
        <p class="admin-page-desc">{{ agent.role_title }} · {{ agent.vendor }}</p>
      </div>
      <button
        class="text-sm px-4 py-2 rounded-lg border"
        :class="agent.status === 'active' ? 'border-amber-300 text-amber-700 hover:bg-amber-50' : 'border-emerald-300 text-emerald-700 hover:bg-emerald-50'"
        :disabled="busy"
        @click="toggleStatus"
      >{{ agent.status === 'active' ? 'Pause agent' : 'Activate agent' }}</button>
    </div>

    <div class="grid gap-4 lg:grid-cols-2">
      <div class="admin-panel p-5">
        <h2 class="font-medium text-gray-900 mb-3">Persona & instructions</h2>
        <div class="space-y-2">
          <label class="block text-xs text-gray-500">Brand voice / tone</label>
          <input v-model="config.brand_voice" class="input-field w-full" placeholder="e.g. professional, technical, trustworthy" />
          <label class="block text-xs text-gray-500">Target audience</label>
          <input v-model="config.audience" class="input-field w-full" placeholder="e.g. villa owners and developers in Poland/Serbia" />
          <label class="block text-xs text-gray-500">Goals</label>
          <input v-model="config.goals" class="input-field w-full" placeholder="e.g. qualified leads for KNX + solar projects" />
          <label class="block text-xs text-gray-500">Never do (forbidden)</label>
          <input v-model="config.forbidden" class="input-field w-full" placeholder="e.g. price promises, competitor claims" />
          <button class="btn-primary text-sm px-4 py-2 mt-2" :disabled="busy" @click="saveConfig">Save persona</button>
        </div>
      </div>

      <div class="admin-panel p-5">
        <h2 class="font-medium text-gray-900 mb-1">Data grants</h2>
        <p class="text-xs text-gray-400 mb-3">Core registered workflows enforce these scopes. Changes are audited; future third-party agents start at zero.</p>
        <div class="space-y-2">
          <label v-for="g in agent.grants" :key="g.scope" class="flex items-center justify-between text-sm border-b pb-2">
            <span class="text-gray-700">{{ scopeLabels[g.scope] || g.scope }}</span>
            <input type="checkbox" :checked="g.granted" :disabled="busy" @change="toggleGrant(g)" />
          </label>
        </div>
      </div>
    </div>

    <div class="admin-panel mt-4">
      <h2 class="font-medium text-gray-900 px-4 pt-4">Execution log (recent)</h2>
      <table class="admin-table w-full text-sm mt-2">
        <tbody>
          <tr v-for="(r, i) in agent.recent_runs" :key="i" class="border-b">
            <td class="px-4 py-2 font-mono text-xs text-gray-600">{{ r.workflow }}</td>
            <td class="px-4 py-2"><StatusBadge :status="r.status" /></td>
            <td class="px-4 py-2 text-gray-500 text-xs">{{ r.tokens }} tok · {{ r.latency_ms }}ms</td>
            <td class="px-4 py-2 text-gray-400 text-xs whitespace-nowrap">{{ new Date(r.created_at).toLocaleString() }}</td>
          </tr>
          <tr v-if="!agent.recent_runs?.length">
            <td class="px-4 py-6 text-center text-gray-400">No executions yet.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const route = useRoute()
const { apiFetch } = useApi()
const agent = ref<any>(null)
const config = ref<any>({})
const busy = ref(false)

const scopeLabels: Record<string, string> = {
  product_data: 'Read product data',
  customer_data: 'Read customer data',
  project_data: 'Read project data',
  quotes: 'Draft quotations',
  email: 'Send emails (drafts to review)',
  ads: 'Publish reviewed campaigns and social content',
  payment: 'Request payment review (never move funds)',
  partners: 'Contact partners',
}

async function load() {
  agent.value = await apiFetch<any>(`/admin/agents/${route.params.slug}`)
  config.value = { ...(agent.value.config_json || {}) }
}

async function saveConfig() {
  busy.value = true
  try {
    await apiFetch(`/admin/agents/${route.params.slug}`, { method: 'PATCH', body: { config_json: config.value } })
    await load()
  } finally {
    busy.value = false
  }
}

async function toggleStatus() {
  busy.value = true
  try {
    await apiFetch(`/admin/agents/${route.params.slug}`, {
      method: 'PATCH',
      body: { status: agent.value.status === 'active' ? 'paused' : 'active' },
    })
    await load()
  } finally {
    busy.value = false
  }
}

async function toggleGrant(g: any) {
  busy.value = true
  try {
    await apiFetch(`/admin/agents/${route.params.slug}/grants`, {
      method: 'POST',
      body: { scope: g.scope, granted: !g.granted },
    })
    await load()
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>
