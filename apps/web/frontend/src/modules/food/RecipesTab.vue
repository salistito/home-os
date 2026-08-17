<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { ApiRequestError } from "../../api/client";
import { foodApi } from "../../api/food";
import FilterModal from "../../components/FilterModal.vue";
import Icon from "../../components/Icon.vue";
import IconButton from "../../components/IconButton.vue";
import Modal from "../../components/Modal.vue";
import SearchBar from "../../components/SearchBar.vue";
import WidgetCard from "../../components/WidgetCard.vue";
import { color } from "../../lib/colors";
import { icons } from "../../lib/icons";
import { pushToast } from "../../lib/toast";
import type {
  Ingredient,
  IngredientStock,
  Recipe,
  RecipeMacros,
  RecipeSummary,
  UserRef
} from "../../types";
import CookRecipeModal from "./CookRecipeModal.vue";
import RecipeDetailModal from "./RecipeDetailModal.vue";
import RecipeFormModal from "./RecipeFormModal.vue";

const { recipes, ingredients, users } = defineProps<{
  recipes: Recipe[];
  ingredients: Ingredient[];
  users: UserRef[];
}>();
const emit = defineEmits<{ reload: [] }>();

const suggesting = ref(false);
const suggestions = ref<RecipeSummary[] | null>(null);

const searchQuery = ref("");
const showFilters = ref(false);

type SortColumn = "name" | "category" | "portions" | "macros" | "feasible"
const sortBy = ref<SortColumn>("name");
const sortOrder = ref<"asc" | "desc">("asc");
const sortColumns = [
  { value: "name", label: "Receta" },
  { value: "category", label: "Categoría" },
  { value: "portions", label: "Porciones" },
  { value: "macros", label: "Macros/porc." },
  { value: "feasible", label: "Estado" },
];

const availableCategories = computed(() => {
  const categories = new Set<string>();
  for (const r of recipes) {
    if (r.category) categories.add(r.category);
  }
  return [...categories].sort((a, b) => a.localeCompare(b, undefined, { sensitivity: "base" }));
});
const categoryOptions = computed(() => [
  { value: "all", label: "Todas las categorías" },
  ...availableCategories.value.map((c) => ({ value: c, label: c })),
]);

const categoryFilter = ref<string | null>(null);
watch(categoryFilter, () => { suggestions.value = null; });

const stock = ref<IngredientStock[]>([]);
const stockLoading = ref(true);
async function loadStock() {
  try { stock.value = await foodApi.listStock(); } catch { /* ignore */ }
  stockLoading.value = false;
}

const detailRecipe = ref<Recipe | null>(null);
const detailMacros = ref<RecipeMacros | null>(null);

const formOpen = ref(false);
const cookRecipe = ref<Recipe | null>(null);
const editing = ref<Recipe | null>(null);
const deleting = ref<Recipe | null>(null);
const deleteBusy = ref(false);

function openFilters() {
  showFilters.value = true;
}

function applySort(value: { sortBy: string; sortOrder: string }) {
  sortBy.value = value.sortBy as SortColumn;
  sortOrder.value = value.sortOrder as "asc" | "desc";
}

function applyCategoryFilter(value: { key: string; value: string }) {
  categoryFilter.value = value.value === "all" ? null : value.value;
}

