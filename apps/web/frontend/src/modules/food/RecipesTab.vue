<script setup lang="ts">
import { ref } from "vue";
import { ApiRequestError } from "../../api/client";
import { foodApi } from "../../api/food";
import Icon from "../../components/Icon.vue";
import IconButton from "../../components/IconButton.vue";
import Modal from "../../components/Modal.vue";
import WidgetCard from "../../components/WidgetCard.vue";
import { icons } from "../../lib/icons";
import { pushToast } from "../../lib/toast";
import type {
  Ingredient,
  IngredientStock,
  Recipe,
  RecipeMacros,
  RecipeSummary,
} from "../../types";
import CookRecipeModal from "./CookRecipeModal.vue";
import RecipeDetailModal from "./RecipeDetailModal.vue";
import RecipeFormModal from "./RecipeFormModal.vue";

const { recipes, ingredients } = defineProps<{
  recipes: Recipe[];
  ingredients: Ingredient[];
}>();
const emit = defineEmits<{ reload: [] }>();

const stock = ref<IngredientStock[]>([]);
const formOpen = ref(false);
const editing = ref<Recipe | null>(null);

const detailRecipe = ref<Recipe | null>(null);
const detailMacros = ref<RecipeMacros | null>(null);

const cookRecipe = ref<Recipe | null>(null);

const deleting = ref<Recipe | null>(null);
const deleteBusy = ref(false);

const suggestions = ref<RecipeSummary[] | null>(null);
const suggesting = ref(false);

function openCreate() {
  editing.value = null;
  formOpen.value = true;
}

function openEdit(recipe: Recipe) {
  editing.value = recipe;
  formOpen.value = true;
}

const macroKeys = ["kcal", "protein_g", "carbs_g", "fat_g", "fiber_g"];

function computeRecipeMacros(recipe: Recipe): RecipeMacros {
  const total: Record<string, number> = {};
  for (const key of macroKeys) total[key] = 0;
  for (const ri of recipe.ingredients) {
    if (!ri.ingredient?.macros) continue;
    const m = ri.ingredient.macros;
    if (ri.unit !== m.serving_unit) continue;
    const factor = ri.quantity / m.serving_amount;
    for (const key of macroKeys) {
      const val = m[key as keyof typeof m];
      if (val != null) total[key] += Number(val) * factor;
    }
  }
  const per_portion: Record<string, number> = {};
  for (const key of macroKeys) {
    per_portion[key] = Math.round((total[key] / recipe.portions) * 100) / 100;
  }
  return { total, per_portion };
}

async function onSaved() {
  const wasEdit = editing.value != null;
  formOpen.value = false;
  editing.value = null;
  emit("reload");
  pushToast(wasEdit ? "Receta actualizada" : "Receta creada");
}

function openDetail(recipe: Recipe) {
  detailRecipe.value = recipe;
  foodApi.suggestRecipes({ limit: 50, only_with_stock: false }).then((summaries) => {
    const match = summaries.find((s) => s.recipe.id === recipe.id);
    if (match) {
      detailMacros.value = match.macros;
    } else {
      detailMacros.value = computeRecipeMacros(recipe);
    }
  }).catch(() => {
    detailMacros.value = computeRecipeMacros(recipe);
  });
}

async function openCook(recipe: Recipe) {
  if (!stock.value.length) {
    try {
      stock.value = await foodApi.listStock();
    } catch {
      stock.value = [];
    }
  }
  cookRecipe.value = recipe;
}

async function onCookSaved() {
  cookRecipe.value = null;
  emit("reload");
}

function askDelete(recipe: Recipe) {
  deleting.value = recipe;
}

async function confirmDelete() {
  if (!deleting.value) return;
  deleteBusy.value = true;
  try {
    await foodApi.deleteRecipe(deleting.value.id);
    deleting.value = null;
    emit("reload");
    pushToast("Receta eliminada");
  } catch (e) {
    pushToast(
      e instanceof ApiRequestError ? e.message : "No se pudo eliminar la receta.",
      "error",
    );
  } finally {
    deleteBusy.value = false;
  }
}

async function suggest() {
  suggesting.value = true;
  try {
    suggestions.value = await foodApi.suggestRecipes({
      limit: 5,
      only_with_stock: true,
    });
  } catch (e) {
    pushToast(
      e instanceof ApiRequestError ? e.message : "No se pudieron obtener sugerencias.",
      "error",
    );
  } finally {
    suggesting.value = false;
  }
}
</script>

