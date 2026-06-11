<template>
  <div>
    <!-- Top Bar -->
    <div class="bg-white border-b border-slate-100 px-4 h-14 flex items-center justify-between sticky top-0 z-40 pt-safe">
      <h1 class="font-bold text-slate-900 text-lg">Catalog</h1>
      <div class="flex items-center gap-2">
        <button @click="showSearch = !showSearch" class="w-8 h-8 flex items-center justify-center text-slate-500">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </button>
        <button type="button" class="bg-primary-600 text-white text-sm font-semibold px-3 py-1.5 rounded-lg" @click="openCreate">
          + Add
        </button>
      </div>
    </div>

    <!-- Search bar (collapsible) -->
    <Transition name="slide-down">
      <div v-if="showSearch" class="bg-white border-b border-slate-100 px-4 py-2.5 flex gap-2">
        <input v-model="keyword" @keyup.enter="loadItems" type="text" placeholder="Search products..."
          class="flex-1 border border-slate-200 rounded-xl px-3 py-2 text-sm outline-none focus:border-indigo-400" />
        <select v-model="modeFilter" @change="loadItems"
          class="border border-slate-200 rounded-xl px-2 py-2 text-xs bg-white text-slate-600 outline-none">
          <option value="">All Modes</option>
          <option value="B2B">B2B</option>
          <option value="B2C">B2C</option>
          <option value="BOTH">Both</option>
        </select>
        <select v-model="statusFilter" @change="loadItems"
          class="border border-slate-200 rounded-xl px-2 py-2 text-xs bg-white text-slate-600 outline-none">
          <option value="">All Status</option>
          <option value="ACTIVE">Active</option>
          <option value="INACTIVE">Inactive</option>
          <option value="INACTIVE">Inactive</option>
        </select>
      </div>
    </Transition>

    <div v-if="companyMissing" class="mx-4 mb-2 rounded-xl border border-amber-200 bg-amber-50 px-3 py-3">
      <p class="text-sm font-semibold text-amber-900">Complete your supplier profile</p>
      <p class="mt-1 text-xs text-amber-800">Catalog items are listed under your company. Finish KYB or continue with your draft profile.</p>
      <NuxtLink to="/profile/company" class="mt-2 inline-block text-xs font-bold text-amber-900 underline">Set up company →</NuxtLink>
    </div>
    <div v-else-if="company" class="mx-4 mb-2 rounded-xl border border-blue-100 bg-blue-50 px-3 py-2.5">
      <p class="text-xs font-semibold text-blue-900">Listing as: {{ company.name }}</p>
      <p class="text-[10px] text-blue-700 mt-0.5">
        {{ company.status === 'ACTIVE' ? 'Verified supplier company' : 'Company profile pending verification' }}
      </p>
    </div>

    <!-- Stats row -->
    <div class="grid grid-cols-4 gap-2 px-4 py-3">
      <div v-for="stat in stats" :key="stat.label" class="bg-white rounded-xl p-2.5 text-center border border-slate-100">
        <p class="text-base font-extrabold" :class="stat.color">{{ stat.value }}</p>
        <p class="text-[10px] text-slate-400 mt-0.5 leading-tight">{{ stat.label }}</p>
      </div>
    </div>

    <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
      <div class="px-4 pb-24">
        <!-- Loading -->
        <div v-if="loading" class="space-y-3">
          <div v-for="n in 4" :key="n" class="bg-white rounded-2xl p-4 border border-slate-100">
            <div class="flex gap-3">
              <div class="shimmer w-16 h-16 rounded-xl flex-shrink-0"></div>
              <div class="flex-1">
                <div class="shimmer h-4 w-3/4 rounded mb-2"></div>
                <div class="shimmer h-3 w-1/2 rounded mb-1"></div>
                <div class="shimmer h-3 w-1/3 rounded"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty -->
        <div v-else-if="displayItems.length === 0" class="empty-state">
          <svg class="w-16 h-16 text-slate-200 mb-3" fill="none" stroke="currentColor" stroke-width="1" viewBox="0 0 24 24">
            <rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" />
            <rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" />
          </svg>
          <p class="text-slate-500 font-medium">No catalog items yet</p>
          <p class="text-slate-400 text-xs mt-1">Add products to get matched with buyer requests</p>
          <button type="button" class="mt-4 btn-primary py-2.5 px-6 w-auto text-sm" @click="openCreate">Add First Item</button>
        </div>

        <!-- Items list -->
        <div v-else class="space-y-3">
          <div v-for="item in displayItems" :key="item.id" class="bg-white rounded-2xl border border-slate-100 overflow-hidden">
            <div class="flex gap-3 p-4">
              <!-- Thumbnail -->
              <div class="w-16 h-16 rounded-xl overflow-hidden bg-slate-100 flex-shrink-0">
                <img v-if="item.images?.[0]" :src="item.images[0]" :alt="item.title" class="w-full h-full object-cover" />
                <div v-else class="w-full h-full flex items-center justify-center text-2xl">📦</div>
              </div>

              <div class="flex-1 min-w-0">
                <div class="flex items-start justify-between gap-1 mb-1">
                  <h3 class="font-semibold text-slate-800 text-sm flex-1 pr-1 line-clamp-2">{{ item.title }}</h3>
                  <span :class="['text-[10px] px-1.5 py-0.5 rounded-full font-bold flex-shrink-0', statusClass(item.status)]">
                    {{ item.status }}
                  </span>
                </div>

                <!-- Mode badges -->
                <div class="flex gap-1 mb-1.5">
                  <span v-if="item.market_mode === 'B2B' || item.market_mode === 'BOTH'" class="text-[9px] bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded-full font-bold">B2B</span>
                  <span v-if="item.market_mode === 'B2C' || item.market_mode === 'BOTH'" class="text-[9px] bg-green-50 text-green-600 px-1.5 py-0.5 rounded-full font-bold">B2C</span>
                </div>

                <div class="flex items-center justify-between">
                  <div>
                    <span class="font-bold text-slate-900 text-base">{{ formatPrice(item.price_minor, item.currency) }}</span>
                    <span class="text-xs text-slate-500 ml-1">/ {{ item.unit }}</span>
                  </div>
                  <span :class="['text-xs font-medium', item.stock_qty > 50 ? 'text-green-600' : item.stock_qty > 0 ? 'text-amber-500' : 'text-red-500']">
                    {{ item.stock_qty > 0 ? `${item.stock_qty} in stock` : 'Out of stock' }}
                  </span>
                </div>

                <!-- Stats row -->
                <div class="flex gap-3 mt-1.5 text-[10px] text-slate-400">
                  <span>👁 {{ (item.view_count ?? 0).toLocaleString() }} views</span>
                  <span>📦 {{ item.order_count ?? 0 }} orders</span>
                  <span v-if="item.origin_country">🌍 {{ item.origin_country }}</span>
                </div>
              </div>
            </div>

            <!-- Action row -->
            <div class="flex border-t border-slate-100">
              <button @click="editItem(item)" class="flex-1 py-2.5 text-xs font-medium text-indigo-600 hover:bg-indigo-50 transition-colors">✏️ Edit</button>
              <div class="w-px bg-slate-100"></div>
              <button @click="toggleStatus(item)" class="flex-1 py-2.5 text-xs font-medium transition-colors"
                :class="item.status === 'ACTIVE' ? 'text-amber-600 hover:bg-amber-50' : 'text-green-600 hover:bg-green-50'">
                {{ item.status === 'ACTIVE' ? '⏸ Deactivate' : '▶ Activate' }}
              </button>
              <div class="w-px bg-slate-100"></div>
              <button @click="deleteItem(item)" class="flex-1 py-2.5 text-xs font-medium text-red-500 hover:bg-red-50 transition-colors">🗑 Delete</button>
            </div>
          </div>

          <button v-if="hasNext" @click="loadMore" :disabled="loadingMore"
            class="w-full py-3 text-sm text-primary-600 font-medium disabled:opacity-50">
            {{ loadingMore ? 'Loading...' : 'Load more' }}
          </button>
        </div>
      </div>
    </van-pull-refresh>

    <!-- ── Create / Edit Bottom Sheet ── -->
    <van-action-sheet v-model:show="showSheet" :title="editing ? 'Edit Item' : 'Add Catalog Item'">
      <div class="px-4 pt-2 pb-10 space-y-4 max-h-[80vh] overflow-y-auto">
        <div>
          <label class="block text-sm font-semibold text-slate-700 mb-1">Title *</label>
          <input v-model="form.title" type="text" placeholder="Product name" class="input-field" />
        </div>
        <div>
          <label class="block text-sm font-semibold text-slate-700 mb-1">Category *</label>
          <select v-model="form.category_id" class="input-field bg-white">
            <option value="">Select category...</option>
            <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-semibold text-slate-700 mb-1">Product Images</label>
          <div class="grid grid-cols-5 gap-2">
            <div v-for="(image, idx) in form.images" :key="`${image}-${idx}`" class="relative aspect-square overflow-hidden rounded-xl bg-slate-100">
              <img :src="image" :alt="`Product image ${idx + 1}`" class="h-full w-full object-cover" />
              <button type="button" class="absolute right-1 top-1 flex h-6 w-6 items-center justify-center rounded-full bg-white/90 text-slate-600 shadow" @click="removeImage(idx)">×</button>
            </div>
            <button
              v-if="form.images.length < maxImages"
              type="button"
              class="aspect-square rounded-xl border border-dashed border-slate-300 bg-slate-50 text-[11px] font-semibold text-slate-500"
              :disabled="uploadingImages"
              @click="imageInput?.click()"
            >
              {{ uploadingImages ? '...' : '+ Image' }}
            </button>
          </div>
          <input ref="imageInput" type="file" accept="image/jpeg,image/png,image/webp" multiple class="hidden" @change="handleImageFiles" />
          <div class="mt-2 flex gap-2">
            <input v-model="imageUrlInput" type="url" placeholder="Or paste image URL" class="input-field flex-1" />
            <button type="button" class="rounded-xl border border-slate-200 px-3 text-xs font-semibold text-slate-600" :disabled="form.images.length >= maxImages" @click="addImageUrl">Add</button>
          </div>
          <p class="mt-1 text-xs text-slate-400">{{ form.images.length }}/{{ maxImages }} images. First image is the cover.</p>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1">Price (₱) *</label>
            <input v-model.number="priceInput" type="number" min="0" step="0.01" placeholder="0.00" class="input-field" />
          </div>
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1">Unit</label>
            <select v-model="form.unit" class="input-field bg-white">
              <option v-for="u in ['pc','bag','box','kg','unit','set','roll','liter']" :key="u" :value="u">{{ u }}</option>
            </select>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1">Stock Qty</label>
            <input v-model.number="form.stock_qty" type="number" min="0" class="input-field" />
          </div>
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1">Min Order</label>
            <input v-model.number="form.min_order_qty" type="number" min="1" class="input-field" />
          </div>
        </div>
        <div>
          <label class="block text-sm font-semibold text-slate-700 mb-1.5">Market Mode</label>
          <div class="flex gap-2">
            <button v-for="m in ['B2B','B2C','BOTH']" :key="m" @click="form.market_mode = m" type="button"
              :class="['flex-1 py-2 rounded-xl text-sm font-bold border-2 transition-colors',
                form.market_mode === m ? 'border-indigo-500 bg-indigo-50 text-indigo-700' : 'border-slate-200 text-slate-500']">
              {{ m }}
            </button>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1">Origin</label>
            <input v-model="form.origin_country" type="text" placeholder="PH, CN, US…" class="input-field" />
          </div>
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1">Weight kg</label>
            <input v-model.number="form.weight_kg" type="number" min="0" step="0.1" class="input-field" />
          </div>
        </div>
        <div>
          <label class="block text-sm font-semibold text-slate-700 mb-1">Tags (comma separated)</label>
          <input v-model="tagsInput" type="text" placeholder="e.g. cement, bulk, construction" class="input-field" />
        </div>
        <div>
          <label class="block text-sm font-semibold text-slate-700 mb-1">Description</label>
          <textarea v-model="form.description" class="input-field resize-none" rows="3" placeholder="Product details..."></textarea>
        </div>
        <button type="button" class="btn-primary"
          :disabled="!form.title || !form.category_id || priceInput <= 0 || saveLoading"
          @click="saveItem">
          <span v-if="!saveLoading">{{ editing ? 'Save Changes' : 'Add to Catalog' }}</span>
          <span v-else>Saving…</span>
        </button>
      </div>
    </van-action-sheet>
  </div>
