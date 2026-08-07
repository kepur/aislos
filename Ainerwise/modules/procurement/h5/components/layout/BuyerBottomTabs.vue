<template>
  <nav class="bottom-tabs">
    <NuxtLink
      v-for="tab in tabs"
      :key="tab.to"
      :to="tab.to"
      class="tab-item"
      :class="{ active: isActive(tab.match) }"
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
import { getLocalePrefixFromPath, stripLocalePrefix, withLocalePrefix } from "~/utils/localeRoutes";

const route = useRoute();
const notifStore = useNotificationStore();
const { t } = useI18n({ useScope: "global" });
const normalizedPath = computed(() => stripLocalePrefix(route.path));
const currentPrefix = computed(() =>
  getLocalePrefixFromPath(route.path) || (import.meta.client ? localStorage.getItem("h5_locale_prefix") || "" : "")
);

const tabs = computed(() => [
  { to: withLocalePrefix("/buyer/home", currentPrefix.value), match: "/buyer/home", label: t("nav.home"), icon: IconHome },
  { to: withLocalePrefix("/marketplace", currentPrefix.value), match: "/marketplace", label: "Market", icon: IconRequests },
  { to: withLocalePrefix("/secondhand", currentPrefix.value), match: "/secondhand", label: t("nav.secondhand") || "2Hands", icon: IconRequests },
  { to: withLocalePrefix("/buyer/requests", currentPrefix.value), match: "/buyer/requests", label: t("nav.requests"), icon: IconOrders },
  { to: withLocalePrefix("/buyer/wallet", currentPrefix.value), match: "/buyer/wallet", label: t("nav.wallet"), icon: IconWallet },
  { to: withLocalePrefix("/buyer/profile", currentPrefix.value), match: "/buyer/profile", label: t("nav.me"), icon: IconProfile, badge: true },
]);

function isActive(path: string) {
  return normalizedPath.value.startsWith(path);
}

onMounted(() => notifStore.fetchNotifications());
</script>
