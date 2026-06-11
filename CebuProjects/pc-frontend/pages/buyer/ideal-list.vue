<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-2xl font-bold text-slate-900">Ideal Supplier List</h1>
      <UButton color="gray" variant="ghost" icon="i-heroicons-plus">Add Supplier</UButton>
    </div>
    
    <p class="text-slate-500 mb-6">Manage your trusted and verified suppliers. When you post a new request, they will be invited to quote first.</p>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <UCard v-for="i in 3" :key="i">
        <div class="flex justify-between items-start">
          <div class="flex items-center">
            <UAvatar :src="`https://i.pravatar.cc/150?u=s${i}`" />
            <div class="ml-3">
              <h3 class="font-medium text-slate-900">Global Build Supply {{i}}</h3>
              <p class="text-xs text-slate-500">Construction Materials</p>
            </div>
          </div>
          <UButton icon="i-heroicons-ellipsis-horizontal" color="gray" variant="ghost" size="xs" />
        </div>
        
        <div class="mt-4 pt-4 border-t border-slate-100 flex justify-between text-sm">
          <div>
            <p class="text-slate-500">Orders</p>
            <p class="font-medium text-slate-900">12</p>
          </div>
          <div>
            <p class="text-slate-500">Rating</p>
            <p class="font-medium text-amber-500 flex items-center">
              <UIcon name="i-heroicons-star-solid" class="w-4 h-4 mr-1" />
              4.9
            </p>
          </div>
        </div>
      </UCard>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'buyer' })
</script>
