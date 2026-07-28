<script setup lang="ts">
import Modal from "../../components/Modal.vue";
import type { Recipe, RecipeMacros } from "../../types";

defineProps<{
  recipe: Recipe;
  macros: RecipeMacros;
}>();
const emit = defineEmits<{ close: [] }>();

const macroKeys = ["kcal", "protein_g", "carbs_g", "fat_g", "fiber_g"];

const macroLabels: Record<string, string> = {
  kcal: "Calorías",
  protein_g: "Proteína (g)",
  carbs_g: "Carbos (g)",
  fat_g: "Grasa (g)",
  fiber_g: "Fibra (g)",
};
</script>

<template>
  <Modal :title="recipe.name" @close="emit('close')">
    <div class="space-y-4">
      <div v-if="recipe.category">
        <span class="text-xs text-slate-400">Categoría:</span>
        <span class="ml-1 text-sm font-medium text-slate-800">{{ recipe.category }}</span>
      </div>

      <div v-if="recipe.description">
        <span class="text-xs text-slate-400">Descripción:</span>
        <span class="ml-1 text-sm font-medium text-slate-800">{{ recipe.description }}</span>
      </div>

      <div>
        <span class="text-xs text-slate-400">Porciones:</span>
        <span class="ml-1 text-sm font-medium text-slate-800">{{ recipe.portions }}</span>
      </div>

      <div>
        <h4 class="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
          Macros por porción
        </h4>
        <div class="grid grid-cols-5 gap-2">
          <div
            v-for="key in macroKeys"
            :key="key"
            class="rounded-lg bg-slate-50 py-2 text-center"
          >
            <div class="text-sm font-semibold text-slate-800">
              {{ Math.round(macros.per_portion[key] ?? 0) }}
            </div>
            <div class="text-[10px] text-slate-400">{{ macroLabels[key] }}</div>
          </div>
        </div>
      </div>

      <div v-if="recipe.ingredients.length">
        <h4 class="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
          Ingredientes
        </h4>
        <ul class="divide-y divide-slate-100 rounded-lg border border-slate-100">
          <li
            v-for="ri in recipe.ingredients"
            :key="ri.id"
            class="px-3 py-2 text-sm"
          >
            <div class="flex items-center justify-between">
              <span class="text-slate-700">
                {{ ri.ingredient?.name ?? `Ingrediente #${ri.ingredient_id}` }}
              </span>
              <span class="tabular-nums text-slate-500">
                {{ ri.quantity }} {{ ri.unit }}
              </span>
            </div>
            <div
              v-if="ri.ingredient?.macros && ri.unit === ri.ingredient.macros.serving_unit"
              class="mt-0.5 text-xs text-slate-400"
            >
              <span class="font-medium text-slate-500">
                {{ Math.round(ri.ingredient.macros.kcal * ri.quantity / ri.ingredient.macros.serving_amount) }}kcal · {{ Math.round(ri.ingredient.macros.protein_g * ri.quantity / ri.ingredient.macros.serving_amount) }}P · {{ Math.round(ri.ingredient.macros.carbs_g * ri.quantity / ri.ingredient.macros.serving_amount) }}C · {{ Math.round(ri.ingredient.macros.fat_g * ri.quantity / ri.ingredient.macros.serving_amount) }}G
              </span>
            </div>
          </li>
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
