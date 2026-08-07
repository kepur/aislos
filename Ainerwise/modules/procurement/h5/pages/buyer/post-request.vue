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
        <section class="relative mb-5 overflow-hidden rounded-3xl bg-gradient-to-br from-slate-950 via-indigo-950 to-primary-700 p-5 text-white shadow-xl shadow-indigo-950/20">
          <div class="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-white/10"></div>
          <div class="absolute -bottom-14 left-10 h-36 w-36 rounded-full bg-cyan-300/10"></div>
          <div class="relative">
            <div class="mb-4 flex items-center gap-2">
              <span class="inline-flex h-8 w-8 items-center justify-center rounded-2xl bg-white/15">
                <svg class="h-4 w-4 text-cyan-100" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v3m0 12v3m9-9h-3M6 12H3m14.95-5.95-2.12 2.12M8.17 15.83l-2.12 2.12m11.9 0-2.12-2.12M8.17 8.17 6.05 6.05" />
                  <circle cx="12" cy="12" r="3" />
                </svg>
              </span>
              <span class="rounded-full border border-white/15 bg-white/10 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.16em] text-cyan-100">
                AI matching
              </span>
            </div>
            <h2 class="text-2xl font-extrabold leading-tight">What are you looking for?</h2>
            <p class="mt-2 text-sm leading-6 text-indigo-100">
              Choose the closest category. AinerWise will use it to route your request to the right suppliers, products and installation partners.
            </p>
            <div class="mt-4 grid grid-cols-3 gap-2 text-center">
              <div class="rounded-2xl border border-white/10 bg-white/10 px-2 py-2">
                <p class="text-base font-black">1</p>
                <p class="text-[10px] text-indigo-100">Category</p>
              </div>
              <div class="rounded-2xl border border-white/10 bg-white/10 px-2 py-2">
                <p class="text-base font-black">AI</p>
                <p class="text-[10px] text-indigo-100">Analyze</p>
              </div>
              <div class="rounded-2xl border border-white/10 bg-white/10 px-2 py-2">
                <p class="text-base font-black">RFQ</p>
                <p class="text-[10px] text-indigo-100">Match</p>
              </div>
            </div>
          </div>
        </section>

        <div v-if="categoriesLoading" class="grid grid-cols-2 gap-3">
          <div v-for="i in 6" :key="i" class="shimmer h-36 rounded-3xl"></div>
        </div>

        <div v-else class="grid grid-cols-2 gap-3">
          <button type="button"
            v-for="cat in categories"
            :key="cat.id"
            class="group relative min-h-[152px] overflow-hidden rounded-3xl border p-4 text-left transition-all active:scale-95"
            :class="form.category_id === cat.id ? 'border-primary-400 bg-white shadow-xl shadow-primary-900/10' : 'border-slate-100 bg-white shadow-card'"
            @click="form.category_id = cat.id"
          >
            <div class="absolute inset-x-0 top-0 h-1.5" :style="{ background: categoryVisual(cat).gradient }"></div>
            <div
              class="absolute -right-8 -top-10 h-28 w-28 rounded-full opacity-10 transition-opacity group-active:opacity-20"
              :style="{ background: categoryVisual(cat).accent }"
            ></div>
            <div class="relative flex h-full flex-col">
              <div class="mb-4 flex items-start justify-between gap-2">
                <span
                  class="inline-flex h-12 w-12 items-center justify-center rounded-2xl border"
                  :style="{ background: categoryVisual(cat).softBg, borderColor: categoryVisual(cat).border }"
                >
                  <svg class="h-6 w-6" :style="{ color: categoryVisual(cat).accent }" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path
                      v-for="path in categoryIconPaths(categoryVisual(cat).icon)"
                      :key="path"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      :d="path"
                    />
                  </svg>
                </span>
                <span
                  v-if="form.category_id === cat.id"
                  class="inline-flex h-7 w-7 items-center justify-center rounded-full bg-primary-600 text-white"
                >
                  <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </span>
              </div>
              <div class="flex-1">
                <p class="text-[10px] font-black uppercase tracking-[0.14em]" :style="{ color: categoryVisual(cat).accent }">
                  {{ categoryVisual(cat).kicker }}
                </p>
                <div class="mt-1 text-sm font-extrabold leading-snug text-slate-900">{{ cat.name }}</div>
                <p class="mt-2 line-clamp-2 text-[11px] leading-5 text-slate-500">
                  {{ categoryVisual(cat).description }}
                </p>
              </div>
            </div>
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
          <label class="block text-sm font-medium text-slate-700 mb-1.5">Settlement Currency</label>
          <select v-model="form.currency" class="input-field bg-white">
            <option v-for="option in appStore.currencyOptions" :key="option.code" :value="option.code">
              {{ option.label }}
            </option>
          </select>
          <p class="text-xs text-slate-400 mt-1">{{ currencyPolicyHint }}</p>
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1.5">Max Budget (optional)</label>
          <div class="relative">
            <span class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 font-medium text-sm">{{ budgetCurrencySymbol }}</span>
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
          <label class="block text-sm font-medium text-slate-700 mb-1.5">Delivery Country *</label>
          <select v-model="form.country" class="input-field bg-white">
            <option v-for="region in regionOptions" :key="region.code" :value="region.code">
              {{ region.label }} ({{ region.code }})
            </option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1.5">City / Area *</label>
          <input v-model="form.city" type="text" :placeholder="cityPlaceholder" class="input-field" />
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
          :disabled="locationStatus === 'loading'"
        >
          <svg class="w-5 h-5 text-primary-600" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="10" /><circle cx="12" cy="12" r="3" />
            <path d="M12 2v2M12 20v2M2 12h2M20 12h2" />
          </svg>
          <span class="text-sm font-medium text-slate-700">
            {{ locationStatus === "loading" ? "Detecting location..." : "Use my current location" }}
          </span>
        </button>
        <p v-if="locationMessage" class="text-xs" :class="locationStatus === 'error' ? 'text-amber-600' : 'text-slate-500'">
          {{ locationMessage }}
        </p>
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
            <p class="font-semibold text-slate-800 mt-0.5">{{ form.city || "Not specified" }}<span v-if="form.country">, {{ form.country }}</span> · {{ form.radius_km }}km radius</p>
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
import { currencyMeta, currencyOptionLabel, localCurrencyLabel } from "~/utils/currencyPolicy";
import { inferLocationFromCoords, inferLocationFromTimezone, type LocationGuess } from "~/utils/geoPolicy";

