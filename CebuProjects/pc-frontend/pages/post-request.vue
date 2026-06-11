<template>
  <div class="max-w-4xl mx-auto py-8">
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-slate-900 mb-2">Post a Request</h1>
      <p class="text-slate-600">Tell suppliers exactly what you need to get the best offers.</p>
    </div>

    <!-- Stepper -->
    <div class="mb-8">
      <div class="flex items-center justify-between relative">
        <div class="absolute left-0 top-1/2 -translate-y-1/2 w-full h-1 bg-slate-200 z-0 rounded-full"></div>
        <div class="absolute left-0 top-1/2 -translate-y-1/2 h-1 bg-indigo-600 z-0 rounded-full transition-all duration-300" :style="{ width: `${(step / 4) * 100}%` }"></div>
        
        <div v-for="(s, index) in steps" :key="index" class="relative z-10 flex flex-col items-center">
          <div :class="[
            'w-10 h-10 rounded-full flex items-center justify-center font-bold border-2 transition-colors duration-300',
            step > index ? 'bg-indigo-600 border-indigo-600 text-white' : 
            step === index ? 'bg-white border-indigo-600 text-indigo-600' : 'bg-white border-slate-300 text-slate-400'
          ]">
            <UIcon v-if="step > index" name="i-heroicons-check" class="w-6 h-6" />
            <span v-else>{{ index + 1 }}</span>
          </div>
          <span :class="['mt-2 text-xs font-medium absolute -bottom-6 w-32 text-center', step >= index ? 'text-indigo-900' : 'text-slate-400']">{{ s }}</span>
        </div>
      </div>
    </div>

    <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-8 mt-12 min-h-[400px]">
      
      <!-- Step 0: Category -->
      <div v-if="step === 0" class="space-y-6 animate-fade-in">
        <h2 class="text-2xl font-bold text-slate-900 mb-6">Select a Category</h2>
        <div class="relative">
          <span class="absolute inset-y-0 left-3 flex items-center pointer-events-none">
            <svg class="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </span>
          <input v-model="categorySearch" type="text" placeholder="Search categories..."
            class="w-full rounded-xl border border-slate-200 bg-white pl-10 pr-4 py-3.5 text-base text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
        </div>
        
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 mt-6">
          <div v-for="cat in categories" :key="cat" @click="form.category = cat; nextStep()" 
               class="border border-slate-200 rounded-xl p-4 text-center cursor-pointer hover:border-indigo-500 hover:bg-indigo-50 transition-all group"
               :class="{ 'border-indigo-500 bg-indigo-50': form.category === cat }">
            <UIcon name="i-heroicons-cube" class="w-8 h-8 text-slate-400 group-hover:text-indigo-600 mb-2 mx-auto" />
            <div class="font-medium text-slate-700 group-hover:text-indigo-700">{{ cat }}</div>
          </div>
        </div>
      </div>

      <!-- Step 1: Details -->
      <div v-if="step === 1" class="space-y-6 animate-fade-in">
        <h2 class="text-2xl font-bold text-slate-900 mb-6">Item Details</h2>
        <div class="text-sm font-medium text-indigo-600 mb-4 bg-indigo-50 p-2 rounded inline-block">
          Category: {{ form.category }} <UButton variant="link" size="xs" @click="step = 0" class="ml-2">Change</UButton>
        </div>
        
        <UFormGroup label="Request Title" required>
          <UInput v-model="form.title" placeholder="e.g. 500 bags of Portland Cement" size="lg" />
        </UFormGroup>
        
        <div class="grid grid-cols-2 gap-6">
          <UFormGroup label="Quantity" required>
            <UInput v-model="form.quantity" type="number" size="lg" />
          </UFormGroup>
          <UFormGroup label="Unit">
            <USelect v-model="form.unit" :options="['piece', 'bag', 'box', 'kg', 'ton', 'liter', 'meter', 'set', 'unit']" size="lg" />
          </UFormGroup>
        </div>

        <div class="grid grid-cols-2 gap-6">
          <div class="space-y-1">
            <label class="block text-sm font-medium text-slate-700">Budget Min</label>
            <div class="relative">
              <span class="absolute inset-y-0 left-3 flex items-center text-slate-400 text-sm pointer-events-none">$</span>
              <input v-model="form.budgetMin" type="number" min="0"
                class="w-full rounded-lg border border-slate-200 bg-white pl-7 pr-4 py-3 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
            </div>
          </div>
          <div class="space-y-1">
            <label class="block text-sm font-medium text-slate-700">Budget Max</label>
            <div class="relative">
              <span class="absolute inset-y-0 left-3 flex items-center text-slate-400 text-sm pointer-events-none">$</span>
              <input v-model="form.budgetMax" type="number" min="0"
                class="w-full rounded-lg border border-slate-200 bg-white pl-7 pr-4 py-3 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
            </div>
          </div>
        </div>
        
        <UFormGroup label="Detailed Description">
          <UTextarea v-model="form.description" :rows="4" placeholder="Describe specific requirements, brands, quality standards..." />
        </UFormGroup>
        
        <UFormGroup label="Upload Photos or Specs">
          <input
            ref="imageInputRef"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            multiple
            class="hidden"
            @change="handleImageChange"
          />
          <button
            type="button"
            class="w-full border-2 border-dashed border-slate-300 rounded-lg p-6 text-center hover:bg-slate-50 transition-colors"
            @click="imageInputRef?.click()"
          >
            <UIcon name="i-heroicons-cloud-arrow-up" class="w-10 h-10 text-slate-400 mx-auto mb-2" />
            <p class="text-sm text-slate-600">{{ uploadingImages ? 'Uploading images...' : 'Click to upload images' }}</p>
            <p class="text-xs text-slate-500 mt-1">PNG/JPG/WEBP, up to {{ maxAttachments }} files, 10MB each</p>
          </button>
          <p class="text-xs text-slate-500 mt-2">{{ form.attachments.length }}/{{ maxAttachments }} uploaded</p>
          <div v-if="form.attachments.length" class="mt-3 grid grid-cols-5 gap-2">
            <div v-for="(url, idx) in form.attachments" :key="`${url}-${idx}`" class="relative rounded-lg overflow-hidden border border-slate-200">
              <img :src="url" alt="attachment" class="w-full h-20 object-cover" />
              <button
                type="button"
                class="absolute top-1 right-1 w-5 h-5 rounded-full bg-black/70 text-white text-xs"
                @click="removeAttachment(idx)"
              >
                ×
              </button>
            </div>
          </div>
        </UFormGroup>
      </div>

      <!-- Step 2: Location -->
      <div v-if="step === 2" class="space-y-6 animate-fade-in">
        <h2 class="text-2xl font-bold text-slate-900 mb-6">Delivery Location & Radius</h2>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div class="md:col-span-1 space-y-6">
            <div class="space-y-1">
              <label class="block text-sm font-medium text-slate-700">Delivery City/Area <span class="text-red-500">*</span></label>
              <div class="relative">
                <span class="absolute inset-y-0 left-3 flex items-center pointer-events-none">
                  <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </span>
                <input v-model="form.location" type="text" placeholder="Search location..."
                  class="w-full rounded-lg border border-slate-200 bg-white pl-9 pr-4 py-3 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
              </div>
            </div>

            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <label class="block text-sm font-medium text-slate-700">Search Radius</label>
                <span class="text-sm font-bold text-indigo-700">{{ form.radius }}km</span>
              </div>
              <input v-model="form.radius" type="range" min="1" max="200" step="1"
                class="w-full h-2 rounded-full bg-slate-200 appearance-none cursor-pointer accent-indigo-600" />
              <p class="text-xs text-slate-500">Ping suppliers within this distance.</p>
            </div>
            
            <UFormGroup label="Delivery Window">
              <UInput type="date" size="lg" />
            </UFormGroup>
          </div>
          
          <div class="md:col-span-2 bg-slate-100 rounded-xl relative overflow-hidden min-h-[300px] border border-slate-200 flex items-center justify-center">
            <!-- Map Placeholder -->
            <div class="absolute inset-0 opacity-50 bg-[url('https://maps.googleapis.com/maps/api/staticmap?center=Cebu+City,Philippines&zoom=11&size=800x400&maptype=roadmap')] bg-cover bg-center mix-blend-multiply"></div>
            
            <!-- Radius overlay simulation -->
            <div class="absolute w-64 h-64 bg-indigo-500/20 rounded-full border border-indigo-500 flex items-center justify-center z-10 shadow-lg backdrop-blur-[1px]">
              <div class="bg-indigo-600 w-4 h-4 rounded-full border-2 border-white shadow"></div>
            </div>
            
            <div class="absolute bottom-4 left-4 bg-white/90 backdrop-blur px-4 py-2 rounded-lg shadow-sm text-sm font-medium z-20 flex items-center">
              <UIcon name="i-heroicons-users" class="w-4 h-4 mr-2 text-indigo-600" />
              Est. 24 suppliers found
            </div>
          </div>
        </div>
      </div>

      <!-- Step 3: Payment -->
      <div v-if="step === 3" class="space-y-6 animate-fade-in">
        <h2 class="text-2xl font-bold text-slate-900 mb-6">Payment & Escrow Authorization</h2>
        
        <div class="bg-indigo-50 border border-indigo-100 rounded-xl p-6 mb-6 flex items-start">
          <UIcon name="i-heroicons-shield-check" class="w-8 h-8 text-green-600 mr-4 flex-shrink-0" />
          <div>
            <h4 class="font-bold text-indigo-900 mb-1">Escrow Protection Active</h4>
            <p class="text-sm text-indigo-800">You will authorize funds now, but they will not be captured until you select a winning offer. Funds are only released to the supplier after you confirm delivery.</p>
          </div>
        </div>
        
        <UFormGroup label="Select Payment Method to Authorize">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-2">
            <div class="border-2 border-indigo-500 bg-indigo-50 rounded-xl p-4 flex items-center cursor-pointer">
              <div class="w-10 h-6 bg-slate-200 rounded mr-3"></div>
              <div>
                <div class="font-semibold text-slate-900">Visa ending in 4242</div>
                <div class="text-xs text-slate-500">Expires 12/26</div>
              </div>
              <UIcon name="i-heroicons-check-circle" class="w-6 h-6 text-indigo-600 ml-auto" />
            </div>
            
            <div class="border border-slate-200 rounded-xl p-4 flex items-center cursor-pointer hover:border-slate-300">
              <UIcon name="i-heroicons-building-library" class="w-8 h-8 text-slate-400 mr-3" />
              <div class="font-semibold text-slate-700">Bank Transfer</div>
            </div>
          </div>
          <UButton variant="link" color="indigo" class="px-0 mt-2" icon="i-heroicons-plus">Add new payment method</UButton>
        </UFormGroup>
      </div>

      <!-- Step 4: Review -->
      <div v-if="step === 4" class="space-y-6 animate-fade-in">
        <h2 class="text-2xl font-bold text-slate-900 mb-6">Review & Publish</h2>
        
        <div class="bg-slate-50 rounded-xl p-6 space-y-4 border border-slate-200">
          <div class="flex justify-between border-b border-slate-200 pb-4">
            <div>
              <h3 class="text-lg font-bold text-slate-900">{{ form.title }}</h3>
              <p class="text-sm text-slate-500">Category: {{ form.category }}</p>
            </div>
            <div class="text-right">
              <div class="text-lg font-bold text-indigo-600">${{ form.budgetMin || 0 }} - ${{ form.budgetMax || 0 }}</div>
              <p class="text-sm text-slate-500">Budget</p>
            </div>
          </div>
          
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 py-2">
            <div>
              <div class="text-xs text-slate-500 uppercase font-semibold tracking-wider">Quantity</div>
              <div class="font-medium text-slate-900">{{ form.quantity }} {{ form.quantity > 1 ? form.unit : form.unit.replace(/s$/, '') }}</div>
            </div>
            <div>
              <div class="text-xs text-slate-500 uppercase font-semibold tracking-wider">Location</div>
              <div class="font-medium text-slate-900">{{ form.location || 'Mandaue City, Cebu' }}</div>
            </div>
            <div>
              <div class="text-xs text-slate-500 uppercase font-semibold tracking-wider">Radius</div>
              <div class="font-medium text-slate-900">{{ form.radius }} km</div>
            </div>
            <div>
              <div class="text-xs text-slate-500 uppercase font-semibold tracking-wider">Supplier Visiblity</div>
              <div class="font-medium text-green-600 flex items-center"><UIcon name="i-heroicons-check-circle" class="w-4 h-4 mr-1"/> Verified Only</div>
            </div>
          </div>
          
          <div>
            <div class="text-xs text-slate-500 uppercase font-semibold tracking-wider mb-1">Description</div>
            <p class="text-sm text-slate-700 whitespace-pre-line">{{ form.description || 'No additional description provided.' }}</p>
          </div>
          <div v-if="form.attachments.length">
            <div class="text-xs text-slate-500 uppercase font-semibold tracking-wider mb-1">Images</div>
            <div class="grid grid-cols-6 gap-2">
              <img
                v-for="(url, idx) in form.attachments"
                :key="`review-${url}-${idx}`"
                :src="url"
                alt="request image"
                class="h-16 w-full rounded-lg object-cover border border-slate-200"
              />
            </div>
          </div>
        </div>
      </div>

    </div>

    <!-- Navigation Buttons -->
    <p v-if="submitError" class="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      {{ submitError }}
    </p>
    <div class="flex justify-between mt-8">
      <UButton v-if="step > 0" @click="prevStep" variant="outline" color="gray" size="lg" icon="i-heroicons-arrow-left">Back</UButton>
      <div v-else></div>
      
      <UButton v-if="step > 0 && step < steps.length - 1" @click="nextStep" color="indigo" size="lg" trailing-icon="i-heroicons-arrow-right">Next Step</UButton>
      <UButton v-if="step === steps.length - 1" @click="submit" color="green" size="lg" icon="i-heroicons-paper-airplane" class="px-8 font-bold">Publish Request</UButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

