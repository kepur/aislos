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
          v-if="tab.badge && pingCount > 0"
          class="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-[10px] rounded-full flex items-center justify-center font-bold"
        >
          {{ pingCount > 9 ? "9+" : pingCount }}
        </span>
      </div>
      <span class="text-[10px] font-medium leading-none">{{ tab.label }}</span>
    </NuxtLink>
  </nav>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";
import IconPings from "~/components/icons/IconPings.vue";
import IconOffers from "~/components/icons/IconOffers.vue";
import IconOrders from "~/components/icons/IconOrders.vue";
import IconWallet from "~/components/icons/IconWallet.vue";
import IconProfile from "~/components/icons/IconProfile.vue";

const route = useRoute();
const offerStore = useOfferStore();
const pingCount = computed(() => offerStore.total);
const { t } = useI18n({ useScope: "global" });

const tabs = computed(() => [
  { to: "/supplier/pings", label: t("nav.pings"), icon: IconPings, badge: true },
  { to: "/supplier/offers", label: t("nav.offers"), icon: IconOffers },
  { to: "/supplier/orders", label: t("nav.orders"), icon: IconOrders },
  { to: "/supplier/wallet", label: t("nav.wallet"), icon: IconWallet },
  { to: "/supplier/profile", label: t("nav.me"), icon: IconProfile },
]);

function isActive(path: string) {
  return route.path.startsWith(path);
}
</script>
