<script setup lang="ts">
import Icon from "../../components/Icon.vue";
import Modal from "../../components/Modal.vue";
import { color } from "../../lib/colors";
import { icons } from "../../lib/icons";
import type { IngredientStock, Recipe, RecipeMacros } from "../../types";
import IngredientListRow from "./IngredientListRow.vue";
import MacroGrid from "./MacroGrid.vue";

const props = defineProps<{
  recipe: Recipe;
  macros: RecipeMacros;
  stock: IngredientStock[];
}>();
const emit = defineEmits<{ close: [] }>();

const stockByIngredient = new Map(
  props.stock.map((s) => [s.ingredient_id, s.quantity]),
);
</script>

<template>
  <Modal :title="recipe.name" @close="emit('close')">
    <div class="space-y-4">
      <div class="space-y-2">
        <div v-if="recipe.category" class="flex items-center gap-3">
          <span class="w-16 shrink-0 text-xs text-slate-500">Categoría:</span>
          <span
            class="inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium ring-1"
            :class="[color(recipe.category).bg, color(recipe.category).text, color(recipe.category).ring]"
          >
            {{ recipe.category }}
          </span>
        </div>

        <div v-if="recipe.description" class="flex items-center gap-3">
          <span class="w-16 shrink-0 text-xs text-slate-500">Descripción:</span>
          <span class="text-sm text-slate-600">{{ recipe.description }}</span>
        </div>

        <div class="flex items-center gap-3">
          <span class="w-16 shrink-0 text-xs text-slate-500">Porciones:</span>
          <span
            class="inline-flex items-center gap-1 rounded-md bg-slate-50 px-2 py-0.5 text-xs tabular-nums text-slate-700 ring-1 ring-slate-200"
          >
            <Icon :path="icons.pot" :size="12" class="shrink-0 text-slate-400" />
            {{ recipe.portions }} porc.
          </span>
        </div>
      </div>

      <div>
        <h4 class="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
          Macros por porción
        </h4>
        <MacroGrid :macros="macros" />
      </div>

      <div v-if="recipe.ingredients.length">
        <h4 class="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
          Ingredientes
        </h4>
        <ul class="divide-y divide-slate-100 rounded-lg border border-slate-100">
          <IngredientListRow
            v-for="ri in recipe.ingredients"
            :key="ri.id"
            :name="ri.ingredient?.name ?? `Ingrediente #${ri.ingredient_id}`"
            :quantity="ri.quantity"
            :stock="stockByIngredient.get(ri.ingredient_id) ?? null"
            :unit="ri.unit"
            :macros="ri.ingredient?.macros"
          />
        </ul>
      </div>

      <div v-if="recipe.steps?.length">
        <h4 class="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
          Pasos
        </h4>
        <ol class="space-y-2">
          <li
            v-for="(step, idx) in recipe.steps"
            :key="idx"
            class="flex gap-2 text-sm text-slate-600"
          >
            <span class="shrink-0 font-medium text-slate-400">{{ idx + 1 }}.</span>
            <span>{{ step }}</span>
          </li>
        </ol>
      </div>

      <div class="flex justify-end pt-2">
        <button
          type="button"
          class="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100"
          @click="emit('close')"
        >
          Cerrar
        </button>
      </div>
    </div>
  </Modal>
</template>
