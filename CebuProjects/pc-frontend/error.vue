<template>
  <div class="min-h-screen bg-slate-50 flex flex-col items-center justify-center px-6 text-center">
    <div class="text-6xl mb-4">{{ error?.statusCode === 404 ? "🔍" : "⚠️" }}</div>
    <h1 class="text-2xl font-bold text-slate-900 mb-2">
      {{ error?.statusCode === 404 ? "Page not found" : "Something went wrong" }}
    </h1>
    <p class="text-slate-500 text-sm mb-8">
      {{ error?.statusCode === 404
        ? "The page you're looking for doesn't exist."
        : "An unexpected error occurred. Please try again." }}
    </p>
    <button class="btn-primary w-auto px-8 py-3" @click="handleError">Go Home</button>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ error: { statusCode?: number; message?: string } | null }>();

function handleError() {
  clearError({ redirect: "/" });
}
</script>
