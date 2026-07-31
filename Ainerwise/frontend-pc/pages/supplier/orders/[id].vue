<template>
  <section class="space-y-6">
    <div class="flex items-center gap-3">
      <NuxtLink to="/supplier/orders" class="text-sm text-indigo-300 hover:text-indigo-200">← 返回订单</NuxtLink>
    </div>

    <div v-if="order">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div class="flex items-center gap-3">
            <h1 class="text-2xl font-bold text-white">订单 #{{ order.id.slice(0, 8) }}</h1>
            <span :class="['rounded-full px-2 py-0.5 text-xs', statusTone(order.status)]">{{ statusLabel(order.status) }}</span>
          </div>
          <p class="mt-1 text-sm text-slate-400">{{ order.created_at ? `授标于 ${new Date(order.created_at).toLocaleDateString()}` : '' }}</p>
        </div>
        <NuxtLink :to="`/supplier/messages?order_id=${order.id}`" class="btn-secondary">联系买家</NuxtLink>
      </div>

      <!-- Settlement (ledger/PSP, not custody) -->
      <div class="pc-card mt-5 flex items-start justify-between gap-4 border-emerald-500/30 bg-emerald-500/[0.06]">
        <div>
          <h4 class="font-semibold text-white">结算金额</h4>
          <p class="mt-1 text-sm text-slate-400">买家确认收货后，平台按 PSP / 记账规则结算到你的结算账户；AISLOS 不托管资金。</p>
        </div>
        <div class="text-right">
          <p class="text-xs text-slate-400">应结</p>
          <p class="text-2xl font-bold text-emerald-300">{{ money(order.total_minor, order.currency) }}</p>
        </div>
      </div>

      <div class="mt-6 grid grid-cols-1 gap-6 md:grid-cols-2">
        <!-- Fulfillment -->
        <div class="pc-card">
          <h3 class="text-lg font-medium text-white">履约状态</h3>
          <div class="mt-5 flex items-center justify-between">
            <div v-for="(s, i) in fulfillSteps" :key="s.key" class="flex flex-1 flex-col items-center">
              <div :class="['flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold', i <= currentStep ? 'bg-indigo-500 text-white' : 'bg-white/10 text-slate-500']">{{ i < currentStep ? '✓' : i + 1 }}</div>
              <span :class="['mt-2 text-xs', i <= currentStep ? 'text-indigo-200' : 'text-slate-500']">{{ s.label }}</span>
            </div>
          </div>

          <form class="mt-6 grid gap-3 border-t border-white/10 pt-5 sm:grid-cols-2" @submit.prevent="schedule">
            <input v-model.trim="delivery.carrier" class="input-field" placeholder="承运商" />
            <input v-model.trim="delivery.tracking_number" class="input-field" placeholder="运单号" />
            <button class="btn-primary sm:col-span-2" :disabled="busy">{{ busy ? '处理中…' : '排程交付' }}</button>
          </form>

          <div class="mt-4 space-y-3">
            <div v-for="d in deliveries" :key="d.id" class="rounded-xl border border-white/10 p-3">
              <div class="flex items-center justify-between">
                <span :class="['rounded-full px-2 py-0.5 text-xs', statusTone(d.status)]">{{ deliveryLabel(d.status) }}</span>
                <button v-if="nextStatus[d.status]" class="text-xs text-indigo-300 hover:text-indigo-200" :disabled="busy" @click="advance(d.id, nextStatus[d.status])">标记为「{{ deliveryLabel(nextStatus[d.status]) }}」</button>
              </div>
              <p class="mt-2 text-xs text-slate-500">{{ d.carrier || '—' }} · {{ d.tracking_number || '无运单号' }}</p>
            </div>
            <p v-if="!deliveries.length" class="rounded-xl border border-dashed border-white/10 p-4 text-center text-sm text-slate-500">尚未排程交付</p>
          </div>
        </div>

        <!-- Logistics / summary -->
        <div class="pc-card">
          <h3 class="text-lg font-medium text-white">交付详情</h3>
          <dl class="mt-4 space-y-4 text-sm">
            <div><dt class="text-xs uppercase tracking-wider text-slate-500">买家</dt><dd class="mt-1 font-medium text-white">{{ order.buyer_company_name || order.buyer_name || '—' }}</dd></div>
            <div class="border-t border-white/5 pt-3"><dt class="text-xs uppercase tracking-wider text-slate-500">收货地址</dt><dd class="mt-1 text-slate-300">{{ order.delivery_address || order.shipping_address || '买家未提供地址' }}</dd></div>
            <div class="border-t border-white/5 pt-3"><dt class="text-xs uppercase tracking-wider text-slate-500">订单摘要</dt>
              <dd class="mt-1 space-y-1">
                <div class="flex justify-between"><span class="text-slate-400">商品</span><span class="text-white">{{ money(order.subtotal_minor ?? order.items_total_minor, order.currency) }}</span></div>
                <div class="flex justify-between"><span class="text-slate-400">运费</span><span class="text-white">{{ money(order.delivery_fee_minor, order.currency) }}</span></div>
                <div class="flex justify-between border-t border-white/5 pt-1 font-semibold"><span class="text-slate-300">合计</span><span class="text-white">{{ money(order.total_minor, order.currency) }}</span></div>
              </dd>
            </div>
          </dl>
        </div>
      </div>
    </div>

    <p v-else-if="error" class="pc-card text-sm text-red-300">{{ error }}</p>
    <p v-else class="pc-card text-sm text-slate-400">加载订单中…</p>
  </section>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'procurement', middleware: ['auth'] })

