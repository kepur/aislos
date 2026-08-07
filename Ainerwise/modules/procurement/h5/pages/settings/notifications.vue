<template>
  <div class="min-h-screen bg-slate-50 flex flex-col">
    <div class="bg-white border-b border-slate-100 px-4 h-14 flex items-center gap-3 sticky top-0 z-40 pt-safe">
      <button type="button" class="text-slate-600 p-1 -ml-1" @click="$router.back()">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h1 class="font-semibold text-slate-900 flex-1">Notification Settings</h1>
    </div>

    <div class="flex-1 px-4 py-6 pb-28 space-y-4">
      <div class="rounded-2xl border border-amber-100 bg-amber-50 p-4">
        <p class="text-sm font-semibold text-amber-900">Email and Telegram are enabled by default.</p>
        <p class="mt-1 text-xs leading-relaxed text-amber-700">
          WhatsApp and Viber are optional reminders. Order evidence, commitments, and dispute records still stay inside AinerWise Market.
        </p>
      </div>

      <div class="bg-white rounded-2xl shadow-card overflow-hidden">
        <div class="border-b border-slate-100 p-4">
          <h2 class="text-sm font-semibold text-slate-900">Contact channels</h2>
          <p class="mt-1 text-xs text-slate-500">Set the accounts and phone numbers used for reminders.</p>
        </div>
        <div class="space-y-3 p-4">
          <div>
            <label class="block text-xs font-semibold text-slate-500 mb-1.5">Email</label>
            <input :value="form.email" type="email" class="input-field bg-slate-50 text-slate-400" disabled />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-500 mb-1.5">Telegram chat ID</label>
            <input v-model="form.telegram_chat_id" type="text" class="input-field" placeholder="@username or chat ID" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-500 mb-1.5">WhatsApp number</label>
            <div class="grid grid-cols-[130px_1fr] gap-2">
              <select v-model="form.whatsapp_country" class="input-field bg-white">
                <option v-for="option in dialOptions" :key="option.countryCode" :value="option.countryCode">
                  {{ option.dialCode }}
                </option>
              </select>
              <input v-model="form.whatsapp_local" type="tel" class="input-field" :placeholder="contactPlaceholder(form.whatsapp_country)" />
            </div>
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-500 mb-1.5">Viber number</label>
            <div class="grid grid-cols-[130px_1fr] gap-2">
              <select v-model="form.viber_country" class="input-field bg-white">
                <option v-for="option in dialOptions" :key="option.countryCode" :value="option.countryCode">
                  {{ option.dialCode }}
                </option>
              </select>
              <input v-model="form.viber_local" type="tel" class="input-field" :placeholder="contactPlaceholder(form.viber_country)" />
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-2xl shadow-card overflow-hidden">
        <div class="border-b border-slate-100 p-4">
          <h2 class="text-sm font-semibold text-slate-900">Reminder channels</h2>
          <p class="mt-1 text-xs text-slate-500">Choose where the platform may remind you to come back.</p>
        </div>
        <button
          v-for="item in channelItems"
          :key="item.key"
          type="button"
          class="flex w-full items-start gap-4 px-4 py-4 text-left border-b last:border-0 border-slate-50"
          @click="form.channels[item.key] = !form.channels[item.key]"
        >
          <span class="text-xl">{{ item.icon }}</span>
          <span class="flex-1">
            <span class="block text-sm font-semibold text-slate-800">{{ item.label }}</span>
            <span class="mt-0.5 block text-xs text-slate-400">{{ item.desc }}</span>
          </span>
          <span
            class="relative mt-0.5 h-6 w-12 rounded-full transition-colors"
            :class="form.channels[item.key] ? 'bg-primary-500' : 'bg-slate-200'"
          >
            <span
              class="absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all"
              :class="form.channels[item.key] ? 'left-6' : 'left-0.5'"
            />
          </span>
        </button>
      </div>

      <div class="bg-white rounded-2xl shadow-card overflow-hidden">
        <div class="border-b border-slate-100 p-4">
          <h2 class="text-sm font-semibold text-slate-900">Event triggers</h2>
          <p class="mt-1 text-xs text-slate-500">Control which workflow events may send reminders.</p>
        </div>
        <button
          v-for="item in eventItems"
          :key="item.key"
          type="button"
          class="flex w-full items-start gap-4 px-4 py-4 text-left border-b last:border-0 border-slate-50"
          @click="form.events[item.key] = !form.events[item.key]"
        >
          <span class="text-xl">{{ item.icon }}</span>
          <span class="flex-1">
            <span class="block text-sm font-semibold text-slate-800">{{ item.label }}</span>
            <span class="mt-0.5 block text-xs text-slate-400">{{ item.desc }}</span>
          </span>
          <span
            class="relative mt-0.5 h-6 w-12 rounded-full transition-colors"
            :class="form.events[item.key] ? 'bg-primary-500' : 'bg-slate-200'"
          >
            <span
              class="absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all"
              :class="form.events[item.key] ? 'left-6' : 'left-0.5'"
            />
          </span>
        </button>
      </div>
    </div>

    <div class="sticky-bottom-action">
      <button type="button" class="btn-primary" :disabled="saving" @click="save">
        <span v-if="!saving">Save Preferences</span>
        <span v-else>Saving...</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { showToast } from "vant";
import {
  CONTACT_DIAL_OPTIONS,
  composeContactNumber,
  contactPlaceholder,
  splitContactNumber,
} from "~/utils/contactPolicy";

definePageMeta({ layout: "default", middleware: ["auth"] });
useHead({ title: "Notification Settings" });