definePageMeta({
  layout: 'buyer'
})

const router = useRouter()
const config = useRuntimeConfig()
const authStore = useAuthStore()
const intentStore = useIntentStore()
const apiFetch = useApiFetch()
const maxAttachments = computed(() => Math.max(0, Number(authStore.systemMode?.intent_max_attachments ?? 10)))
const step = ref(0)
const steps = ['Category', 'Details', 'Location', 'Payment', 'Review']
const categorySearch = ref('')
const imageInputRef = ref<HTMLInputElement | null>(null)
const uploadingImages = ref(false)
const submitError = ref('')

const categories = ref<string[]>([
  'Construction Materials', 'Marine Parts', 'Auto Parts', 'IT / Electronics',
  'Office Supplies', 'Home & Furniture', 'Services', 'Custom Request'
])
const categoryIdMap = ref<Record<string, string>>({})

const form = ref({
  category: '',
  category_id: '',
  title: '',
  quantity: 1,
  unit: 'piece',
  budgetMin: null,
  budgetMax: null,
  description: '',
  location: 'Cebu City',
  radius: 25,
  attachments: [] as string[],
})

onMounted(async () => {
  if (!authStore.systemMode) {
    await authStore.fetchSystemMode()
  }
  try {
    const data = await $fetch<Array<{ id: string; name: string }>>(`${config.public.apiBase}/categories`)
    if (Array.isArray(data) && data.length) {
      categories.value = data.map((c) => c.name)
      categoryIdMap.value = data.reduce<Record<string, string>>((acc, c) => {
        acc[c.name] = c.id
        return acc
      }, {})
    }
  } catch {
    // keep fallback categories
  }
})

