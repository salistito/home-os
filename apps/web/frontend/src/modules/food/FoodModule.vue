<script setup lang="ts">
import { onMounted, ref } from "vue";
import { foodApi } from "../../api/food";
import Skeleton from "../../components/Skeleton.vue";
import { icons } from "../../lib/icons";
import type { Ingredient, IngredientPurchase, IngredientStock, Recipe } from "../../types";
import CookEventsTab from "./CookEventsTab.vue";
import IngredientsTab from "./IngredientsTab.vue";
import PurchasesTab from "./PurchasesTab.vue";
import RecipesTab from "./RecipesTab.vue";
import StockTab from "./StockTab.vue";

const activeTab = ref("ingredients");
const loading = ref(true);
const error = ref<string | null>(null);

const ingredients = ref<Ingredient[]>([]);
const stock = ref<IngredientStock[]>([]);
const purchases = ref<IngredientPurchase[]>([]);
const recipes = ref<Recipe[]>([]);

const tabs = [
  { id: "ingredients", label: "Ingredientes", icon: icons.list },
  { id: "stock", label: "Stock", icon: icons.shoppingBag },
  { id: "purchases", label: "Compras", icon: icons.wallet },
  { id: "recipes", label: "Recetas", icon: icons.utensils },
  { id: "cook-events", label: "Cocciones", icon: icons.clock },
];

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
  const [ings, stk, recs, pur] = await Promise.all([
    foodApi.listIngredients(),
    foodApi.listStock(),
    foodApi.listRecipes(),
    foodApi.listPurchases(),
  ]);
  ingredients.value = ings;
  stock.value = stk;
  recipes.value = recs;
  purchases.value = pur;
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
      <nav class="flex gap-6 border-b border-slate-200">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="-mb-px flex items-center gap-1.5 border-b-2 pb-2 text-sm transition-colors"
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

      <IngredientsTab
        v-if="activeTab === 'ingredients'"
        :ingredients="ingredients"
        @reload="reloadAll"
      />
      <StockTab
        v-else-if="activeTab === 'stock'"
        :ingredients="ingredients"
        :stock="stock"
        @reload="reloadAll"
      />
      <PurchasesTab
        v-else-if="activeTab === 'purchases'"
        :purchases="purchases"
        :ingredients="ingredients"
        @reload="reloadAll"
      />
      <RecipesTab
        v-else-if="activeTab === 'recipes'"
        :recipes="recipes"
        :ingredients="ingredients"
        @reload="reloadAll"
      />
      <CookEventsTab
        v-else-if="activeTab === 'cook-events'"
        :recipes="recipes"
      />
    </template>
  </div>
</template>
