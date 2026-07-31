<template>
  <section class="space-y-5">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-xs font-bold uppercase tracking-[0.2em] text-indigo-300">Catalog</p>
        <h1 class="mt-1 text-2xl font-bold text-white">供应目录</h1>
        <p class="mt-1 text-sm text-slate-400">维护挂牌商品，目录越完善匹配到的采购需求越多。</p>
      </div>
      <button class="btn-primary" @click="start()">+ 新增目录项</button>
    </div>

    <div class="grid grid-cols-3 gap-4">
      <div class="pc-card"><p class="text-sm text-slate-400">全部</p><p class="mt-1 text-2xl font-bold text-white">{{ items.length }}</p></div>
      <div class="pc-card"><p class="text-sm text-slate-400">已上架</p><p class="mt-1 text-2xl font-bold text-emerald-300">{{ countBy('active') }}</p></div>
      <div class="pc-card"><p class="text-sm text-slate-400">草稿</p><p class="mt-1 text-2xl font-bold text-amber-300">{{ countBy('draft') }}</p></div>
    </div>

    <!-- Editor -->
    <form v-if="editing" class="pc-card grid gap-4 md:grid-cols-2" @submit.prevent="save">
      <h2 class="text-lg font-medium text-white md:col-span-2">{{ form.id ? '编辑目录项' : '新增目录项' }}</h2>
      <div><label class="mb-1 block text-sm text-slate-400">标题 *</label><input v-model.trim="form.title" required class="input-field" /></div>
      <div><label class="mb-1 block text-sm text-slate-400">类目</label>
        <select v-model="form.category_schema_id" class="input-field"><option value="">未分类</option><option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name || c.title }}</option></select>
      </div>
      <div><label class="mb-1 block text-sm text-slate-400">单价</label><input v-model.number="price" type="number" min="0" step="0.01" class="input-field" /></div>
      <div><label class="mb-1 block text-sm text-slate-400">币种</label>
        <select v-model="form.currency" class="input-field"><option v-for="c in currencies" :key="c" :value="c">{{ c }}</option></select>
      </div>
      <div><label class="mb-1 block text-sm text-slate-400">单位</label><input v-model.trim="attr.unit" class="input-field" placeholder="件 / 台 / 套" /></div>
      <div><label class="mb-1 block text-sm text-slate-400">起订量 (MOQ)</label><input v-model.number="attr.min_order_qty" type="number" min="1" class="input-field" /></div>
      <div><label class="mb-1 block text-sm text-slate-400">品牌</label><input v-model.trim="attr.brand" class="input-field" /></div>
      <div><label class="mb-1 block text-sm text-slate-400">库存</label><input v-model.number="attr.stock_qty" type="number" min="0" class="input-field" /></div>
      <div><label class="mb-1 block text-sm text-slate-400">状态</label>
        <select v-model="form.status" class="input-field"><option value="active">已上架</option><option value="inactive">已下架</option><option value="draft">草稿</option></select>
      </div>
      <div><label class="mb-1 block text-sm text-slate-400">交易模式</label>
        <select v-model="attr.market_mode" class="input-field"><option value="B2B">B2B</option><option value="B2C">B2C</option></select>
      </div>
      <div class="md:col-span-2"><label class="mb-1 block text-sm text-slate-400">描述</label><textarea v-model.trim="attr.description" rows="3" class="input-field" /></div>
      <div class="flex gap-3 md:col-span-2">
        <button class="btn-primary" :disabled="saving">{{ saving ? '保存中…' : (form.id ? '保存' : '创建') }}</button>
        <button type="button" class="btn-secondary" @click="editing = false">取消</button>
      </div>
    </form>

    <!-- Toolbar -->
    <div class="pc-card flex flex-wrap items-center gap-3">
      <input v-model.trim="keyword" class="input-field max-w-xs" placeholder="搜索商品…" />
      <div class="flex gap-1">
        <button v-for="f in statusFilters" :key="f.value" :class="['rounded-lg px-3 py-1.5 text-sm transition', statusFilter === f.value ? 'bg-indigo-500/15 text-indigo-200' : 'text-slate-400 hover:bg-white/5']" @click="statusFilter = f.value">{{ f.label }}</button>
      </div>
    </div>

    <p v-if="error" class="pc-card text-sm text-red-300">{{ error }}</p>

    <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      <article v-for="item in filtered" :key="item.id" class="pc-card">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <p class="truncate font-semibold text-white">{{ item.title }}</p>
            <p class="mt-1 text-lg font-bold text-indigo-300">{{ money(item.price_minor, item.currency) }}</p>
          </div>
          <span :class="['shrink-0 rounded-full px-2 py-0.5 text-xs', statusTone(item.status)]">{{ statusLabel(item.status) }}</span>
        </div>
        <div class="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-slate-500">
          <span v-if="attrOf(item).brand">品牌 {{ attrOf(item).brand }}</span>
          <span v-if="attrOf(item).unit">单位 {{ attrOf(item).unit }}</span>
          <span v-if="attrOf(item).min_order_qty">MOQ {{ attrOf(item).min_order_qty }}</span>
          <span v-if="attrOf(item).stock_qty != null">库存 {{ attrOf(item).stock_qty }}</span>
        </div>
        <div class="mt-3 flex gap-3 border-t border-white/5 pt-3">
          <button class="text-sm text-indigo-300 hover:text-indigo-200" @click="start(item)">编辑</button>
          <button class="text-sm text-red-300 hover:text-red-200" @click="archive(item.id)">下架</button>
        </div>
      </article>
      <p v-if="!loading && !filtered.length" class="pc-card text-sm text-slate-400 md:col-span-2 xl:col-span-3">暂无目录项，点击「新增目录项」开始。</p>
    </div>
  </section>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'procurement', middleware: ['auth'] })

