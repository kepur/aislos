<template>
  <section class="mx-auto max-w-5xl space-y-6">
    <div class="flex items-center gap-3">
      <NuxtLink :to="localized('/supplier/pings')" class="text-sm text-indigo-300 hover:text-indigo-200">← 返回匹配需求</NuxtLink>
    </div>
    <div>
      <h1 class="text-2xl font-bold text-white">提交报价</h1>
      <p class="mt-1 text-sm text-slate-400">{{ request?.title ? `针对需求：${request.title}` : '请选择要报价的需求' }}</p>
    </div>

    <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <!-- Request summary (real data) -->
      <div class="lg:col-span-1">
        <div class="pc-card space-y-4">
          <h3 class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">需求详情</h3>
          <div v-if="!form.request_id">
            <label class="mb-1 block text-sm text-slate-400">选择需求</label>
            <select v-model="form.request_id" class="input-field" @change="loadRequest">
              <option value="">— 选择匹配需求 —</option>
              <option v-for="p in pings" :key="p.id" :value="requestId(p)">{{ p.title }}</option>
            </select>
          </div>
          <dl v-if="request" class="space-y-3 text-sm">
            <div><dt class="text-slate-500">标题</dt><dd class="mt-0.5 font-semibold text-white">{{ request.title }}</dd></div>
            <div><dt class="text-slate-500">预算</dt><dd class="mt-0.5 font-semibold text-white">{{ budgetOf(request) }}</dd></div>
            <div v-if="reqQty"><dt class="text-slate-500">数量</dt><dd class="mt-0.5 font-semibold text-white">{{ reqQty }} {{ reqUnit }}</dd></div>
            <div v-if="request.description"><dt class="text-slate-500">说明</dt><dd class="mt-0.5 italic text-slate-300">{{ request.description }}</dd></div>
            <div><dt class="text-slate-500">状态</dt><dd class="mt-0.5"><span class="rounded-full bg-blue-500/15 px-2 py-0.5 text-xs text-blue-300">{{ request.status }}</span></dd></div>
          </dl>
          <p v-else-if="form.request_id && loadingReq" class="text-sm text-slate-500">加载需求中…</p>
        </div>
      </div>

      <!-- Offer form -->
      <div class="lg:col-span-2">
        <form class="pc-card space-y-5" @submit.prevent="submit">
          <div>
            <label class="mb-1 block text-sm text-slate-400">绑定目录商品（可选）</label>
            <select v-model="form.supplier_listing_id" class="input-field">
              <option value="">不绑定目录商品</option>
              <option v-for="l in listings" :key="l.id" :value="l.id">{{ l.title }}</option>
            </select>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div><label class="mb-1 block text-sm text-slate-400">单价 *</label><input v-model.number="form.unitPrice" type="number" min="0" step="0.01" required class="input-field" /></div>
            <div><label class="mb-1 block text-sm text-slate-400">数量</label><input v-model.number="form.quantity" type="number" min="1" class="input-field" /></div>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div><label class="mb-1 block text-sm text-slate-400">运费</label><input v-model.number="form.deliveryFee" type="number" min="0" step="0.01" class="input-field" /></div>
            <div><label class="mb-1 block text-sm text-slate-400">币种</label>
              <select v-model="form.currency" class="input-field"><option v-for="c in currencies" :key="c" :value="c">{{ c }}</option></select>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div class="rounded-xl border border-white/10 bg-white/5 px-4 py-3"><p class="text-xs text-slate-500">商品小计</p><p class="mt-1 font-semibold text-white">{{ money(itemTotal) }}</p></div>
            <div class="rounded-xl border border-indigo-500/30 bg-indigo-500/10 px-4 py-3"><p class="text-xs text-indigo-300">到岸总价</p><p class="mt-1 text-lg font-bold text-indigo-200">{{ money(landedTotal) }}</p></div>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div><label class="mb-1 block text-sm text-slate-400">预计到货 (ETA)</label><input v-model.trim="form.eta" class="input-field" placeholder="例如：3-5 天 / 明天下午" /></div>
            <div><label class="mb-1 block text-sm text-slate-400">库存信心</label>
              <select v-model="form.stock" class="input-field"><option v-for="s in stockLevels" :key="s.value" :value="s.value">{{ s.label }}</option></select>
            </div>
          </div>
          <div><label class="mb-1 block text-sm text-slate-400">质保</label><input v-model.trim="form.warranty" class="input-field" placeholder="例如：12 个月" /></div>
          <div><label class="mb-1 block text-sm text-slate-400">商务条款 / 备注</label><textarea v-model.trim="form.notes" rows="3" class="input-field" placeholder="品牌、规格、付款条件等" /></div>

          <p v-if="error" class="text-sm text-red-300">{{ error }}</p>
          <button class="btn-primary" :disabled="saving || !form.request_id">{{ saving ? '提交中…' : '提交报价' }}</button>
        </form>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()