definePageMeta({ layout: "default", middleware: ["buyer"] });
useHead({ title: "Post Request" });

const router = useRouter();
const intentStore = useIntentStore();
const authStore = useAuthStore();
const appStore = useAppStore();
const config = useRuntimeConfig();
const { formatPrice } = useApiUtils();

const step = ref(1);
const totalSteps = 5;
const loading = ref(false);
const uploadingImages = ref(false);
const error = ref("");
const budgetDisplay = ref<number | null>(null);
const expiryDays = ref(7);
const categoriesLoading = ref(true);
const locationStatus = ref<"idle" | "loading" | "success" | "error">("idle");
const locationMessage = ref("");

const form = reactive({
  category_id: "",
  title: "",
  notes: "",
  qty: 1,
  unit: "piece",
  budget_max_minor: 0,
  currency: "EUR",
  radius_km: 50,
  delivery_window_end: "",
  city: "",
  country: "RS",
  lat: null as number | null,
  lng: null as number | null,
  attachments: [] as string[],
});
const imageInputRef = ref<HTMLInputElement | null>(null);
const maxAttachments = computed(() => Math.max(0, Number(authStore.systemMode?.intent_max_attachments ?? 10)));

interface Category { id: string; name: string; slug: string }
const categories = ref<Category[]>([]);

