<template>
  <div>
    <div class="mb-6">
      <h1 class="admin-page-title">AI Employees</h1>
      <p class="admin-page-desc">Your governed digital team. Core workflows enforce grants and record each execution under an explicit Agent identity.</p>
    </div>

    <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      <NuxtLink
        v-for="a in agents"
        :key="a.slug"
        :to="`/agents/${a.slug}`"
        class="admin-panel p-5 block hover:shadow-md transition"
      >
        <div class="flex items-start justify-between">
          <div>
            <h2 class="font-semibold text-gray-900">{{ a.name }}</h2>
            <p class="text-xs text-gray-500">{{ a.role_title }}</p>
          </div>
          <StatusBadge :status="a.status" />
        </div>
        <p class="text-xs text-gray-600 mt-3 line-clamp-2">{{ a.description }}</p>
        <div class="flex gap-4 mt-4 text-xs text-gray-500">
          <span><b class="text-gray-900">{{ a.stats.runs_30d }}</b> runs / 30d</span>
          <span><b class="text-gray-900">{{ formatTokens(a.stats.tokens_30d) }}</b> tokens</span>
          <span v-if="a.stats.last_run_at">last: {{ timeAgo(a.stats.last_run_at) }}</span>
        </div>
        <div class="flex flex-wrap gap-1 mt-3">
          <span v-for="w in a.workflows" :key="w" class="text-[10px] bg-gray-100 text-gray-600 rounded-full px-2 py-0.5 font-mono">{{ w }}</span>
        </div>
      </NuxtLink>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { apiFetch } = useApi()
const agents = ref<any[]>([])

function formatTokens(n: number) {
  return n > 1000 ? `${(n / 1000).toFixed(1)}k` : String(n)
}
function timeAgo(iso: string) {
  const hours = Math.round((Date.now() - new Date(iso).getTime()) / 3600e3)
  return hours < 24 ? `${hours}h ago` : `${Math.round(hours / 24)}d ago`
}

onMounted(async () => {
  const res = await apiFetch<any>('/admin/agents')
  agents.value = res.items || []
})
</script>
