<template>
  <div class="min-h-screen bg-slate-50 flex flex-col">
    <div class="bg-white border-b border-slate-100 px-4 h-14 flex items-center gap-3 sticky top-0 z-40 pt-safe">
      <button type="button" class="text-slate-600 p-1 -ml-1" @click="$router.back()">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h1 class="font-semibold text-slate-900 flex-1">Edit Profile</h1>
    </div>

    <div class="flex-1 px-4 py-6 space-y-4">
      <!-- Avatar -->
      <div class="flex flex-col items-center gap-3 py-4">
        <div class="w-20 h-20 rounded-full bg-primary-100 flex items-center justify-center text-3xl font-extrabold text-primary-700">
          {{ authStore.displayName.charAt(0).toUpperCase() }}
        </div>
        <button type="button" class="text-xs text-primary-600 font-medium">Change Photo</button>
      </div>

      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1.5">Full Name</label>
        <input v-model="form.full_name" type="text" class="input-field" placeholder="Your full name" />
      </div>

      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1.5">Email</label>
        <input :value="authStore.user?.email" type="email" class="input-field bg-slate-50 text-slate-400" disabled />
        <p class="text-xs text-slate-400 mt-1">Email cannot be changed</p>
      </div>

      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1.5">Phone</label>
        <input v-model="form.phone" type="tel" class="input-field" placeholder="+63 9XX XXX XXXX" />
      </div>

      <div class="pt-2">
        <h2 class="text-sm font-semibold text-slate-900 mb-2">Delivery Address Book</h2>
        <div class="mb-2">
          <select v-model="selectedAddressType" class="input-field text-sm" @change="loadAddresses">
            <option value="DELIVERY_TO">Delivery To</option>
            <option value="SHIPPING_FROM">Shipping From</option>
          </select>
        </div>
        <div v-if="addressLoading" class="text-xs text-slate-500 mb-2">Loading addresses...</div>
        <div v-else-if="!addresses.length" class="text-xs text-slate-500 mb-2">No delivery address yet.</div>
        <div v-else class="space-y-2 mb-3">
          <div v-for="addr in addresses" :key="addr.id" class="border border-slate-200 rounded-xl p-3 bg-white">
            <div class="flex items-center justify-between">
              <p class="text-sm font-semibold text-slate-900">{{ addr.label }} <span v-if="addr.is_default" class="text-xs text-green-600 ml-1">Default</span></p>
              <div class="flex items-center gap-2">
                <button type="button" class="text-xs text-indigo-600 font-medium" @click="startEditAddress(addr)">Edit</button>
                <button type="button" class="text-xs text-primary-600 font-medium" @click="setDefaultAddress(addr.id)">Set default</button>
                <button type="button" class="text-xs text-red-500 font-medium" @click="deleteAddress(addr.id)">Delete</button>
              </div>
            </div>
            <p class="text-xs text-slate-600 mt-1">{{ addr.contact_name }} · {{ addr.contact_phone }}</p>
            <p class="text-xs text-slate-600">{{ addr.address_line1 }}, {{ addr.city }}</p>
          </div>
        </div>

        <div class="space-y-2 bg-white border border-slate-200 rounded-xl p-3">
          <p class="text-xs font-semibold text-slate-800">{{ editingAddressId ? 'Edit address' : 'Add address' }}</p>
          <input v-model="addressForm.label" type="text" class="input-field" placeholder="Label (Home/Office)" />
          <input v-model="addressForm.contact_name" type="text" class="input-field" placeholder="Contact name" />
          <input v-model="addressForm.contact_phone" type="tel" class="input-field" placeholder="Contact phone" />
          <input v-model="addressForm.city" type="text" class="input-field" placeholder="City" />
          <input v-model="addressForm.address_line1" type="text" class="input-field" placeholder="Address line 1" />
          <div class="flex gap-2">
            <button type="button" v-if="editingAddressId" class="flex-1 rounded-xl border border-slate-200 text-slate-600 text-sm font-medium py-2" @click="cancelEditAddress">
              Cancel
            </button>
            <button type="button" class="btn-primary text-sm !py-2 flex-1" :disabled="addressSaving" @click="saveAddress">
              <span v-if="!addressSaving">{{ editingAddressId ? 'Save Address' : 'Add Address' }}</span>
              <span v-else>{{ editingAddressId ? 'Saving…' : 'Adding…' }}</span>
            </button>
          </div>
        </div>
      </div>

      <p v-if="success" class="bg-green-50 text-green-700 text-sm px-4 py-3 rounded-xl border border-green-200">
        Profile updated successfully.
      </p>
      <p v-if="error" class="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-xl border border-red-200">{{ error }}</p>
    </div>

    <div class="sticky-bottom-action">
      <button type="button" class="btn-primary" :disabled="loading" @click="save">
        <span v-if="!loading">Save Changes</span>
        <span v-else>Saving…</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: "default", middleware: ["auth"] });
