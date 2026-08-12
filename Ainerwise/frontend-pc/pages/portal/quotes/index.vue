<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-xl font-bold ws-title">{{ $t('portal.myQuotes') }}</h1>
      <p class="text-sm ws-faint mt-1">{{ $t('pQuotes.subtitle') }}</p>
    </div>

    <div v-if="error" class="portal-card border-red-200 bg-red-50 text-sm text-red-700">
      {{ error }} <button class="ml-2 font-semibold underline" @click="loadData">{{ $t('common.retry') }}</button>
    </div>
    <div class="portal-card p-0 overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="ws-sunken/80 border-b ws-hairline">
            <th class="text-left px-4 py-3 text-xs font-semibold ws-faint uppercase tracking-wider">{{ $t('pQuotes.colQuote') }}</th>
            <th class="text-left px-4 py-3 text-xs font-semibold ws-faint uppercase tracking-wider">{{ $t('pQuotes.colTotal') }}</th>
            <th class="text-left px-4 py-3 text-xs font-semibold ws-faint uppercase tracking-wider">{{ $t('pQuotes.colValidUntil') }}</th>
            <th class="text-left px-4 py-3 text-xs font-semibold ws-faint uppercase tracking-wider">{{ $t('common.status') }}</th>
            <th class="text-left px-4 py-3 text-xs font-semibold ws-faint uppercase tracking-wider">{{ $t('common.actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="quote in quotes" :key="quote.id" class="border-b border-slate-50 hover:bg-blue-50/30 transition-colors">
            <td class="px-4 py-3 font-mono text-xs ws-muted">{{ quote.id.slice(0, 8) }}...</td>
            <td class="px-4 py-3 font-semibold ws-title">{{ quote.currency }} {{ quote.total?.toFixed(2) }}</td>
            <td class="px-4 py-3 ws-faint">{{ quote.valid_until || '-' }}</td>
            <td class="px-4 py-3">
              <span :class="['text-xs font-semibold px-2.5 py-1 rounded-full', statusClass(quote.status)]">{{ quote.status }}</span>
            </td>
            <td class="px-4 py-3">
              <div class="flex gap-2">
                <button v-if="quote.status === 'sent'" @click="respondToQuote(quote.id, 'accepted')"
 class="text-xs font-semibold text-emerald-600 hover:text-emerald-700 bg-emerald-50 px-3 py-1 rounded-lg transition">{{ $t('portal.approvals.accept') }}</button>
                <button v-if="quote.status === 'sent'" @click="respondToQuote(quote.id, 'rejected')"
 class="text-xs font-semibold text-red-500 hover:text-red-600 bg-red-50 px-3 py-1 rounded-lg transition">{{ $t('portal.approvals.decline') }}</button>
              </div>
            </td>
          </tr>
          <tr v-if="loading && !quotes.length">
            <td colspan="5" class="px-4 py-12 text-center text-sm ws-faint">{{ $t('pQuotes.loading') }}</td>
          </tr>
          <tr v-else-if="!quotes.length">
            <td colspan="5" class="px-4 py-12 text-center">
              <div class="text-3xl mb-2">💰</div>
              <p class="text-sm ws-faint">{{ $t('common.noData') }}</p>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'procurement', middleware: 'auth' })

const { t } = useI18n()
const { apiFetch } = useApi()
const quotes = ref<any[]>([])
const loading = ref(true)
const error = ref('')

function statusClass(status: string) {
 const map: Record<string, string> = {
 draft: 'ws-sunken ws-muted',
 sent: 'bg-blue-500/15 ws-accent dark:text-blue-300',
 accepted: 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300',
 rejected: 'bg-red-50 text-red-500',
  }
 return map[status] || 'ws-soft ws-muted'
}

onMounted(loadData)

async function loadData() {
 loading.value = true
 error.value = ''
 try {
 const res = await apiFetch<any>('/quotes/my')
 quotes.value = res.items || []
  } catch (e: any) {
 quotes.value = []
 error.value = e?.data?.detail || e?.message || t('pQuotes.loadFailed')
  } finally {
 loading.value = false
  }
}

async function respondToQuote(id: string, status: string) {
 error.value = ''
 try {
 await apiFetch(`/quotes/${id}/status`, { method: 'PATCH', body: { status } })
 await loadData()
  } catch (e: any) {
 error.value = e?.data?.detail || e?.message || t('pQuotes.updateFailed')
  }
}
</script>
