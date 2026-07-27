<script setup lang="ts">
import { computed, ref } from "vue";
import { ApiRequestError } from "../../api/client";
import { foodApi } from "../../api/food";
import Modal from "../../components/Modal.vue";
import type { ExternalSearchResult, FoodUnit, Ingredient, IngredientMacros } from "../../types";

const props = defineProps<{
  ingredient?: Ingredient | null;
  importMode?: boolean;
}>();
const emit = defineEmits<{ close: []; saved: [] }>();

const isEdit = computed(() => props.ingredient != null);
const showImport = ref(props.importMode ?? false);

const name = ref(props.ingredient?.name ?? "");
const category = ref(props.ingredient?.category ?? "");
const unit = ref<FoodUnit>(props.ingredient?.unit ?? "g");

const servingAmount = ref(props.ingredient?.macros.serving_amount ?? 100);
const servingUnit = ref(props.ingredient?.macros.serving_unit ?? "g");
const kcal = ref(props.ingredient?.macros.kcal ?? 0);
const proteinG = ref(props.ingredient?.macros.protein_g ?? 0);
const carbsG = ref(props.ingredient?.macros.carbs_g ?? 0);
const fatG = ref(props.ingredient?.macros.fat_g ?? 0);
const fiberG = ref(props.ingredient?.macros.fiber_g ?? 0);

const searchQuery = ref("");
const searching = ref(false);
const searchError = ref<string | null>(null);
const searchResults = ref<ExternalSearchResult[]>([]);

const error = ref<string | null>(null);
const saving = ref(false);

const unitOptions = [
  { value: "g", label: "Gramos (g)" },
  { value: "ml", label: "Mililitros (ml)" },
  { value: "unit", label: "Unidad" },
  { value: "tablespoon", label: "Cucharada" },
];

async function searchOff() {
  if (!searchQuery.value.trim()) return;
  searching.value = true;
  searchError.value = null;
  searchResults.value = [];
  try {
    const results = await foodApi.searchExternal(searchQuery.value.trim());
    if (results.length === 0) {
      searchError.value = "No se encontraron resultados en Open Food Facts.";
    } else {
      searchResults.value = results;
    }
  } catch (e) {
    searchError.value =
      e instanceof ApiRequestError
        ? e.message
        : "No se pudo buscar en Open Food Facts.";
  } finally {
    searching.value = false;
  }
}

function pickResult(result: ExternalSearchResult) {
  name.value = result.name;
  if (result.macros) {
    servingAmount.value = result.macros.serving_amount;
    servingUnit.value = result.macros.serving_unit;
    kcal.value = result.macros.kcal;
    proteinG.value = result.macros.protein_g;
    carbsG.value = result.macros.carbs_g;
    fatG.value = result.macros.fat_g;
    fiberG.value = result.macros.fiber_g;
  }
  searchResults.value = [];
  showImport.value = false;
}

function buildMacros(): IngredientMacros {
  return {
    serving_amount: servingAmount.value,
    serving_unit: servingUnit.value,
    kcal: kcal.value,
    protein_g: proteinG.value,
    carbs_g: carbsG.value,
    fat_g: fatG.value,
    fiber_g: fiberG.value,
  };
}

