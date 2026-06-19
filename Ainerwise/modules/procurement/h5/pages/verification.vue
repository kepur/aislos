<template>
  <div class="min-h-screen bg-slate-50 flex flex-col">
    <div class="bg-white border-b border-slate-100 px-4 h-14 flex items-center gap-3 sticky top-0 z-40 pt-safe">
      <button type="button" class="text-slate-600 p-1 -ml-1" @click="$router.back()">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h1 class="font-semibold text-slate-900 flex-1">Verification Status</h1>
    </div>

    <div class="flex-1 overflow-y-auto pb-10">
      <!-- Current Level -->
      <div class="mx-4 mt-4 card">
        <div class="flex items-center gap-4 mb-4">
          <div class="w-14 h-14 rounded-full flex items-center justify-center text-3xl"
            :class="levelConfig[currentLevel].bg">
            {{ levelConfig[currentLevel].icon }}
          </div>
          <div>
            <p class="text-xs text-slate-400 uppercase tracking-wide font-medium">Current Level</p>
            <h2 class="font-bold text-slate-900 text-lg">{{ levelConfig[currentLevel].label }}</h2>
            <p class="text-xs text-slate-500 mt-0.5">{{ levelConfig[currentLevel].desc }}</p>
          </div>
        </div>
      </div>

      <!-- Levels Progress -->
      <div class="mx-4 mt-4 space-y-3">
        <p class="text-xs font-semibold text-slate-500 uppercase tracking-wide">Verification Levels</p>

        <div v-for="(level, key) in levelConfig" :key="key"
          class="card flex gap-4 items-start"
          :class="currentLevel === key ? 'border-2 border-primary-400' : ''">
          <div class="w-10 h-10 rounded-xl flex items-center justify-center text-xl flex-shrink-0" :class="level.bg">
            {{ level.icon }}
          </div>
          <div class="flex-1">
            <div class="flex items-center justify-between">
              <p class="font-semibold text-slate-800">{{ level.label }}</p>
              <span v-if="currentLevel === key"
                class="text-xs px-2 py-0.5 bg-primary-100 text-primary-700 rounded-full font-medium">Current</span>
              <span v-else-if="isUnlocked(key)"
                class="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded-full font-medium">✓ Done</span>
            </div>
            <p class="text-xs text-slate-500 mt-0.5">{{ level.desc }}</p>
            <ul class="mt-2 space-y-1">
              <li v-for="req in level.requirements" :key="req" class="text-xs text-slate-500 flex items-center gap-1.5">
                <span :class="isUnlocked(key) ? 'text-green-500' : 'text-slate-300'">✓</span>
                {{ req }}
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Upload CTA -->
      <div v-if="currentLevel === 'NONE'" class="mx-4 mt-4">
        <div class="bg-white border border-slate-100 rounded-2xl p-4 space-y-4">
          <div>
            <p class="text-sm font-semibold text-slate-900 mb-1">Supplier KYB Submission</p>
            <p class="text-xs text-slate-500">Upload company documents after login. Guest users cannot submit KYB.</p>
          </div>

          <div v-if="!company" class="space-y-3">
            <input v-model="companyForm.name" class="input-field" placeholder="Legal company name" />
            <input v-model="companyForm.tax_id" class="input-field" placeholder="TIN / registration number" />
            <input v-model="companyForm.country" class="input-field" placeholder="Country" />
            <input v-model="companyForm.city" class="input-field" placeholder="City" />
            <textarea v-model="companyForm.address" class="input-field min-h-20" placeholder="Business address" />
          </div>

          <div class="space-y-3">
            <label class="block border border-dashed border-slate-300 rounded-xl p-4 text-center bg-slate-50">
              <p class="text-xs font-semibold text-slate-700">Business Registration</p>
              <p class="text-xs text-slate-500 mt-1">{{ businessFile?.name || docLabel('BUSINESS_REGISTRATION') }}</p>
              <input class="hidden" type="file" accept="application/pdf,image/*" @change="setFile('business', $event)" />
            </label>
            <label class="block border border-dashed border-slate-300 rounded-xl p-4 text-center bg-slate-50">
              <p class="text-xs font-semibold text-slate-700">Owner / Authorized ID</p>
              <p class="text-xs text-slate-500 mt-1">{{ ownerFile?.name || docLabel('OWNER_ID') }}</p>
              <input class="hidden" type="file" accept="application/pdf,image/*" @change="setFile('owner', $event)" />
            </label>
          </div>

          <div v-if="notice" class="text-xs rounded-xl px-3 py-2" :class="noticeType === 'error' ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'">
            {{ notice }}
          </div>

          <button type="button" class="btn-primary text-sm py-2.5 w-full disabled:opacity-60" :disabled="submitting" @click="submitVerification">
            {{ submitting ? 'Submitting...' : 'Submit KYB' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: "default", middleware: ["auth"] });
