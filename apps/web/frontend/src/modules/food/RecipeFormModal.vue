<script setup lang="ts">
import { computed, ref } from "vue";
import { ApiRequestError } from "../../api/client";
import { foodApi } from "../../api/food";
import Icon from "../../components/Icon.vue";
import Modal from "../../components/Modal.vue";
import { formatFoodUnit } from "../../lib/food";
import { icons } from "../../lib/icons";
import { valueOrNull } from "../../lib/utils";
import type { Ingredient, Recipe, RecipeIngredientInput } from "../../types";

const props = defineProps<{
  recipe?: Recipe | null;
  ingredients: Ingredient[];
}>();
const emit = defineEmits<{ close: []; saved: [] }>();

const isEdit = computed(() => props.recipe != null);

interface IngredientRow {
  ingredientId: number | null;
  quantity: number;
  unit: string;
}

const name = ref(props.recipe?.name ?? "");
const category = ref(props.recipe?.category ?? "");
const description = ref(props.recipe?.description ?? "");
const portions = ref(props.recipe?.portions ?? 1);
const pointsAwarded = ref<number | "">(props.recipe?.points_awarded ?? "");
const pointsMinPortions = ref<number | "">(props.recipe?.points_min_portions ?? "");
const ingredientRows = ref<IngredientRow[]>(
  props.recipe?.ingredients.map((ri) => ({
    ingredientId: ri.ingredient_id,
    quantity: ri.quantity,
    unit: ri.unit,
  })) ?? [],
);
const steps = ref<string[]>(props.recipe?.steps ?? []);

const error = ref<string | null>(null);
const saving = ref(false);

const usedIngredientIds = computed(
  () => new Set(ingredientRows.value.map((r) => r.ingredientId).filter(Boolean)),
);

function availableIngredients(excludeIndex: number) {
  return props.ingredients.filter(
    (ing) => !usedIngredientIds.value.has(ing.id) || ing.id === ingredientRows.value[excludeIndex]?.ingredientId,
  );
}

function onIngredientChange(index: number) {
  const row = ingredientRows.value[index];
  if (row.ingredientId) {
    const ing = props.ingredients.find((i) => i.id === row.ingredientId);
    if (ing) row.unit = ing.unit;
  }
}

function addIngredient() {
  ingredientRows.value.push({ ingredientId: null, quantity: 0, unit: "g" });
}

function removeIngredient(index: number) {
  ingredientRows.value.splice(index, 1);
}

function rowMacros(row: IngredientRow) {
  if (!row.ingredientId || row.quantity <= 0) return null;
  const ing = props.ingredients.find((i) => i.id === row.ingredientId);
  if (!ing) return null;
  const m = ing.macros;
  if (row.unit !== m.serving_unit) return null;
  const factor = row.quantity / m.serving_amount;
  return {
    kcal: Math.round(m.kcal * factor),
    protein_g: Math.round(m.protein_g * factor),
    carbs_g: Math.round(m.carbs_g * factor),
    fat_g: Math.round(m.fat_g * factor),
  };
}

function addStep() {
  steps.value.push("");
}

function removeStep(index: number) {
  steps.value.splice(index, 1);
}

function buildIngredientsPayload(): RecipeIngredientInput[] {
  return ingredientRows.value
    .filter((r) => r.ingredientId != null && r.quantity > 0)
    .map((r) => ({
      ingredient_id: r.ingredientId!,
      quantity: r.quantity,
      unit: r.unit,
    }));
}

function buildStepsPayload(): string[] | null {
  const filtered = steps.value.filter((s) => s.trim());
  return filtered.length > 0 ? filtered : null;
}

