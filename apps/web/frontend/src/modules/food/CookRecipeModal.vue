<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { ApiRequestError } from "../../api/client";
import { foodApi } from "../../api/food";
import DateInput from "../../components/DateInput.vue";
import Icon from "../../components/Icon.vue";
import Modal from "../../components/Modal.vue";
import SelectMenu, { type SelectOption } from "../../components/SelectMenu.vue";
import { auth } from "../../lib/auth";
import { colorsByUser } from "../../lib/colors";
import { getToday } from "../../lib/date";
import { icons } from "../../lib/icons";
import { pushToast } from "../../lib/toast";
import type {
  CookRecipeIngredientOverride,
  CookEventIngredientRow,
  Ingredient,
  IngredientStock,
  Recipe,
  RecipeMacros,
  UserRef
} from "../../types";
import CookIngredientRow from "./CookIngredientRow.vue";
import IngredientListRow from "./IngredientListRow.vue";
import MacroGrid from "./MacroGrid.vue";

const props = defineProps<{
  recipe: Recipe;
  ingredients: Ingredient[];
  stock: IngredientStock[];
  users: UserRef[];
  showBack?: boolean;
}>();
const emit = defineEmits<{ reload: []; saved: []; back: []; close: [] }>();

let rowIdCounter = 0;

function recipeRow(ri: typeof props.recipe.ingredients[number]): CookEventIngredientRow {
  return {
    id: rowIdCounter++,
    ingredient_id: ri.ingredient_id,
    quantity: ri.quantity,
    unit: ri.unit,
    isOriginal: true,
    originalQuantity: ri.quantity,
    originalIngredientId: ri.ingredient_id,
    edited: false,
  };
}

function emptyRow(): CookEventIngredientRow {
  return {
    id: rowIdCounter++,
    ingredient_id: null,
    quantity: 0,
    unit: "",
    isOriginal: false,
    originalQuantity: 0,
    originalIngredientId: null,
    edited: true,
  };
}

const sortedUsers = computed<UserRef[]>(() => {
  const loggedUser = auth.userId.value;
  return [...props.users]
    .filter((u) => u.deleted_at === null)
    .sort((a, b) => (a.id === loggedUser ? -1 : b.id === loggedUser ? 1 : 0));
});

const userColors = colorsByUser(props.users.map((u) => ({ id: u.id })));

const chefOptions = computed<SelectOption[]>(() =>
  sortedUsers.value.map((u) => ({
    value: String(u.id),
    label: u.name,
    dot: userColors[u.id]?.solid,
  })),
);

const chefId = ref<string>(
  String(auth.userId.value ?? sortedUsers.value[0]?.id ?? ""),
);

const portions = ref(props.recipe.portions);
const cookedAt = ref(getToday());
const rows = ref<CookEventIngredientRow[]>(
  props.recipe.ingredients.map((ri) => recipeRow(ri)),
);

const editingStockRow = ref<CookEventIngredientRow | null>(null);
const stockQty = ref(0);
const stockBusy = ref(false);
const stockError = ref<string | null>(null);

const confirming = ref(false);
const saving = ref(false);

const error = ref<string | null>(null);
const missingIds = ref<number[]>([]);

const modalTitle = computed(() =>
  confirming.value ? "¿Estás seguro de registrar esta cocción?" : "Registrar cocción",
);

const macroKeys = ["kcal", "protein_g", "carbs_g", "fat_g", "fiber_g"];

function ingredientById(id: number | null): Ingredient | undefined {
  if (id == null) return undefined;
  return props.ingredients.find((i) => i.id === id);
}

function ingredientName(id: number | null): string {
  if (id == null) return "—";
  return props.ingredients.find((i) => i.id === id)?.name ?? `#${id}`;
}

function totalNeeded(ingredientId: number | null): number {
  if (ingredientId == null) return 0;
  return rows.value
    .filter((r) => r.ingredient_id === ingredientId)
    .reduce((sum, r) => sum + r.quantity, 0);
}

