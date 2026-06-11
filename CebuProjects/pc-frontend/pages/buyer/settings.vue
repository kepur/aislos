<template>
  <div class="mx-auto max-w-5xl space-y-6">
    <div class="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Buyer Settings</h1>
        <p class="mt-1 text-sm text-slate-500">Control receiving addresses, reminder channels, and the contact details tied to your buyer account.</p>
      </div>
      <div class="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-xs text-slate-500 shadow-sm">
        In-site chat and transaction records remain the canonical source for disputes and audits.
      </div>
    </div>

    <div class="rounded-3xl border border-amber-200 bg-gradient-to-r from-amber-50 via-white to-orange-50 px-5 py-4 shadow-sm">
      <p class="text-sm font-semibold text-slate-900">Reminder channels are optional. Order evidence is not.</p>
      <p class="mt-1 text-sm text-slate-600">Email and Telegram can pull you back into the platform quickly, but messages, commitments, and settlement-sensitive details always stay in-site.</p>
    </div>

    <div class="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
      <div class="space-y-6">
        <UCard id="profile">
          <template #header>
            <div>
              <h2 class="text-lg font-semibold text-slate-900">Account Contact</h2>
              <p class="mt-1 text-sm text-slate-500">Keep the buyer identity and callback details current.</p>
            </div>
          </template>

          <form class="space-y-4" @submit.prevent="saveProfile">
            <div class="grid gap-4 sm:grid-cols-2">
              <UFormGroup label="Full Name">
                <UInput v-model="profileForm.full_name" placeholder="Buyer name" />
              </UFormGroup>
              <UFormGroup label="Mobile Number">
                <UInput v-model="profileForm.phone" placeholder="09xx xxx xxxx" />
              </UFormGroup>
            </div>

            <UFormGroup label="Email">
              <UInput :model-value="profileForm.email" disabled />
            </UFormGroup>

            <UFormGroup label="Telegram Chat ID">
              <UInput v-model="profileForm.telegram_chat_id" placeholder="Optional: used only for reminder pings" />
            </UFormGroup>

            <div class="flex justify-end border-t border-slate-100 pt-4">
              <UButton type="submit" color="indigo" :loading="profileSaving">Save Contact Details</UButton>
            </div>
          </form>
        </UCard>

        <UCard id="addresses">
          <template #header>
            <div>
              <h2 class="text-lg font-semibold text-slate-900">Receiving Address Book</h2>
              <p class="mt-1 text-sm text-slate-500">These are the drop-off destinations buyers can switch to quickly during checkout.</p>
            </div>
          </template>

          <div class="space-y-4">
            <div v-if="addressLoading" class="text-sm text-slate-500">Loading addresses...</div>
            <div v-else-if="!addresses.length" class="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-5 text-sm text-slate-500">
              No receiving address yet. Add your most common warehouse, site office, or delivery point.
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
                    <UButton size="xs" color="indigo" variant="soft" @click="startEditAddress(addr)">Edit</UButton>
                    <UButton size="xs" color="gray" variant="soft" @click="setDefaultAddress(addr.id)">Set Default</UButton>
                    <UButton size="xs" color="red" variant="soft" @click="deleteAddress(addr.id)">Delete</UButton>
                  </div>
                </div>
              </div>
            </div>

            <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p class="text-sm font-semibold text-slate-900">{{ editingAddressId ? 'Edit Receiving Address' : 'Add Receiving Address' }}</p>
              <div class="mt-4 grid gap-3 sm:grid-cols-2">
                <UInput v-model="addressForm.label" placeholder="Label: Main warehouse" />
                <UInput v-model="addressForm.contact_name" placeholder="Receiver name" />
                <UInput v-model="addressForm.contact_phone" placeholder="Receiver phone" />
                <UInput v-model="addressForm.city" placeholder="City" />
                <UInput v-model="addressForm.address_line1" placeholder="Address line 1" class="sm:col-span-2" />
                <UInput v-model="addressForm.postal_code" placeholder="Postal code" />
              </div>
              <div class="mt-4 flex justify-end gap-2">
                <UButton v-if="editingAddressId" color="gray" variant="soft" @click="cancelEditAddress">Cancel</UButton>
                <UButton color="indigo" :loading="addressSaving" @click="saveAddress">
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
            <p class="mt-1 text-sm text-slate-500">Choose which reminder channels are allowed to pull you back to the in-site workflow.</p>
          </div>
        </template>

        <form class="space-y-5" @submit.prevent="saveNotifications">
          <div class="space-y-3">
            <p class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Reminder Channels</p>
            <label class="flex items-start gap-3 rounded-2xl border border-slate-200 p-4 transition hover:border-indigo-200 hover:bg-indigo-50/40">
              <input v-model="notificationForm.channels.email" type="checkbox" class="mt-1 h-4 w-4 rounded border-slate-300 accent-indigo-600" />
              <div>
                <p class="text-sm font-semibold text-slate-900">Email reminders</p>
                <p class="mt-1 text-sm text-slate-500">Send a summary when a new message, order change, or supplier response needs attention.</p>
              </div>
            </label>
            <label class="flex items-start gap-3 rounded-2xl border border-slate-200 p-4 transition hover:border-indigo-200 hover:bg-indigo-50/40">
              <input v-model="notificationForm.channels.telegram" type="checkbox" class="mt-1 h-4 w-4 rounded border-slate-300 accent-indigo-600" />
              <div>
                <p class="text-sm font-semibold text-slate-900">Telegram reminders</p>
                <p class="mt-1 text-sm text-slate-500">Only enabled when a Telegram chat ID is saved above.</p>
              </div>
            </label>
          </div>

          <div class="space-y-3">
            <p class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Event Triggers</p>
            <label v-for="event in buyerEventOptions" :key="event.key" class="flex items-start gap-3 rounded-2xl border border-slate-200 p-4 transition hover:border-indigo-200 hover:bg-indigo-50/40">
              <input v-model="notificationForm.events[event.key]" type="checkbox" class="mt-1 h-4 w-4 rounded border-slate-300 accent-indigo-600" />
              <div>
                <p class="text-sm font-semibold text-slate-900">{{ event.label }}</p>
                <p class="mt-1 text-sm text-slate-500">{{ event.description }}</p>
              </div>
            </label>
          </div>

          <div class="flex justify-end border-t border-slate-100 pt-4">
            <UButton type="submit" color="indigo" :loading="notificationSaving">Save Notification Settings</UButton>
          </div>
        </form>
      </UCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

