<template>
  <div class="min-h-screen bg-slate-50 flex flex-col">
    <!-- Top Bar -->
    <div class="bg-white border-b border-slate-100 px-4 h-14 flex items-center gap-3 pt-safe sticky top-0 z-40">
      <button type="button" class="text-slate-600 p-1 -ml-1" @click="handleBack">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <div class="flex-1">
        <p class="font-semibold text-slate-900 text-sm">Post Request</p>
        <p class="text-xs text-slate-500">Step {{ step }} of {{ totalSteps }}</p>
      </div>
      <button type="button" class="text-slate-400 text-xs" @click="saveDraft">Save draft</button>
    </div>

    <!-- Progress Bar -->
    <div class="h-1 bg-slate-100">
      <div class="h-full bg-primary-600 transition-all duration-300" :style="{ width: `${(step / totalSteps) * 100}%` }"></div>
    </div>

    <!-- Steps -->
    <div class="flex-1 overflow-y-auto">
      <!-- Step 1: Category -->
      <div v-if="step === 1" class="px-4 py-6">
        <h2 class="text-lg font-bold text-slate-900 mb-1">What are you looking for?</h2>
        <p class="text-sm text-slate-500 mb-5">Select a category to help suppliers match your request.</p>

        <div v-if="categoriesLoading" class="grid grid-cols-2 gap-3">
          <div v-for="i in 6" :key="i" class="shimmer h-24 rounded-2xl"></div>
        </div>

        <div v-else class="grid grid-cols-2 gap-3">
          <button type="button"
            v-for="cat in categories"
            :key="cat.id"
            class="bg-white rounded-2xl p-4 text-left border-2 transition-all active:scale-95"
            :class="form.category_id === cat.id ? 'border-primary-500 bg-primary-50' : 'border-transparent shadow-card'"
            @click="form.category_id = cat.id"
          >
            <div class="text-3xl mb-2">{{ categoryEmoji(cat.slug) }}</div>
            <div class="font-semibold text-slate-800 text-sm">{{ cat.name }}</div>
          </button>
        </div>
      </div>

      <!-- Step 2: Request Details -->
      <div v-if="step === 2" class="px-4 py-6 space-y-4">
        <h2 class="text-lg font-bold text-slate-900 mb-1">Request Details</h2>
        <p class="text-sm text-slate-500 mb-5">Describe what you need clearly so suppliers can give accurate offers.</p>

        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1.5">Request Title *</label>
          <input v-model="form.title" type="text" placeholder="e.g. 500 bags Holcim Portland Cement" class="input-field" maxlength="200" />
          <p class="text-xs text-slate-400 mt-1">{{ form.title.length }}/200</p>
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1.5">Description / Notes</label>
          <textarea
            v-model="form.notes"
            placeholder="Add specifications, brand preferences, quality requirements…"
            class="input-field resize-none"
            rows="4"
          ></textarea>
        </div>

        <div>
          <div class="flex items-center justify-between mb-1.5">
            <label class="block text-sm font-medium text-slate-700">Request Images</label>
            <span class="text-xs text-slate-400">{{ form.attachments.length }}/{{ maxAttachments }}</span>
          </div>
          <input
            ref="imageInputRef"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            multiple
            class="hidden"
            @change="handleImageChange"
          />
          <button type="button" class="w-full rounded-xl border-2 border-dashed border-slate-300 bg-white px-4 py-4 text-sm text-slate-600" @click="openImagePicker">
            {{ uploadingImages ? "Uploading images..." : `Upload up to ${maxAttachments} images` }}
          </button>
          <p class="text-xs text-slate-400 mt-1">PNG/JPG/WEBP only. Max 10MB each.</p>
          <div v-if="form.attachments.length" class="mt-3 grid grid-cols-4 gap-2">
            <div v-for="(url, idx) in form.attachments" :key="`${url}-${idx}`" class="relative rounded-lg overflow-hidden border border-slate-200">
              <img :src="url" alt="attachment" class="w-full h-20 object-cover" />
              <button
                type="button"
                class="absolute top-1 right-1 w-5 h-5 rounded-full bg-black/70 text-white text-xs leading-none"
                @click="removeAttachment(idx)"
              >
                ×
              </button>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1.5">Quantity *</label>
            <input v-model.number="form.qty" type="number" min="1" placeholder="500" class="input-field" />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1.5">Unit *</label>
            <select v-model="form.unit" class="input-field bg-white">
              <option value="piece">piece</option>
              <option value="bag">bag</option>
              <option value="box">box</option>
              <option value="kg">kg</option>
              <option value="ton">ton</option>
              <option value="liter">liter</option>
              <option value="meter">meter</option>
              <option value="set">set</option>
              <option value="unit">unit</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Step 3: Budget -->
      <div v-if="step === 3" class="px-4 py-6 space-y-4">
        <h2 class="text-lg font-bold text-slate-900 mb-1">Budget & Timeline</h2>
        <p class="text-sm text-slate-500 mb-5">Setting a budget helps suppliers tailor their offers.</p>

        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1.5">Max Budget (optional)</label>
          <div class="relative">
            <span class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 font-medium text-sm">₱</span>
            <input
              v-model.number="budgetDisplay"
              type="number"
              placeholder="0"
              class="input-field pl-9"
              min="0"
            />
          </div>
          <p class="text-xs text-slate-400 mt-1">Leave blank to receive all offers</p>
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1.5">Delivery Deadline (optional)</label>
          <input v-model="form.delivery_window_end" type="date" class="input-field" :min="minDate" />
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1.5">Request Expires In</label>
          <div class="flex gap-2">
            <button type="button"
              v-for="days in [3, 7, 14, 30]"
              :key="days"
              class="flex-1 py-2 rounded-xl border-2 text-sm font-medium transition-all"
              :class="expiryDays === days ? 'border-primary-500 bg-primary-50 text-primary-700' : 'border-slate-200 bg-white text-slate-600'"
              @click="expiryDays = days"
            >
              {{ days }}d
            </button>
          </div>
        </div>
      </div>

      <!-- Step 4: Location -->
      <div v-if="step === 4" class="px-4 py-6 space-y-4">
        <h2 class="text-lg font-bold text-slate-900 mb-1">Delivery Location</h2>
        <p class="text-sm text-slate-500 mb-5">Tell suppliers where you need the items delivered.</p>

        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1.5">City / Area *</label>
          <input v-model="form.city" type="text" placeholder="e.g. Mandaue City, Cebu" class="input-field" />
        </div>

        <div class="bg-primary-50 border border-primary-100 rounded-xl p-4">
          <div class="flex items-center gap-3 mb-3">
            <svg class="w-5 h-5 text-primary-600" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <span class="text-sm font-semibold text-primary-800">Supplier Search Radius</span>
          </div>
          <div class="mb-2">
            <div class="flex justify-between text-xs text-slate-500 mb-1">
              <span>5 km</span>
              <span class="font-semibold text-primary-700">{{ form.radius_km }} km</span>
              <span>200 km</span>
            </div>
            <input
              v-model.number="form.radius_km"
              type="range"
              min="5"
              max="200"
              step="5"
              class="w-full accent-primary-600"
            />
          </div>
          <p class="text-xs text-primary-600">Suppliers within {{ form.radius_km }}km will be notified</p>
        </div>

        <button type="button"
          class="flex items-center gap-3 w-full bg-white border border-slate-200 rounded-xl p-4 text-left active:bg-slate-50"
          @click="useCurrentLocation"
        >
          <svg class="w-5 h-5 text-primary-600" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="10" /><circle cx="12" cy="12" r="3" />
            <path d="M12 2v2M12 20v2M2 12h2M20 12h2" />
          </svg>
          <span class="text-sm font-medium text-slate-700">Use my current location</span>
        </button>
      </div>

      <!-- Step 5: Review -->
      <div v-if="step === 5" class="px-4 py-6">
        <h2 class="text-lg font-bold text-slate-900 mb-1">Review Your Request</h2>
        <p class="text-sm text-slate-500 mb-5">Check everything before posting to suppliers.</p>

        <div class="card space-y-4 mb-4">
          <div>
            <p class="text-xs text-slate-500 font-medium uppercase tracking-wide">Category</p>
            <p class="font-semibold text-slate-800 mt-0.5">{{ selectedCategoryName }}</p>
          </div>
          <div class="divider -mx-4"></div>
          <div>
            <p class="text-xs text-slate-500 font-medium uppercase tracking-wide">Request</p>
            <p class="font-semibold text-slate-800 mt-0.5">{{ form.title }}</p>
            <p v-if="form.notes" class="text-sm text-slate-500 mt-1">{{ form.notes }}</p>
          </div>
          <div class="divider -mx-4"></div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-xs text-slate-500 font-medium uppercase tracking-wide">Quantity</p>
              <p class="font-semibold text-slate-800 mt-0.5">{{ form.qty }} {{ form.unit }}</p>
            </div>
            <div>
              <p class="text-xs text-slate-500 font-medium uppercase tracking-wide">Budget</p>
              <p class="font-semibold text-slate-800 mt-0.5">{{ form.budget_max_minor ? formatPrice(form.budget_max_minor) : "Open" }}</p>
            </div>
          </div>
          <div class="divider -mx-4"></div>
          <div>
            <p class="text-xs text-slate-500 font-medium uppercase tracking-wide">Location</p>
            <p class="font-semibold text-slate-800 mt-0.5">{{ form.city || "Not specified" }} · {{ form.radius_km }}km radius</p>
          </div>
          <div v-if="form.attachments.length" class="divider -mx-4"></div>
          <div v-if="form.attachments.length">
            <p class="text-xs text-slate-500 font-medium uppercase tracking-wide">Images</p>
            <div class="mt-2 grid grid-cols-4 gap-2">
              <img
                v-for="(url, idx) in form.attachments"
                :key="`review-${url}-${idx}`"
                :src="url"
                alt="request image"
                class="w-full h-16 rounded-lg object-cover border border-slate-200"
              />
            </div>
          </div>
        </div>

        <div class="bg-primary-50 rounded-xl p-4 border border-primary-100 mb-4">
          <p class="text-xs text-primary-700 font-semibold mb-1">What happens next?</p>
          <p class="text-xs text-primary-600 leading-relaxed">
            Verified suppliers in your area will be notified immediately. You can start comparing offers as soon as they arrive.
          </p>
        </div>

        <p v-if="error" class="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-xl border border-red-200 mb-4">
          {{ error }}
        </p>
      </div>
    </div>

    <!-- Bottom Action -->
    <div class="sticky-bottom-action">
      <div class="flex gap-3">
        <button type="button" v-if="step > 1" class="btn-secondary flex-none w-14 py-3.5" @click="step--">
          <svg class="w-5 h-5 mx-auto" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <button type="button"
          v-if="step < totalSteps"
          class="btn-primary flex-1"
          :disabled="!canProceed"
          @click="step++"
        >
          Continue
        </button>
        <button type="button"
          v-else
          class="btn-primary flex-1"
          :disabled="loading || !canProceed"
          @click="submitRequest"
        >
          <span v-if="!loading">Post Request 🚀</span>
          <span v-else class="flex items-center justify-center gap-2">
            <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Posting…
          </span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: "default", middleware: ["buyer"] });
