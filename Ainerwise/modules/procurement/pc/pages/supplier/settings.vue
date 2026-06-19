<template>
  <div class="mx-auto max-w-5xl space-y-6">
    <div class="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Supplier Settings</h1>
        <p class="mt-1 text-sm text-slate-500">Manage operational contact info, ship-from addresses, and reminder policies without pushing deals off-platform.</p>
      </div>
      <div class="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-xs text-slate-500 shadow-sm">
        Quotes, order commitments, and dispute evidence stay inside the platform thread.
      </div>
    </div>

    <div class="rounded-3xl border border-emerald-200 bg-gradient-to-r from-emerald-50 via-white to-cyan-50 px-5 py-4 shadow-sm">
      <p class="text-sm font-semibold text-slate-900">External alerts should accelerate response, not replace the deal record.</p>
      <p class="mt-1 text-sm text-slate-600">Use email or Telegram as reminder channels while keeping pricing, delivery promises, and evidence in-site for arbitration safety.</p>
    </div>

    <div class="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
      <div class="space-y-6">
        <UCard id="profile">
          <template #header>
            <div>
              <h2 class="text-lg font-semibold text-slate-900">Operational Contact</h2>
              <p class="mt-1 text-sm text-slate-500">This controls how buyers and internal reminders identify your supplier account.</p>
            </div>
          </template>

          <form class="space-y-4" @submit.prevent="saveProfile">
            <div class="grid gap-4 sm:grid-cols-2">
              <UFormGroup label="Contact Name">
                <UInput v-model="profileForm.full_name" placeholder="Business contact" />
              </UFormGroup>
              <UFormGroup label="Mobile Number">
                <UInput v-model="profileForm.phone" placeholder="09xx xxx xxxx" />
              </UFormGroup>
            </div>

            <UFormGroup label="Email">
              <UInput :model-value="profileForm.email" disabled />
            </UFormGroup>

            <UFormGroup label="Telegram Chat ID">
              <UInput v-model="profileForm.telegram_chat_id" placeholder="Optional: for reminder pings only" />
            </UFormGroup>

            <div class="flex justify-end border-t border-slate-100 pt-4">
              <UButton type="submit" color="emerald" :loading="profileSaving">Save Supplier Contact</UButton>
            </div>
          </form>
        </UCard>

        <UCard id="addresses">
          <template #header>
            <div>
              <h2 class="text-lg font-semibold text-slate-900">Ship-From Address Book</h2>
              <p class="mt-1 text-sm text-slate-500">Set the warehouse or branch origins buyers should expect during order fulfillment.</p>
            </div>
          </template>

          <div class="space-y-4">
            <div v-if="addressLoading" class="text-sm text-slate-500">Loading addresses...</div>
            <div v-else-if="!addresses.length" class="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-5 text-sm text-slate-500">
              No ship-from address yet. Add your main warehouse or branch dispatch point.
            </div>
            <div v-else class="space-y-3">
              <div v-for="addr in addresses" :key="addr.id" class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p class="text-sm font-semibold text-slate-900">
                      {{ addr.label }}
                      <span v-if="addr.is_default" class="ml-2 rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-semibold text-emerald-700">Default</span>
                    </p>
                    <p class="mt-1 text-sm text-slate-600">{{ addr.contact_name }}<span v-if="addr.contact_phone"> · {{ addr.contact_phone }}</span></p>
                    <p class="mt-1 text-sm text-slate-500">{{ addr.address_line1 }}, {{ addr.city }}, {{ addr.country_name }}</p>
                  </div>
                  <div class="flex flex-wrap gap-2">
                    <UButton size="xs" color="emerald" variant="soft" @click="startEditAddress(addr)">Edit</UButton>
                    <UButton size="xs" color="gray" variant="soft" @click="setDefaultAddress(addr.id)">Set Default</UButton>
                    <UButton size="xs" color="red" variant="soft" @click="deleteAddress(addr.id)">Delete</UButton>
                  </div>
                </div>
              </div>
            </div>

            <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p class="text-sm font-semibold text-slate-900">{{ editingAddressId ? 'Edit Ship-From Address' : 'Add Ship-From Address' }}</p>
              <div class="mt-4 grid gap-3 sm:grid-cols-2">
                <UInput v-model="addressForm.label" placeholder="Label: Main warehouse" />
                <UInput v-model="addressForm.contact_name" placeholder="Dispatch contact" />
                <UInput v-model="addressForm.contact_phone" placeholder="Dispatch phone" />
                <UInput v-model="addressForm.city" placeholder="City" />
                <UInput v-model="addressForm.address_line1" placeholder="Address line 1" class="sm:col-span-2" />
                <UInput v-model="addressForm.postal_code" placeholder="Postal code" />
              </div>
              <div class="mt-4 flex justify-end gap-2">
                <UButton v-if="editingAddressId" color="gray" variant="soft" @click="cancelEditAddress">Cancel</UButton>
                <UButton color="emerald" :loading="addressSaving" @click="saveAddress">
                  {{ editingAddressId ? 'Save Address' : 'Add Address' }}
                </UButton>
              </div>
            </div>
          </div>
        </UCard>
      </div>

      <UCard id="notifications" class="h-fit">
        <template #header>
          <div>
            <h2 class="text-lg font-semibold text-slate-900">Notification Settings</h2>
            <p class="mt-1 text-sm text-slate-500">Choose which reminders can pull your team back into active negotiations and order handling.</p>
          </div>
        </template>

        <form class="space-y-5" @submit.prevent="saveNotifications">
          <div class="space-y-3">
            <p class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Reminder Channels</p>
            <label class="flex items-start gap-3 rounded-2xl border border-slate-200 p-4 transition hover:border-emerald-200 hover:bg-emerald-50/40">
              <input v-model="notificationForm.channels.email" type="checkbox" class="mt-1 h-4 w-4 rounded border-slate-300 accent-emerald-600" />
              <div>
                <p class="text-sm font-semibold text-slate-900">Email reminders</p>
                <p class="mt-1 text-sm text-slate-500">Use email when a buyer message, award, or delivery status needs quick attention.</p>
              </div>
            </label>
            <label class="flex items-start gap-3 rounded-2xl border border-slate-200 p-4 transition hover:border-emerald-200 hover:bg-emerald-50/40">
              <input v-model="notificationForm.channels.telegram" type="checkbox" class="mt-1 h-4 w-4 rounded border-slate-300 accent-emerald-600" />
              <div>
                <p class="text-sm font-semibold text-slate-900">Telegram reminders</p>
                <p class="mt-1 text-sm text-slate-500">Only works when a Telegram chat ID is connected above.</p>
              </div>
            </label>
          </div>

          <div class="space-y-3">
            <p class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Event Triggers</p>
            <label v-for="event in supplierEventOptions" :key="event.key" class="flex items-start gap-3 rounded-2xl border border-slate-200 p-4 transition hover:border-emerald-200 hover:bg-emerald-50/40">
              <input v-model="notificationForm.events[event.key]" type="checkbox" class="mt-1 h-4 w-4 rounded border-slate-300 accent-emerald-600" />
              <div>
                <p class="text-sm font-semibold text-slate-900">{{ event.label }}</p>
                <p class="mt-1 text-sm text-slate-500">{{ event.description }}</p>
              </div>
            </label>
          </div>

          <div class="flex justify-end border-t border-slate-100 pt-4">
            <UButton type="submit" color="emerald" :loading="notificationSaving">Save Notification Settings</UButton>
          </div>
        </form>
      </UCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

