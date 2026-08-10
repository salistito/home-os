<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { foodApi } from "../../api/food";
import ActionBar from "../../components/ActionBar.vue";
import Icon from "../../components/Icon.vue";
import Skeleton from "../../components/Skeleton.vue";
import { icons } from "../../lib/icons";
import type { Ingredient, IngredientPurchase, IngredientStock, Recipe } from "../../types";
import CookEventsTab from "./CookEventsTab.vue";
import IngredientsTab from "./IngredientsTab.vue";
import MealsTab from "./MealsTab.vue";
import PurchasesTab from "./PurchasesTab.vue";
import RecipesTab from "./RecipesTab.vue";
import StockTab from "./StockTab.vue";

const tabs = [
  { id: "meals", label: "Alimentación" },
  { id: "cook-events", label: "Cocciones" },
  { id: "recipes", label: "Recetas" },
  { id: "purchases", label: "Compras" },
  { id: "stock", label: "Stock" },
  { id: "ingredients", label: "Ingredientes" },
];

const primaryActions: Record<string, string> = {
  meals: "Registrar comida",
  "cook-events": "Registrar cocción",
  recipes: "Crear receta",
  purchases: "Registrar compra",
  ingredients: "Crear ingrediente",
};

const activeTab = ref("meals");
const activeTabRef = ref<{ openCreate: () => void } | null>(null);
const primaryAction = computed(() => primaryActions[activeTab.value]);

function runPrimaryAction() {
  activeTabRef.value?.openCreate();
}
const loading = ref(true);
const error = ref<string | null>(null);

const ingredients = ref<Ingredient[]>([]);
const stock = ref<IngredientStock[]>([]);
const purchases = ref<IngredientPurchase[]>([]);
const recipes = ref<Recipe[]>([]);

async function load() {
  try {
    await reloadAll();
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Error inesperado";
  } finally {
    loading.value = false;
  }
}

async function reloadAll() {
  const [ings, stk, pur, recs] = await Promise.all([
    foodApi.listIngredients(),
    foodApi.listStock(),
    foodApi.listPurchases(),
    foodApi.listRecipes(),
  ]);
  ingredients.value = ings;
  stock.value = stk;
  purchases.value = pur;
  recipes.value = recs;
}

onMounted(load);
</script>

<template>
  <div class="mx-auto max-w-5xl space-y-4">
    <p v-if="error" class="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-600">
      {{ error }}
    </p>

    <div v-else-if="loading" class="space-y-4">
      <div class="flex gap-4 border-b border-slate-200 pb-2">
        <Skeleton width="5rem" height="1.5rem" />
        <Skeleton width="4rem" height="1.5rem" />
        <Skeleton width="5rem" height="1.5rem" />
        <Skeleton width="5rem" height="1.5rem" />
        <Skeleton width="5rem" height="1.5rem" />
      </div>
      <div class="divide-y divide-slate-100 rounded-xl border border-slate-200 bg-white">
        <div v-for="n in 4" :key="n" class="flex items-center gap-3 px-4 py-3">
          <Skeleton width="8rem" class="flex-1" />
          <Skeleton width="4rem" />
          <Skeleton width="3rem" />
          <Skeleton width="2rem" />
        </div>
      </div>
    </div>

    <template v-else>
      <nav class="flex gap-5 overflow-x-auto overflow-y-hidden border-b border-slate-200 sm:gap-6">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="-mb-px flex shrink-0 items-center gap-1.5 border-b-2 py-2.5 text-sm transition-colors sm:pb-2 sm:pt-0"
          :class="
            activeTab === tab.id
              ? 'border-slate-900 font-medium text-slate-900'
              : 'border-transparent text-slate-400 hover:text-slate-600'
          "
          @click="activeTab = tab.id"
        >
          {{ tab.label }}
        </button>
      </nav>

      <Transition
        mode="out-in"
        enter-from-class="opacity-0"
        leave-to-class="opacity-0"
        enter-active-class="transition-opacity duration-150"
        leave-active-class="transition-opacity duration-75"
      >
        <div :key="activeTab">
          <MealsTab
            v-if="activeTab === 'meals'"
            ref="activeTabRef"
            :recipes="recipes"
            :stock="stock"
            :ingredients="ingredients"
          />
          <CookEventsTab
            v-else-if="activeTab === 'cook-events'"
            ref="activeTabRef"
            :recipes="recipes"
            :ingredients="ingredients"
            :stock="stock"
            @reload="reloadAll"
          />
          <RecipesTab
            v-else-if="activeTab === 'recipes'"
            ref="activeTabRef"
            :recipes="recipes"
            :ingredients="ingredients"
            @reload="reloadAll"
          />
          <PurchasesTab
            v-else-if="activeTab === 'purchases'"
            ref="activeTabRef"
            :purchases="purchases"
            :ingredients="ingredients"
            @reload="reloadAll"
          />
          <StockTab
            v-else-if="activeTab === 'stock'"
            :ingredients="ingredients"
            :stock="stock"
            @reload="reloadAll"
          />
          <IngredientsTab
            v-else-if="activeTab === 'ingredients'"
            ref="activeTabRef"
            :ingredients="ingredients"
            @reload="reloadAll"
          />
        </div>
      </Transition>

      <ActionBar>
        <Transition
          appear
          enter-from-class="translate-y-3 opacity-0"
          enter-active-class="transition duration-300 ease-out"
        >
          <button
            v-if="primaryAction"
            type="button"
            class="flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-slate-900 text-sm font-semibold text-white shadow-sm transition active:scale-[0.98] active:bg-slate-700"
            @click="runPrimaryAction"
          >
            <Icon :path="icons.plus" :size="18" />
            <Transition
              mode="out-in"
              enter-from-class="opacity-0"
              leave-to-class="opacity-0"
              enter-active-class="transition-opacity duration-100"
              leave-active-class="transition-opacity duration-75"
            >
              <span :key="primaryAction">{{ primaryAction }}</span>
            </Transition>
          </button>
        </Transition>
      </ActionBar>
    </template>
  </div>
</template>