</template>

<script setup lang="ts">
import { showToast, showConfirmDialog } from "vant";

definePageMeta({ layout: "supplier", middleware: ["supplier"] });
useHead({ title: "Catalog" });

const config = useRuntimeConfig();
const authStore = useAuthStore();
const { formatPrice } = useApiUtils();

const items = ref<any[]>([]);
const categories = ref<any[]>([]);
const company = ref<{ name: string; status: string } | null>(null);
const companyMissing = ref(false);
const loading = ref(true);
const refreshing = ref(false);
const loadingMore = ref(false);
const saveLoading = ref(false);
const hasNext = ref(false);
const page = ref(1);
const showSheet = ref(false);
const showSearch = ref(false);
const editing = ref<any>(null);
const keyword = ref('');
const modeFilter = ref('');
const statusFilter = ref('');
const priceInput = ref(0);
const tagsInput = ref('');
const imageInput = ref<HTMLInputElement | null>(null);
const imageUrlInput = ref('');
const uploadingImages = ref(false);
const maxImages = 10;

const form = reactive({
  title: '', description: '', unit: 'pc', stock_qty: 0, min_order_qty: 1,
  currency: 'PHP', price_minor: 0, category_id: '', tags: [] as string[],
  images: [] as string[],
  market_mode: 'B2B', origin_country: '', weight_kg: null as number | null, status: 'ACTIVE',
});