definePageMeta({ layout: 'supplier' })

interface AddressItem {
  id: string
  label: string
  contact_name: string
  contact_phone: string
  country_code: string
  country_name: string
  city: string
  address_line1: string
  postal_code: string
  is_default: boolean
}

type NotificationEventKey = 'new_message' | 'intent_match' | 'offer_received' | 'offer_awarded' | 'order_update' | 'delivery_update'

interface NotificationPreferencesResponse {
  email: string
  telegram_chat_id: string | null
  telegram_connected: boolean
  channels: {
    email: boolean
    telegram: boolean
  }
  events: Record<NotificationEventKey, boolean>
}

const api = useApiFetch()
const authStore = useAuthStore()
const toast = useToast()

const supplierEventOptions: Array<{ key: NotificationEventKey; label: string; description: string }> = [
  { key: 'new_message', label: 'New buyer messages', description: 'Bring me back when a buyer adds new negotiation or delivery detail inside the thread.' },
  { key: 'intent_match', label: 'Matching buyer requests', description: 'Notify me when new sourcing demand matches my supplier profile.' },
  { key: 'offer_received', label: 'Buyer-side offer activity', description: 'Keep me aware when offer handling requires supplier attention.' },
  { key: 'offer_awarded', label: 'Award confirmations', description: 'Remind me immediately when an offer turns into a live order path.' },
  { key: 'order_update', label: 'Order status changes', description: 'Escrow, acceptance, and operational milestones should reach me quickly.' },
  { key: 'delivery_update', label: 'Delivery status changes', description: 'Alert me when shipment state changes and fulfillment action is needed.' },
]

const profileForm = ref({
  full_name: '',
  phone: '',
  email: '',
  telegram_chat_id: '',
})

const notificationForm = ref<NotificationPreferencesResponse>({
  email: '',
  telegram_chat_id: null,
  telegram_connected: false,
  channels: {
    email: true,
    telegram: false,
  },
  events: {
    new_message: true,
    intent_match: true,
    offer_received: true,
    offer_awarded: true,
    order_update: true,
    delivery_update: true,
  },
})

