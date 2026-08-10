<template>
  <section class="space-y-6">
    <div v-if="loading" class="pc-card text-sm text-slate-400">正在加载订单交付...</div>

    <template v-else-if="order">
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div>
          <NuxtLink to="/market/buyer/orders" class="text-sm text-indigo-300 hover:text-indigo-200">← 返回订单列表</NuxtLink>
          <div class="mt-4 flex flex-wrap items-center gap-3">
            <p class="text-xs font-bold uppercase tracking-[0.2em] text-indigo-300">Order {{ shortId(order.id) }}</p>
            <span :class="['rounded-full px-3 py-1 text-xs font-semibold', statusTone(order.status)]">{{ order.status }}</span>
          </div>
          <h1 class="mt-2 text-3xl font-bold tracking-tight text-white">{{ formatMinor(order.total_minor, order.currency) }}</h1>
          <p class="mt-3 text-sm text-slate-400">由报价授标生成，继续跟踪交付、验收、争议和记账状态。</p>
        </div>
        <div class="flex flex-wrap gap-2">
          <NuxtLink :to="`/market/buyer/requests/${order.procurement_request_id}/offers`" class="btn-secondary">查看授标报价</NuxtLink>
          <NuxtLink :to="`/market/buyer/messages?order_id=${order.id}`" class="btn-secondary">订单会话</NuxtLink>
          <button v-if="canCompleteOrder" class="btn-primary" :disabled="completing" @click="complete">
            {{ completing ? '完成中...' : '确认完成' }}
          </button>
        </div>
      </div>

      <JourneyProgress :status="order.status" />

      <p v-if="message" class="pc-card text-sm text-emerald-300">{{ message }}</p>
      <p v-if="error" class="pc-card text-sm text-red-300">{{ error }}</p>

      <div class="pc-card overflow-hidden !p-0">
        <div class="grid gap-0 lg:grid-cols-[1.15fr_0.85fr]">
          <div class="p-6 lg:p-8">
            <p class="text-sm font-semibold text-indigo-300">Ledger-first delivery</p>
            <h2 class="mt-3 text-2xl font-bold text-white">线下收款 + 交付验收 + 记账留痕</h2>
            <p class="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
              当前阶段不做真实在线钱包或平台托管资金。订单金额、支付意图、结算记录和交付状态先进入 Core ledger，后续接 PSP 时只替换收款入口，不重构业务流程。
            </p>
            <div class="mt-6 flex flex-wrap gap-3">
              <NuxtLink to="/market/buyer/wallet" class="btn-secondary">查看支付/结算台账</NuxtLink>
              <NuxtLink :to="`/market/buyer/disputes/new?order_id=${order.id}`" class="btn-secondary">发起争议</NuxtLink>
            </div>
          </div>
          <div class="border-t border-white/10 bg-indigo-500/[0.06] p-6 lg:border-l lg:border-t-0 lg:p-8">
            <dl class="grid gap-4 text-sm">
              <div class="rounded-2xl border border-white/10 bg-white/5 p-4">
                <dt class="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Winning offer</dt>
                <dd class="mt-2 font-medium text-slate-100">{{ shortId(order.winning_offer_id) || '—' }}</dd>
              </div>
              <div class="rounded-2xl border border-white/10 bg-white/5 p-4">
                <dt class="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Supplier</dt>
                <dd class="mt-2 font-medium text-slate-100">{{ supplierLabel }}</dd>
              </div>
              <div class="rounded-2xl border border-white/10 bg-white/5 p-4">
                <dt class="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Completed at</dt>
                <dd class="mt-2 font-medium text-slate-100">{{ formatDate(order.completed_at) }}</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>

      <div class="pc-card">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p class="text-xs font-bold uppercase tracking-[0.18em] text-indigo-300">Order progress</p>
            <h2 class="mt-2 text-xl font-semibold text-white">订单进度</h2>
          </div>
          <span class="text-sm text-slate-500">{{ progressPercent }}%</span>
        </div>
        <div class="mt-6">
          <div class="relative mx-auto max-w-4xl">
            <div class="absolute left-0 right-0 top-4 h-1 rounded-full bg-white/10" />
            <div class="absolute left-0 top-4 h-1 rounded-full bg-indigo-400 transition-all" :style="{ width: `${progressPercent}%` }" />
            <div class="relative grid grid-cols-4 gap-3">
              <div v-for="(step, index) in orderSteps" :key="step.key" class="text-center">
                <div :class="['mx-auto flex h-9 w-9 items-center justify-center rounded-full border-4 border-slate-950 text-sm font-bold', step.done ? 'bg-indigo-400 text-slate-950' : step.active ? 'bg-indigo-600 text-white' : 'bg-white/10 text-slate-500']">
                  {{ step.done ? '✓' : index + 1 }}
                </div>
                <p :class="['mt-3 text-xs font-semibold', step.done || step.active ? 'text-white' : 'text-slate-500']">{{ step.label }}</p>
                <p class="mt-1 text-xs text-slate-500">{{ step.hint }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="grid gap-6 lg:grid-cols-2">
        <div class="pc-card">
          <p class="text-xs font-bold uppercase tracking-[0.18em] text-indigo-300">Order details</p>
          <h2 class="mt-2 text-xl font-semibold text-white">订单摘要</h2>
          <dl class="mt-5 space-y-4 text-sm">
            <div class="flex justify-between gap-4">
              <dt class="text-slate-500">采购需求</dt>
              <dd class="text-right text-slate-200">{{ request?.title || shortId(order.procurement_request_id) }}</dd>
            </div>
            <div class="flex justify-between gap-4">
              <dt class="text-slate-500">需求状态</dt>
              <dd class="text-right text-slate-200">{{ request?.status || '—' }}</dd>
            </div>
            <div class="flex justify-between gap-4">
              <dt class="text-slate-500">报价金额</dt>
              <dd class="text-right font-semibold text-indigo-200">{{ offer ? formatMinor(offer.price_minor, offer.currency) : '—' }}</dd>
            </div>
            <div class="flex justify-between gap-4 border-t border-white/10 pt-4">
              <dt class="font-semibold text-white">订单总额</dt>
              <dd class="text-right font-bold text-emerald-300">{{ formatMinor(order.total_minor, order.currency) }}</dd>
            </div>
          </dl>
        </div>

        <div class="pc-card">
          <p class="text-xs font-bold uppercase tracking-[0.18em] text-indigo-300">Supplier & logistics</p>
          <h2 class="mt-2 text-xl font-semibold text-white">供应商与物流</h2>
          <div class="mt-5 rounded-2xl border border-white/10 bg-white/[0.03] p-4">
            <p class="font-semibold text-white">{{ supplierLabel }}</p>
            <p class="mt-1 text-xs text-slate-500">Supplier company {{ shortId(order.supplier_company_id) || '—' }}</p>
          </div>
          <dl class="mt-5 space-y-4 text-sm">
            <div class="flex justify-between gap-4">
              <dt class="text-slate-500">交付记录</dt>
              <dd class="text-right text-slate-200">{{ deliveries.length }}</dd>
            </div>
            <div class="flex justify-between gap-4">
              <dt class="text-slate-500">最近交付状态</dt>
              <dd class="text-right text-slate-200">{{ latestDelivery?.status || '供应商尚未派送' }}</dd>
            </div>
            <div class="flex justify-between gap-4">
              <dt class="text-slate-500">预计时间</dt>
              <dd class="text-right text-slate-200">{{ formatDate(latestDelivery?.estimated_at) }}</dd>
            </div>
          </dl>
        </div>
      </div>

      <div class="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <div class="pc-card">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p class="text-xs font-bold uppercase tracking-[0.18em] text-indigo-300">Delivery records</p>
              <h2 class="mt-2 text-xl font-semibold text-white">交付与验收</h2>
            </div>
            <NuxtLink :to="`/market/buyer/messages?order_id=${order.id}`" class="text-sm text-indigo-300 hover:text-indigo-200">联系供应商 →</NuxtLink>
          </div>

          <div v-if="deliveries.length" class="mt-6 space-y-4">
            <div v-for="item in deliveries" :key="item.id" class="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
              <div class="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div class="flex flex-wrap items-center gap-2">
                    <span :class="['rounded-full px-2 py-0.5 text-xs font-semibold', deliveryTone(item.status)]">{{ item.status }}</span>
                    <span class="text-xs text-slate-500">Delivery {{ shortId(item.id) }}</span>
                  </div>
                  <p class="mt-3 font-semibold text-white">{{ item.carrier || 'Supplier delivery' }} <span v-if="item.tracking_number" class="text-slate-400">· {{ item.tracking_number }}</span></p>
                  <p class="mt-1 text-sm text-slate-500">预计 {{ formatDate(item.estimated_at) }} · 发出 {{ formatDate(item.shipped_at) }} · 送达 {{ formatDate(item.delivered_at) }}</p>
                </div>
                <button
                  v-if="item.status === 'delivered'"
                  class="btn-primary"
                  :disabled="acceptingId === item.id"
                  @click="accept(item.id)"
                >
                  {{ acceptingId === item.id ? '验收中...' : '确认收货' }}
                </button>
              </div>
              <div v-if="item.proof_json" class="mt-4 rounded-xl border border-white/10 bg-slate-950/60 p-3 text-xs text-slate-400">
                {{ proofLabel(item.proof_json) }}
              </div>
            </div>
          </div>

          <p v-else class="mt-6 rounded-2xl border border-dashed border-white/10 p-6 text-sm text-slate-500">
            供应商还没有创建交付记录。Partner/Supplier 端排期后，这里会显示承运方、追踪号、照片证据和验收按钮。
          </p>
        </div>

        <div class="space-y-6">
          <div class="pc-card">
            <div class="flex items-center justify-between gap-3">
              <div>
                <p class="text-xs font-bold uppercase tracking-[0.18em] text-indigo-300">Disputes</p>
                <h2 class="mt-2 text-xl font-semibold text-white">争议</h2>
              </div>
              <NuxtLink :to="`/market/buyer/disputes/new?order_id=${order.id}`" class="btn-secondary">发起</NuxtLink>
            </div>
            <div v-if="disputes.length" class="mt-5 space-y-3">
              <div v-for="item in disputes" :key="item.id" class="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <div class="flex items-center justify-between gap-3">
                  <p class="font-semibold text-white">{{ item.reason_code }}</p>
                  <span :class="['rounded-full px-2 py-0.5 text-xs font-semibold', statusTone(item.status)]">{{ item.status }}</span>
                </div>
                <p class="mt-2 text-sm text-slate-500">{{ item.description || '暂无描述' }}</p>
              </div>
            </div>
            <p v-else class="mt-5 text-sm text-slate-500">暂无争议。</p>
          </div>

          <div class="pc-card">
            <div class="flex items-center justify-between gap-3">
              <div>
                <p class="text-xs font-bold uppercase tracking-[0.18em] text-indigo-300">Payment ledger</p>
                <h2 class="mt-2 text-xl font-semibold text-white">支付/结算台账</h2>
              </div>
              <NuxtLink to="/market/buyer/wallet" class="text-sm text-indigo-300 hover:text-indigo-200">全部 →</NuxtLink>
            </div>
            <div v-if="ledgerRows.length" class="mt-5 space-y-3">
              <div v-for="item in ledgerRows" :key="item.id" class="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <div class="flex justify-between gap-3">
                  <div>
                    <p class="font-semibold text-white">{{ item.kind }}</p>
                    <p class="mt-1 text-xs text-slate-500">{{ formatDate(item.created_at) }}</p>
                  </div>
                  <div class="text-right">
                    <p class="font-semibold text-indigo-200">{{ formatMinor(item.amount_minor, item.currency) }}</p>
                    <p class="mt-1 text-xs text-slate-500">{{ item.status }}</p>
                  </div>
                </div>
              </div>
            </div>
            <p v-else class="mt-5 text-sm text-slate-500">当前订单还没有 payment intent / settlement 记录。</p>
          </div>
        </div>
      </div>
    </template>

    <p v-else class="pc-card text-sm text-red-300">{{ error || '订单不存在或当前账号无权访问。' }}</p>
  </section>
</template>

<script setup lang="ts">
const props = defineProps<{ id: string }>()
const api = useCommerce()

const order = ref<any>()
const request = ref<any>()
const offer = ref<any>()
const deliveries = ref<any[]>([])
const disputes = ref<any[]>([])
const ledgerRows = ref<any[]>([])
const loading = ref(true)
const completing = ref(false)
const acceptingId = ref('')
const error = ref('')
const message = ref('')

const latestDelivery = computed(() => deliveries.value[0])
const supplierLabel = computed(() => offer.value?.supplier_name || offer.value?.supplier_company_name || `Supplier ${shortId(order.value?.supplier_company_id) || '—'}`)

const canCompleteOrder = computed(() => {
  const status = String(order.value?.status || '').toLowerCase()
  if (['completed', 'cancelled'].includes(status)) return false
  return !hasOpenDispute.value
})

const hasOpenDispute = computed(() =>
  disputes.value.some(item => ['open', 'under_review'].includes(String(item.status || '').toLowerCase())),
)

const orderSteps = computed(() => {
  const orderStatus = String(order.value?.status || '').toLowerCase()
  const deliveryStatuses = deliveries.value.map(item => String(item.status || '').toLowerCase())
  const hasDelivery = deliveries.value.length > 0
  const delivered = deliveryStatuses.some(s => ['delivered', 'accepted'].includes(s))
  const completed = ['completed'].includes(orderStatus)
  return [
    { key: 'confirmed', label: '授标成单', hint: '报价已授标', done: true, active: orderStatus === 'confirmed' && !hasDelivery },
    { key: 'scheduled', label: '安排交付', hint: '供应商创建交付', done: hasDelivery || delivered || completed, active: hasDelivery && !delivered && !completed },
    { key: 'delivered', label: '送达验收', hint: '买家确认收货', done: delivered || completed, active: delivered && !completed },
    { key: 'completed', label: '订单完成', hint: '进入资产/维保', done: completed, active: completed },
  ]
})

const progressPercent = computed(() => {
  const done = orderSteps.value.filter(step => step.done).length
  return Math.round(Math.max(1, done) / orderSteps.value.length * 100)
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [orderRes, deliveryRes, disputeRes, ledgerRes] = await Promise.allSettled([
      api.getOrder(props.id),
      api.listDeliveries(props.id),
      api.listOrderDisputes(props.id),
      api.listPaymentLedger(),
    ])
    if (orderRes.status === 'fulfilled') order.value = orderRes.value
    else throw orderRes.reason
    if (deliveryRes.status === 'fulfilled') deliveries.value = deliveryRes.value.items || []
    if (disputeRes.status === 'fulfilled') disputes.value = disputeRes.value.items || []
    if (ledgerRes.status === 'fulfilled') ledgerRows.value = (ledgerRes.value.items || []).filter((item: any) => item.order_id === props.id)
    await loadLinkedRecords()
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || '加载订单失败'
  } finally {
    loading.value = false
  }
}

async function loadLinkedRecords() {
  const tasks: Promise<any>[] = []
  tasks.push(order.value?.procurement_request_id ? api.getProcurementRequest(order.value.procurement_request_id) : Promise.resolve(null))
  tasks.push(order.value?.winning_offer_id ? api.getOffer(order.value.winning_offer_id) : Promise.resolve(null))
  const [req, winningOffer] = await Promise.allSettled(tasks)
  if (req.status === 'fulfilled') request.value = req.value
  if (winningOffer.status === 'fulfilled') offer.value = winningOffer.value
}

async function complete() {
  completing.value = true
  error.value = ''
  message.value = ''
  try {
    order.value = await api.completeOrder(props.id)
    message.value = '订单已确认完成。'
    await load()
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || '确认完成失败'
  } finally {
    completing.value = false
  }
}

async function accept(id: string) {
  acceptingId.value = id
  error.value = ''
  message.value = ''
  try {
    await api.acceptDelivery(id)
    message.value = '交付已验收。'
    await load()
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || '确认收货失败'
  } finally {
    acceptingId.value = ''
  }
}

function statusTone(status?: string) {
  const s = String(status || '').toLowerCase()
  if (s.includes('complete') || s.includes('accept') || s.includes('confirm') || s.includes('resolved')) return 'bg-emerald-500/15 text-emerald-300'
  if (s.includes('deliver') || s.includes('ship') || s.includes('transit')) return 'bg-blue-500/15 text-blue-300'
  if (s.includes('dispute') || s.includes('open') || s.includes('review')) return 'bg-red-500/15 text-red-300'
  if (s.includes('pending') || s.includes('scheduled')) return 'bg-amber-500/15 text-amber-300'
  return 'bg-white/10 text-slate-300'
}

function deliveryTone(status?: string) {
  return statusTone(status)
}

function proofLabel(proof: any) {
  if (!proof || typeof proof !== 'object') return '交付证据已记录'
  const keys = Object.keys(proof)
  return keys.length ? `交付证据：${keys.join(', ')}` : '交付证据已记录'
}

function formatMinor(minor?: number | null, currency = 'EUR') {
  if (minor == null) return '—'
  try {
    return new Intl.NumberFormat(undefined, { style: 'currency', currency, maximumFractionDigits: 0 }).format(minor / 100)
  } catch {
    return `${(minor / 100).toLocaleString()} ${currency}`
  }
}

function formatDate(value?: string) {
  if (!value) return '—'
  try {
    return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }).format(new Date(value))
  } catch {
    return value
  }
}

function shortId(value?: string) {
  return value ? String(value).slice(0, 8) : ''
}

onMounted(load)
</script>
