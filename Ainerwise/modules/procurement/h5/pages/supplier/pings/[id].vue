<template>
  <div class="min-h-screen bg-slate-50 flex flex-col">
    <div class="bg-white border-b border-slate-100 px-4 h-14 flex items-center gap-3 sticky top-0 z-40 pt-safe">
      <button type="button" class="text-slate-600 p-1 -ml-1" @click="$router.back()">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h1 class="font-semibold text-slate-900 flex-1">{{ $t("pages.request_detail") }}</h1>
    </div>

    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <div class="w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin"></div>
    </div>

    <div v-else-if="intent" class="flex-1 overflow-y-auto pb-32">
      <!-- Status badge -->
      <div class="px-4 pt-4">
        <span class="badge-primary text-xs px-3 py-1 rounded-full">{{ intent.status }}</span>
      </div>

      <!-- Title & Meta -->
      <div class="mx-4 mt-3 card">
        <h2 class="font-bold text-slate-900 text-lg mb-1">{{ intent.title }}</h2>
        <p v-if="intent.notes" class="text-sm text-slate-500 mb-3">{{ intent.notes }}</p>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <p class="text-xs text-slate-400 font-medium uppercase tracking-wide">Quantity</p>
            <p class="font-semibold text-slate-800 mt-0.5">{{ intent.qty }} {{ intent.unit }}</p>
          </div>
          <div v-if="intent.budget_max_minor">
            <p class="text-xs text-slate-400 font-medium uppercase tracking-wide">Budget</p>
            <p class="font-semibold text-slate-800 mt-0.5">{{ formatPrice(intent.budget_max_minor, intent.currency) }}</p>
          </div>
          <div v-if="intent.city">
            <p class="text-xs text-slate-400 font-medium uppercase tracking-wide">Location</p>
            <p class="font-semibold text-slate-800 mt-0.5">{{ intent.city }} · {{ intent.radius_km }}km</p>
          </div>
          <div v-if="intent.delivery_window_end">
            <p class="text-xs text-slate-400 font-medium uppercase tracking-wide">Deadline</p>
            <p class="font-semibold text-slate-800 mt-0.5">{{ formatDate(intent.delivery_window_end) }}</p>
          </div>
        </div>
      </div>

      <!-- Attributes -->
      <div v-if="intent.attrs_jsonb && Object.keys(intent.attrs_jsonb).length" class="mx-4 mt-3 card">
        <p class="text-xs text-slate-400 font-medium uppercase tracking-wide mb-3">Specifications</p>
        <div class="space-y-2">
          <div v-for="(val, key) in intent.attrs_jsonb" :key="key" class="flex justify-between">
            <span class="text-sm text-slate-500 capitalize">{{ key }}</span>
            <span class="text-sm font-medium text-slate-800">{{ val }}</span>
          </div>
        </div>
      </div>

      <!-- Posted -->
      <div class="mx-4 mt-3 mb-4">
        <p class="text-xs text-slate-400 text-center">Posted {{ formatRelativeTime(intent.created_at) }}</p>
      </div>
    </div>

    <div v-else class="flex-1 flex items-center justify-center text-slate-400 text-sm">
      Request not found.
    </div>

    <!-- CTA -->
    <div v-if="intent && intent.status === 'ACTIVE'" class="sticky-bottom-action">
      <NuxtLink :to="`/supplier/make-offer?intent_id=${intent.id}`">
        <button type="button" class="btn-primary">{{ $t("supplier.make_offer") }}</button>
      </NuxtLink>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: "default", middleware: ["supplier"] });

const route = useRoute();
const intentStore = useIntentStore();
const { formatPrice, formatDate, formatRelativeTime } = useApiUtils();

const id = route.params.id as string;
const loading = ref(true);
const intent = computed(() => intentStore.currentIntent);

onMounted(async () => {
  await intentStore.fetchIntent(id);
  loading.value = false;
});

useHead({ title: computed(() => intent.value?.title || "Request Detail") });
</script>
