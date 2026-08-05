<template>
  <div class="mx-auto max-w-5xl space-y-6">
    <div class="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">{{ t('buyer.settings.title') }}</h1>
        <p class="mt-1 text-sm text-slate-500">{{ t('buyer.settings.subtitle') }}</p>
      </div>
      <div class="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-xs text-slate-500 shadow-sm">
        {{ t('buyer.settings.auditNotice') }}
      </div>
    </div>

    <div class="rounded-3xl border border-amber-200 bg-gradient-to-r from-amber-50 via-white to-orange-50 px-5 py-4 shadow-sm">
      <p class="text-sm font-semibold text-slate-900">{{ t('buyer.settings.guardTitle') }}</p>
      <p class="mt-1 text-sm text-slate-600">{{ t('buyer.settings.guardDesc') }}</p>
    </div>

    <div class="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
      <div class="space-y-6">
        <UCard id="profile">
          <template #header>
            <div>
              <h2 class="text-lg font-semibold text-slate-900">{{ t('buyer.settings.contactTitle') }}</h2>
              <p class="mt-1 text-sm text-slate-500">{{ t('buyer.settings.contactDesc') }}</p>
            </div>
          </template>

          <form class="space-y-4" @submit.prevent="saveProfile">
            <div class="grid gap-4 sm:grid-cols-2">
              <UFormGroup :label="t('buyer.settings.fullName')">
                <UInput v-model="profileForm.full_name" :placeholder="t('buyer.settings.fullNamePlaceholder')" />
              </UFormGroup>
              <UFormGroup :label="t('buyer.settings.mobile')">
                <div class="grid grid-cols-[130px_1fr] gap-2">
                  <USelect
                    v-model="profileForm.phone_country"
                    :options="dialOptions"
                    option-attribute="label"
                    value-attribute="countryCode"
                  />
                  <UInput v-model="profileForm.phone_local" :placeholder="contactPlaceholder(profileForm.phone_country)" />
                </div>
              </UFormGroup>
            </div>

            <UFormGroup :label="t('buyer.settings.email')">
              <UInput :model-value="profileForm.email" disabled />
            </UFormGroup>

            <div class="grid gap-4 sm:grid-cols-3">
              <UFormGroup :label="t('buyer.settings.telegram')">
                <UInput v-model="profileForm.telegram_chat_id" :placeholder="t('buyer.settings.telegramPlaceholder')" />
              </UFormGroup>
              <UFormGroup :label="t('buyer.settings.whatsapp')">
                <div class="grid grid-cols-[130px_1fr] gap-2">
                  <USelect
                    v-model="profileForm.whatsapp_country"
                    :options="dialOptions"
                    option-attribute="label"
                    value-attribute="countryCode"
                  />
                  <UInput v-model="profileForm.whatsapp_local" :placeholder="contactPlaceholder(profileForm.whatsapp_country)" />
                </div>
              </UFormGroup>
              <UFormGroup :label="t('buyer.settings.viber')">
                <div class="grid grid-cols-[130px_1fr] gap-2">
                  <USelect
                    v-model="profileForm.viber_country"
                    :options="dialOptions"
                    option-attribute="label"
                    value-attribute="countryCode"
                  />
                  <UInput v-model="profileForm.viber_local" :placeholder="contactPlaceholder(profileForm.viber_country)" />
                </div>
              </UFormGroup>
            </div>

            <div class="flex justify-end border-t border-slate-100 pt-4">
              <UButton type="submit" color="indigo" :loading="profileSaving">{{ t('buyer.settings.saveContact') }}</UButton>
            </div>
          </form>
        </UCard>

        <UCard id="addresses">
          <template #header>
            <div>
              <h2 class="text-lg font-semibold text-slate-900">{{ t('buyer.settings.addressTitle') }}</h2>
              <p class="mt-1 text-sm text-slate-500">{{ t('buyer.settings.addressDesc') }}</p>
            </div>
          </template>

          <div class="space-y-4">
            <div v-if="addressLoading" class="text-sm text-slate-500">{{ t('buyer.settings.loadingAddresses') }}</div>
            <div v-else-if="!addresses.length" class="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-5 text-sm text-slate-500">
              {{ t('buyer.settings.noAddress') }}
            </div>
            <div v-else class="space-y-3">
              <div v-for="addr in addresses" :key="addr.id" class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p class="text-sm font-semibold text-slate-900">
                      {{ addr.label }}
                      <span v-if="addr.is_default" class="ml-2 rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-semibold text-emerald-700">{{ t('buyer.settings.default') }}</span>
                    </p>
                    <p class="mt-1 text-sm text-slate-600">{{ addr.contact_name }}<span v-if="addr.contact_phone"> · {{ addr.contact_phone }}</span></p>
                    <p class="mt-1 text-sm text-slate-500">{{ addr.address_line1 }}, {{ addr.city }}, {{ addr.country_name }}</p>
                  </div>
                  <div class="flex flex-wrap gap-2">
                    <UButton size="xs" color="indigo" variant="soft" @click="startEditAddress(addr)">{{ t('buyer.settings.edit') }}</UButton>
                    <UButton size="xs" color="gray" variant="soft" @click="setDefaultAddress(addr.id)">{{ t('buyer.settings.setDefault') }}</UButton>
                    <UButton size="xs" color="red" variant="soft" @click="deleteAddress(addr.id)">{{ t('buyer.settings.delete') }}</UButton>
                  </div>
                </div>
              </div>
            </div>

            <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p class="text-sm font-semibold text-slate-900">{{ editingAddressId ? t('buyer.settings.editAddress') : t('buyer.settings.addAddress') }}</p>
              <div class="mt-4 grid gap-3 sm:grid-cols-2">
                <UInput v-model="addressForm.label" :placeholder="t('buyer.settings.addressLabelPlaceholder')" />
                <UInput v-model="addressForm.contact_name" :placeholder="t('buyer.settings.receiverNamePlaceholder')" />
                <UInput v-model="addressForm.contact_phone" :placeholder="t('buyer.settings.receiverPhonePlaceholder')" />
                <UInput v-model="addressForm.city" :placeholder="t('buyer.settings.cityPlaceholder')" />
                <UInput v-model="addressForm.address_line1" :placeholder="t('buyer.settings.addressLinePlaceholder')" class="sm:col-span-2" />
                <UInput v-model="addressForm.postal_code" :placeholder="t('buyer.settings.postalPlaceholder')" />
              </div>
              <div class="mt-4 flex justify-end gap-2">
                <UButton v-if="editingAddressId" color="gray" variant="soft" @click="cancelEditAddress">{{ t('buyer.settings.cancel') }}</UButton>
                <UButton color="indigo" :loading="addressSaving" @click="saveAddress">
                  {{ editingAddressId ? t('buyer.settings.saveAddress') : t('buyer.settings.addAddressButton') }}
                </UButton>
              </div>
            </div>
          </div>
        </UCard>
      </div>

      <UCard id="notifications" class="h-fit">
        <template #header>
          <div>
            <h2 class="text-lg font-semibold text-slate-900">{{ t('buyer.settings.notificationsTitle') }}</h2>
            <p class="mt-1 text-sm text-slate-500">{{ t('buyer.settings.notificationsDesc') }}</p>
          </div>
        </template>

        <form class="space-y-5" @submit.prevent="saveNotifications">
          <div class="space-y-3">
            <p class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{{ t('buyer.settings.reminderChannels') }}</p>
            <label class="flex items-start gap-3 rounded-2xl border border-slate-200 p-4 transition hover:border-indigo-200 hover:bg-indigo-50/40">
              <input v-model="notificationForm.channels.email" type="checkbox" class="mt-1 h-4 w-4 rounded border-slate-300 accent-indigo-600" />
              <div>
                <p class="text-sm font-semibold text-slate-900">{{ t('buyer.settings.emailReminder') }}</p>
                <p class="mt-1 text-sm text-slate-500">{{ t('buyer.settings.emailReminderDesc') }}</p>
              </div>
            </label>
            <label class="flex items-start gap-3 rounded-2xl border border-slate-200 p-4 transition hover:border-indigo-200 hover:bg-indigo-50/40">
              <input v-model="notificationForm.channels.telegram" type="checkbox" class="mt-1 h-4 w-4 rounded border-slate-300 accent-indigo-600" />
              <div>
                <p class="text-sm font-semibold text-slate-900">{{ t('buyer.settings.telegramReminder') }}</p>
                <p class="mt-1 text-sm text-slate-500">{{ t('buyer.settings.telegramReminderDesc') }}</p>
              </div>
            </label>
            <label class="flex items-start gap-3 rounded-2xl border border-slate-200 p-4 transition hover:border-indigo-200 hover:bg-indigo-50/40">
              <input v-model="notificationForm.channels.whatsapp" type="checkbox" class="mt-1 h-4 w-4 rounded border-slate-300 accent-indigo-600" />
              <div>
                <p class="text-sm font-semibold text-slate-900">{{ t('buyer.settings.whatsappReminder') }}</p>
                <p class="mt-1 text-sm text-slate-500">{{ t('buyer.settings.whatsappReminderDesc') }}</p>
              </div>
            </label>
            <label class="flex items-start gap-3 rounded-2xl border border-slate-200 p-4 transition hover:border-indigo-200 hover:bg-indigo-50/40">
              <input v-model="notificationForm.channels.viber" type="checkbox" class="mt-1 h-4 w-4 rounded border-slate-300 accent-indigo-600" />
              <div>
                <p class="text-sm font-semibold text-slate-900">{{ t('buyer.settings.viberReminder') }}</p>
                <p class="mt-1 text-sm text-slate-500">{{ t('buyer.settings.viberReminderDesc') }}</p>
              </div>
            </label>
          </div>

          <div class="space-y-3">
            <p class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{{ t('buyer.settings.eventTriggers') }}</p>
            <label v-for="event in buyerEventOptions" :key="event.key" class="flex items-start gap-3 rounded-2xl border border-slate-200 p-4 transition hover:border-indigo-200 hover:bg-indigo-50/40">
              <input v-model="notificationForm.events[event.key]" type="checkbox" class="mt-1 h-4 w-4 rounded border-slate-300 accent-indigo-600" />
              <div>
                <p class="text-sm font-semibold text-slate-900">{{ event.label }}</p>
                <p class="mt-1 text-sm text-slate-500">{{ event.description }}</p>
              </div>
            </label>
          </div>

          <div class="flex justify-end border-t border-slate-100 pt-4">
            <UButton type="submit" color="indigo" :loading="notificationSaving">{{ t('buyer.settings.saveNotifications') }}</UButton>
          </div>
        </form>
      </UCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  CONTACT_DIAL_OPTIONS,
  composeContactNumber,
  contactPlaceholder,
  dialOptionForCountry,
  splitContactNumber,
} from '~/utils/contactPolicy'

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
  whatsapp_number: string | null
  viber_number: string | null
  telegram_connected: boolean
  channels: {
    email: boolean
    telegram: boolean
    whatsapp: boolean
    viber: boolean
  }
  events: Record<NotificationEventKey, boolean>
}

