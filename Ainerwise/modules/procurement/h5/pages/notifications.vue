<template>
  <div class="min-h-screen bg-slate-50">
    <div class="bg-white border-b border-slate-100 px-4 h-14 flex items-center justify-between sticky top-0 z-40 pt-safe">
      <div class="flex items-center gap-3">
        <button type="button" class="text-slate-600 p-1 -ml-1" @click="$router.back()">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <h1 class="font-bold text-slate-900">Notifications</h1>
      </div>
      <button type="button" v-if="notifStore.unreadCount > 0" class="text-sm text-primary-600 font-medium" @click="notifStore.markAllRead()">
        Mark all read
      </button>
    </div>

    <div class="divide-y divide-slate-100">
      <div v-if="notifStore.loading" class="p-4 space-y-3">
        <div v-for="n in 5" :key="n" class="flex gap-3">
          <div class="shimmer w-10 h-10 rounded-full flex-shrink-0"></div>
          <div class="flex-1">
            <div class="shimmer h-4 w-3/4 rounded mb-1.5"></div>
            <div class="shimmer h-3 w-full rounded"></div>
          </div>
        </div>
      </div>

      <div v-else-if="notifStore.notifications.length === 0" class="empty-state py-20">
        <svg class="w-16 h-16 text-slate-200 mb-3" fill="none" stroke="currentColor" stroke-width="1" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        <p class="text-slate-500 font-medium">No notifications</p>
        <p class="text-slate-400 text-xs mt-1">You're all caught up!</p>
      </div>

      <button type="button"
        v-for="notif in notifStore.notifications"
        :key="notif.id"
        class="w-full flex items-start gap-3 px-4 py-4 text-left active:bg-slate-50 transition-colors"
        :class="!notif.is_read ? 'bg-primary-50/50' : 'bg-white'"
        @click="notifStore.markRead(notif.id)"
      >
        <div class="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0"
             :class="getNotifIconBg(notif.notification_type)">
          <span class="text-lg">{{ getNotifEmoji(notif.notification_type) }}</span>
        </div>
        <div class="flex-1 min-w-0">
          <p v-if="notif.subject" class="font-semibold text-slate-900 text-sm">{{ notif.subject }}</p>
          <p class="text-sm text-slate-600 leading-snug mt-0.5 line-clamp-2">{{ notif.body }}</p>
          <p class="text-xs text-slate-400 mt-1.5">{{ formatRelativeTime(notif.created_at) }}</p>
        </div>
        <div v-if="!notif.is_read" class="w-2 h-2 bg-primary-500 rounded-full flex-shrink-0 mt-2"></div>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: "default", middleware: ["auth"] });
useHead({ title: "Notifications" });

const notifStore = useNotificationStore();
const { formatRelativeTime } = useApiUtils();

function getNotifEmoji(key?: string) {
  if (!key) return "🔔";
  if (key.includes("INTENT") || key.includes("REQUEST")) return "📋";
  if (key.includes("OFFER")) return "💼";
  if (key.includes("ORDER")) return "📦";
  if (key.includes("DELIVERY")) return "🚚";
  if (key.includes("DISPUTE")) return "⚠️";
  if (key.includes("PAYOUT") || key.includes("PAYMENT")) return "💰";
  return "🔔";
}

function getNotifIconBg(key?: string) {
  if (!key) return "bg-slate-100";
  if (key.includes("DISPUTE")) return "bg-red-50";
  if (key.includes("ORDER") || key.includes("DELIVERY")) return "bg-primary-50";
  if (key.includes("OFFER")) return "bg-amber-50";
  return "bg-primary-50";
}

onMounted(() => notifStore.fetchNotifications());
</script>