async function submit() {
  error.value = null;

  if (!name.value.trim()) {
    error.value = "El nombre de la receta es obligatorio.";
    return;
  }
  if (!Number.isInteger(portions.value) || portions.value < 1) {
    error.value = "Las porciones deben ser un entero mayor que 0.";
    return;
  }
  const awarded = valueOrNull(pointsAwarded.value);
  const minPortions = valueOrNull(pointsMinPortions.value);
  if (awarded != null && (!Number.isInteger(awarded) || awarded < 0)) {
    error.value = "Los puntos deben ser un entero mayor o igual que 0.";
    return;
  }
  if (minPortions != null && (!Number.isInteger(minPortions) || minPortions < 1)) {
    error.value = "Las porciones mínimas deben ser un entero mayor que 0.";
    return;
  }
  if (ingredientRows.value.length === 0) {
    error.value = "Agrega al menos un ingrediente.";
    return;
  }
  for (const row of ingredientRows.value) {
    if (!row.ingredientId) {
      error.value = "Selecciona un ingrediente en cada fila.";
      return;
    }
    if (row.quantity <= 0) {
      error.value = "La cantidad debe ser mayor a 0 en todas las filas.";
      return;
    }
  }

  const payload = {
    name: name.value.trim(),
    category: category.value.trim() || null,
    description: description.value.trim() || null,
    portions: portions.value,
    points_awarded: awarded,
    points_min_portions: minPortions,
    steps: buildStepsPayload(),
    ingredients: buildIngredientsPayload(),
  };

  saving.value = true;
  try {
    if (props.recipe) {
      await foodApi.updateRecipe(props.recipe.id, payload);
    } else {
      await foodApi.createRecipe(payload);
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
  <Modal :title="isEdit ? 'Editar receta' : 'Crear receta'" @close="emit('close')">
    <form class="space-y-4" @submit.prevent="submit">
      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">Receta</label>
        <input
          v-model="name"
          type="text"
          placeholder="Arroz con pollo"
          class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
        />
      </div>

      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">Categoría</label>
        <input
          v-model="category"
          type="text"
          placeholder="Desayuno, Almuerzo, Postre, Snack…"
          class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
        />
      </div>

      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">Descripción (Opcional)</label>
        <textarea
          v-model="description"
          rows="2"
          placeholder="Como lo hacía la Nonna"
          class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
        />
      </div>

      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">Porciones</label>
        <input
          v-model.number="portions"
          type="number"
          min="1"
          class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
        />
      </div>

      <div class="rounded-lg border border-slate-100 bg-slate-50/50 p-3">
        <p class="mb-1 flex items-center gap-1.5 text-xs font-semibold tracking-wider text-slate-400">
          <Icon :path="icons.trophy" :size="12" class="shrink-0 text-amber-400" />
          Puntos por cocinar
        </p>
        <p class="mb-3 text-xs text-slate-500">
          Puedes definir cuántos puntos otorga preparar esta receta. Al registrar una preparación, esos puntos se sumarán al usuario que la cocinó en el ranking mensual del hogar.
        </p>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-500">Puntos otorgados</label>
            <div class="flex items-center gap-1.5">
              <input
                v-model.number="pointsAwarded"
                type="number"
                min="1"
                placeholder="0"
                class="min-w-0 flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
              />
              <span class="shrink-0 rounded-md bg-slate-100 px-2 py-1.5 text-xs font-medium text-slate-500">pts</span>
            </div>
            <p class="mt-1 text-xs text-slate-400">Déjalos vacíos si la receta no debe otorgar puntos.</p>
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-500">Mínimo de porciones</label>
            <div class="flex items-center gap-1.5">
              <input
                v-model.number="pointsMinPortions"
                type="number"
                min="1"
                placeholder="1"
                class="min-w-0 flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
              />
              <span class="shrink-0 rounded-md bg-slate-100 px-2 py-1.5 text-xs font-medium text-slate-500">porc.</span>
            </div>
            <p class="mt-1 text-xs text-slate-400">
              Cantidad mínima que se debe preparar para ganar puntos.
            </p>
          </div>
        </div>
      </div>

    <div class="border-t border-slate-100 pt-4">
        <h4 class="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
          Ingredientes
        </h4>
        <div class="space-y-2">
          <div
            v-for="(row, idx) in ingredientRows"
            :key="idx"
          >
            <div class="flex items-center gap-2">
              <select
                :value="row.ingredientId ?? ''"
                class="min-w-0 flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
                @change=";(row.ingredientId = Number(($event.target as HTMLSelectElement).value) || null), onIngredientChange(idx)"
              >
                <option value="" disabled>Selecciona un ingrediente</option>
                <option
                  v-for="ing in availableIngredients(idx)"
                  :key="ing.id"
                  :value="ing.id"
                >
                  {{ ing.name }}
                </option>
              </select>
              <input
                v-model.number="row.quantity"
                type="number"
                min="0"
                step="any"
                placeholder="Cant."
                class="w-20 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
              />
              <span class="w-13 text-left text-xs text-slate-400">{{ formatFoodUnit(row.unit, row.quantity) }}</span>
              <button
                type="button"
                class="shrink-0 rounded-lg p-2 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-500"
                @click="removeIngredient(idx)"
              >
                <Icon :path="icons.trash" :size="14" />
              </button>
            </div>
            <div v-if="rowMacros(row)" class="ml-1 text-xs text-slate-400">
              {{ rowMacros(row)!.kcal }}kcal · {{ rowMacros(row)!.protein_g }}P · {{ rowMacros(row)!.carbs_g }}C · {{ rowMacros(row)!.fat_g }}G
            </div>
          </div>
        </div>
        <button
          type="button"
          class="mt-2 inline-flex items-center gap-1 text-sm font-medium text-slate-600 transition-colors hover:text-slate-900"
          @click="addIngredient"
        >
          <Icon :path="icons.plus" :size="14" />
          Agregar ingrediente
        </button>
      </div>

      <div class="border-t border-slate-100 pt-4">
        <h4 class="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
          Pasos
        </h4>
        <div class="space-y-2">
          <div v-for="(_, idx) in steps" :key="idx" class="flex items-start gap-2">
            <span class="mt-2 shrink-0 text-xs font-medium text-slate-400">
              {{ idx + 1 }}.
            </span>
            <textarea
              v-model="steps[idx]"
              rows="2"
              :placeholder="`Paso ${idx + 1}`"
              class="min-w-0 flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
            />
            <button
              type="button"
              class="shrink-0 rounded-lg p-2 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-500"
              @click="removeStep(idx)"
            >
              <Icon :path="icons.trash" :size="14" />
            </button>
          </div>
        </div>
        <button
          type="button"
          class="mt-2 inline-flex items-center gap-1 text-sm font-medium text-slate-600 transition-colors hover:text-slate-900"
          @click="addStep"
        >
          <Icon :path="icons.plus" :size="14" />
          Agregar paso
        </button>
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