watch(priceInput, (v) => { form.price_minor = Math.round(v * 100); });

const MOCK_ITEMS = [
  { id: 'mi1', title: 'Portland Cement Type I – 40kg', description: 'OPC certified cement for construction.', price_minor: 4900000, currency: 'PHP', unit: 'bag', stock_qty: 500, market_mode: 'B2B', status: 'ACTIVE', images: ['https://picsum.photos/seed/201/200/200'], tags: ['cement','construction'], view_count: 1240, order_count: 87, origin_country: 'PH', min_order_qty: 20, weight_kg: 40 },
  { id: 'mi2', title: 'Steel Rebar 10mm × 6m', description: 'Grade 60 deformed steel bar.', price_minor: 28000000, currency: 'PHP', unit: 'bundle', stock_qty: 120, market_mode: 'B2B', status: 'ACTIVE', images: ['https://picsum.photos/seed/202/200/200'], tags: ['steel','rebar'], view_count: 890, order_count: 42, origin_country: 'CN', min_order_qty: 5, weight_kg: 120 },
  { id: 'mi3', title: 'Nitrile Gloves 100pcs/box', description: 'Powder-free disposable gloves.', price_minor: 35000000, currency: 'PHP', unit: 'box', stock_qty: 2000, market_mode: 'BOTH', status: 'ACTIVE', images: ['https://picsum.photos/seed/203/200/200'], tags: ['gloves','ppe'], view_count: 3200, order_count: 215, origin_country: 'CN', min_order_qty: 10, weight_kg: 0.8 },
  { id: 'mi4', title: 'Office Chair Ergonomic Mesh', description: 'Lumbar support, adjustable height.', price_minor: 50000000, currency: 'PHP', unit: 'pc', stock_qty: 45, market_mode: 'B2C', status: 'ACTIVE', images: ['https://picsum.photos/seed/204/200/200'], tags: ['chair','office'], view_count: 670, order_count: 23, origin_country: 'CN', min_order_qty: 1, weight_kg: 12 },
  { id: 'mi5', title: 'Marine Plywood 3/4 × 4 × 8', description: '18mm marine-grade, moisture resistant.', price_minor: 165000, currency: 'PHP', unit: 'sheet', stock_qty: 0, market_mode: 'B2B', status: 'INACTIVE', images: [], tags: ['plywood','marine'], view_count: 320, order_count: 18, origin_country: 'PH', min_order_qty: 10, weight_kg: 22 },
]

