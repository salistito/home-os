<script setup lang="ts">
import { formatFoodUnit } from "../../lib/food";
import type { CookEventIngredientRow, Ingredient } from "../../types";

const props = defineProps<{
  row: CookEventIngredientRow;
  ingredients: Ingredient[];
  stockByIngredient: Map<number, { needed: number; available: number }>;
}>();
const emit = defineEmits<{ remove: [id: number] }>();

function onIngredientChange() {
  const ing = props.ingredients.find((i) => i.id === props.row.ingredient_id);
  if (ing) {
    props.row.unit = ing.unit;
    props.row.edited = true;
  } else {
    props.row.unit = "";
  }
}

function onQuantityChange() {
  props.row.edited = true;
}
</script>

<template>
  <li
    class="flex items-center gap-2 px-2 py-1.5"
  >
    <select
      v-model="row.ingredient_id"
      class="min-w-0 flex-1 rounded border border-slate-200 px-2 py-1 text-xs text-slate-700 outline-none focus:border-amber-400"
      @change="onIngredientChange"
    >
      <option :value="null">—</option>
      <option
        v-for="ing in ingredients"
        :key="ing.id"
        :value="ing.id"
      >
        {{ ing.name }}
      </option>
    </select>
    <input
      v-model.number="row.quantity"
      type="number"
      min="0"
      step="any"
      class="w-12 rounded border border-slate-200 px-1 py-1 text-xs text-slate-700 outline-none focus:border-amber-400"
      @input="onQuantityChange"
    />
    <span class="w-10 text-left text-xs text-slate-400">{{ formatFoodUnit(row.unit, row.quantity) || "—" }}</span>
    <span
      class="w-16 text-center text-xs tabular-nums"
      :class="
        stockByIngredient.get(row.ingredient_id!) != null &&
        stockByIngredient.get(row.ingredient_id!)!.needed >
          stockByIngredient.get(row.ingredient_id!)!.available
          ? 'font-medium text-red-600'
          : 'text-slate-500'
      "
    >
      <template v-if="row.ingredient_id != null && stockByIngredient.get(row.ingredient_id)">
        {{ stockByIngredient.get(row.ingredient_id)!.needed }} /
        {{ stockByIngredient.get(row.ingredient_id)!.available }}
      </template>
      <template v-else>—</template>
    </span>
    <button
      type="button"
      class="shrink-0 rounded p-0.5 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-500"
      @click="emit('remove', row.id)"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/></svg>
    </button>
  </li>
</template>
