<script setup lang="ts">
import Modal from "../../components/Modal.vue";
import type { Recipe, RecipeMacros } from "../../types";
import IngredientListRow from "./IngredientListRow.vue";
import MacroGrid from "./MacroGrid.vue";

defineProps<{
  recipe: Recipe;
  macros: RecipeMacros;
}>();
const emit = defineEmits<{ close: [] }>();
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