const displayItems = computed(() => {
  if (items.value.length > 0) return items.value
  let list = [...MOCK_ITEMS]
  if (keyword.value) list = list.filter(i => i.title.toLowerCase().includes(keyword.value.toLowerCase()))
  if (modeFilter.value) list = list.filter(i => i.market_mode === modeFilter.value || (modeFilter.value !== 'BOTH' && i.market_mode === 'BOTH'))
  if (statusFilter.value) list = list.filter(i => i.status === statusFilter.value)
  return list
})

const stats = computed(() => [
  { label: 'Total', value: displayItems.value.length, color: 'text-slate-900' },
  { label: 'Active', value: displayItems.value.filter(i => i.status === 'ACTIVE').length, color: 'text-green-600' },
  { label: 'Low Stock', value: displayItems.value.filter(i => (i.stock_qty ?? 0) > 0 && (i.stock_qty ?? 0) < 10).length, color: 'text-amber-500' },
  { label: 'B2C', value: displayItems.value.filter(i => i.market_mode === 'B2C' || i.market_mode === 'BOTH').length, color: 'text-indigo-600' },
])

async function loadItems() {
  loading.value = true; page.value = 1;
  try {
    const params: any = { page: 1, page_size: 20 };
    if (keyword.value.trim()) params.keyword = keyword.value.trim();
    if (statusFilter.value) params.status = statusFilter.value;
    if (modeFilter.value) params.market_mode = modeFilter.value;
    const data = await $fetch<any>(`${config.public.apiBase}/supplier/catalog/items`, {
      params, headers: { Authorization: `Bearer ${authStore.accessToken}` },
    });
    items.value = data.items ?? data ?? [];
    hasNext.value = data.has_next ?? false;
  } catch { items.value = []; } finally { loading.value = false; refreshing.value = false; }
}