useHead({ title: "Verification Status" });

const authStore = useAuthStore();
const config = useRuntimeConfig();

type Company = {
  id: string;
  name: string;
  country: string;
  city?: string;
  address?: string;
  tax_id?: string;
  verification_level: keyof typeof levelConfig;
  status: string;
};
type CompanyDocument = {
  id: string;
  doc_type: string;
  original_filename?: string;
  status: string;
};

const company = ref<Company | null>(null);
const documents = ref<CompanyDocument[]>([]);
const businessFile = ref<File | null>(null);
const ownerFile = ref<File | null>(null);
const submitting = ref(false);
const notice = ref("");
const noticeType = ref<"success" | "error">("success");
const companyForm = reactive({
  name: "",
  tax_id: "",
  country: "Philippines",
  city: "Cebu City",
  address: "",
});

const levelConfig = {
  NONE: {
    icon: "👤",
    label: "Unverified",
    bg: "bg-slate-100",
    desc: "Basic account access only",
    requirements: ["Register an account"],
  },
  BASIC: {
    icon: "✅",
    label: "Basic Verified",
    bg: "bg-blue-50",
    desc: "Can submit offers and receive orders",
    requirements: ["Valid government ID", "Active email address"],
  },
  BUSINESS: {
    icon: "🏢",
    label: "Business Verified",
    bg: "bg-green-50",
    desc: "Full platform access, higher trust badge",
    requirements: ["Business registration", "Tax ID (TIN)", "Bank account details", "Proof of address"],
  },
} as const;

type Level = keyof typeof levelConfig;

const currentLevel = computed<Level>(() => {
  const level = company.value?.verification_level;
  return level && level in levelConfig ? level : "NONE";
});

function isUnlocked(key: Level): boolean {
  const order: Level[] = ["NONE", "BASIC", "BUSINESS"];
  return order.indexOf(currentLevel.value as Level) > order.indexOf(key);
}

function authHeaders() {
  return { Authorization: `Bearer ${authStore.accessToken}` };
}

function setFile(kind: "business" | "owner", event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0] ?? null;
  if (kind === "business") businessFile.value = file;
  else ownerFile.value = file;
}

function docLabel(type: string) {
  const doc = documents.value.find((item) => item.doc_type === type);
  if (!doc) return "Tap to upload PDF or image";
  return `${doc.original_filename || "Uploaded"} · ${doc.status}`;
}

async function loadVerification() {
  try {
    company.value = await $fetch<Company>(`${config.public.apiBase}/companies/me`, {
      headers: authHeaders(),
    });
    documents.value = await $fetch<CompanyDocument[]>(`${config.public.apiBase}/companies/me/documents`, {
      headers: authHeaders(),
    });
  } catch {
    company.value = null;
    documents.value = [];
  }
}

async function ensureCompany() {
  if (company.value) return;
  company.value = await $fetch<Company>(`${config.public.apiBase}/companies`, {
    method: "POST",
    body: companyForm,
    headers: authHeaders(),
  });
}

async function uploadDocument(file: File, docType: "BUSINESS_REGISTRATION" | "OWNER_ID") {
  const body = new FormData();
  body.append("file", file);
  const uploaded = await $fetch<{ url: string }>(`${config.public.apiBase}/uploads`, {
    method: "POST",
    body,
    headers: authHeaders(),
  });
  await $fetch(`${config.public.apiBase}/companies/me/documents`, {
    method: "POST",
    body: {
      doc_type: docType,
      file_url: uploaded.url,
      original_filename: file.name,
    },
    headers: authHeaders(),
  });
}

async function submitVerification() {
  notice.value = "";
  submitting.value = true;
  try {
    await ensureCompany();
    if (businessFile.value) await uploadDocument(businessFile.value, "BUSINESS_REGISTRATION");
    if (ownerFile.value) await uploadDocument(ownerFile.value, "OWNER_ID");
    await $fetch(`${config.public.apiBase}/companies/me/verification/submit`, {
      method: "POST",
      headers: authHeaders(),
    });
    noticeType.value = "success";
    notice.value = "KYB submitted. Admin review is pending.";
    await loadVerification();
  } catch (err: any) {
    noticeType.value = "error";
    notice.value = err?.data?.detail || err?.message || "Submission failed.";
  } finally {
    submitting.value = false;
  }
}

onMounted(loadVerification);
</script>
