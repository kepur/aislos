<template>
  <section class="space-y-6">
    <div v-if="loading" class="pc-card text-sm text-slate-400">正在加载采购需求...</div>

    <template v-else-if="request">
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div class="min-w-0 flex-1">
          <NuxtLink to="/market/buyer/requests" class="text-sm text-indigo-300 hover:text-indigo-200">← 返回需求列表</NuxtLink>
          <div class="mt-4 flex flex-wrap items-center gap-3">
            <p class="text-xs font-bold uppercase tracking-[0.2em] text-indigo-300">Request {{ shortId(request.id) }}</p>
            <span :class="['rounded-full px-3 py-1 text-xs font-semibold', statusTone(request.status)]">{{ request.status }}</span>
          </div>
          <h1 class="mt-2 text-3xl font-bold tracking-tight text-white">{{ request.title || '未命名采购需求' }}</h1>
          <p class="mt-3 max-w-3xl text-sm leading-6 text-slate-400">{{ request.description || '暂无详细描述，建议补充规格、数量、预算和交付约束。' }}</p>
          <p class="mt-3 text-xs text-slate-500">
            创建于 {{ formatDate(request.created_at) }}
            <span v-if="request.published_at"> · 发布于 {{ formatDate(request.published_at) }}</span>
          </p>
        </div>
        <div class="flex flex-wrap gap-2">
          <button
            v-if="canPublish"
            class="btn-primary"
            :disabled="publishing"
            @click="publish"
          >
            {{ publishing ? '发布中...' : '发布需求' }}
          </button>
          <NuxtLink :to="`/market/buyer/requests/${request.id}/offers`" class="btn-secondary">对比报价</NuxtLink>
          <NuxtLink to="/market/marketplace" class="btn-secondary">浏览匹配挂牌</NuxtLink>
        </div>
      </div>

      <JourneyProgress :status="request.status" />

      <p v-if="error" class="pc-card text-sm text-red-300">{{ error }}</p>

      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div v-for="kpi in kpis" :key="kpi.label" class="pc-card">
          <p class="text-sm text-slate-400">{{ kpi.label }}</p>
          <p class="mt-2 text-3xl font-bold text-white">{{ kpi.value }}</p>
          <p class="mt-1 text-xs text-slate-500">{{ kpi.hint }}</p>
        </div>
      </div>

      <div class="grid gap-6 lg:grid-cols-[1.35fr_0.85fr]">
        <div class="pc-card">
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p class="text-xs font-bold uppercase tracking-[0.18em] text-indigo-300">Request specifications</p>
              <h2 class="mt-2 text-xl font-semibold text-white">采购规格</h2>
            </div>
            <NuxtLink to="/market/post-request" class="text-sm text-indigo-300 hover:text-indigo-200">发布新需求 →</NuxtLink>
          </div>

          <dl class="mt-6 grid gap-4 sm:grid-cols-2">
            <div v-for="row in specRows" :key="row.label" class="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
              <dt class="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">{{ row.label }}</dt>
              <dd class="mt-2 text-sm font-medium text-slate-100">{{ row.value }}</dd>
            </div>
          </dl>

          <div class="mt-6 rounded-2xl border border-white/10 bg-white/[0.03] p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Detailed description</p>
            <p class="mt-3 whitespace-pre-line text-sm leading-6 text-slate-300">{{ request.description || requirements.description || '暂无描述' }}</p>
          </div>

          <div class="mt-6">
            <div class="flex items-center justify-between gap-3">
              <h3 class="text-sm font-semibold text-white">附件</h3>
              <span class="text-xs text-slate-500">{{ attachments.length }} 个文件</span>
            </div>
            <div v-if="attachments.length" class="mt-3 grid gap-3 sm:grid-cols-2">
              <a
                v-for="file in attachments"
                :key="file.url || file.name"
                :href="file.url || '#'"
                class="rounded-2xl border border-white/10 bg-white/[0.03] p-3 text-sm text-slate-200 transition hover:border-indigo-400/40"
                target="_blank"
              >
                <p class="font-medium">{{ file.name || file.filename || 'Attachment' }}</p>
                <p class="mt-1 text-xs text-slate-500">{{ file.type || file.mime || '采购文件' }}</p>
              </a>
            </div>
            <p v-else class="mt-3 rounded-2xl border border-dashed border-white/10 p-4 text-sm text-slate-500">当前 Core 记录没有附件；后续 Document Center 接入后这里会直接展示图纸、规格书和照片。</p>
          </div>
        </div>

        <div class="space-y-6">
          <div class="pc-card">
            <p class="text-xs font-bold uppercase tracking-[0.18em] text-indigo-300">Logistics</p>
            <h2 class="mt-2 text-xl font-semibold text-white">交付与区域</h2>
            <dl class="mt-5 space-y-4 text-sm">
              <div class="flex justify-between gap-4">
                <dt class="text-slate-500">Region ID</dt>
                <dd class="text-right text-slate-200">{{ shortId(request.region_id) || '未指定' }}</dd>
              </div>
              <div class="flex justify-between gap-4">
                <dt class="text-slate-500">Delivery area</dt>
                <dd class="text-right text-slate-200">{{ deliveryArea }}</dd>
              </div>
              <div class="flex justify-between gap-4">
                <dt class="text-slate-500">Search radius</dt>
                <dd class="text-right text-slate-200">{{ requirements.radius_km || attrs.radius_km || 'Core 默认匹配' }}</dd>
              </div>
              <div class="flex justify-between gap-4">
                <dt class="text-slate-500">Bound listings</dt>
                <dd class="text-right text-slate-200">{{ boundListingIds.length }}</dd>
              </div>
            </dl>
          </div>

          <div class="pc-card">
            <p class="text-xs font-bold uppercase tracking-[0.18em] text-indigo-300">Commercial flow</p>
            <h2 class="mt-2 text-xl font-semibold text-white">商业状态</h2>
            <div class="mt-5 space-y-3">
              <div v-for="step in flowSteps" :key="step.label" class="flex items-start gap-3">
                <div :class="['mt-0.5 h-3 w-3 rounded-full', step.done ? 'bg-indigo-300' : 'bg-white/15']" />
                <div>
                  <p :class="step.done ? 'text-sm font-semibold text-white' : 'text-sm text-slate-500'">{{ step.label }}</p>
                  <p class="text-xs text-slate-500">{{ step.hint }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="pc-card">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p class="text-xs font-bold uppercase tracking-[0.18em] text-indigo-300">Supplier candidates</p>
            <h2 class="mt-2 text-xl font-semibold text-white">AI 匹配供应商候选</h2>
            <p class="mt-1 text-sm text-slate-400">来自 Core 的真实挂牌匹配；可绑定到本需求，后续供应商报价会进入同一商业记录。</p>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <select v-model="candidateSort" class="rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-slate-200 outline-none focus:border-indigo-400/60">
              <option value="comprehensive">综合排序</option>
              <option value="cost">价格优先</option>
              <option value="newest">最新挂牌</option>
              <option value="bound">已绑定优先</option>
            </select>
            <button class="btn-secondary" :disabled="candidatesLoading" @click="loadCandidates">
              {{ candidatesLoading ? '刷新中...' : '刷新候选' }}
            </button>
          </div>
        </div>

        <div v-if="candidatesLoading" class="mt-6 rounded-2xl border border-white/10 bg-white/[0.03] p-5 text-sm text-slate-400">正在匹配候选...</div>

        <div v-else-if="sortedCandidates.length" class="mt-6 grid gap-4">
          <div
            v-for="(item, index) in sortedCandidates"
            :key="candidateId(item)"
            class="rounded-2xl border border-white/10 bg-white/[0.03] p-4 transition hover:border-indigo-400/40"
          >
            <div class="flex flex-wrap items-start justify-between gap-4">
              <div class="min-w-0 flex-1">
                <div class="flex flex-wrap items-center gap-2">
                  <span class="rounded-full bg-indigo-500/15 px-2 py-0.5 text-xs font-semibold text-indigo-200">#{{ index + 1 }}</span>
                  <span v-if="isBound(item)" class="rounded-full bg-emerald-500/15 px-2 py-0.5 text-xs font-semibold text-emerald-300">已绑定</span>
                  <span class="rounded-full bg-white/10 px-2 py-0.5 text-xs text-slate-300">{{ item.status || 'active' }}</span>
                </div>
                <h3 class="mt-3 text-lg font-semibold text-white">{{ item.title || '供应商挂牌' }}</h3>
                <p class="mt-1 text-sm text-slate-400">{{ candidateCompany(item) }}</p>
                <p class="mt-3 max-w-3xl text-sm leading-6 text-slate-400">{{ candidateWhy(item) }}</p>
                <div class="mt-4 flex flex-wrap gap-2">
                  <span v-for="chip in candidateChips(item)" :key="chip" class="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-xs text-slate-300">{{ chip }}</span>
                </div>
              </div>
              <div class="min-w-[180px] text-left sm:text-right">
                <p class="text-xs uppercase tracking-[0.14em] text-slate-500">挂牌价格</p>
                <p class="mt-1 text-2xl font-bold text-indigo-200">{{ formatMinor(candidatePriceMinor(item), item.currency || request.currency || 'EUR') }}</p>
                <div class="mt-4 flex flex-wrap justify-start gap-2 sm:justify-end">
                  <button class="btn-secondary" @click="selectedCandidate = item">详情</button>
                  <NuxtLink :to="`/market/marketplace/${candidateId(item)}`" class="btn-secondary">挂牌</NuxtLink>
                  <button
                    class="btn-primary"
                    :disabled="isBound(item) || bindingId === candidateId(item)"
                    @click="bind(candidateId(item))"
                  >
                    {{ isBound(item) ? '已绑定' : bindingId === candidateId(item) ? '绑定中...' : '绑定' }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="mt-6 rounded-2xl border border-dashed border-white/10 p-6 text-sm text-slate-500">
          当前没有候选。若需求仍是 draft，请先发布；若类目或区域过窄，可以去市场浏览后手动绑定挂牌。
        </div>
      </div>
    </template>

    <p v-else class="pc-card text-sm text-red-300">{{ error || '采购需求不存在或当前账号无权访问。' }}</p>

    <div v-if="selectedCandidate" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur">
      <div class="w-full max-w-2xl rounded-3xl border border-white/10 bg-slate-950 p-6 shadow-2xl">
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-xs font-bold uppercase tracking-[0.18em] text-indigo-300">Candidate detail</p>
            <h3 class="mt-2 text-2xl font-bold text-white">{{ selectedCandidate.title }}</h3>
            <p class="mt-1 text-sm text-slate-400">{{ candidateCompany(selectedCandidate) }}</p>
          </div>
          <button class="rounded-full border border-white/10 px-3 py-1 text-sm text-slate-300 hover:border-indigo-400/40" @click="selectedCandidate = null">关闭</button>
        </div>
        <div class="mt-6 grid gap-3 sm:grid-cols-3">
          <div class="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
            <p class="text-xs text-slate-500">挂牌价格</p>
            <p class="mt-2 text-lg font-semibold text-white">{{ formatMinor(candidatePriceMinor(selectedCandidate), selectedCandidate.currency || 'EUR') }}</p>
          </div>
          <div class="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
            <p class="text-xs text-slate-500">类目</p>
            <p class="mt-2 text-lg font-semibold text-white">{{ shortId(selectedCandidate.category_schema_id) || '—' }}</p>
          </div>
          <div class="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
            <p class="text-xs text-slate-500">区域</p>
            <p class="mt-2 text-lg font-semibold text-white">{{ shortId(selectedCandidate.region_id) || '不限' }}</p>
          </div>
        </div>
        <p class="mt-5 rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm leading-6 text-slate-300">{{ candidateWhy(selectedCandidate) }}</p>
        <div class="mt-5 flex flex-wrap justify-end gap-2">
          <NuxtLink :to="`/market/marketplace/${candidateId(selectedCandidate)}`" class="btn-secondary">查看挂牌</NuxtLink>
          <button class="btn-primary" :disabled="isBound(selectedCandidate)" @click="bind(candidateId(selectedCandidate))">{{ isBound(selectedCandidate) ? '已绑定' : '绑定到需求' }}</button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
const props = defineProps<{ id: string }>()
const api = useCommerce()

const request = ref<any>(null)
const offers = ref<any[]>([])
const candidates = ref<any[]>([])
const error = ref('')
const loading = ref(true)
const publishing = ref(false)
const candidatesLoading = ref(false)
const bindingId = ref('')
const candidateSort = ref('comprehensive')
const selectedCandidate = ref<any | null>(null)

const attrs = computed<Record<string, any>>(() => request.value?.attrs_json || {})
const requirements = computed<Record<string, any>>(() => request.value?.requirements_json || {})
const boundListingIds = computed<string[]>(() => (attrs.value.bound_listing_ids || []).map(String))
const canPublish = computed(() => ['draft', 'matching'].includes(String(request.value?.status || '').toLowerCase()))
const attachments = computed<any[]>(() => {
  const raw = requirements.value.attachments || attrs.value.attachments || []
  return Array.isArray(raw) ? raw : []
})

const budgetLabel = computed(() => {
  const min = pickNumber(requirements.value.budget_min_minor, requirements.value.budget_min, attrs.value.budget_min_minor)
  const max = pickNumber(requirements.value.budget_max_minor, requirements.value.budget_max, attrs.value.budget_max_minor)
  const currency = requirements.value.currency || attrs.value.currency || 'EUR'
  if (min != null && max != null) return `${formatMinor(min, currency)} - ${formatMinor(max, currency)}`
  if (max != null) return `≤ ${formatMinor(max, currency)}`
  if (min != null) return `≥ ${formatMinor(min, currency)}`
  return '待供应商报价'
})

const deliveryArea = computed(() => {
  return requirements.value.delivery_area
    || requirements.value.location
    || attrs.value.delivery_area
    || attrs.value.location
    || '按区域匹配'
})

const deliveryWindow = computed(() => {
  return requirements.value.delivery_window
    || requirements.value.required_by
    || attrs.value.delivery_window
    || attrs.value.required_by
    || '供应商报价时确认'
})

const quantityLabel = computed(() => {
  const qty = requirements.value.quantity || attrs.value.quantity
  const unit = requirements.value.unit || attrs.value.unit || ''
  return qty ? `${qty} ${unit}`.trim() : '报价时确认'
})

const specRows = computed(() => [
  { label: 'Category ID', value: shortId(request.value.category_schema_id) || '未指定' },
  { label: 'Budget range', value: budgetLabel.value },
  { label: 'Quantity', value: quantityLabel.value },
  { label: 'Delivery window', value: deliveryWindow.value },
])

const kpis = computed(() => [
  { label: '收到报价', value: offers.value.length, hint: '来自供应商的真实报价' },
  { label: '绑定候选', value: boundListingIds.value.length, hint: '已关联到本需求的挂牌' },
  { label: '推荐候选', value: candidates.value.length, hint: 'Core 按类目/区域匹配' },
  { label: '当前状态', value: request.value.status || '—', hint: 'draft → published → awarded' },
])

const flowSteps = computed(() => {
  const status = String(request.value?.status || '').toLowerCase()
  return [
    { label: '需求创建', hint: 'Buyer 提交或 AI 顾问生成', done: true },
    { label: '公开寻源', hint: '发布后可匹配挂牌与供应商', done: !['draft'].includes(status) },
    { label: '收到报价', hint: '供应商报价进入对比页', done: offers.value.length > 0 || ['offer_received', 'awarded', 'closed'].includes(status) },
    { label: '人工授标', hint: 'Buyer/Admin 确认后创建订单', done: ['awarded', 'closed'].includes(status) },
  ]
})

const sortedCandidates = computed(() => {
  const rows = [...candidates.value]
  if (candidateSort.value === 'cost') {
    return rows.sort((a, b) => (candidatePriceMinor(a) ?? Number.MAX_SAFE_INTEGER) - (candidatePriceMinor(b) ?? Number.MAX_SAFE_INTEGER))
  }
  if (candidateSort.value === 'newest') {
    return rows.sort((a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime())
  }
  if (candidateSort.value === 'bound') {
    return rows.sort((a, b) => Number(isBound(b)) - Number(isBound(a)))
  }
  return rows.sort((a, b) => (candidateScore(b) ?? 0) - (candidateScore(a) ?? 0))
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [req, offerRes] = await Promise.allSettled([
      api.getProcurementRequest(props.id),
      api.listOffers(props.id),
    ])
    if (req.status === 'fulfilled') request.value = req.value
    else throw req.reason
    if (offerRes.status === 'fulfilled') offers.value = offerRes.value.items || []
    await loadCandidates(false)
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || '加载采购需求失败'
  } finally {
    loading.value = false
  }
}

async function loadCandidates(showSpinner = true) {
  if (showSpinner) candidatesLoading.value = true
  try {
    const res = await api.listCandidates(props.id)
    candidates.value = res.items || []
  } catch (e: any) {
    if (!['draft'].includes(String(request.value?.status || '').toLowerCase())) {
      error.value = e?.data?.detail || e?.message || '加载候选供应商失败'
    }
    candidates.value = []
  } finally {
    candidatesLoading.value = false
  }
}

async function publish() {
  publishing.value = true
  error.value = ''
  try {
    request.value = await api.publishRequest(props.id)
    await Promise.all([loadCandidates(), refreshOffers()])
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || '发布失败'
  } finally {
    publishing.value = false
  }
}

async function refreshOffers() {
  try {
    const res = await api.listOffers(props.id)
    offers.value = res.items || []
  } catch {
    offers.value = []
  }
}

async function bind(id: string) {
  if (!id) return
  bindingId.value = id
  error.value = ''
  try {
    request.value = await api.bindCandidate(props.id, id)
    selectedCandidate.value = null
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || '绑定候选失败'
  } finally {
    bindingId.value = ''
  }
}

function candidateId(item: any) {
  return String(item?.id || item?.supplier_listing_id || item?.catalog_item_id || '')
}

function candidateCompany(item: any) {
  return item?.company_name || item?.supplier_name || item?.attributes_json?.company_name || `Company ${shortId(item?.company_id) || '—'}`
}

function candidatePriceMinor(item: any) {
  return pickNumber(item?.price_minor, item?.unit_price_minor, item?.attributes_json?.price_minor)
}

function candidateScore(item: any) {
  return pickNumber(item?.ranking_score, item?.score, item?.attributes_json?.ranking_score)
}

function candidateWhy(item: any) {
  return item?.why_recommended
    || item?.attributes_json?.why_recommended
    || 'Core 根据需求类目、区域和可用挂牌匹配该供应商；更细的 AI 评分会在 Phase C/D 接入。'
}

function candidateChips(item: any) {
  const chips = [
    item?.category_schema_id ? `类目 ${shortId(item.category_schema_id)}` : '',
    item?.region_id ? `区域 ${shortId(item.region_id)}` : '跨区域',
    item?.legacy_catalog_item_id ? `Legacy ${item.legacy_catalog_item_id}` : '',
    item?.created_at ? `上架 ${formatDate(item.created_at)}` : '',
  ]
  return chips.filter(Boolean)
}

function isBound(item: any) {
  return boundListingIds.value.includes(candidateId(item))
}

function pickNumber(...values: any[]) {
  for (const value of values) {
    if (value === null || value === undefined || value === '') continue
    const num = Number(value)
    if (Number.isFinite(num)) return num
  }
  return null
}

function statusTone(status?: string) {
  const s = String(status || '').toLowerCase()
  if (s.includes('award') || s.includes('closed') || s.includes('complete')) return 'bg-emerald-500/15 text-emerald-300'
  if (s.includes('publish') || s.includes('matching') || s.includes('offer')) return 'bg-blue-500/15 text-blue-300'
  if (s.includes('draft') || s.includes('pending')) return 'bg-amber-500/15 text-amber-300'
  if (s.includes('cancel')) return 'bg-red-500/15 text-red-300'
  return 'bg-white/10 text-slate-300'
}

function formatMinor(minor?: number | null, currency = 'EUR') {
  if (minor == null) return '待报价'
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