const profileSaving = ref(false)
const notificationSaving = ref(false)
const addresses = ref<AddressItem[]>([])
const addressLoading = ref(false)
const addressSaving = ref(false)
const editingAddressId = ref<string | null>(null)
const addressForm = ref({
  label: '',
  contact_name: '',
  contact_phone: '',
  country_code: 'PH',
  country_name: 'Philippines',
  city: '',
  address_line1: '',
  postal_code: '',
  is_default: false,
})

async function loadProfileAndPreferences() {
  const [me, prefs] = await Promise.all([
    api('/users/me'),
    api<NotificationPreferencesResponse>('/users/me/notification-preferences'),
  ])

  profileForm.value = {
    full_name: me.full_name || '',
    phone: me.phone || '',
    email: me.email || '',
    telegram_chat_id: me.telegram_chat_id || '',
  }

  notificationForm.value = {
    ...prefs,
    channels: { ...prefs.channels },
    events: { ...prefs.events },
  }
}

async function saveProfile() {
  profileSaving.value = true
  try {
    await api('/users/me', {
      method: 'PATCH',
      body: {
        full_name: profileForm.value.full_name,
        phone: profileForm.value.phone,
      },
    })
    await api('/users/me/telegram', {
      method: 'PATCH',
      body: {
        telegram_chat_id: profileForm.value.telegram_chat_id.trim() || null,
      },
    })
    await authStore.fetchMe()
    await loadProfileAndPreferences()
    toast.add({ title: 'Supplier contact updated', color: 'green' })
  } catch {
    toast.add({ title: 'Failed to update supplier contact', color: 'red' })
  } finally {
    profileSaving.value = false
  }
}

async function saveNotifications() {
  notificationSaving.value = true
  try {
    const prefs = await api<NotificationPreferencesResponse>('/users/me/notification-preferences', {
      method: 'PATCH',
      body: {
        channels: notificationForm.value.channels,
        events: notificationForm.value.events,
      },
    })
    notificationForm.value = {
      ...prefs,
      channels: { ...prefs.channels },
      events: { ...prefs.events },
    }
    toast.add({ title: 'Notification settings updated', color: 'green' })
  } catch {
    toast.add({ title: 'Failed to update notification settings', color: 'red' })
  } finally {
    notificationSaving.value = false
  }
}

async function loadAddresses() {
  addressLoading.value = true
  try {
    addresses.value = await api<AddressItem[]>('/addresses?address_type=SHIPPING_FROM')
  } catch {
    addresses.value = []
  } finally {
    addressLoading.value = false
  }
}

function resetAddressForm() {
  editingAddressId.value = null
  addressForm.value = {
    label: '',
    contact_name: '',
    contact_phone: '',
    country_code: 'PH',
    country_name: 'Philippines',
    city: '',
    address_line1: '',
    postal_code: '',
    is_default: false,
  }
}

function startEditAddress(addr: AddressItem) {
  editingAddressId.value = addr.id
  addressForm.value = {
    label: addr.label || '',
    contact_name: addr.contact_name || '',
    contact_phone: addr.contact_phone || '',
    country_code: addr.country_code || 'PH',
    country_name: addr.country_name || 'Philippines',
    city: addr.city || '',
    address_line1: addr.address_line1 || '',
    postal_code: addr.postal_code || '',
    is_default: !!addr.is_default,
  }
}

function cancelEditAddress() {
  resetAddressForm()
}

async function saveAddress() {
  addressSaving.value = true
  try {
    if (editingAddressId.value) {
      await api(`/addresses/${editingAddressId.value}`, {
        method: 'PATCH',
        body: { ...addressForm.value },
      })
    } else {
      await api('/addresses', {
        method: 'POST',
        body: {
          ...addressForm.value,
          address_type: 'SHIPPING_FROM',
        },
      })
    }
    resetAddressForm()
    await loadAddresses()
    toast.add({ title: 'Ship-from address updated', color: 'green' })
  } catch {
    toast.add({ title: 'Failed to save ship-from address', color: 'red' })
  } finally {
    addressSaving.value = false
  }
}

async function setDefaultAddress(id: string) {
  try {
    await api(`/addresses/${id}/set-default`, { method: 'POST' })
    await loadAddresses()
    toast.add({ title: 'Default ship-from address updated', color: 'green' })
  } catch {
    toast.add({ title: 'Failed to update default address', color: 'red' })
  }
}

async function deleteAddress(id: string) {
  try {
    await api(`/addresses/${id}`, { method: 'DELETE' })
    await loadAddresses()
    toast.add({ title: 'Address removed', color: 'green' })
  } catch {
    toast.add({ title: 'Failed to remove address', color: 'red' })
  }
}

onMounted(async () => {
  await Promise.all([loadProfileAndPreferences(), loadAddresses()])
})
</script>
