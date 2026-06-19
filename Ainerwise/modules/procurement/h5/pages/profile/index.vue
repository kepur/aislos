<template>
  <MobileAccount />
</template>

<script setup lang="ts">
definePageMeta({ layout: "default", middleware: ["auth"] });
useHead({ title: "My Account" });
</script>
