<template>
  <section class="space-y-5">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-xs font-bold uppercase tracking-[0.2em] text-indigo-300">{{ $t('supNav.catalog') }}</p>
        <h1 class="mt-1 text-2xl font-bold text-white">{{ $t('supCat.title') }}</h1>
        <p class="mt-1 text-sm text-slate-400">{{ $t('supCat.subtitle') }}</p>
      </div>
      <button class="btn-primary" @click="start()">{{ $t('supCat.newItem') }}</button>
    </div>

    <div class="grid grid-cols-3 gap-4">
      <div class="pc-card"><p class="text-sm text-slate-400">{{ $t('supCat.all') }}</p><p class="mt-1 text-2xl font-bold text-white">{{ items.length }}</p></div>
      <div class="pc-card"><p class="text-sm text-slate-400">{{ $t('supCat.listed') }}</p><p class="mt-1 text-2xl font-bold text-emerald-300">{{ countBy('active') }}</p></div>
      <div class="pc-card"><p class="text-sm text-slate-400">{{ $t('supCat.draft') }}</p><p class="mt-1 text-2xl font-bold text-amber-300">{{ countBy('draft') }}</p></div>
    </div>

    <!-- Editor -->
    <form v-if="editing" class="pc-card grid gap-4 md:grid-cols-2" @submit.prevent="save">
      <h2 class="text-lg font-medium text-white md:col-span-2">{{ form.id ? $t('supCat.editItem') : $t('supCat.newItemTitle') }}</h2>
      <div><label class="mb-1 block text-sm text-slate-400">{{ $t('supCat.titleLabel') }}</label><input v-model.trim="form.title" required class="input-field" /></div>
      <div><label class="mb-1 block text-sm text-slate-400">{{ $t('supCat.category') }}</label>
        <select v-model="form.category_schema_id" class="input-field"><option value="">{{ $t('supCat.uncategorized') }}</option><option v-for="c in categories" :key="c.id" :value="c.id">{{ categoryLabel(c) }}</option></select>
      </div>
      <div><label class="mb-1 block text-sm text-slate-400">{{ $t('supCat.unitPrice') }}</label><input v-model.number="price" type="number" min="0" step="0.01" class="input-field" /></div>
      <div><label class="mb-1 block text-sm text-slate-400">{{ $t('reqForm.currency') }}</label>
        <select v-model="form.currency" class="input-field"><option v-for="c in currencies" :key="c" :value="c">{{ c }}</option></select>
      </div>
      <div><label class="mb-1 block text-sm text-slate-400">{{ $t('supCat.unit') }}</label><input v-model.trim="attr.unit" class="input-field" :placeholder="$t('supCat.unitPh')" /></div>
      <div><label class="mb-1 block text-sm text-slate-400">{{ $t('supCat.moq') }}</label><input v-model.number="attr.min_order_qty" type="number" min="1" class="input-field" /></div>
      <div><label class="mb-1 block text-sm text-slate-400">{{ $t('supCat.brand') }}</label><input v-model.trim="attr.brand" class="input-field" /></div>
      <div><label class="mb-1 block text-sm text-slate-400">{{ $t('supCat.stock') }}</label><input v-model.number="attr.stock_qty" type="number" min="0" class="input-field" /></div>
      <div><label class="mb-1 block text-sm text-slate-400">{{ $t('common.status') }}</label>
        <select v-model="form.status" class="input-field"><option value="active">{{ $t('supCat.stActive') }}</option><option value="inactive">{{ $t('supCat.stInactive') }}</option><option value="draft">{{ $t('supCat.stDraft') }}</option></select>
      </div>
      <div><label class="mb-1 block text-sm text-slate-400">{{ $t('supCat.marketMode') }}</label>
        <select v-model="attr.market_mode" class="input-field"><option value="B2B">B2B</option><option value="B2C">B2C</option></select>
      </div>
      <div class="md:col-span-2"><label class="mb-1 block text-sm text-slate-400">{{ $t('supCat.description') }}</label><textarea v-model.trim="attr.description" rows="3" class="input-field" /></div>
      <div class="flex gap-3 md:col-span-2">
        <button class="btn-primary" :disabled="saving">{{ saving ? $t('supTeam.saving') : (form.id ? $t('common.save') : $t('common.create')) }}</button>
        <button type="button" class="btn-secondary" @click="editing = false">{{ $t('common.cancel') }}</button>
      </div>
    </form>

    <!-- Toolbar -->
    <div class="pc-card flex flex-wrap items-center gap-3">
      <input v-model.trim="keyword" class="input-field max-w-xs" :placeholder="$t('supCat.searchPh')" />
      <div class="flex gap-1">
        <button v-for="f in statusFilters" :key="f.value" :class="['rounded-lg px-3 py-1.5 text-sm transition', statusFilter === f.value ? 'bg-indigo-500/15 text-indigo-200' : 'text-slate-400 hover:bg-white/5']" @click="statusFilter = f.value">{{ $t(f.label) }}</button>
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
          <span v-if="attrOf(item).brand">{{ $t('supCat.chipBrand') }} {{ attrOf(item).brand }}</span>
          <span v-if="attrOf(item).unit">{{ $t('supCat.chipUnit') }} {{ attrOf(item).unit }}</span>
          <span v-if="attrOf(item).min_order_qty">MOQ {{ attrOf(item).min_order_qty }}</span>
          <span v-if="attrOf(item).stock_qty != null">{{ $t('supCat.chipStock') }} {{ attrOf(item).stock_qty }}</span>
        </div>
        <div class="mt-3 flex gap-3 border-t border-white/5 pt-3">
          <button class="text-sm text-indigo-300 hover:text-indigo-200" @click="start(item)">{{ $t('common.edit') }}</button>
          <button class="text-sm text-red-300 hover:text-red-200" @click="archive(item.id)">{{ $t('supCat.delist') }}</button>
        </div>
      </article>
      <p v-if="!loading && !filtered.length" class="pc-card text-sm text-slate-400 md:col-span-2 xl:col-span-3">{{ $t('supCat.empty') }}</p>
    </div>
  </section>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'procurement', middleware: ['auth'] })

