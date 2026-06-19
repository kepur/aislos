<template>
  <nav class="bottom-tabs">
    <NuxtLink
      v-for="tab in tabs"
      :key="tab.to"
      :to="tab.to"
      class="tab-item"
      :class="{ active: isActive(tab.to) }"
    >
      <div class="relative">
        <component :is="tab.icon" class="w-6 h-6" />
        <span
          v-if="tab.badge && notifStore.unreadCount > 0"
          class="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-[10px] rounded-full flex items-center justify-center font-bold"
        >
          {{ notifStore.unreadCount > 9 ? "9+" : notifStore.unreadCount }}
        </span>
      </div>
      <span class="text-[10px] font-medium leading-none">{{ tab.label }}</span>
    </NuxtLink>
  </nav>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";
import IconHome from "~/components/icons/IconHome.vue";
import IconRequests from "~/components/icons/IconRequests.vue";
import IconOrders from "~/components/icons/IconOrders.vue";
import IconWallet from "~/components/icons/IconWallet.vue";
import IconProfile from "~/components/icons/IconProfile.vue";

const route = useRoute();
const notifStore = useNotificationStore();
const { t } = useI18n({ useScope: "global" });

const tabs = computed(() => [
  { to: "/buyer/home", label: t("nav.home"), icon: IconHome },
  { to: "/marketplace", label: "Market", icon: IconRequests },
  { to: "/buyer/requests", label: t("nav.requests"), icon: IconOrders },
  { to: "/buyer/wallet", label: t("nav.wallet"), icon: IconWallet },
  { to: "/buyer/profile", label: t("nav.me"), icon: IconProfile, badge: true },
]);

function isActive(path: string) {
  return route.path.startsWith(path);
}

onMounted(() => notifStore.fetchNotifications());
</script>