async function loadMore() {
  loadingMore.value = true; page.value++;
  try {
    const data = await $fetch<any>(`${config.public.apiBase}/supplier/catalog/items`, {
      params: { page: page.value, page_size: 20 },
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    });
    items.value.push(...(data.items ?? []));
    hasNext.value = data.has_next ?? false;
  } catch {} finally { loadingMore.value = false; }
}

async function loadCategories() {
  try {
    const data = await $fetch<any>(`${config.public.apiBase}/categories`);
    categories.value = Array.isArray(data) ? data : (data.items ?? []);
  } catch {}
}

async function loadCompany() {
  try {
    company.value = await $fetch<any>(`${config.public.apiBase}/companies/me`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    });
    companyMissing.value = false;
  } catch (e: any) {
    if (e?.statusCode === 404 || e?.response?.status === 404) {
      company.value = null;
      companyMissing.value = true;
    }
  }
}

function openCreate() {
  editing.value = null; priceInput.value = 0; tagsInput.value = ''; imageUrlInput.value = '';
  Object.assign(form, { title: '', description: '', unit: 'pc', stock_qty: 0, min_order_qty: 1, currency: 'PHP', price_minor: 0, category_id: '', tags: [], images: [], market_mode: 'B2B', origin_country: '', weight_kg: null, status: 'ACTIVE' });
  showSheet.value = true;
}

function editItem(item: any) {
  editing.value = item; priceInput.value = item.price_minor / 100; tagsInput.value = (item.tags ?? []).join(', '); imageUrlInput.value = '';
  Object.assign(form, { title: item.title, description: item.description ?? '', unit: item.unit, stock_qty: item.stock_qty, min_order_qty: item.min_order_qty ?? 1, currency: item.currency ?? 'PHP', price_minor: item.price_minor, category_id: item.category_id ?? '', tags: item.tags ?? [], images: [...(item.images ?? [])].slice(0, maxImages), market_mode: item.market_mode ?? 'B2B', origin_country: item.origin_country ?? '', weight_kg: item.weight_kg ?? null, status: item.status });
  showSheet.value = true;
}

async function handleImageFiles(event: Event) {
  const input = event.target as HTMLInputElement;
  const selected = Array.from(input.files || []).filter((file) => file.type.startsWith('image/'));
  input.value = '';
  if (!selected.length) return;
  const remaining = maxImages - form.images.length;
  if (remaining <= 0) {
    showToast({ type: 'fail', message: `Maximum ${maxImages} images allowed` });
    return;
  }
  if (selected.length > remaining) showToast({ message: `Only ${remaining} more image(s) can be uploaded` });
  uploadingImages.value = true;
  try {
    const headers = { Authorization: `Bearer ${authStore.accessToken}` };
    for (const file of selected.slice(0, remaining)) {
      const body = new FormData();
      body.append('file', file);
      const res = await $fetch<{ url: string }>(`${config.public.apiBase}/uploads`, { method: 'POST', body, headers });
      form.images.push(res.url);
    }
  } catch (e: any) {
    showToast({ type: 'fail', message: e?.data?.detail ?? 'Image upload failed' });
  } finally {
    uploadingImages.value = false;
  }
}

