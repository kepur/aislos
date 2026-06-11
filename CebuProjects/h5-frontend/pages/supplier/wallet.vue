<template>
  <MobileWallet :show-back="false" :title="$t('nav.wallet')" />
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";

definePageMeta({ layout: "supplier", middleware: ["supplier"] });
const { t } = useI18n({ useScope: "global" });
useHead({ title: t("nav.wallet") });
</script>
