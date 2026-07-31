<template><CebuBuyerRequestDetail :id="String(route.params.id)" /></template>
<script setup lang="ts">definePageMeta({ layout: 'procurement', middleware: ['auth'], alias: ['/buyer/requests/:id'] }); const route = useRoute()</script>
