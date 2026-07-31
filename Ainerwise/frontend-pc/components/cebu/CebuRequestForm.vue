<template>
  <div class="space-y-8">
    <!-- Stepper -->
    <div class="relative flex items-center justify-between">
      <div class="absolute left-0 top-4 -z-0 h-0.5 w-full rounded bg-white/10"></div>
      <div class="absolute left-0 top-4 -z-0 h-0.5 rounded bg-indigo-500 transition-all duration-300" :style="{ width: `${(step / (steps.length - 1)) * 100}%` }"></div>
      <div v-for="(s, i) in steps" :key="i" class="relative z-10 flex flex-col items-center">
        <div :class="['flex h-8 w-8 items-center justify-center rounded-full border-2 text-sm font-bold transition', i < step ? 'border-indigo-500 bg-indigo-500 text-white' : i === step ? 'border-indigo-400 bg-slate-950 text-indigo-300' : 'border-white/15 bg-slate-950 text-slate-500']">
          <span v-if="i < step">✓</span><span v-else>{{ i + 1 }}</span>
        </div>
        <span :class="['mt-2 text-xs', i <= step ? 'text-indigo-200' : 'text-slate-500']">{{ s }}</span>
      </div>
    </div>

    <div class="pc-card min-h-[360px]">
      <!-- Step 0: Category -->
      <div v-if="step === 0" class="space-y-5">
        <h2 class="text-xl font-bold text-white">选择类目</h2>
        <input v-model.trim="categorySearch" class="input-field" placeholder="搜索类目…" />
        <div class="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
          <button
            type="button"
            :class="['rounded-xl border p-4 text-center text-sm transition', !form.category_schema_id ? 'border-indigo-400 bg-indigo-500/10 text-indigo-200' : 'border-white/10 text-slate-300 hover:border-indigo-400/50']"
            @click="pickCategory('', '')"
          >
            <div class="text-2xl">🤖</div>
            <div class="mt-1 font-medium">让 AI 分类</div>
          </button>
          <button
            v-for="c in filteredCategories"
            :key="c.id"
            type="button"
            :class="['rounded-xl border p-4 text-center text-sm transition', form.category_schema_id === c.id ? 'border-indigo-400 bg-indigo-500/10 text-indigo-200' : 'border-white/10 text-slate-300 hover:border-indigo-400/50']"
            @click="pickCategory(c.id, c.name || c.title)"
          >
            <div class="text-2xl">📦</div>
            <div class="mt-1 font-medium">{{ c.name || c.title }}</div>
          </button>
        </div>
        <p v-if="categoryError" class="text-sm text-amber-300">{{ categoryError }} <button type="button" class="underline" @click="loadCategories">重试</button></p>
      </div>

      <!-- Step 1: Details -->
      <div v-else-if="step === 1" class="space-y-5">
        <h2 class="text-xl font-bold text-white">需求明细</h2>
        <div v-if="form.categoryName" class="inline-block rounded bg-indigo-500/10 px-2 py-1 text-sm text-indigo-200">类目：{{ form.categoryName }} <button type="button" class="ml-1 underline" @click="step = 0">更改</button></div>
        <div>
          <label class="mb-1 block text-sm text-slate-300">需求标题 *</label>
          <input v-model.trim="form.title" class="input-field" placeholder="例如：20 间客房的智能门锁" />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="mb-1 block text-sm text-slate-300">数量</label>
            <input v-model.number="form.quantity" type="number" min="0" class="input-field" />
          </div>
          <div>
            <label class="mb-1 block text-sm text-slate-300">单位</label>
            <select v-model="form.unit" class="input-field">
              <option v-for="u in units" :key="u" :value="u">{{ u }}</option>
            </select>
          </div>
        </div>
        <div class="grid grid-cols-3 gap-4">
          <div>
            <label class="mb-1 block text-sm text-slate-300">预算下限</label>
            <input v-model.number="form.budgetMin" type="number" min="0" class="input-field" />
          </div>
          <div>
            <label class="mb-1 block text-sm text-slate-300">预算上限</label>
            <input v-model.number="form.budgetMax" type="number" min="0" class="input-field" />
          </div>
          <div>
            <label class="mb-1 block text-sm text-slate-300">币种</label>
            <select v-model="form.currency" class="input-field">
              <option v-for="c in currencies" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>
        </div>
        <div>
          <label class="mb-1 block text-sm text-slate-300">详细描述 *</label>
          <textarea v-model.trim="form.description" rows="4" class="input-field" placeholder="规格、品牌、质量标准、目标日期、约束条件…" />
        </div>
      </div>

      <!-- Step 2: Delivery -->
      <div v-else-if="step === 2" class="space-y-5">
        <h2 class="text-xl font-bold text-white">交付信息</h2>
        <div>
          <label class="mb-1 block text-sm text-slate-300">交付区域</label>
          <select v-model="form.region_id" class="input-field">
            <option value="">暂不确定</option>
            <option v-for="r in regions" :key="r.id" :value="r.id">{{ r.name }} ({{ r.code }})</option>
          </select>
        </div>
        <div>
          <label class="mb-1 block text-sm text-slate-300">期望交付日期</label>
          <input v-model="form.targetDate" type="date" class="input-field" />
        </div>
        <div>
          <label class="mb-1 block text-sm text-slate-300">交付地址 / 备注</label>
          <textarea v-model.trim="form.deliveryNote" rows="3" class="input-field" placeholder="收货地址、现场条件、安装要求等" />
        </div>
      </div>

      <!-- Step 3: Review -->
      <div v-else class="space-y-5">
        <h2 class="text-xl font-bold text-white">确认并提交</h2>
        <dl class="divide-y divide-white/5 text-sm">
          <div class="flex justify-between py-2"><dt class="text-slate-400">类目</dt><dd class="text-white">{{ form.categoryName || 'AI 自动分类' }}</dd></div>
          <div class="flex justify-between py-2"><dt class="text-slate-400">标题</dt><dd class="text-white">{{ form.title || '—' }}</dd></div>
          <div class="flex justify-between py-2"><dt class="text-slate-400">数量</dt><dd class="text-white">{{ form.quantity || '—' }} {{ form.unit }}</dd></div>
          <div class="flex justify-between py-2"><dt class="text-slate-400">预算</dt><dd class="text-white">{{ budgetSummary }}</dd></div>
          <div class="flex justify-between py-2"><dt class="text-slate-400">交付区域</dt><dd class="text-white">{{ regionName || '暂不确定' }}</dd></div>
          <div class="flex justify-between py-2"><dt class="text-slate-400">期望日期</dt><dd class="text-white">{{ form.targetDate || '—' }}</dd></div>
        </dl>
        <label class="flex items-start gap-3 text-sm text-slate-300">
          <input v-model="publishNow" type="checkbox" class="mt-1 accent-indigo-400" />
          立即发布，让已认证供应商可以响应（不勾选则保存为草稿）
        </label>
      </div>

      <p v-if="error" class="mt-4 text-sm text-red-300">{{ error }}</p>

      <!-- Nav -->
      <div class="mt-6 flex items-center justify-between border-t border-white/10 pt-5">
        <button type="button" class="btn-secondary" :class="{ 'pointer-events-none opacity-0': step === 0 }" @click="step--">上一步</button>
        <button v-if="step < steps.length - 1" type="button" class="btn-primary" :disabled="!canNext" @click="step++">下一步</button>
        <button v-else type="button" class="btn-primary" :disabled="saving || !canSubmit" @click="submit">{{ saving ? '提交中…' : (publishNow ? '提交并发布' : '保存草稿') }}</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{ redirectPrefix?: string }>(), { redirectPrefix: '/market/buyer/requests' })
