<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { ApiRequestError } from "../../api/client";
import { foodApi } from "../../api/food";
import Modal from "../../components/Modal.vue";
import { FOOD_UNIT_OPTIONS, formatFoodUnit, formatFoodUnitPlural } from "../../lib/food";
import type {
  ExternalSearchResult,
  FoodUnit,
  Ingredient,
  IngredientMacros,
  IngredientStock,
} from "../../types";

const props = defineProps<{
  ingredient?: Ingredient | null;
  stock?: IngredientStock | null;
  importMode?: boolean;
}>();
const emit = defineEmits<{ close: []; saved: [] }>();

const isEdit = computed(() => props.ingredient != null);
const showImport = ref(props.importMode ?? false);

const name = ref(props.ingredient?.name ?? "");
const category = ref(props.ingredient?.category ?? "");
const unit = ref<FoodUnit>(props.ingredient?.unit ?? "g");
const purchaseUnit = ref(props.ingredient?.purchase_unit ?? "");
const purchaseConversionFactor = ref(props.ingredient?.purchase_conversion_factor ?? null);

const hasPurchaseUnit = computed(() =>
  Boolean(purchaseUnit.value.trim() && purchaseConversionFactor.value && purchaseConversionFactor.value > 0),
);
const stockQuantity = ref(props.stock?.quantity ?? 0);
const stockPurchaseQuantity = computed({
  get: () =>
    hasPurchaseUnit.value ? stockQuantity.value / purchaseConversionFactor.value! : 0,
  set: (val) => {
    stockQuantity.value = val * purchaseConversionFactor.value!;
  },
});

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
    error.value = "El nombre del ingrediente es obligatorio.";
    return;
  }
  if (purchaseUnit.value.trim() && (!purchaseConversionFactor.value || purchaseConversionFactor.value <= 0)) {
    error.value = "Si especificas una unidad de compra, el factor de conversión debe ser mayor a 0.";
    return;
  }
  if (stockQuantity.value < 0) {
    error.value = "La cantidad de stock no puede ser negativa.";
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
    const purchaseUnitVal = purchaseUnit.value.trim();
    const payload = {
      name: name.value.trim(),
      category: category.value.trim() || null,
      unit: unit.value,
      macros,
      purchase_unit: purchaseUnitVal,
      purchase_conversion_factor: purchaseUnitVal ? purchaseConversionFactor.value : null,
    };
    if (props.ingredient) {
      await foodApi.updateIngredient(props.ingredient.id, payload);
      const existingQuantity = props.stock?.quantity ?? 0;
      if (Math.abs(stockQuantity.value - existingQuantity) > 1e-9) {
        await foodApi.setStock(props.ingredient.id, {
          quantity: stockQuantity.value,
          min_alert_quantity: props.stock?.min_alert_quantity ?? 0,
          expiration_date: props.stock?.expiration_date ?? null,
        });
      }
    } else {
      const createdIngredient = await foodApi.createIngredient(payload);
      if (stockQuantity.value > 0) {
        await foodApi.setStock(createdIngredient.id, { quantity: stockQuantity.value });
      }
    }
    emit("saved");
  } catch (e) {
    error.value =
      e instanceof ApiRequestError ? e.message : "Error inesperado al guardar.";
  } finally {
    saving.value = false;
  }
}

watch(purchaseUnit, (val) => {
  if (!val.trim()) purchaseConversionFactor.value = null;
});
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
            <span class="shrink-0 text-[10px] tabular-nums text-slate-400">
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
        <label class="mb-1 block text-xs font-medium text-slate-500">Ingrediente</label>
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
            <option v-for="opt in FOOD_UNIT_OPTIONS" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </div>
      </div>

      <div class="rounded-lg border border-slate-100 bg-slate-50/50 p-3">
        <p class="mb-2 text-xs font-semibold tracking-wider text-slate-400">
          Información de Compra/Stock (Opcional)
        </p>
        <p class="mb-2 text-xs text-slate-500">
          Puedes gestionar las compras o el stock del ingrediente en una
          unidad distinta a la que usarás en las recetas (ej: stock en kg / recetas en g).
        </p>
        <div class="space-y-2">
          <div class="grid grid-cols-2 gap-x-3 gap-y-1">
            <label class="text-xs font-medium text-slate-500">Unidad de compra</label>
            <label class="text-xs font-medium text-slate-500">Equivale a</label>
            <input
              v-model="purchaseUnit"
              type="text"
              placeholder="kg, lt, bandejas, cajas…"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
            />
            <div class="flex items-center gap-1.5">
              <input
                v-model.number="purchaseConversionFactor"
                type="number"
                min="0"
                step="any"
                :disabled="!purchaseUnit.trim()"
                placeholder="Ej: 1000"
                class="min-w-0 flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100 disabled:opacity-50"
              />
              <span
                class="shrink-0 rounded-md bg-slate-100 px-2 py-1.5 text-xs font-medium text-slate-500"
              >{{ formatFoodUnit(unit, purchaseConversionFactor ?? 0) }}</span>
            </div>
          </div>
          <div :class="hasPurchaseUnit ? 'grid grid-cols-2 gap-3' : ''">
            <div v-if="hasPurchaseUnit">
              <label class="mb-1 block text-xs font-medium text-slate-500">
                Stock en {{ purchaseUnit }}
              </label>
              <div class="flex items-center gap-1.5">
                <input
                  v-model.number="stockPurchaseQuantity"
                  type="number"
                  min="0"
                  step="any"
                  placeholder="0"
                  class="min-w-0 flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
                />
                <span class="shrink-0 rounded-md bg-slate-100 px-2 py-1.5 text-xs font-medium text-slate-500">
                  {{ purchaseUnit }}
                </span>
              </div>
            </div>
            <div>
              <label class="mb-1 block text-xs font-medium text-slate-500">
                Stock en {{ formatFoodUnitPlural(unit) }}
              </label>
              <div class="flex items-center gap-1.5">
                <input
                  v-model.number="stockQuantity"
                  type="number"
                  min="0"
                  step="any"
                  placeholder="0"
                  class="min-w-0 flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
                />
                <span class="shrink-0 rounded-md bg-slate-100 px-2 py-1.5 text-xs font-medium text-slate-500">
                  {{ formatFoodUnit(unit, stockQuantity) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="border-t border-slate-100 pt-4">
        <h4 class="mb-3 text-xs font-semibold tracking-wider text-slate-400">
          Macros
        </h4>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-500">Cantidad referencial</label>
            <input
              v-model.number="servingAmount"
              type="number"
              min="1"
              step="any"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
            />
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-500">Unidad referencial</label>
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
            <label class="mb-1 block text-xs font-medium text-slate-500">Carbohidratos (g)</label>
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
          {{ saving ? "Cargando…" : isEdit ? "Guardar" : "Crear" }}
        </button>
      </div>
    </form>
  </Modal>
</template>