function setSort(col: SortColumn) {
  if (sortBy.value === col) {
    sortOrder.value = sortOrder.value === "asc" ? "desc" : "asc";
  } else {
    sortBy.value = col;
    sortOrder.value = "asc";
  }
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

const macroDisplay = computed(() => {
  const map = new Map<number, string>();
  for (const r of recipes) {
    const pp = computeRecipeMacros(r).per_portion;
    const kcal = Math.round(pp.kcal ?? 0);
    const protein = Math.round(pp.protein_g ?? 0);
    const carbs = Math.round(pp.carbs_g ?? 0);
    const fat = Math.round(pp.fat_g ?? 0);
    const fiber = Math.round(pp.fiber_g ?? 0);
    if (kcal || protein || carbs || fat || fiber) {
      map.set(r.id, `${kcal}kcal · ${protein}P · ${carbs}C · ${fat}G · ${fiber}F`);
    }
  }
  return map;
});

function isRecipeFeasible(recipe: Recipe): boolean {
  const stockMap = new Map(stock.value.map((s) => [s.ingredient_id, s]));
  for (const ri of recipe.ingredients) {
    const s = stockMap.get(ri.ingredient_id);
    if (!s || s.quantity < ri.quantity) return false;
  }
  return recipe.ingredients.length > 0;
}

const feasibilityMap = computed(() => {
  const map = new Map<number, boolean>();
  for (const r of recipes) map.set(r.id, isRecipeFeasible(r));
  return map;
});

const hasFeasibleRecipes = computed(() => {
  for (const r of filteredRecipes.value) {
    if (feasibilityMap.value.get(r.id)) return true;
  }
  return false;
});

const filteredBySearch = computed(() => {
  const term = searchQuery.value.trim().toLowerCase();
  if (!term) return recipes;
  return recipes.filter((r) => r.name.toLowerCase().includes(term));
});

const filteredRecipes = computed(() => {
  if (!categoryFilter.value) return filteredBySearch.value;
  return filteredBySearch.value.filter((r) => r.category === categoryFilter.value);
});

const sortedRecipes = computed(() => {
  const dir = sortOrder.value === "asc" ? 1 : -1;
  return [...filteredRecipes.value].sort((a, b) => {
    let cmp = 0;
    switch (sortBy.value) {
      case "name":
        cmp = a.name.localeCompare(b.name, undefined, { sensitivity: "base" });
        break;
      case "category": {
        const ca = a.category ?? "";
        const cb = b.category ?? "";
        if (ca && cb) {
          cmp = ca.localeCompare(cb, undefined, { sensitivity: "base" });
        } else if (ca) {
          cmp = -dir;
        } else if (cb) {
          cmp = dir;
        } else {
          cmp = 0;
        }
        break;
      }
      case "portions":
        cmp = a.portions - b.portions;
        break;
      case "macros": {
        const ma = computeRecipeMacros(a);
        const mb = computeRecipeMacros(b);
        cmp = (ma.per_portion.kcal ?? 0) - (mb.per_portion.kcal ?? 0);
        break;
      }
      case "feasible":
        cmp = (feasibilityMap.value.get(a.id) ? 0 : 1) - (feasibilityMap.value.get(b.id) ? 0 : 1);
        break;
    }
    if (cmp === 0) {
      cmp = a.name.localeCompare(b.name, undefined, { sensitivity: "base" });
    }
    return cmp * dir;
  });
});

interface TableRow {
  recipe: Recipe;
  isSuggestion: boolean;
  macroStr: string;
  feasible: boolean;
}

const tableRows = computed(() => {
  const seen = new Set<number>();
  const rows: TableRow[] = [];

  for (const s of suggestions.value ?? []) {
    if (!seen.has(s.recipe.id)) {
      seen.add(s.recipe.id);
      const pp = s.macros.per_portion;
      const kcal = Math.round(pp.kcal ?? 0);
      const protein = Math.round(pp.protein_g ?? 0);
      const carbs = Math.round(pp.carbs_g ?? 0);
      const fat = Math.round(pp.fat_g ?? 0);
      const fiber = Math.round(pp.fiber_g ?? 0);
      const macroStr = (kcal || protein || carbs || fat || fiber)
        ? `${kcal}kcal · ${protein}P · ${carbs}C · ${fat}G · ${fiber}F`
        : "";
      rows.push({
        recipe: s.recipe,
        isSuggestion: true,
        macroStr,
        feasible: s.feasible,
      });
    }
  }

  for (const r of sortedRecipes.value) {
    if (!seen.has(r.id)) {
      rows.push({
        recipe: r,
        isSuggestion: false,
        macroStr: macroDisplay.value.get(r.id) ?? "",
        feasible: feasibilityMap.value.get(r.id) ?? false,
      });
    }
  }

  return rows;
});

function openCreate() {
  editing.value = null;
  formOpen.value = true;
}

async function suggest() {
  suggesting.value = true;
  try {
    suggestions.value = await foodApi.suggestRecipes({
      limit: 5,
      only_with_stock: true,
      category: categoryFilter.value ?? undefined,
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

function openEdit(recipe: Recipe) {
  editing.value = recipe;
  formOpen.value = true;
}

async function onSaved() {
  const wasEdit = editing.value != null;
  formOpen.value = false;
  editing.value = null;
  emit("reload");
  pushToast(wasEdit ? "Receta actualizada" : "Receta creada");
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
defineExpose({ openCreate });

onMounted(loadStock);
</script>

<template>
  <WidgetCard title="Recetas" :count="recipes.length">
    <template #actions>
      <button
        type="button"
        class="hidden items-center gap-1 rounded-lg bg-slate-900 px-2.5 py-1.5 text-xs font-medium text-white transition-colors hover:bg-slate-700 lg:inline-flex"
        @click="openCreate"
      >
        <Icon :path="icons.plus" :size="14" />
        Crear receta
      </button>
    </template>

    <template #filter>
      <SearchBar v-model="searchQuery" placeholder="Buscar receta…" />
      <span class="relative">
        <IconButton :icon="icons.filter" label="Filtros" @click="openFilters" />
      </span>
    </template>


    <p
      v-if="!recipes.length"
      class="px-4 py-10 text-center text-sm text-slate-500"
    >
      Todavía no hay recetas registradas.
    </p>

    <div v-else>
      <div class="flex flex-wrap items-center justify-start gap-2 px-4 py-3 sm:justify-end">
        <button
          v-if="!stockLoading && hasFeasibleRecipes"
          type="button"
          :disabled="suggesting"
          class="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-50 disabled:opacity-50"
          @click="suggest"
        >
          {{ suggesting ? "Buscando…" : suggestions?.length ? "Actualizar sugerencias" : "Buscar sugerencias" }}
        </button>
      </div>

      <div
        class="hidden grid-cols-[1fr_8rem_6rem_12rem_6rem_7rem] items-center gap-2 border-b border-slate-100 bg-slate-50/60 px-4 py-2 text-xs font-semibold tracking-wider text-slate-400 sm:grid"
      >
        <button type="button" class="flex items-center gap-1 text-left" @click="setSort('name')">
          Receta
          <span v-if="sortBy === 'name'">{{ sortOrder === "asc" ? "↑": "↓" }}</span>
        </button>
        <button type="button" class="flex items-center gap-1" @click="setSort('category')">
          Categoría
          <span v-if="sortBy === 'category'">{{ sortOrder === "asc" ? "↑": "↓" }}</span>
        </button>
        <button type="button" class="flex items-center gap-1" @click="setSort('portions')">
          Porciones
          <span v-if="sortBy === 'portions'">{{ sortOrder === "asc" ? "↑": "↓" }}</span>
        </button>
        <button type="button" class="flex items-center gap-1" @click="setSort('macros')">
          Macros por porción
          <span v-if="sortBy === 'macros'">{{ sortOrder === "asc" ? "↑": "↓" }}</span>
        </button>
        <button type="button" class="flex items-center gap-1" @click="setSort('feasible')">
          Estado
          <span v-if="sortBy === 'feasible'">{{ sortOrder === "asc" ? "↑": "↓" }}</span>
        </button>
        <span></span>
      </div>

      <ul class="divide-y divide-slate-100">
        <li
          v-for="row in tableRows"
          :key="row.recipe.id"
           class="group flex cursor-pointer items-start gap-3 px-4 py-3 transition-colors sm:grid sm:grid-cols-[1fr_8rem_6rem_12rem_6rem_7rem] sm:items-center sm:gap-2 sm:py-2.5"
          :class="row.isSuggestion ? 'bg-amber-50/50 hover:bg-amber-100/50' : 'hover:bg-slate-50'"
          @click="openDetail(row.recipe)"
        >
          <div class="min-w-0 flex-1 sm:contents">
            <span class="block truncate text-[13px] font-medium text-slate-800">
              {{ row.recipe.name }}
            </span>

            <div class="sm:contents">
              <div class="mt-1.5 flex flex-wrap items-center gap-2 sm:contents">
                <span
                  v-if="row.recipe.category"
                  class="inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium ring-1 sm:justify-self-start"
                  :class="[color(row.recipe.category).bg, color(row.recipe.category).text, color(row.recipe.category).ring]"
                >
                  {{ row.recipe.category }}
                </span>
                <span v-else class="hidden text-xs text-slate-400 sm:inline sm:ml-6.5">—</span>

                <span class="inline-flex items-center gap-1 rounded-md bg-slate-50 px-2 py-0.5 text-xs tabular-nums text-slate-700 ring-1 ring-slate-200 sm:justify-self-start">
                  <Icon :path="icons.pot" :size="12" class="shrink-0 text-slate-400" />
                  {{ row.recipe.portions }} porc.
                </span>
              </div>

              <div class="mt-1 flex flex-wrap items-center gap-2 sm:contents">
                <span class="text-xs text-slate-600 sm:justify-self-start">
                  {{ row.macroStr || "—" }}
                </span>
              </div>

              <div class="mt-1 flex flex-wrap items-center gap-2 sm:contents">
                <span class="inline-flex flex-wrap items-center gap-1 sm:justify-self-start">
                  <span
                    v-if="row.isSuggestion"
                    class="hidden sm:inline-flex items-center gap-1 rounded-md bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700 ring-1 ring-amber-100"
                  >
                    <Icon :path="icons.star" :size="12" />
                    Sugerencia
                  </span>
                  <span
                    v-if="row.feasible"
                    class="inline-flex items-center gap-1 rounded-md bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700 ring-1 ring-emerald-100"
                  >
                    <Icon :path="icons.check" :size="12" />
                    Con stock
                  </span>
                  <span
                    v-else
                    class="inline-flex items-center gap-1 rounded-md bg-red-50 px-2 py-0.5 text-xs font-medium text-red-700 ring-1 ring-red-100"
                  >
                    <Icon :path="icons.close" :size="12" />
                    Sin stock
                  </span>
                </span>
              </div>
            </div>
          </div>
          <span class="flex items-center gap-1">
            <span
              v-if="row.isSuggestion"
              class="sm:hidden inline-flex items-center gap-1 rounded-md bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700 ring-1 ring-amber-100"
            >
              <Icon :path="icons.star" :size="12" />
              Sugerencia
            </span>
            <span
              class="ml-auto flex shrink-0 items-center gap-0.5 transition-opacity sm:opacity-0 sm:group-hover:opacity-100"
              @click.stop
            >
              <IconButton :icon="icons.pot" label="Cocinar" @click="openCook(row.recipe)" />
              <IconButton :icon="icons.pencil" label="Editar" @click="openEdit(row.recipe)" />
              <IconButton :icon="icons.trash" label="Eliminar" variant="danger" @click="askDelete(row.recipe)" />
            </span>
          </span>
        </li>
      </ul>
    </div>
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
    :stock="stock"
    @close="detailRecipe = null"
  />

  <CookRecipeModal
    v-if="cookRecipe"
    :recipe="cookRecipe"
    :ingredients="ingredients"
    :stock="stock"
    :users="users"
    @reload="loadStock"
    @close="cookRecipe = null"
    @saved="onCookSaved"
  />

  <Modal v-if="deleting" title="Eliminar receta" @close="deleting = null">
    <p class="text-sm text-slate-600">
      ¿Seguro que quieres eliminar la receta
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

  <FilterModal
    :show="showFilters"
    title="Filtros de recetas"
    :columns="sortColumns"
    :current-sort-by="sortBy"
    :current-sort-order="sortOrder"
    :filters="[{ key: 'category', label: 'Categoría', options: categoryOptions }]"
    :current-filters="{ category: categoryFilter ?? 'all' }"
    @update:show="showFilters = $event"
    @apply:sort="applySort"
    @apply:filter="applyCategoryFilter"
  />
</template>