const api = useApiFetch()
const authStore = useAuthStore()
const appStore = useAppStore()
const toast = useToast()
const t = (key: string) => appStore.t(key)
const dialOptions = CONTACT_DIAL_OPTIONS

const buyerEventOptions = computed<Array<{ key: NotificationEventKey; label: string; description: string }>>(() => [
  { key: 'new_message', label: t('buyer.settings.event.newMessage'), description: t('buyer.settings.event.newMessageDesc') },
  { key: 'intent_match', label: t('buyer.settings.event.intentMatch'), description: t('buyer.settings.event.intentMatchDesc') },
  { key: 'offer_received', label: t('buyer.settings.event.offerReceived'), description: t('buyer.settings.event.offerReceivedDesc') },
  { key: 'offer_awarded', label: t('buyer.settings.event.offerAwarded'), description: t('buyer.settings.event.offerAwardedDesc') },
  { key: 'order_update', label: t('buyer.settings.event.orderUpdate'), description: t('buyer.settings.event.orderUpdateDesc') },
  { key: 'delivery_update', label: t('buyer.settings.event.deliveryUpdate'), description: t('buyer.settings.event.deliveryUpdateDesc') },
])

const profileForm = ref({
  full_name: '',
  phone_country: 'RS',
  phone_local: '',
  email: '',
  telegram_chat_id: '',
  whatsapp_country: 'RS',
  whatsapp_local: '',
  viber_country: 'RS',
  viber_local: '',
})