const regionOptions = computed(() => appStore.regionOptions.map((region) => ({
  code: String(region.code || "").toUpperCase().slice(0, 2),
  label: region.label || region.code,
})));
const budgetCurrencySymbol = computed(() => currencyMeta(form.currency || appStore.currency).symbol || form.currency || appStore.currency);
const currencyPolicyHint = computed(() => {
  const policy = appStore.paymentPolicy;
  return `Budget is recorded in ${currencyOptionLabel(form.currency || appStore.currency)}; local reference for ${policy.country_name || form.country} is ${localCurrencyLabel(policy)}.`;
});
const cityPlaceholder = computed(() => {
  if (form.country === "RS") return "e.g. Belgrade";
  if (form.country === "PL") return "e.g. Warsaw";
  if (form.country === "PH") return "e.g. Cebu City";
  return "Enter city or area";
});

type CategoryVisual = {
  icon: string;
  kicker: string;
  description: string;
  accent: string;
  softBg: string;
  border: string;
  gradient: string;
};

const ICON_PATHS: Record<string, string[]> = {
  access: [
    "M8 11V7a4 4 0 118 0v4",
    "M6 11h12v9H6z",
    "M12 15v2",
  ],
  audio: [
    "M5 9h4l5-4v14l-5-4H5z",
    "M17 9.5a4 4 0 010 5",
    "M19.5 7a8 8 0 010 10",
  ],
  blinds: [
    "M4 5h16",
    "M6 8h12M6 11h12M6 14h12",
    "M18 5v14",
    "M15 19h6",
  ],
  battery: [
    "M4 8h15v8H4z",
    "M19 10h2v4h-2",
    "M7 11v2M10 11v2M13 11v2",
  ],
  bolt: [
    "M13 2L5 14h6l-1 8 8-12h-6z",
  ],
  building: [
    "M4 20h16",
    "M6 20V6l6-3 6 3v14",
    "M9 9h1M14 9h1M9 13h1M14 13h1M9 17h1M14 17h1",
  ],
  charging: [
    "M7 3v6M11 3v6",
    "M6 9h6v4a3 3 0 01-3 3v5",
    "M16 7l-3 5h4l-3 5",
  ],
  climate: [
    "M12 3v18",
    "M5 6l14 12",
    "M19 6L5 18",
    "M12 12m-2 0a2 2 0 104 0a2 2 0 10-4 0",
  ],
  construction: [
    "M3 20h18",
    "M5 20V9l7-5 7 5v11",
    "M9 20v-6h6v6",
  ],
  fire: [
    "M12 21a7 7 0 007-7c0-4-3-6-5-10 0 4-4 5-4 9",
    "M10 21a5 5 0 01-3-5c0-2 1-4 3-6 0 3 4 4 4 7",
  ],
  hvac: [
    "M12 12m-3 0a3 3 0 106 0a3 3 0 10-6 0",
    "M12 3c2 3 2 6 0 9",
    "M21 12c-3 2-6 2-9 0",
    "M12 21c-2-3-2-6 0-9",
    "M3 12c3-2 6-2 9 0",
  ],
  network: [
    "M12 5v4",
    "M6 14h12",
    "M6 14v5M18 14v5M12 14v5",
    "M10 3h4v4h-4zM4 19h4v2H4zM10 19h4v2h-4zM16 19h4v2h-4z",
  ],
  recycle: [
    "M7 7l2-4 2 4",
    "M9 3a8 8 0 016 3",
    "M17 17l-2 4-2-4",
    "M15 21a8 8 0 01-6-3",
    "M4 13l-2-4 4 1",
    "M2 9a8 8 0 013-5",
  ],
  security: [
    "M12 3l7 3v5c0 5-3 8-7 10-4-2-7-5-7-10V6z",
    "M9 12l2 2 4-5",
  ],
  solar: [
    "M12 4v2M12 18v2M4 12h2M18 12h2M6.3 6.3l1.4 1.4M16.3 16.3l1.4 1.4M17.7 6.3l-1.4 1.4M7.7 16.3l-1.4 1.4",
    "M9 12a3 3 0 106 0 3 3 0 10-6 0",
    "M4 20h16l-2-5H6z",
  ],
  box: [
    "M21 8l-9-5-9 5 9 5 9-5z",
    "M3 8v8l9 5 9-5V8",
    "M12 13v8",
  ],
};