useHead({ title: "Post Request" });

const router = useRouter();
const intentStore = useIntentStore();
const authStore = useAuthStore();
const { formatPrice } = useApiUtils();

const step = ref(1);
const totalSteps = 5;
const loading = ref(false);
const uploadingImages = ref(false);
const error = ref("");
const budgetDisplay = ref<number | null>(null);
const expiryDays = ref(7);
const categoriesLoading = ref(true);

const form = reactive({
  category_id: "",
  title: "",
  notes: "",
  qty: 1,
  unit: "piece",
  budget_max_minor: 0,
  currency: "PHP",
  radius_km: 50,
  delivery_window_end: "",
  city: "",
  country: "PH",
  lat: null as number | null,
  lng: null as number | null,
  attachments: [] as string[],
});
const imageInputRef = ref<HTMLInputElement | null>(null);
const maxAttachments = computed(() => Math.max(0, Number(authStore.systemMode?.intent_max_attachments ?? 10)));

interface Category { id: string; name: string; slug: string }
const categories = ref<Category[]>([]);

// Full 25-category map — synced with PC categories.vue
const EMOJI_MAP: Record<string, string> = {
  'construction-materials': '🏗️',
  'it-office-equipment': '💻',
  'automotive-parts': '🚗',
  'electronics-components': '⚡',
  'machinery-industrial': '⚙️',
  'raw-materials-chemicals': '🧪',
  'textiles-garments': '👕',
  'food-beverages': '🍜',
  'agriculture-farming': '🌾',
  'medical-healthcare': '🏥',
  'packaging-printing': '🗂️',
  'furniture-home': '🪑',
  'lighting-electrical': '💡',
  'plumbing-hvac': '🔧',
  'safety-security': '🛡️',
  'sports-outdoor': '⛺',
  'beauty-personal-care': '💄',
  'toys-baby-products': '🧸',
  'pet-supplies': '🐾',
  'jewelry-accessories': '💍',
  'energy-solar': '☀️',
  'marine-shipping': '⚓',
  'mining-minerals': '⛏️',
  'telecom-networking': '📡',
  'tools-hardware': '🔨',
}