const route = useRoute()
const { apiFetch } = useApi()
const api = useCommerce()
const order = ref<any>()
const deliveries = ref<any[]>([])
const error = ref('')
const busy = ref(false)
const delivery = reactive({ carrier: '', tracking_number: '' })
const nextStatus: Record<string, string> = { scheduled: 'shipped', shipped: 'in_transit', in_transit: 'delivered' }

const fulfillSteps = [
  { key: 'awarded', label: '已授标' },
  { key: 'shipped', label: '已发货' },
  { key: 'in_transit', label: '运输中' },
  { key: 'delivered', label: '已送达' },
]
const currentStep = computed(() => {
  const latest = deliveries.value[deliveries.value.length - 1]?.status || order.value?.status || 'awarded'
  const map: Record<string, number> = { scheduled: 0, awarded: 0, confirmed: 0, shipped: 1, in_transit: 2, in_delivery: 2, delivered: 3, completed: 3 }
  return map[String(latest)] ?? 0
})

function statusLabel(s?: string) {
  return { confirmed: '已确认', awarded: '已授标', in_delivery: '配送中', delivered: '已送达', completed: '已完成', disputed: '争议中', cancelled: '已取消' }[String(s || '')] || s || '—'
}
function deliveryLabel(s?: string) {
  return { scheduled: '已排程', shipped: '已发货', in_transit: '运输中', delivered: '已送达', accepted: '已签收' }[String(s || '')] || s || '—'
}
function statusTone(s?: string) {
  const v = String(s || '').toLowerCase()
  if (/complete|deliver|accept/.test(v)) return 'bg-emerald-500/15 text-emerald-300'
  if (/dispute|cancel/.test(v)) return 'bg-red-500/15 text-red-300'
  return 'bg-blue-500/15 text-blue-300'
}
function money(v?: number, c = 'EUR') {
  if (v == null) return '—'
  try { return new Intl.NumberFormat(undefined, { style: 'currency', currency: c, maximumFractionDigits: 2 }).format(v / 100) } catch { return `${(v / 100).toLocaleString()} ${c}` }
}

async function load() {
  order.value = await api.getOrder(String(route.params.id))
  deliveries.value = (await api.listDeliveries(String(route.params.id))).items || []
}
async function schedule() {
  if (!delivery.carrier && !delivery.tracking_number) return
  busy.value = true
  try { await apiFetch(`/commerce/orders/${route.params.id}/deliveries`, { method: 'POST', body: { ...delivery } }); delivery.carrier = ''; delivery.tracking_number = ''; await load() }
  catch (e: any) { error.value = e?.data?.detail || e?.message || '排程失败' }
  finally { busy.value = false }
}
async function advance(id: string, status: string) {
  busy.value = true
  try { await apiFetch(`/commerce/deliveries/${id}/status`, { method: 'PATCH', body: { status } }); await load() }
  catch (e: any) { error.value = e?.data?.detail || e?.message || '更新失败' }
  finally { busy.value = false }
}

onMounted(() => load().catch((e: any) => { error.value = e?.data?.detail || e?.message || '加载订单失败' }))
</script>
