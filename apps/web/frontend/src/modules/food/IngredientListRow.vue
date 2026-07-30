<script setup lang="ts">
import type { IngredientMacros } from "../../types";

defineProps<{
  name: string;
  quantity: number;
  unit: string;
  macros?: IngredientMacros | null;
}>();
</script>

<template>
  <li class="px-3 py-2 text-sm">
    <div class="flex items-center justify-between">
      <span class="text-slate-700">{{ name }}</span>
      <span class="tabular-nums text-slate-500">{{ quantity }} {{ unit }}</span>
    </div>
    <div
      v-if="macros && unit === macros.serving_unit"
      class="mt-0.5 text-xs text-slate-500"
    >
      <span class="font-medium text-slate-500">
        {{ Math.round(macros.kcal * quantity / macros.serving_amount) }}kcal
        · {{ Math.round(macros.protein_g * quantity / macros.serving_amount) }}P
        · {{ Math.round(macros.carbs_g * quantity / macros.serving_amount) }}C
        · {{ Math.round(macros.fat_g * quantity / macros.serving_amount) }}G
      </span>
    </div>
  </li>
</template>
