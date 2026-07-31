<template><CebuBuyerOrderDetail :id="String(route.params.id)" /></template>
<script setup lang="ts">definePageMeta({ layout: 'procurement', middleware: ['auth'], alias: ['/buyer/orders/:id'] }); const route = useRoute()</script>