const nextStep = () => {
  if (step.value === 0 && form.value.category) {
    form.value.category_id = categoryIdMap.value[form.value.category] || ''
  }
  if (step.value < steps.length - 1) step.value++
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const prevStep = () => {
  if (step.value > 0) step.value--
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const removeAttachment = (idx: number) => {
  form.value.attachments.splice(idx, 1)
}

const handleImageChange = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files || [])
  if (!files.length) return
  const remaining = maxAttachments.value - form.value.attachments.length
  const selected = files.slice(0, Math.max(0, remaining))
  if (!selected.length) {
    submitError.value = `Maximum ${maxAttachments.value} images are allowed.`
    input.value = ''
    return
  }
  uploadingImages.value = true
  try {
    for (const file of selected) {
      const fd = new FormData()
      fd.append('file', file)
      const res = await apiFetch<{ url: string }>('/uploads', { method: 'POST', body: fd })
      if (res?.url) form.value.attachments.push(res.url)
    }
  } catch (e: any) {
    submitError.value = e?.data?.detail || 'Image upload failed.'
  } finally {
    uploadingImages.value = false
    input.value = ''
  }
}

const submit = async () => {
  submitError.value = ''
  try {
    if (!form.value.category_id) {
      form.value.category_id = categoryIdMap.value[form.value.category] || ''
    }
    if (!form.value.category_id) throw new Error('Please select a valid category.')
    const expiresAt = new Date()
    expiresAt.setDate(expiresAt.getDate() + 7)

    const payload = {
      category_id: form.value.category_id,
      title: form.value.title,
      qty: Number(form.value.quantity || 1),
      unit: form.value.unit || 'piece',
      budget_min_minor: form.value.budgetMin ? Number(form.value.budgetMin) * 100 : undefined,
      budget_max_minor: form.value.budgetMax ? Number(form.value.budgetMax) * 100 : undefined,
      currency: 'PHP',
      notes: form.value.description || undefined,
      city: form.value.location || undefined,
      country: 'PH',
      radius_km: Number(form.value.radius || 25),
      attachments: form.value.attachments,
      expires_at: expiresAt.toISOString(),
    }

    const intent = await intentStore.createIntent(payload as any)
    router.push(`/buyer/requests/${intent.id}?posted=1`)
  } catch (e: any) {
    submitError.value = e?.data?.detail || e?.message || 'Failed to publish request.'
  }
}
</script>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.3s ease-in-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
