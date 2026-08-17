<script setup lang="ts">
import Icon from "../../components/Icon.vue";
import { formatFoodUnit } from "../../lib/food";
import { icons } from "../../lib/icons";
import type { CookEventIngredientRow, Ingredient } from "../../types";

const props = defineProps<{
  row: CookEventIngredientRow;
  ingredients: Ingredient[];
  stockByIngredient: Map<number, { needed: number; available: number }>;
  editingStock: boolean;
  stockQty: number;
  stockBusy: boolean;
  stockError: string | null;
}>();
const emit = defineEmits<{
  editStock: [];
  "update:stockQty": [value: number];
  saveStock: [];
  cancelStock: [];
  remove: [id: number];
}>();

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
  <li class="px-2 py-1.5">
    <div class="flex items-center gap-2">
      <select
        v-model="row.ingredient_id"
        class="w-0 flex-1 rounded border border-slate-200 px-2 py-1 text-xs text-slate-700 outline-none focus:border-amber-400"
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
      <span class="shrink-0 text-left text-xs text-slate-400">{{ formatFoodUnit(row.unit, row.quantity) || "—" }}</span>
      <button
        type="button"
        title="Eliminar ingrediente"
        class="shrink-0 rounded p-0.5 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-500"
        @click="emit('remove', row.id)"
      >
        <Icon :path="icons.trash" :size="14" />
      </button>
    </div>

    <div v-if="row.ingredient_id != null" class="mt-1 flex items-center gap-2 pl-1">
      <span
        class="text-xs tabular-nums"
        :class="
          (stockByIngredient.get(row.ingredient_id)?.available ?? 0) === 0
            ? 'text-red-600'
            : (stockByIngredient.get(row.ingredient_id)?.needed ?? 0) >
              (stockByIngredient.get(row.ingredient_id)?.available ?? 0)
              ? 'text-red-600'
              : 'text-slate-500'
        "
      >
        <template v-if="stockByIngredient.get(row.ingredient_id)">
          {{ stockByIngredient.get(row.ingredient_id)!.available === 0
            ? "Sin stock disponible"
            : `Stock disponible: ${stockByIngredient.get(row.ingredient_id)!.available} ${formatFoodUnit(row.unit, stockByIngredient.get(row.ingredient_id)!.available)}` }}
        </template>
        <template v-else>—</template>
      </span>
      <button
        v-if="!editingStock"
        type="button"
        class="inline-flex shrink-0 items-center gap-1 rounded-md px-1.5 py-0.5 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-100"
        @click="emit('editStock')"
      >
        <Icon :path="icons.shoppingBag" :size="12" />
        Actualizar stock
      </button>
    </div>

    <div v-if="editingStock" class="mt-2 space-y-2">
      <span class="inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-xs font-medium text-slate-600">
        <Icon :path="icons.shoppingBag" :size="12" />
        Actualizar stock
      </span>
      <div class="flex flex-wrap items-center gap-2">
        <input
          :value="stockQty"
          type="number"
          min="0"
          step="any"
          class="h-9 w-24 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100 [appearance:textfield] [&::-webkit-inner-spin-button]:m-0 [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
          @input="emit('update:stockQty', Number(($event.target as HTMLInputElement).value))"
        />
        <span class="text-xs text-slate-400">{{ formatFoodUnit(row.unit, stockQty) }}</span>
      </div>
      <p v-if="stockError" class="text-xs text-red-600">{{ stockError }}</p>
      <div class="flex items-center gap-3">
        <button
          type="button"
          class="rounded-lg px-2 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-100"
          @click="emit('cancelStock')"
        >
          Cancelar
        </button>
        <button
          type="button"
          :disabled="stockBusy"
          class="rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-slate-700 disabled:opacity-50"
          @click="emit('saveStock')"
        >
          {{ stockBusy ? "Guardando…" : "Guardar" }}
        </button>
      </div>
    </div>
  </li>
</template>
