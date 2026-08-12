<template><section class="mx-auto max-w-3xl space-y-5"><h1 class="text-2xl font-bold text-white">{{ $t('procPages.newReqTitle') }}</h1><CebuRequestForm /></section></template>
<script setup lang="ts">definePageMeta({ layout: 'procurement', middleware: ['auth'] })</script>