const CATEGORY_VISUAL_PRESETS = [
  {
    match: ["2hands", "second", "used", "recycle", "refurb"],
    icon: "recycle",
    kicker: "Cost saver",
    description: "Used, recycled or refurbished options to reduce project cost.",
    accent: "#f59e0b",
  },
  {
    match: ["access", "lock", "door", "gate"],
    icon: "access",
    kicker: "Entry",
    description: "Locks, access control, identity and entry devices.",
    accent: "#2563eb",
  },
  {
    match: ["audio", "video", "multiroom", "speaker"],
    icon: "audio",
    kicker: "Experience",
    description: "Audio, display, scene and room entertainment systems.",
    accent: "#8b5cf6",
  },
  {
    match: ["blind", "shading", "curtain", "window"],
    icon: "blinds",
    kicker: "Comfort",
    description: "Shading, curtains and window automation for buildings.",
    accent: "#0ea5e9",
  },
  {
    match: ["battery", "storage", "ups"],
    icon: "battery",
    kicker: "Backup",
    description: "Storage, batteries, backup power and energy resilience.",
    accent: "#16a34a",
  },
  {
    match: ["energy management", "meter", "monitor"],
    icon: "bolt",
    kicker: "Energy",
    description: "Metering, monitoring and optimization for energy use.",
    accent: "#059669",
  },
  {
    match: ["ev", "charging", "charger"],
    icon: "charging",
    kicker: "Mobility",
    description: "EV chargers, parking power and installation support.",
    accent: "#7c3aed",
  },
  {
    match: ["fire", "safety", "alarm"],
    icon: "fire",
    kicker: "Safety",
    description: "Fire, alarm and safety equipment for compliance.",
    accent: "#dc2626",
  },
  {
    match: ["hvac", "climate", "air"],
    icon: "hvac",
    kicker: "Climate",
    description: "HVAC, ventilation and comfort control equipment.",
    accent: "#0891b2",
  },
  {
    match: ["knx", "automation", "building automation", "smart panel"],
    icon: "network",
    kicker: "Automation",
    description: "KNX, smart panels, gateways and building control.",
    accent: "#4f46e5",
  },
  {
    match: ["security", "cctv", "camera"],
    icon: "security",
    kicker: "Security",
    description: "CCTV, sensors, alarms and site protection devices.",
    accent: "#0f766e",
  },
  {
    match: ["solar", "photovoltaic"],
    icon: "solar",
    kicker: "Solar",
    description: "Solar equipment, monitoring and renewable energy systems.",
    accent: "#d97706",
  },
  {
    match: ["construction", "material", "building material"],
    icon: "construction",
    kicker: "Build",
    description: "Materials, site supplies and construction procurement.",
    accent: "#475569",
  },
  {
    match: ["network", "telecom", "router", "wifi", "it"],
    icon: "network",
    kicker: "Network",
    description: "Network devices, telecom, IT and connectivity hardware.",
    accent: "#2563eb",
  },
];

const DEFAULT_CATEGORY_VISUAL = {
  icon: "box",
  kicker: "Product",
  description: "Products, suppliers and quotes matched through AinerWise.",
  accent: "#6366f1",
};

function categoryVisual(cat: Category): CategoryVisual {
  const text = `${cat.slug || ""} ${cat.name || ""}`.toLowerCase();
  const found = CATEGORY_VISUAL_PRESETS.find((preset) => preset.match.some((keyword) => text.includes(keyword)));
  const preset = found || DEFAULT_CATEGORY_VISUAL;
  return {
    icon: preset.icon,
    kicker: preset.kicker,
    description: preset.description,
    accent: preset.accent,
    softBg: `${preset.accent}12`,
    border: `${preset.accent}22`,
    gradient: `linear-gradient(90deg, ${preset.accent}, ${preset.accent}66)`,
  };
}