definePageMeta({ layout: 'procurement', middleware: ['auth'] })

const route = useRoute()
const api = useCommerce()
const pings = ref<any[]>([])
const listings = ref<any[]>([])
const request = ref<any>(null)
const loadingReq = ref(false)
const saving = ref(false)
const error = ref('')
const currencies = ['EUR', 'RSD', 'PLN', 'BAM', 'USD']
const stockLevels = [
  { value: 'high', label: '充足（自有库存）' },
  { value: 'medium', label: '中等（供应网络）' },
  { value: 'low', label: '需采购' },
]
const form = reactive({
  request_id: String(route.query.request_id || ''),
  supplier_listing_id: '',
  unitPrice: null as number | null,
  quantity: 1,
  deliveryFee: null as number | null,
  currency: 'EUR',
  eta: '',
  stock: 'high',
  warranty: '',
  notes: '',
})

const itemTotal = computed(() => (form.unitPrice || 0) * (form.quantity || 1))
const landedTotal = computed(() => itemTotal.value + (form.deliveryFee || 0))
const reqQty = computed(() => request.value?.requirements_json?.quantity ?? request.value?.attrs_json?.quantity ?? null)
const reqUnit = computed(() => request.value?.requirements_json?.unit ?? request.value?.attrs_json?.unit ?? '')

function requestId(p: any) {
  return p.procurement_request_id || p.request_id || p.id
}
function budgetOf(r: any) {
  const req = r?.requirements_json || r?.attrs_json || {}
  const min = req.budget_min_minor, max = req.budget_max_minor, cur = req.currency || r?.currency || 'EUR'
  const f = (v: any) => (v == null ? null : new Intl.NumberFormat(undefined, { style: 'currency', currency: cur, maximumFractionDigits: 0 }).format(v / 100))
  if (min != null && max != null) return `${f(min)} - ${f(max)}`
  if (max != null) return `≤ ${f(max)}`
  return '开放预算'
}
function money(v: number) {
  try { return new Intl.NumberFormat(undefined, { style: 'currency', currency: form.currency, maximumFractionDigits: 2 }).format(v) } catch { return `${v.toLocaleString()} ${form.currency}` }
}

async function loadRequest() {
  if (!form.request_id) { request.value = null; return }
  loadingReq.value = true
  try {
    request.value = await api.getProcurementRequest(form.request_id)
    const cur = request.value?.requirements_json?.currency
    if (cur) form.currency = cur
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || '加载需求失败'
  } finally {
    loadingReq.value = false
  }
}

async function submit() {
  if (!form.request_id) { error.value = '请先选择需求'; return }
  saving.value = true
  error.value = ''
  try {
    await api.submitSupplierOffer(form.request_id, {
      supplier_listing_id: form.supplier_listing_id || null,
      unit_price_minor: form.unitPrice != null ? Math.round(form.unitPrice * 100) : undefined,
      total_price_minor: Math.round(landedTotal.value * 100),
      delivery_fee_minor: form.deliveryFee != null ? Math.round(form.deliveryFee * 100) : undefined,
      currency: form.currency,
      eta: form.eta || undefined,
      stock_confidence: form.stock,
      warranty: form.warranty || undefined,
      terms_json: { quantity: form.quantity, notes: form.notes, eta: form.eta, stock: form.stock, warranty: form.warranty },
    })
    await navigateTo('/supplier/offers')
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || '提交报价失败'
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  const [a, b] = await Promise.allSettled([api.listSupplierPings(), api.listSupplierListings('active')])
  if (a.status === 'fulfilled') pings.value = a.value.items || []
  if (b.status === 'fulfilled') listings.value = b.value.items || []
  if (form.request_id) await loadRequest()
})
</script>