function stockFor(ingredientId: number | null): number {
  if (ingredientId == null) return 0;
  const s = props.stock.find((st) => st.ingredient_id === ingredientId);
  return s?.quantity ?? 0;
}

const hasStock = computed(() =>
  rows.value.every((row) => {
    if (row.ingredient_id == null) return true;
    return totalNeeded(row.ingredient_id) <= stockFor(row.ingredient_id);
  }),
);

const stockByIngredient = computed(() => {
  const map = new Map<number, { needed: number; available: number }>();
  for (const row of rows.value) {
    if (row.ingredient_id == null) continue;
    const entry = map.get(row.ingredient_id) ?? { needed: 0, available: stockFor(row.ingredient_id) };
    entry.needed += row.quantity;
    map.set(row.ingredient_id, entry);
  }
  return map;
});

function ingredientStock(row: CookEventIngredientRow): number {
  return row.ingredient_id == null
    ? 0
    : (props.stock.find((s) => s.ingredient_id === row.ingredient_id)?.quantity ?? 0);
}

function openStockEditor(row: CookEventIngredientRow) {
  stockQty.value = ingredientStock(row);
  stockError.value = null;
  editingStockRow.value = row;
}

async function saveStock(row: CookEventIngredientRow) {
  if (row.ingredient_id == null) return;
  if (!(stockQty.value >= 0)) {
    stockError.value = "La cantidad no puede ser negativa.";
    return;
  }
  stockBusy.value = true;
  stockError.value = null;
  try {
    await foodApi.setStock(row.ingredient_id, { quantity: stockQty.value });
    editingStockRow.value = null;
    emit("reload");
  } catch (e) {
    stockError.value =
      e instanceof ApiRequestError ? e.message : "Error inesperado al guardar el stock.";
  } finally {
    stockBusy.value = false;
  }
}

const totalMacros = computed((): RecipeMacros => {
  const total: Record<string, number> = {};
  for (const key of macroKeys) total[key] = 0;

  for (const row of rows.value) {
    const ing = ingredientById(row.ingredient_id);
    if (!ing?.macros) continue;
    if (row.unit !== ing.macros.serving_unit) continue;
    const factor = row.quantity / ing.macros.serving_amount;
    for (const key of macroKeys) {
      const val = ing.macros[key as keyof typeof ing.macros] as number | undefined;
      if (val != null) total[key] += val * factor;
    }
  }

  const per: Record<string, number> = {};
  const div = portions.value > 0 ? portions.value : 1;
  for (const key of macroKeys) {
    per[key] = Math.round((total[key] / div) * 100) / 100;
  }
  return { total, per_portion: per };
});

watch(portions, () => {
  const ratio = portions.value / props.recipe.portions;
  for (const row of rows.value) {
    if (row.isOriginal && !row.edited) {
      row.quantity =
        Math.round(row.originalQuantity * ratio * 100) / 100;
    }
  }
});

function addRow() {
  rows.value.push(emptyRow());
}

function removeRow(id: number) {
  rows.value = rows.value.filter((r) => r.id !== id);
}

const validRows = computed(() =>
  rows.value.filter(
    (r) => r.ingredient_id != null && r.quantity > 0,
  ),
);

function buildPayload(): CookRecipeIngredientOverride[] {
  return validRows.value.map((r) => ({
    ingredient_id: r.ingredient_id!,
    quantity: r.quantity,
    unit: r.unit,
  }));
}

