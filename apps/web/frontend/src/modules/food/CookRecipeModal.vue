<script setup lang="ts">
import { computed, ref } from "vue";
import { ApiRequestError } from "../../api/client";
import { foodApi } from "../../api/food";
import Modal from "../../components/Modal.vue";
import { pushToast } from "../../lib/toast";
import type { Ingredient, IngredientStock, Recipe } from "../../types";

const props = defineProps<{
  recipe: Recipe;
  ingredients: Ingredient[];
  stock: IngredientStock[];
}>();
const emit = defineEmits<{ close: []; saved: [] }>();

const portions = ref(1);
const cookedAt = ref(new Date().toISOString().slice(0, 10));

const error = ref<string | null>(null);
const missingIds = ref<number[]>([]);
const confirming = ref(false);
const saving = ref(false);

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

function ingredientName(id: number): string {
  return props.ingredients.find((i) => i.id === id)?.name ?? `#${id}`;
}

function stockFor(ingredientId: number): number {
  const s = props.stock.find((st) => st.ingredient_id === ingredientId);
  return s?.quantity ?? 0;
}

const scale = computed(() => portions.value / props.recipe.portions);

const needed = computed(() =>
  props.recipe.ingredients.map((ri) => ({
    ...ri,
    needed: ri.quantity * scale.value,
  })),
);

const hasStock = computed(() =>
  needed.value.every((ri) => stockFor(ri.ingredient_id) >= ri.needed),
);

function askConfirm() {
  error.value = null;
  missingIds.value = [];

  if (!Number.isInteger(portions.value) || portions.value < 1) {
    error.value = "Las porciones deben ser un entero mayor que 0.";
    return;
  }

  if (!hasStock.value) {
    error.value = "Stock insuficiente para uno o más ingredientes.";
    return;
  }

  confirming.value = true;
}

async function submit() {
  confirming.value = false;
  saving.value = true;
  try {
    await foodApi.cookRecipe(props.recipe.id, {
      portions: portions.value,
      cooked_at: cookedAt.value || null,
    });
    pushToast("Cocción registrada");
    emit("saved");
  } catch (e) {
    if (e instanceof ApiRequestError && (e as unknown as { code?: string }).code === "insufficient_stock") {
      const body = (e as unknown as { body?: { missing_ingredient_ids?: number[] } }).body;
      missingIds.value = body?.missing_ingredient_ids ?? [];
      error.value = "Stock insuficiente para uno o más ingredientes.";
    } else {
      error.value = e instanceof ApiRequestError ? e.message : "Error inesperado al registrar la cocción.";
    }
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <Modal title="Registrar cocción" @close="emit('close')">
    <form v-if="!confirming" class="space-y-4" @submit.prevent="askConfirm">
      <p class="text-sm font-medium text-slate-800">{{ recipe.name }}</p>

      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">Porciones cocinadas</label>
          <input
            v-model.number="portions"
            type="number"
            min="1"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
          />
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">Fecha de cocción</label>
          <input
            v-model="cookedAt"
            type="date"
            :max="today()"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
          />
          <p class="mt-1 text-xs text-slate-400">Puede ser una fecha pasada</p>
        </div>
      </div>

      <div v-if="recipe.ingredients.length">
        <h4 class="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
          Ingredientes utilizados
        </h4>
        <ul class="divide-y divide-slate-100 rounded-lg border border-slate-100">
          <li
            v-for="ri in needed"
            :key="ri.id"
            class="flex items-center justify-between px-3 py-2 text-sm"
          >
            <span class="min-w-0 truncate text-slate-700">
              {{ ri.ingredient?.name ?? ingredientName(ri.ingredient_id) }}
            </span>
            <span
              class="whitespace-nowrap tabular-nums"
              :class="
                stockFor(ri.ingredient_id) >= ri.needed
                  ? 'text-slate-500'
                  : 'font-medium text-red-600'
              "
            >
              {{ ri.needed }} {{ ri.unit }} / {{ stockFor(ri.ingredient_id) }} {{ ri.unit }}
            </span>
          </li>
        </ul>
      </div>

      <div v-if="missingIds.length" class="rounded-lg bg-red-50 p-3">
        <p class="text-sm font-medium text-red-700">Stock insuficiente:</p>
        <ul class="mt-1 list-inside list-disc text-xs text-red-600">
          <li v-for="id in missingIds" :key="id">{{ ingredientName(id) }}</li>
        </ul>
      </div>

      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

      <div class="flex justify-end gap-2 pt-1">
        <button
          type="button"
          class="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100"
          @click="emit('close')"
        >
          Cancelar
        </button>
        <button
          type="submit"
          :disabled="saving"
          class="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-700 disabled:opacity-50"
        >
          {{ saving ? "Guardando…" : "Registrar" }}
        </button>
      </div>
    </form>

    <div v-else class="space-y-4">
      <p class="text-sm text-slate-600">
        ¿Estás seguro de registrar esta cocción?<br>
        Al confirmar se descontarán los ingredientes del stock.<br>
        Esta acción no se puede editar ni eliminar.
      </p>
      <div class="flex justify-end gap-2 pt-1">
        <button
          type="button"
          class="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100"
          @click="emit('close')"
        >
          Cancelar
        </button>
        <button
          type="button"
          class="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-700"
          @click="submit"
        >
          Confirmar
        </button>
      </div>
    </div>
  </Modal>
</template>
