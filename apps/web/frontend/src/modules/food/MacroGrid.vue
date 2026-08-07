<script setup lang="ts">
import { MACRO_KEYS, type RecipeMacros } from "../../types";

defineProps<{ macros: RecipeMacros }>();

const macroLabels: Record<string, string> = {
  kcal: "Calorías",
  protein_g: "Proteína (g)",
  carbs_g: "Carbos (g)",
  fat_g: "Grasa (g)",
  fiber_g: "Fibra (g)",
};
</script>

<template>
  <div class="grid grid-cols-5 gap-2">
    <div
      v-for="key in MACRO_KEYS"
      :key="key"
      class="rounded-lg bg-slate-50 py-2 text-center"
    >
      <div class="text-sm font-semibold text-slate-800">
        {{ Math.round(macros.per_portion[key] ?? 0) }}
      </div>
      <div class="text-[10px] text-slate-400">{{ macroLabels[key] }}</div>
    </div>
  </div>
</template>
