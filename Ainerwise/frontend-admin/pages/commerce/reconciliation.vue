<template>
  <div class="p-6 space-y-6 max-w-4xl">
    <h1 class="text-2xl font-semibold">Commerce 对账</h1>
    <p class="text-sm text-gray-500">Settlement / Reconciliation — Core 账本核对</p>
    <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
    <div class="flex gap-2">
      <button
        class="px-4 py-2 text-sm bg-primary-600 text-white rounded-lg disabled:opacity-50"
        :disabled="running"
        @click="runRecon"
      >
        {{ running ? '对账中…' : '运行本期对账' }}
      </button>
    </div>
    <div v-if="lastRun" class="rounded-lg border p-4 text-sm space-y-1 bg-white">
      <p><span class="text-gray-500">状态:</span> {{ lastRun.status }}</p>
      <p><span class="text-gray-500">匹配:</span> {{ lastRun.matched_count }}</p>
      <p><span class="text-gray-500">差异:</span> {{ lastRun.mismatch_count }}</p>
      <p><span class="text-gray-500">待处理:</span> {{ lastRun.pending_count }}</p>
    </div>
    <div>
      <h2 class="font-medium mb-2">结算记录</h2>
      <ul class="space-y-2 text-sm">
        <li v-for="s in settlements" :key="s.id" class="border rounded p-3 bg-white">
          订单 {{ s.commerce_order_id?.slice(0, 8) }}… · {{ s.status }} ·
          {{ (s.amount_minor / 100).toFixed(2) }} {{ s.currency }}
        </li>
        <li v-if="!settlements.length" class="text-gray-500">暂无结算记录</li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default', middleware: ['auth'] })

const { listSettlements, runReconciliation } = useCommerce()
const settlements = ref<any[]>([])
const lastRun = ref<any>(null)
const running = ref(false)
const error = ref('')

onMounted(async () => {
  try {
    const res = await listSettlements()
    settlements.value = res.items
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Load failed'
  }
})

async function runRecon() {
  running.value = true
  error.value = ''
  const end = new Date()
  const start = new Date(end.getTime() - 30 * 24 * 60 * 60 * 1000)
  try {
    lastRun.value = await runReconciliation(start.toISOString(), end.toISOString())
    const res = await listSettlements()
    settlements.value = res.items
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Reconciliation failed'
  } finally {
    running.value = false
  }
}
</script>