definePageMeta({ layout: 'buyer' })

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

const buyerEventOptions: Array<{ key: NotificationEventKey; label: string; description: string }> = [
  { key: 'new_message', label: 'New in-site messages', description: 'Alert me when a supplier replies in a thread that affects a live order or quote.' },
  { key: 'intent_match', label: 'Request matches', description: 'Tell me when my posted buying needs have fresh marketplace matches.' },
  { key: 'offer_received', label: 'New offers received', description: 'Notify me when suppliers respond with a concrete quotation.' },
  { key: 'offer_awarded', label: 'Award follow-up reminders', description: 'Keep me aware when an awarded flow needs follow-up action.' },
  { key: 'order_update', label: 'Order status updates', description: 'Payment, acceptance, and order progress changes should pull me back in quickly.' },
  { key: 'delivery_update', label: 'Delivery updates', description: 'Remind me when shipment or arrival status changes.' },
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
    toast.add({ title: 'Buyer profile updated', color: 'green' })
  } catch {
    toast.add({ title: 'Failed to update buyer profile', color: 'red' })
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
    addresses.value = await api<AddressItem[]>('/addresses?address_type=DELIVERY_TO')
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
          address_type: 'DELIVERY_TO',
        },
      })
    }
    resetAddressForm()
    await loadAddresses()
    toast.add({ title: 'Address book updated', color: 'green' })
  } catch {
    toast.add({ title: 'Failed to save address', color: 'red' })
  } finally {
    addressSaving.value = false
  }
}

async function setDefaultAddress(id: string) {
  try {
    await api(`/addresses/${id}/set-default`, { method: 'POST' })
    await loadAddresses()
    toast.add({ title: 'Default address updated', color: 'green' })
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