useHead({ title: "Edit Profile" });

const authStore = useAuthStore();
const config = useRuntimeConfig();
const loading = ref(false);
const addressLoading = ref(false);
const addressSaving = ref(false);
const selectedAddressType = ref<"DELIVERY_TO" | "SHIPPING_FROM">(authStore.isSupplier ? "SHIPPING_FROM" : "DELIVERY_TO");
const editingAddressId = ref<string | null>(null);
const success = ref(false);
const error = ref("");
const api = useApiFetch();
const addresses = ref<any[]>([]);

const form = reactive({
  full_name: authStore.user?.full_name || "",
  phone: authStore.user?.phone || "",
});

const addressForm = reactive({
  label: "",
  contact_name: "",
  contact_phone: "",
  country_code: "PH",
  country_name: "Philippines",
  city: "",
  address_line1: "",
  postal_code: "",
  is_default: false,
});

async function save() {
  loading.value = true;
  success.value = false;
  error.value = "";
  try {
    await $fetch(`${config.public.apiBase}/users/me`, {
      method: "PATCH",
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
      body: { full_name: form.full_name, phone: form.phone || undefined },
    });
    await authStore.fetchMe();
    success.value = true;
  } catch (err: unknown) {
    const e = err as { data?: { detail?: string } };
    error.value = e?.data?.detail || "Failed to update profile";
  } finally {
    loading.value = false;
  }
}

async function loadAddresses() {
  addressLoading.value = true;
  try {
    addresses.value = await api(`/addresses?address_type=${selectedAddressType.value}`);
  } catch {
    addresses.value = [];
  } finally {
    addressLoading.value = false;
  }
}

function resetAddressForm() {
  editingAddressId.value = null;
  addressForm.label = "";
  addressForm.contact_name = "";
  addressForm.contact_phone = "";
  addressForm.city = "";
  addressForm.address_line1 = "";
}

function startEditAddress(addr: any) {
  editingAddressId.value = addr.id;
  addressForm.label = addr.label || "";
  addressForm.contact_name = addr.contact_name || "";
  addressForm.contact_phone = addr.contact_phone || "";
  addressForm.country_code = addr.country_code || "PH";
  addressForm.country_name = addr.country_name || "Philippines";
  addressForm.city = addr.city || "";
  addressForm.address_line1 = addr.address_line1 || "";
  addressForm.postal_code = addr.postal_code || "";
  addressForm.is_default = !!addr.is_default;
}

function cancelEditAddress() {
  resetAddressForm();
}

async function saveAddress() {
  addressSaving.value = true;
  try {
    if (editingAddressId.value) {
      await api(`/addresses/${editingAddressId.value}`, {
        method: "PATCH",
        body: {
          ...addressForm,
        },
      });
    } else {
      await api("/addresses", {
        method: "POST",
        body: {
          ...addressForm,
          address_type: selectedAddressType.value,
        },
      });
    }
    resetAddressForm();
    await loadAddresses();
  } finally {
    addressSaving.value = false;
  }
}

async function setDefaultAddress(addressId: string) {
  await api(`/addresses/${addressId}/set-default`, { method: "POST" });
  await loadAddresses();
}

async function deleteAddress(addressId: string) {
  await api(`/addresses/${addressId}`, { method: "DELETE" });
  await loadAddresses();
}

onMounted(loadAddresses);
</script>