const { t } = useI18n()
const { categoryLabel } = useCategoryLabel()
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
  { value: '', label: 'supCat.all' }, { value: 'active', label: 'supCat.stActive' }, { value: 'inactive', label: 'supCat.stInactive' }, { value: 'draft', label: 'supCat.stDraft' },
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
function statusLabel(s?: string) {
  const map: Record<string, string> = { active: 'stActive', inactive: 'stInactive', draft: 'stDraft' }
  const key = map[String(s || '')]
  return key ? t(`supCat.${key}`) : (s || '—')
}
function statusTone(s?: string) {
  const v = String(s || '')
  if (v === 'active') return 'bg-emerald-500/15 text-emerald-300'
  if (v === 'draft') return 'bg-amber-500/15 text-amber-300'
  return 'bg-white/10 text-slate-400'
}
function money(v?: number | null, c = 'EUR') { return v == null ? t('mkt.inquire') : new Intl.NumberFormat(undefined, { style: 'currency', currency: c, maximumFractionDigits: 0 }).format(v / 100) }

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
    error.value = e?.data?.detail || e?.message || t('supCat.saveFailed')
  } finally {
    saving.value = false
  }
}

async function archive(id: string) {
  try { await api.archiveSupplierListing(id); await load() } catch (e: any) { error.value = e?.data?.detail || e?.message || t('supCat.delistFailed') }
}

async function load() {
  loading.value = true
  try {
    const [a, b] = await Promise.allSettled([api.listSupplierListings(), api.listPublicCategories()])
    if (a.status === 'fulfilled') items.value = a.value.items || []
    if (b.status === 'fulfilled') categories.value = b.value.items || []
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || t('supCat.loadFailed')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
