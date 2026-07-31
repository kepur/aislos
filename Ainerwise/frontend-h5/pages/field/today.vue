<template>
  <div class="p-4 space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-semibold text-gray-900">今日任务</h1>
        <p class="text-sm text-gray-500">Field Worker PWA</p>
      </div>
      <span class="text-xs" :class="online ? 'text-emerald-600' : 'text-amber-600'">
        {{ online ? '在线' : '离线' }}
      </span>
    </div>
    <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
    <p v-if="lastSyncAt" class="text-xs text-gray-400">上次同步 {{ lastSyncAt }}</p>
    <div v-if="conflicts.length" class="m-card border-amber-200 bg-amber-50">
      <p class="text-sm font-semibold text-amber-800">需要处理的同步冲突</p>
      <div v-for="item in conflicts" :key="item.idempotency_key" class="mt-3 rounded-xl bg-white p-3">
        <p class="text-xs font-semibold text-slate-700">{{ item.type }} · {{ item.task_id }}</p>
        <p class="mt-1 text-[10px] text-amber-600">{{ item.detail }}</p>
        <div class="mt-3 grid grid-cols-2 gap-2">
          <button class="rounded-lg bg-amber-500 px-2 py-2 text-xs font-semibold text-white" @click="resolve(item.idempotency_key, 'retry')">按服务器版本重试</button>
          <button class="rounded-lg border border-slate-200 px-2 py-2 text-xs text-slate-500" @click="resolve(item.idempotency_key, 'discard')">放弃本地操作</button>
        </div>
      </div>
    </div>
    <div v-if="loading" class="text-gray-500 text-sm">Loading…</div>
    <ul v-else class="space-y-3">
      <li v-for="task in tasks" :key="task.id">
        <NuxtLink
          :to="`/field/tasks/${task.id}`"
          class="block rounded-lg border p-3 bg-white hover:border-primary-300"
        >
          <p class="font-medium">{{ task.title }}</p>
          <p class="text-xs text-gray-500">{{ task.task_type }} · {{ task.status }}</p>
          <p v-if="task.schedule_start" class="text-xs text-gray-400 mt-1">{{ task.schedule_start }}</p>
        </NuxtLink>
      </li>
      <li v-if="!tasks.length" class="text-sm text-gray-500">暂无分配任务</li>
    </ul>
    <button
      class="w-full py-2 text-sm border rounded-lg"
      :disabled="syncing"
      @click="flushQueue"
    >
      {{ syncing ? '同步中…' : '立即同步离线队列' }}
    </button>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default', middleware: ['auth'] })

const { online, syncing, lastSyncAt, refreshToday, flushQueue, listQueue, resolveConflict } = useFieldWorkerSync()
const tasks = ref<any[]>([])
const loading = ref(true)
const error = ref('')
const conflicts = ref<any[]>([])
async function refreshConflicts() {
  conflicts.value = (await listQueue()).filter(item => item.conflict)
}
async function resolve(id: string, strategy: 'retry' | 'discard') {
  await resolveConflict(id, strategy)
  await refreshConflicts()
}

onMounted(async () => {
  try {
    tasks.value = await refreshToday()
    await refreshConflicts()
  } catch (e: any) {
    error.value = e?.message || 'Load failed'
  } finally {
    loading.value = false
  }
})
</script>
