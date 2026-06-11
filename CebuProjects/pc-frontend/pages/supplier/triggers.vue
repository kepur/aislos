<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Matching Triggers</h1>
        <p class="text-sm text-slate-500 mt-1">Configure which buyer requests ping your inbox.</p>
      </div>
      <UButton color="indigo" icon="i-heroicons-plus" size="md">New Trigger Rule</UButton>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <!-- Active Triggers -->
      <div class="md:col-span-2 space-y-4">
        <UCard v-for="(rule, index) in rules" :key="index" :class="rule.active ? 'border-l-4 border-l-indigo-500' : 'opacity-60 border-l-4 border-l-slate-300'">
          <div class="flex justify-between items-start">
            <div>
              <div class="flex items-center space-x-3 mb-2">
                <h3 class="text-lg font-bold text-slate-900">{{ rule.name }}</h3>
                <UBadge :color="rule.active ? 'green' : 'gray'" variant="subtle" size="xs">
                  {{ rule.active ? 'Active' : 'Paused' }}
                </UBadge>
              </div>
              
              <div class="space-y-2 mt-4">
                <div class="flex items-center text-sm">
                  <UIcon name="i-heroicons-tag" class="w-4 h-4 text-slate-400 mr-2" />
                  <span class="font-medium text-slate-700 w-24">Categories:</span>
                  <span class="text-slate-600">{{ rule.categories.join(', ') }}</span>
                </div>
                <div class="flex items-center text-sm">
                  <UIcon name="i-heroicons-map" class="w-4 h-4 text-slate-400 mr-2" />
                  <span class="font-medium text-slate-700 w-24">Delivery Area:</span>
                  <span class="text-slate-600">{{ rule.location }} (Max {{ rule.radius }}km)</span>
                </div>
                <div class="flex items-center text-sm">
                  <UIcon name="i-heroicons-currency-dollar" class="w-4 h-4 text-slate-400 mr-2" />
                  <span class="font-medium text-slate-700 w-24">Min Budget:</span>
                  <span class="text-slate-600">${{ rule.minBudget }}</span>
                </div>
              </div>
            </div>
            
            <div class="flex flex-col space-y-2">
              <UToggle v-model="rule.active" color="indigo" />
              <UButton color="gray" variant="ghost" size="xs" icon="i-heroicons-pencil-square" />
            </div>
          </div>
        </UCard>
      </div>

      <!-- Instructions Panel -->
      <div class="md:col-span-1">
        <UCard class="bg-indigo-50 border-indigo-100">
          <template #header>
            <h3 class="font-bold text-indigo-900 flex items-center">
              <UIcon name="i-heroicons-information-circle" class="w-5 h-5 mr-2" />
              How Triggers Work
            </h3>
          </template>
          <div class="text-sm text-indigo-800 space-y-3">
            <p>Triggers act as your automatic sales team.</p>
            <ul class="list-disc pl-5 space-y-1">
              <li>When a buyer posts a request matching your rules, you receive an instant Ping.</li>
              <li>You can set up multiple rules for different product lines or geographic areas.</li>
              <li>Setting a minimum budget helps filter out low-value requests.</li>
            </ul>
            <p class="mt-4 font-semibold">Pro Tip: Enable SMS notifications in your account settings to get pinged on your phone instantly.</p>
          </div>
        </UCard>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

definePageMeta({
  layout: 'supplier'
})

const rules = ref([
  {
    name: 'Core Cement & Steel (Cebu)',
    active: true,
    categories: ['Construction > Cement', 'Construction > Steel'],
    location: 'Mandaue City Base',
    radius: 30,
    minBudget: 500
  },
  {
    name: 'High Value Machinery (Visayas)',
    active: true,
    categories: ['Heavy Machinery', 'HVAC'],
    location: 'Mandaue City Base',
    radius: 100,
    minBudget: 5000
  },
  {
    name: 'Small Hardware Retail',
    active: false,
    categories: ['Tools', 'Fasteners'],
    location: 'Cebu City Branch',
    radius: 5,
    minBudget: 50
  }
])
</script>