function categoryEmoji(slug: string): string {
  // Exact match first
  if (EMOJI_MAP[slug]) return EMOJI_MAP[slug]
  // Partial match fallback
  for (const key of Object.keys(EMOJI_MAP)) {
    if (slug?.includes(key)) return EMOJI_MAP[key]
  }
  return '📦'
}

onMounted(async () => {
  if (!authStore.systemMode) {
    await authStore.fetchSystemMode();
  }
  const config = useRuntimeConfig();
  try {
    categories.value = await $fetch<Category[]>(`${config.public.apiBase}/categories`);
  } catch {
    categories.value = [];
  } finally {
    categoriesLoading.value = false;
  }
});

const selectedCategoryName = computed(
  () => categories.value.find((c) => c.id === form.category_id)?.name || "—"
);

const minDate = computed(() => new Date().toISOString().slice(0, 10));

watch(budgetDisplay, (val) => {
  form.budget_max_minor = val ? val * 100 : 0;
});

const canProceed = computed(() => {
  if (step.value === 1) return !!form.category_id;
  if (step.value === 2) return !!form.title && form.qty > 0 && !!form.unit;
  if (step.value === 3) return true;
  if (step.value === 4) return true;
  if (step.value === 5) return !!form.title && !!form.category_id;
  return true;
});