type ChannelKey = "email" | "telegram" | "whatsapp" | "viber";
type EventKey = "new_message" | "intent_match" | "offer_received" | "offer_awarded" | "order_update" | "delivery_update";

const api = useApiFetch();
const authStore = useAuthStore();
const appStore = useAppStore();
const dialOptions = CONTACT_DIAL_OPTIONS;
const saving = ref(false);

const form = reactive({
  email: "",
  telegram_chat_id: "",
  whatsapp_country: "RS",
  whatsapp_local: "",
  viber_country: "RS",
  viber_local: "",
  channels: {
    email: true,
    telegram: true,
    whatsapp: false,
    viber: false,
  } as Record<ChannelKey, boolean>,
  events: {
    new_message: true,
    intent_match: true,
    offer_received: true,
    offer_awarded: true,
    order_update: true,
    delivery_update: true,
  } as Record<EventKey, boolean>,
});

const channelItems: Array<{ key: ChannelKey; icon: string; label: string; desc: string }> = [
  { key: "email", icon: "✉️", label: "Email reminders", desc: "Send summaries when messages, orders, or supplier replies need attention." },
  { key: "telegram", icon: "💬", label: "Telegram reminders", desc: "Enabled by default. Requires a saved Telegram chat ID." },
  { key: "whatsapp", icon: "🟢", label: "WhatsApp reminders", desc: "Only enabled after a WhatsApp number is saved." },
  { key: "viber", icon: "📞", label: "Viber reminders", desc: "Only enabled after a Viber number is saved." },
];

const eventItems: Array<{ key: EventKey; icon: string; label: string; desc: string }> = [
  { key: "new_message", icon: "💬", label: "New in-site messages", desc: "Buyer, supplier, and support messages that affect active work." },
  { key: "intent_match", icon: "🎯", label: "Request matches", desc: "New marketplace matches for your buying or selling flow." },
  { key: "offer_received", icon: "📩", label: "Offers received", desc: "Supplier quotes, counter-offers, or offer updates." },
  { key: "offer_awarded", icon: "🏆", label: "Award events", desc: "Awarded offers and next-step reminders." },
  { key: "order_update", icon: "📦", label: "Order updates", desc: "Payment, dispatch, settlement, and order lifecycle changes." },
  { key: "delivery_update", icon: "🚚", label: "Delivery updates", desc: "Shipment and completion events from suppliers or field teams." },
];

onMounted(async () => {
  await appStore.fetchMarketLocalizationConfig();
  await loadPreferences();
});

async function loadPreferences() {
  const fallbackCountry = appStore.regionCountry || "RS";
  try {
    const [me, prefs] = await Promise.all([
      api<any>("/users/me"),
      api<any>("/users/me/notification-preferences"),
    ]);
    const whatsapp = splitContactNumber(prefs?.whatsapp_number, fallbackCountry);
    const viber = splitContactNumber(prefs?.viber_number, fallbackCountry);
    form.email = prefs?.email || me?.email || authStore.user?.email || "";
    form.telegram_chat_id = prefs?.telegram_chat_id || "";
    form.whatsapp_country = whatsapp.countryCode;
    form.whatsapp_local = whatsapp.localNumber;
    form.viber_country = viber.countryCode;
    form.viber_local = viber.localNumber;
    form.channels.email = prefs?.email_enabled ?? true;
    form.channels.telegram = prefs?.telegram_enabled ?? true;
    form.channels.whatsapp = prefs?.whatsapp_enabled ?? false;
    form.channels.viber = prefs?.viber_enabled ?? false;
    form.events.new_message = prefs?.alerts_enabled ?? true;
    form.events.intent_match = prefs?.alerts_enabled ?? true;
    form.events.offer_received = prefs?.alerts_enabled ?? true;
    form.events.offer_awarded = prefs?.renewal_enabled ?? true;
    form.events.order_update = prefs?.maintenance_enabled ?? true;
    form.events.delivery_update = prefs?.maintenance_enabled ?? true;
  } catch {
    form.email = authStore.user?.email || "";
  }
}

async function save() {
  saving.value = true;
  try {
    const whatsappNumber = composeContactNumber(form.whatsapp_country, form.whatsapp_local) || null;
    const viberNumber = composeContactNumber(form.viber_country, form.viber_local) || null;
    await api("/users/me/telegram", {
      method: "PATCH",
      body: { telegram_chat_id: form.telegram_chat_id.trim() || null },
    });
    const prefs = await api<any>("/users/me/notification-preferences", {
      method: "PATCH",
      body: {
        email: form.email || null,
        telegram_chat_id: form.telegram_chat_id.trim() || null,
        whatsapp_number: whatsappNumber,
        viber_number: viberNumber,
        email_enabled: form.channels.email,
        telegram_enabled: form.channels.telegram,
        whatsapp_enabled: form.channels.whatsapp,
        viber_enabled: form.channels.viber,
        alerts_enabled: Boolean(form.events.new_message || form.events.intent_match || form.events.offer_received),
        renewal_enabled: Boolean(form.events.offer_awarded),
        maintenance_enabled: Boolean(form.events.order_update || form.events.delivery_update),
      },
    });
    form.channels.email = prefs?.email_enabled ?? form.channels.email;
    form.channels.telegram = prefs?.telegram_enabled ?? form.channels.telegram;
    form.channels.whatsapp = prefs?.whatsapp_enabled ?? form.channels.whatsapp;
    form.channels.viber = prefs?.viber_enabled ?? form.channels.viber;
    showToast({ type: "success", message: "Preferences saved" });
  } catch {
    showToast({ type: "fail", message: "Could not save preferences" });
  } finally {
    saving.value = false;
  }
}
</script>
