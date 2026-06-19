#!/bin/bash
mkdir -p pages/buyer/requests pages/buyer/orders pages/buyer/messages pages/buyer/ideal-list pages/buyer/settings pages/buyer/wallet
mkdir -p pages/supplier/messages pages/supplier/payouts pages/supplier/reviews pages/supplier/settings
mkdir -p pages/admin/users pages/admin/risk pages/admin/categories pages/admin/pricing-intel pages/admin/settings
mkdir -p pages/how-it-works pages/categories pages/supplier-onboarding pages/trust-safety pages/pricing

TEMPLATE="<template>
  <div class=\"flex flex-col items-center justify-center py-20 text-center\">
    <UIcon name=\"i-heroicons-wrench-screwdriver\" class=\"w-16 h-16 text-indigo-300 mb-4\" />
    <h1 class=\"text-2xl font-bold text-slate-800 mb-2\">Module in Development</h1>
    <p class=\"text-slate-500 max-w-md\">This section is part of the expanded roadmap and is currently under construction.</p>
    <UButton to=\"/\" color=\"indigo\" class=\"mt-6\">Return</UButton>
  </div>
</template>
"

for file in pages/buyer/requests/index.vue pages/buyer/orders/index.vue pages/buyer/messages.vue pages/buyer/ideal-list.vue pages/buyer/settings.vue pages/buyer/wallet.vue \
pages/supplier/messages.vue pages/supplier/payouts.vue pages/supplier/reviews.vue pages/supplier/settings.vue \
pages/admin/users.vue pages/admin/risk.vue pages/admin/categories.vue pages/admin/pricing-intel.vue pages/admin/settings.vue \
pages/how-it-works.vue pages/categories.vue pages/supplier-onboarding.vue pages/trust-safety.vue pages/pricing.vue; do
  if [ ! -f "$file" ]; then
    echo "$TEMPLATE" > "$file"
  fi
done