const api = useCommerce()
const items = ref<any[]>([])
const categories = ref<any[]>([])
const editing = ref(false)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const price = ref(0)
const keyword = ref('')
const statusFilter = ref('')
const currencies = ['EUR', 'RSD', 'PLN', 'BAM', 'USD']
const statusFilters = [
  { value: '', label: '全部' }, { value: 'active', label: '已上架' }, { value: 'inactive', label: '已下架' }, { value: 'draft', label: '草稿' },
]
const form = reactive<any>({ id: '', title: '', category_schema_id: '', status: 'active', currency: 'EUR' })
const attr = reactive<any>({ unit: '', min_order_qty: null, brand: '', stock_qty: null, market_mode: 'B2B', description: '' })

const filtered = computed(() => {
  const kw = keyword.value.toLowerCase()
  return items.value.filter((it) => {
    if (statusFilter.value && String(it.status) !== statusFilter.value) return false
    if (kw && !String(it.title || '').toLowerCase().includes(kw)) return false
    return true
  })
})

function countBy(s: string) { return items.value.filter(i => String(i.status) === s).length }
function attrOf(it: any) { return it?.attributes_json && typeof it.attributes_json === 'object' ? it.attributes_json : {} }
function statusLabel(s?: string) { return { active: '已上架', inactive: '已下架', draft: '草稿' }[String(s || '')] || s || '—' }
function statusTone(s?: string) {
  const v = String(s || '')
  if (v === 'active') return 'bg-emerald-500/15 text-emerald-300'
  if (v === 'draft') return 'bg-amber-500/15 text-amber-300'
  return 'bg-white/10 text-slate-400'
}
function money(v?: number | null, c = 'EUR') { return v == null ? '询价' : new Intl.NumberFormat(undefined, { style: 'currency', currency: c, maximumFractionDigits: 0 }).format(v / 100) }

function start(item?: any) {
  Object.assign(form, { id: item?.id || '', title: item?.title || '', category_schema_id: item?.category_schema_id || '', status: item?.status || 'active', currency: item?.currency || 'EUR' })
  price.value = (item?.price_minor || 0) / 100
  const a = attrOf(item)
  Object.assign(attr, { unit: a.unit || '', min_order_qty: a.min_order_qty ?? null, brand: a.brand || '', stock_qty: a.stock_qty ?? null, market_mode: a.market_mode || 'B2B', description: a.description || '' })
  editing.value = true
}

async function save() {
  saving.value = true
  error.value = ''
  try {
    const body: any = {
      title: form.title,
      category_schema_id: form.category_schema_id || null,
      status: form.status,
      currency: form.currency,
      price_minor: Math.round(price.value * 100),
      attributes_json: {
        unit: attr.unit || undefined,
        min_order_qty: attr.min_order_qty ?? undefined,
        brand: attr.brand || undefined,
        stock_qty: attr.stock_qty ?? undefined,
        market_mode: attr.market_mode,
        description: attr.description || undefined,
      },
    }
    if (form.id) await api.updateSupplierListing(form.id, body)
    else await api.createSupplierListing(body)
    editing.value = false
    await load()
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || '保存失败'
  } finally {
    saving.value = false
  }
}

async function archive(id: string) {
  try { await api.archiveSupplierListing(id); await load() } catch (e: any) { error.value = e?.data?.detail || e?.message || '下架失败' }
}

async function load() {
  loading.value = true
  try {
    const [a, b] = await Promise.allSettled([api.listSupplierListings(), api.listPublicCategories()])
    if (a.status === 'fulfilled') items.value = a.value.items || []
    if (b.status === 'fulfilled') categories.value = b.value.items || []
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || '加载目录失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