function addImageUrl() {
  const url = imageUrlInput.value.trim();
  if (!url) return;
  if (form.images.length >= maxImages) {
    showToast({ type: 'fail', message: `Maximum ${maxImages} images allowed` });
    return;
  }
  form.images.push(url);
  imageUrlInput.value = '';
}

function removeImage(index: number) {
  form.images.splice(index, 1);
}

async function saveItem() {
  form.tags = tagsInput.value.split(',').map(t => t.trim()).filter(Boolean);
  form.images = form.images.filter(Boolean).slice(0, maxImages);
  form.price_minor = Math.round(priceInput.value * 100);
  if (!form.weight_kg) form.weight_kg = null;
  if (!form.category_id) {
    showToast({ type: 'fail', message: 'Please select a category' });
    return;
  }
  saveLoading.value = true;
  try {
    const headers = { Authorization: `Bearer ${authStore.accessToken}` };
    if (editing.value && !editing.value.id.startsWith('mi')) {
      await $fetch(`${config.public.apiBase}/supplier/catalog/items/${editing.value.id}`, { method: 'PATCH', body: { ...form }, headers });
      showToast({ type: 'success', message: 'Item updated!' });
    } else if (!editing.value) {
      await $fetch(`${config.public.apiBase}/supplier/catalog/items`, { method: 'POST', body: { ...form }, headers });
      showToast({ type: 'success', message: 'Item added!' });
    } else {
      showToast({ type: 'success', message: 'Updated (demo mode)' });
    }
    showSheet.value = false;
    await loadItems();
    await loadCompany();
  } catch (e: any) {
    const detail = e?.data?.detail;
    const msg = typeof detail === 'string' ? detail : 'Save failed';
    if (msg.toLowerCase().includes('company')) {
      companyMissing.value = true;
      showToast({ type: 'fail', message: 'Complete your company profile first' });
    } else {
      showToast({ type: 'fail', message: msg });
    }
  } finally { saveLoading.value = false; }
}

async function toggleStatus(item: any) {
  const newStatus = item.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE';
  try {
    if (!item.id.startsWith('mi')) {
      await $fetch(`${config.public.apiBase}/supplier/catalog/items/${item.id}`, {
        method: 'PATCH', body: { status: newStatus }, headers: { Authorization: `Bearer ${authStore.accessToken}` },
      });
    }
    item.status = newStatus;
    showToast({ type: 'success', message: `Item ${newStatus.toLowerCase()}` });
  } catch (e: any) { showToast({ type: 'fail', message: e?.data?.detail ?? 'Update failed' }); }
}

async function deleteItem(item: any) {
  try {
    await showConfirmDialog({ title: 'Delete item?', message: `"${item.title}" will be removed.` });
    if (!item.id.startsWith('mi')) {
      await $fetch(`${config.public.apiBase}/supplier/catalog/items/${item.id}`, {
        method: 'DELETE', headers: { Authorization: `Bearer ${authStore.accessToken}` },
      });
    }
    items.value = items.value.filter(i => i.id !== item.id);
    showToast({ type: 'success', message: 'Item deleted' });
  } catch {}
}

function statusClass(s: string) {
  const m: Record<string, string> = { ACTIVE: 'bg-green-100 text-green-700', INACTIVE: 'bg-amber-100 text-amber-700', OUT_OF_STOCK: 'bg-red-100 text-red-600', REJECTED: 'bg-red-100 text-red-600' };
  return m[s] ?? 'bg-slate-100 text-slate-500';
}

function onRefresh() { loadItems(); }
onMounted(() => { loadCompany(); loadCategories(); loadItems(); });
</script>

<style scoped>
.slide-down-enter-active, .slide-down-leave-active { transition: all 0.2s ease; }
.slide-down-enter-from, .slide-down-leave-to { opacity: 0; transform: translateY(-8px); }
</style>