function categoryIconPaths(icon: string) {
  return ICON_PATHS[icon] || ICON_PATHS.box;
}

onMounted(async () => {
  if (!authStore.systemMode) {
    await authStore.fetchSystemMode();
  }
  await appStore.fetchMarketLocalizationConfig();
  await appStore.fetchPaymentRegionConfig(appStore.regionCountry || "RS");
  ensureDefaultRegionAndCurrency();
  applyTimezoneDefault();
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

watch(regionOptions, ensureDefaultRegionAndCurrency, { immediate: true });

watch(() => appStore.regionCountry, (country) => {
  const normalized = String(country || "").toUpperCase().slice(0, 2);
  if (normalized && normalized !== form.country) form.country = normalized;
}, { immediate: true });

watch(() => form.country, async (country) => {
  const normalized = String(country || "").toUpperCase().slice(0, 2);
  if (normalized && normalized !== appStore.regionCountry) await appStore.setRegionCountry(normalized);
  ensureDefaultRegionAndCurrency();
});

watch(() => appStore.currency, (currency) => {
  if (currency && !form.currency) form.currency = currency;
});

watch(() => form.currency, (currency) => {
  if (currency && currency !== appStore.currency) appStore.setCurrency(currency);
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
  if (!import.meta.client || !navigator.geolocation) {
    locationStatus.value = "error";
    locationMessage.value = "Browser location is not available. Choose country and city manually.";
    return;
  }

  locationStatus.value = "loading";
  locationMessage.value = "";
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const latitude = pos.coords.latitude;
      const longitude = pos.coords.longitude;
      form.lat = latitude;
      form.lng = longitude;
      const guess = inferLocationFromCoords(latitude, longitude, regionOptions.value);
      if (guess) {
        applyLocationGuess(guess, true);
        locationStatus.value = "success";
        locationMessage.value = `Detected ${guess.city || guess.countryName}. You can still edit it.`;
        return;
      }
      const fallbackGuess = inferLocationFromTimezone(Intl.DateTimeFormat().resolvedOptions().timeZone, regionOptions.value);
      if (fallbackGuess) {
        applyLocationGuess(fallbackGuess, false);
        locationStatus.value = "success";
        locationMessage.value = "Country inferred from browser timezone. Please confirm the city.";
        return;
      }
      locationStatus.value = "error";
      locationMessage.value = "Coordinates are outside the currently open countries. Select a country manually.";
    },
    () => {
      locationStatus.value = "error";
      locationMessage.value = "Location permission was denied or timed out. Manual country and city still work.";
    },
    { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 }
  );
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
    currency: form.currency || appStore.currency || "EUR",
    radius_km: form.radius_km,
    city: form.city || undefined,
    country: form.country || appStore.regionCountry || "RS",
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

function ensureDefaultRegionAndCurrency() {
  if (regionOptions.value.length && !regionOptions.value.some((region) => region.code === form.country)) {
    form.country = regionOptions.value[0].code;
  }
  if (!form.country && regionOptions.value.length) form.country = regionOptions.value[0].code;
  if (!form.currency || !appStore.currencyOptions.some((option) => option.code === form.currency)) {
    form.currency = appStore.currency || appStore.defaultSettlementCurrency || "EUR";
  }
}

function applyTimezoneDefault() {
  if (!import.meta.client) return;
  const guess = inferLocationFromTimezone(Intl.DateTimeFormat().resolvedOptions().timeZone, regionOptions.value);
  if (guess) applyLocationGuess(guess, false);
}

function applyLocationGuess(guess: LocationGuess, overwriteCity: boolean) {
  if (guess.countryCode) form.country = guess.countryCode;
  if (guess.city && (overwriteCity || !form.city.trim())) form.city = guess.city;
}
</script>
