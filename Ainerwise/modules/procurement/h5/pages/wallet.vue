<template>
  <MobileWallet />
</template>

<script setup lang="ts">
definePageMeta({ layout: "default", middleware: ["auth"] });
useHead({ title: "Wallet" });
</script>
