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

    <div class="flex-1 px-4 py-6 space-y-4">
      <p class="text-sm text-slate-500">Choose which notifications you receive and how.</p>

      <div class="bg-white rounded-2xl shadow-card overflow-hidden">
        <div v-for="(item, i) in settings" :key="item.key"
          class="flex items-center gap-4 px-4 py-4 border-b last:border-0 border-slate-50">
          <div>
            <span class="text-xl">{{ item.icon }}</span>
          </div>
          <div class="flex-1">
            <p class="text-sm font-medium text-slate-800">{{ item.label }}</p>
            <p class="text-xs text-slate-400 mt-0.5">{{ item.desc }}</p>
          </div>
          <div
            class="w-12 h-6 rounded-full transition-colors cursor-pointer relative flex-shrink-0"
            :class="item.enabled ? 'bg-primary-500' : 'bg-slate-200'"
            @click="item.enabled = !item.enabled"
          >
            <div class="w-5 h-5 bg-white rounded-full absolute top-0.5 shadow transition-all"
              :class="item.enabled ? 'left-6' : 'left-0.5'"></div>
          </div>
        </div>
      </div>

      <div class="bg-amber-50 border border-amber-100 rounded-xl p-4">
        <p class="text-xs text-amber-700 font-medium">Email & Telegram notifications require system configuration by an admin.</p>
      </div>
    </div>

    <div class="sticky-bottom-action">
      <button type="button" class="btn-primary" @click="save">Save Preferences</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { showToast } from "vant";

definePageMeta({ layout: "default", middleware: ["auth"] });
useHead({ title: "Notification Settings" });

const settings = reactive([
  { key: "new_offer", icon: "📩", label: "New Offers", desc: "When suppliers submit offers on your requests", enabled: true },
  { key: "order_update", icon: "📦", label: "Order Updates", desc: "Delivery and order status changes", enabled: true },
  { key: "dispute_update", icon: "⚖️", label: "Dispute Updates", desc: "Messages from our resolution team", enabled: true },
  { key: "pings", icon: "🔔", label: "Matching Requests", desc: "When new buyer requests match your catalog", enabled: true },
  { key: "marketing", icon: "📢", label: "Tips & Announcements", desc: "Platform updates and tips", enabled: false },
]);

function save() {
  showToast({ type: "success", message: "Preferences saved" });
}
</script>