<template>
  <WidgetCard title="Recetas" :count="recipes.length">
    <template #actions>
      <button
        type="button"
        :disabled="suggesting"
        class="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-50 disabled:opacity-50"
        @click="suggest"
      >
        {{ suggesting ? "Buscando…" : "Sugerir" }}
      </button>
      <button
        type="button"
        class="inline-flex items-center gap-1 rounded-lg bg-slate-900 px-2.5 py-1.5 text-xs font-medium text-white transition-colors hover:bg-slate-700"
        @click="openCreate"
      >
        <Icon :path="icons.plus" :size="14" />
        Nueva
      </button>
    </template>

    <div v-if="suggestions?.length" class="border-b border-slate-100 bg-amber-50/50 px-4 py-3">
      <h4 class="mb-2 text-xs font-semibold text-amber-700">Sugerencias</h4>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="s in suggestions"
          :key="s.recipe.id"
          type="button"
          class="inline-flex items-center gap-2 rounded-lg border border-amber-200 bg-white px-3 py-1.5 text-sm transition-colors hover:border-amber-300"
          :class="s.feasible ? 'text-slate-800' : 'text-slate-400'"
          @click="openDetail(s.recipe)"
        >
          <span>{{ s.recipe.name }}</span>
          <span class="text-xs tabular-nums text-slate-400">
            {{ Math.round(s.macros.per_portion.kcal ?? 0) }}kcal · {{ Math.round(s.macros.per_portion.protein_g ?? 0) }}P · {{ Math.round(s.macros.per_portion.carbs_g ?? 0) }}C · {{ Math.round(s.macros.per_portion.fat_g ?? 0) }}G
          </span>
          <span
            v-if="!s.feasible"
            class="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-400"
          >
            Sin stock
          </span>
        </button>
      </div>
    </div>

    <p
      v-if="!recipes.length"
      class="px-4 py-10 text-center text-sm text-slate-500"
    >
      Todavía no hay recetas.
    </p>

    <ul v-else class="divide-y divide-slate-100">
      <li
        v-for="recipe in recipes"
        :key="recipe.id"
        class="group flex items-center gap-3 px-4 py-3 transition-colors hover:bg-slate-50"
      >
        <button
          type="button"
          class="min-w-0 flex-1 text-left"
          @click="openDetail(recipe)"
        >
          <span class="block text-[13px] font-medium text-slate-800">
            {{ recipe.name }}
          </span>
          <span class="text-xs text-slate-400">
            {{ recipe.portions }} porc. · {{ recipe.ingredients.length }} ingrediente{{ recipe.ingredients.length !== 1 ? "s" : "" }}
          </span>
        </button>
        <span
          class="flex shrink-0 items-center gap-0.5 transition-opacity sm:opacity-0 sm:group-hover:opacity-100"
        >
          <IconButton :icon="icons.utensils" label="Cocinar" @click="openCook(recipe)" />
          <IconButton :icon="icons.pencil" label="Editar" @click="openEdit(recipe)" />
          <IconButton :icon="icons.trash" label="Eliminar" variant="danger" @click="askDelete(recipe)" />
        </span>
      </li>
    </ul>
  </WidgetCard>

  <RecipeFormModal
    v-if="formOpen"
    :recipe="editing"
    :ingredients="ingredients"
    @close="formOpen = false"
    @saved="onSaved"
  />

  <RecipeDetailModal
    v-if="detailRecipe && detailMacros"
    :recipe="detailRecipe"
    :macros="detailMacros"
    @close="detailRecipe = null"
  />

  <CookRecipeModal
    v-if="cookRecipe"
    :recipe="cookRecipe"
    :ingredients="ingredients"
    :stock="stock"
    @close="cookRecipe = null"
    @saved="onCookSaved"
  />

  <Modal v-if="deleting" title="Eliminar receta" @close="deleting = null">
    <p class="text-sm text-slate-600">
      ¿Seguro que quieres eliminar
      <span class="font-medium text-slate-900">{{ deleting.name }}</span>?
    </p>
    <div class="mt-5 flex justify-end gap-2">
      <button
        type="button"
        class="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100"
        @click="deleting = null"
      >
        Cancelar
      </button>
      <button
        type="button"
        :disabled="deleteBusy"
        class="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-500 disabled:opacity-50"
        @click="confirmDelete"
      >
        {{ deleteBusy ? "Eliminando…" : "Eliminar" }}
      </button>
    </div>
  </Modal>
</template>