const { token } = useAuth()
const { apiFetch } = useApi()
const { listPublicCategories, createProcurementRequest, publishRequest } = useCommerce()

const steps = ['类目', '明细', '交付', '确认']
const step = ref(0)
const categories = ref<any[]>([])
const regions = ref<any[]>([])
const saving = ref(false)
const publishNow = ref(true)
const error = ref('')
const categoryError = ref('')
const categorySearch = ref('')
const units = ['件', '台', '套', '箱', 'kg', '吨', '米', '个', 'unit']
const currencies = ['EUR', 'RSD', 'PLN', 'BAM', 'USD']
const form = reactive({
  title: '', description: '', category_schema_id: '', categoryName: '', region_id: '',
  quantity: null as number | null, unit: '件', budgetMin: null as number | null, budgetMax: null as number | null,
  currency: 'EUR', targetDate: '', deliveryNote: '',
})

const filteredCategories = computed(() => {
  const kw = categorySearch.value.toLowerCase()
  if (!kw) return categories.value
  return categories.value.filter(c => String(c.name || c.title || '').toLowerCase().includes(kw))
})
const regionName = computed(() => regions.value.find(r => r.id === form.region_id)?.name || '')
const budgetSummary = computed(() => {
  const f = (v: number | null) => (v == null ? null : `${form.currency} ${v.toLocaleString()}`)
  if (form.budgetMin != null && form.budgetMax != null) return `${f(form.budgetMin)} - ${f(form.budgetMax)}`
  if (form.budgetMax != null) return `≤ ${f(form.budgetMax)}`
  if (form.budgetMin != null) return `≥ ${f(form.budgetMin)}`
  return '开放预算'
})
const canNext = computed(() => {
  if (step.value === 1) return !!form.title && !!form.description
  return true
})
const canSubmit = computed(() => !!form.title && !!form.description)

function pickCategory(id: string, name: string) {
  form.category_schema_id = id
  form.categoryName = name
  step.value = 1
}

async function submit() {
  if (!token.value) {
    await navigateTo({ path: '/login', query: { redirect: '/market/post-request' } })
    return
  }
  if (!canSubmit.value) { error.value = '请填写标题和描述'; return }
  saving.value = true
  error.value = ''
  try {
    const row: any = await createProcurementRequest({
      title: form.title,
      description: form.description,
      category_schema_id: form.category_schema_id || undefined,
      region_id: form.region_id || undefined,
      requirements: {
        quantity: form.quantity ?? undefined,
        unit: form.unit,
        budget_min_minor: form.budgetMin != null ? Math.round(form.budgetMin * 100) : undefined,
        budget_max_minor: form.budgetMax != null ? Math.round(form.budgetMax * 100) : undefined,
        currency: form.currency,
        target_date: form.targetDate || undefined,
        delivery_note: form.deliveryNote || undefined,
      },
    })
    if (publishNow.value) await publishRequest(row.id)
    await navigateTo(`${props.redirectPrefix}/${row.id}`)
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || '创建需求失败'
  } finally {
    saving.value = false
  }
}

async function loadCategories() {
  categoryError.value = ''
  try {
    categories.value = (await listPublicCategories()).items || []
  } catch (e: any) {
    categories.value = []
    categoryError.value = e?.data?.detail || e?.message || '无法加载类目，可用 AI 自动分类'
  }
}

onMounted(async () => {
  await Promise.all([
    loadCategories(),
    apiFetch<any>('/regions').then((data: any) => { regions.value = data.items || [] }).catch(() => {}),
  ])
})
</script>