function handleBack() {
  if (step.value > 1) { step.value--; return; }
  router.back();
}

function saveDraft() {
  // TODO: persist to localStorage
}

function openImagePicker() {
  if (uploadingImages.value) return;
  imageInputRef.value?.click();
}

function removeAttachment(index: number) {
  form.attachments.splice(index, 1);
}

async function handleImageChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const files = Array.from(input.files || []);
  if (!files.length) return;
  const remaining = maxAttachments.value - form.attachments.length;
  if (remaining <= 0) {
    error.value = `Maximum ${maxAttachments.value} images are allowed.`;
    input.value = "";
    return;
  }

  const selected = files.slice(0, remaining);
  if (files.length > remaining) {
    error.value = `Only ${remaining} more image(s) can be uploaded.`;
  }

  const api = useApiFetch();
  uploadingImages.value = true;
  try {
    for (const file of selected) {
      const fd = new FormData();
      fd.append("file", file);
      const res = await api<{ url: string }>("/uploads", { method: "POST", body: fd });
      if (res?.url) form.attachments.push(res.url);
    }
  } catch (err: unknown) {
    const e = err as { data?: { detail?: unknown } };
    const detail = e?.data?.detail;
    error.value = typeof detail === "string" ? detail : "Image upload failed.";
  } finally {
    uploadingImages.value = false;
    input.value = "";
  }
}

async function useCurrentLocation() {
  if (!navigator.geolocation) return;
  navigator.geolocation.getCurrentPosition((pos) => {
    form.lat = pos.coords.latitude;
    form.lng = pos.coords.longitude;
    if (!form.city) form.city = `${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)}`;
  });
}

async function submitRequest() {
  if (loading.value) return;
  loading.value = true;
  error.value = "";

  const expiresAt = new Date();
  expiresAt.setDate(expiresAt.getDate() + expiryDays.value);

  const payload: Record<string, unknown> = {
    category_id: form.category_id,
    title: form.title,
    notes: form.notes || undefined,
    qty: form.qty,
    unit: form.unit,
    currency: form.currency,
    radius_km: form.radius_km,
    city: form.city || undefined,
    country: form.country || undefined,
    lat: form.lat || undefined,
    lng: form.lng || undefined,
    attachments: form.attachments,
    expires_at: expiresAt.toISOString(),
  };

  if (form.budget_max_minor) payload.budget_max_minor = form.budget_max_minor;
  if (form.delivery_window_end) payload.delivery_window_end = form.delivery_window_end;

  try {
    const intent = await intentStore.createIntent(payload);
    router.push(`/buyer/requests/${intent.id}?posted=1`);
  } catch (err: unknown) {
    const e = err as { data?: { detail?: unknown } };
    const detail = e?.data?.detail;
    error.value = typeof detail === "string" ? detail : JSON.stringify(detail) || "Failed to post request. Please try again.";
  } finally {
    loading.value = false;
  }
}
</script>