async function submit() {
  error.value = null;

  if (!name.value.trim()) {
    error.value = "El nombre es obligatorio.";
    return;
  }
  if (servingAmount.value <= 0) {
    error.value = "La cantidad de referencia debe ser mayor a 0.";
    return;
  }

  const macros = buildMacros();
  if (Object.values(macros).some((v) => typeof v === "number" && v < 0)) {
    error.value = "Los valores de macros no pueden ser negativos.";
    return;
  }

  saving.value = true;
  try {
    if (props.ingredient) {
      await foodApi.updateIngredient(props.ingredient.id, {
        name: name.value.trim(),
        category: category.value.trim() || null,
        unit: unit.value,
        macros,
      });
    } else {
      await foodApi.createIngredient({
        name: name.value.trim(),
        category: category.value.trim() || null,
        unit: unit.value,
        macros,
      });
    }
    emit("saved");
  } catch (e) {
    error.value =
      e instanceof ApiRequestError ? e.message : "Error inesperado al guardar.";
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <Modal :title="isEdit ? 'Editar ingrediente' : 'Nuevo ingrediente'" @close="emit('close')">
    <form class="space-y-4" @submit.prevent="submit">
      <div v-if="!isEdit" class="rounded-lg border border-amber-200 bg-amber-50 p-3">
        <button
          type="button"
          class="flex items-center gap-2 text-sm font-medium text-amber-700"
          @click="showImport = !showImport"
        >
          {{ showImport ? "Ocultar búsqueda" : "Buscar en Open Food Facts" }}
        </button>
        <div v-if="showImport" class="mt-2 flex gap-2">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Nombre del ingrediente..."
            class="flex-1 rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-800 outline-none focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
            @keydown.enter.prevent="searchOff"
          />
          <button
            type="button"
            :disabled="searching"
            class="inline-flex items-center gap-1 rounded-lg bg-amber-500 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-amber-600 disabled:opacity-50"
            @click="searchOff"
          >
            {{ searching ? "Buscando…" : "Buscar" }}
          </button>
        </div>
        <p v-if="searchError" class="mt-2 text-xs text-red-600">{{ searchError }}</p>
        <div v-if="searchResults.length" class="mt-2 space-y-1">
          <button
            v-for="(result, idx) in searchResults"
            :key="idx"
            type="button"
            class="flex w-full items-center justify-between rounded-lg border border-amber-100 bg-white px-3 py-2 text-left text-sm transition-colors hover:border-amber-300"
            @click="pickResult(result)"
          >
            <span class="font-medium text-slate-800">{{ result.name }}</span>
            <span class="shrink-0 text-[11px] tabular-nums text-slate-400">
              {{ result.macros.serving_amount }}{{ result.macros.serving_unit }} ·
              {{ result.macros.kcal }} kcal ·
              {{ result.macros.protein_g }}g P ·
              {{ result.macros.carbs_g }}g C ·
              {{ result.macros.fat_g }}g G
            </span>
          </button>
        </div>
      </div>

      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">Nombre</label>
        <input
          v-model="name"
          type="text"
          placeholder="Pechuga de pollo"
          class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
        />
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">Categoría</label>
          <input
            v-model="category"
            type="text"
            placeholder="Carnes"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
          />
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">Unidad</label>
          <select
            v-model="unit"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
          >
            <option v-for="opt in unitOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </div>
      </div>

      <div class="border-t border-slate-100 pt-4">
        <h4 class="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
          Macros por unidad de referencia
        </h4>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-500">Cantidad ref.</label>
            <input
              v-model.number="servingAmount"
              type="number"
              min="1"
              step="any"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
            />
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-500">Unidad ref.</label>
            <input
              v-model="servingUnit"
              type="text"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
            />
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-500">kcal</label>
            <input
              v-model.number="kcal"
              type="number"
              min="0"
              step="any"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
            />
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-500">Proteína (g)</label>
            <input
              v-model.number="proteinG"
              type="number"
              min="0"
              step="any"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
            />
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-500">Carbos (g)</label>
            <input
              v-model.number="carbsG"
              type="number"
              min="0"
              step="any"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
            />
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-500">Grasa (g)</label>
            <input
              v-model.number="fatG"
              type="number"
              min="0"
              step="any"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
            />
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-500">Fibra (g)</label>
            <input
              v-model.number="fiberG"
              type="number"
              min="0"
              step="any"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
            />
          </div>
        </div>
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
          {{ saving ? "Guardando…" : isEdit ? "Guardar" : "Crear" }}
        </button>
      </div>
    </form>
  </Modal>
</template>
