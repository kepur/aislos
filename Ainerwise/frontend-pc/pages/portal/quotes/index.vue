<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-xl font-bold text-slate-800">{{ $t('portal.myQuotes') }}</h1>
      <p class="text-sm text-slate-400 mt-1">Review and respond to your quotes</p>
    </div>

    <div class="portal-card p-0 overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="bg-slate-50/80 border-b border-slate-100">
            <th class="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Quote</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Total</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Valid Until</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">{{ $t('common.status') }}</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">{{ $t('common.actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="quote in quotes" :key="quote.id" class="border-b border-slate-50 hover:bg-blue-50/30 transition-colors">
            <td class="px-4 py-3 font-mono text-xs text-slate-600">{{ quote.id.slice(0, 8) }}...</td>
            <td class="px-4 py-3 font-semibold text-slate-700">{{ quote.currency }} {{ quote.total?.toFixed(2) }}</td>
            <td class="px-4 py-3 text-slate-400">{{ quote.valid_until || '-' }}</td>
            <td class="px-4 py-3">
              <span :class="['text-xs font-semibold px-2.5 py-1 rounded-full', statusClass(quote.status)]">{{ quote.status }}</span>
            </td>
            <td class="px-4 py-3">
              <div class="flex gap-2">
                <button v-if="quote.status === 'sent'" @click="respondToQuote(quote.id, 'accepted')"
                  class="text-xs font-semibold text-emerald-600 hover:text-emerald-700 bg-emerald-50 px-3 py-1 rounded-lg transition">Accept</button>
                <button v-if="quote.status === 'sent'" @click="respondToQuote(quote.id, 'rejected')"
                  class="text-xs font-semibold text-red-500 hover:text-red-600 bg-red-50 px-3 py-1 rounded-lg transition">Decline</button>
              </div>
            </td>
          </tr>
          <tr v-if="!quotes.length">
            <td colspan="5" class="px-4 py-12 text-center">
              <div class="text-3xl mb-2">💰</div>
              <p class="text-sm text-slate-400">{{ $t('common.noData') }}</p>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'portal', middleware: 'auth' })

const { apiFetch } = useApi()
const quotes = ref<any[]>([])

function statusClass(status: string) {
  const map: Record<string, string> = {
    draft: 'bg-slate-50 text-slate-500',
    sent: 'bg-blue-50 text-blue-600',
    accepted: 'bg-emerald-50 text-emerald-600',
    rejected: 'bg-red-50 text-red-500',
  }
  return map[status] || 'bg-slate-50 text-slate-600'
}

onMounted(loadData)

async function loadData() {
  try {
    const res = await apiFetch<any>('/quotes/my')
    quotes.value = res.items || []
  } catch {}
}

async function respondToQuote(id: string, status: string) {
  try {
    await apiFetch(`/quotes/${id}/status`, { method: 'PATCH', body: { status } })
    await loadData()
  } catch (e: any) { console.error(e) }
}
</script>