const notificationForm = ref<NotificationPreferencesResponse>({
  email: '',
  telegram_chat_id: null,
  whatsapp_number: null,
  viber_number: null,
  telegram_connected: false,
    channels: {
      email: true,
      telegram: true,
      whatsapp: false,
      viber: false,
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

function normalizePreferences(raw: any): NotificationPreferencesResponse {
  return {
    email: raw?.email || profileForm.value.email || '',
    telegram_chat_id: raw?.telegram_chat_id || null,
    whatsapp_number: raw?.whatsapp_number || null,
    viber_number: raw?.viber_number || null,
    telegram_connected: Boolean(raw?.telegram_connected || raw?.telegram_chat_id),
    channels: {
      email: raw?.channels?.email ?? raw?.email_enabled ?? true,
      telegram: raw?.channels?.telegram ?? raw?.telegram_enabled ?? true,
      whatsapp: raw?.channels?.whatsapp ?? raw?.whatsapp_enabled ?? false,
      viber: raw?.channels?.viber ?? raw?.viber_enabled ?? false,
    },
    events: {
      new_message: raw?.events?.new_message ?? raw?.alerts_enabled ?? true,
      intent_match: raw?.events?.intent_match ?? raw?.alerts_enabled ?? true,
      offer_received: raw?.events?.offer_received ?? raw?.alerts_enabled ?? true,
      offer_awarded: raw?.events?.offer_awarded ?? raw?.renewal_enabled ?? true,
      order_update: raw?.events?.order_update ?? raw?.maintenance_enabled ?? true,
      delivery_update: raw?.events?.delivery_update ?? raw?.maintenance_enabled ?? true,
    },
  }
}

async function loadProfileAndPreferences() {
  const [me, prefs] = await Promise.all([
    api('/users/me'),
    api<NotificationPreferencesResponse>('/users/me/notification-preferences'),
  ])

  const normalizedPrefs = normalizePreferences(prefs)
  const fallbackCountry = appStore.regionCountry || 'RS'
  const phone = splitContactNumber(me.phone, fallbackCountry)
  const whatsapp = splitContactNumber(normalizedPrefs.whatsapp_number, fallbackCountry)
  const viber = splitContactNumber(normalizedPrefs.viber_number, fallbackCountry)

  profileForm.value = {
    full_name: me.full_name || '',
    phone_country: phone.countryCode,
    phone_local: phone.localNumber,
    email: me.email || normalizedPrefs.email || '',
    telegram_chat_id: normalizedPrefs.telegram_chat_id || '',
    whatsapp_country: whatsapp.countryCode,
    whatsapp_local: whatsapp.localNumber,
    viber_country: viber.countryCode,
    viber_local: viber.localNumber,
  }

  notificationForm.value = normalizedPrefs
}

async function saveProfile() {
  profileSaving.value = true
  try {
    await api('/users/me', {
      method: 'PATCH',
      body: {
        full_name: profileForm.value.full_name,
        phone: composeContactNumber(profileForm.value.phone_country, profileForm.value.phone_local) || null,
      },
    })
    await api('/users/me/telegram', {
      method: 'PATCH',
      body: {
        telegram_chat_id: profileForm.value.telegram_chat_id.trim() || null,
      },
    })
    await api('/users/me/notification-preferences', {
      method: 'PATCH',
      body: {
        email: profileForm.value.email || null,
        telegram_chat_id: profileForm.value.telegram_chat_id.trim() || null,
        whatsapp_number: composeContactNumber(profileForm.value.whatsapp_country, profileForm.value.whatsapp_local) || null,
        viber_number: composeContactNumber(profileForm.value.viber_country, profileForm.value.viber_local) || null,
      },
    })
    await authStore.fetchMe()
    await loadProfileAndPreferences()
    toast.add({ title: t('buyer.settings.profileUpdated'), color: 'green' })
  } catch {
    toast.add({ title: t('buyer.settings.profileFailed'), color: 'red' })
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
        email_enabled: notificationForm.value.channels.email,
        telegram_enabled: notificationForm.value.channels.telegram,
        whatsapp_enabled: notificationForm.value.channels.whatsapp,
        viber_enabled: notificationForm.value.channels.viber,
        telegram_chat_id: profileForm.value.telegram_chat_id.trim() || null,
        whatsapp_number: composeContactNumber(profileForm.value.whatsapp_country, profileForm.value.whatsapp_local) || null,
        viber_number: composeContactNumber(profileForm.value.viber_country, profileForm.value.viber_local) || null,
        alerts_enabled: Boolean(
          notificationForm.value.events.new_message ||
          notificationForm.value.events.intent_match ||
          notificationForm.value.events.offer_received,
        ),
        renewal_enabled: Boolean(notificationForm.value.events.offer_awarded),
        maintenance_enabled: Boolean(
          notificationForm.value.events.order_update ||
          notificationForm.value.events.delivery_update,
        ),
      },
    })
    notificationForm.value = normalizePreferences(prefs)
    toast.add({ title: t('buyer.settings.notificationsUpdated'), color: 'green' })
  } catch {
    toast.add({ title: t('buyer.settings.notificationsFailed'), color: 'red' })
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
  const country = dialOptionForCountry(appStore.regionCountry || 'RS')
  editingAddressId.value = null
  addressForm.value = {
    label: '',
    contact_name: '',
    contact_phone: '',
    country_code: country.countryCode,
    country_name: country.countryName,
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
    country_code: addr.country_code || appStore.regionCountry || 'RS',
    country_name: addr.country_name || dialOptionForCountry(appStore.regionCountry || 'RS').countryName,
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
    toast.add({ title: t('buyer.settings.addressUpdated'), color: 'green' })
  } catch {
    toast.add({ title: t('buyer.settings.addressFailed'), color: 'red' })
  } finally {
    addressSaving.value = false
  }
}

async function setDefaultAddress(id: string) {
  try {
    await api(`/addresses/${id}/set-default`, { method: 'POST' })
    await loadAddresses()
    toast.add({ title: t('buyer.settings.defaultAddressUpdated'), color: 'green' })
  } catch {
    toast.add({ title: t('buyer.settings.defaultAddressFailed'), color: 'red' })
  }
}

async function deleteAddress(id: string) {
  try {
    await api(`/addresses/${id}`, { method: 'DELETE' })
    await loadAddresses()
    toast.add({ title: t('buyer.settings.addressRemoved'), color: 'green' })
  } catch {
    toast.add({ title: t('buyer.settings.addressRemoveFailed'), color: 'red' })
  }
}

onMounted(async () => {
  await Promise.all([loadProfileAndPreferences(), loadAddresses()])
})
</script>