function askConfirm() {
  error.value = null;
  missingIds.value = [];

  if (!Number.isInteger(portions.value) || portions.value < 1) {
    error.value = "Las porciones deben ser un entero mayor que 0.";
    return;
  }

  if (!validRows.value.length) {
    error.value = "Debe haber al menos un ingrediente con cantidad mayor a 0.";
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
    const result = await foodApi.cookRecipe(props.recipe.id, {
      user_id: Number(chefId.value),
      portions: portions.value,
      ingredients: buildPayload(),
      cooked_at: cookedAt.value || null,
    });
    if (result.points_awarded > 0) {
      pushToast(`Cocción registrada: +${result.points_awarded} pts`);
    } else {
      pushToast("Cocción registrada");
    }
    emit("saved");
  } catch (e) {
    if (
      e instanceof ApiRequestError &&
      (e as unknown as { code?: string }).code === "insufficient_stock"
    ) {
      const body = (
        e as unknown as { body?: { missing_ingredient_ids?: number[] } }
      ).body;
      missingIds.value = body?.missing_ingredient_ids ?? [];
      error.value = "Stock insuficiente para uno o más ingredientes.";
    } else {
      error.value =
        e instanceof ApiRequestError
          ? e.message
          : "Error inesperado al registrar la cocción.";
    }
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <Modal :title="modalTitle" @close="emit('close')">
    <form v-if="!confirming" class="space-y-4" @submit.prevent="askConfirm">
      <p class="text-sm font-medium text-slate-800">{{ recipe.name }}</p>

      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">Chef</label>
        <SelectMenu v-model="chefId" :options="chefOptions" />
      </div>

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
          <DateInput v-model="cookedAt" :max="getToday()" />
          <p class="mt-1 text-xs text-slate-400">Puede ser una fecha pasada</p>
        </div>
      </div>

      <div v-if="validRows.length">
        <h4 class="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
          Macros por porción
        </h4>
        <MacroGrid :macros="totalMacros" />
      </div>

      <div>
        <div class="mb-2 flex items-center justify-between">
          <h4 class="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Ingredientes utilizados
          </h4>
          <button
            type="button"
            class="rounded-md border border-slate-200 px-2 py-0.5 text-xs font-medium text-slate-500 transition-colors hover:bg-slate-50"
            @click="addRow"
          >
            + Añadir
          </button>
        </div>

        <ul class="divide-y divide-slate-100 rounded-lg border border-slate-100">
          <CookIngredientRow
            v-for="row in rows"
            :key="row.id"
            :row="row"
            :ingredients="ingredients"
            :stock-by-ingredient="stockByIngredient"
            :editing-stock="editingStockRow === row"
            :stock-qty="editingStockRow === row ? stockQty : 0"
            :stock-busy="stockBusy"
            :stock-error="editingStockRow === row ? stockError : null"
            @edit-stock="openStockEditor(row)"
            @update:stock-qty="stockQty = $event"
            @save-stock="saveStock(row)"
            @cancel-stock="editingStockRow = null"
            @remove="removeRow"
          />
        </ul>
      </div>

      <div v-if="missingIds.length" class="rounded-lg bg-red-50 p-3">
        <p class="text-sm font-medium text-red-700">Stock insuficiente:</p>
        <ul class="mt-1 list-inside list-disc text-xs text-red-600">
          <li v-for="id in missingIds" :key="id">{{ ingredientName(id) }}</li>
        </ul>
      </div>

      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

      <div class="flex items-center justify-end gap-2 pt-1">
        <button
          v-if="props.showBack"
          type="button"
          class="mr-auto inline-flex items-center gap-1 rounded-lg px-2 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100"
          @click="emit('back')"
        >
          <Icon :path="icons.chevronLeft" :size="14" />
          Otra receta
        </button>
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
        Al confirmar se descontarán los ingredientes del stock.<br />
        Esta acción no se puede editar ni eliminar.
      </p>

      <div v-if="validRows.length">
        <h4 class="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
          Macros por porción
        </h4>
        <MacroGrid :macros="totalMacros" />
      </div>

      <div v-if="validRows.length">
        <h4 class="mb-1 text-xs font-semibold uppercase tracking-wider text-slate-400">
          Ingredientes utilizados
        </h4>
        <ul class="divide-y divide-slate-100 rounded-lg border border-slate-100">
          <IngredientListRow
            v-for="row in validRows"
            :key="row.id"
            :name="ingredientName(row.ingredient_id)"
            :quantity="row.quantity"
            :unit="row.unit"
            :macros="ingredientById(row.ingredient_id)?.macros"
          />
        </ul>
      </div>

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
