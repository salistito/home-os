<script setup lang="ts">
import { computed, ref } from "vue";
import { ApiRequestError } from "../../api/client";
import { foodApi } from "../../api/food";
import DateInput from "../../components/DateInput.vue";
import Icon from "../../components/Icon.vue";
import Modal from "../../components/Modal.vue";
import { addDays, getCurrentTime, getToday } from "../../lib/date";
import { recipeName, MACRO_SHORT_LABELS } from "../../lib/food";
import { capitalize, formatWeekdayAndDay } from "../../lib/format";
import { icons } from "../../lib/icons";
import { MACRO_KEYS, MEAL_TYPE_LABELS } from "../../types";
import type {
  CookEvent,
  Ingredient,
  IngredientStock,
  MacroKey,
  MealEntry,
  MealEntryItemInput,
  MealType,
  Recipe,
} from "../../types";
import MacroGrid from "./MacroGrid.vue";

const props = defineProps<{
  entry?: MealEntry | null;
  cookEvents: CookEvent[];
  recipes: Recipe[];
  stock: IngredientStock[];
  ingredients: Ingredient[];
  defaultDate?: string;
}>();
const emit = defineEmits<{ close: []; saved: [] }>();

const isEdit = computed(() => props.entry != null);

const maxTime = computed(() =>
  date.value === getToday() ? getCurrentTime() : undefined,
);

const mealTypes: { value: MealType; label: string }[] = Object.entries(MEAL_TYPE_LABELS).map(
  ([value, label]) => ({ value: value as MealType, label }),
);

interface CookEventRow {
  kind: "cook_event";
  uid: number;
  cookEventId: number | null;
  portions: number;
}

interface IngredientRow {
  kind: "ingredient";
  uid: number;
  ingredientId: number | null;
  quantity: number;
}

interface ManualRow {
  kind: "manual";
  uid: number;
  name: string;
  macros: Record<MacroKey, number>;
}

type ItemRow = CookEventRow | IngredientRow | ManualRow;

let uid = 0;
const nextUid = () => ++uid;

const entryDate = props.entry
  ? props.entry.eaten_at.slice(0, 10)
  : (props.defaultDate ?? getToday());
const entryTime = props.entry ? props.entry.eaten_at.slice(11, 16) || "12:00" : getCurrentTime();

function defaultMealType(): MealType {
  const hour = Number(getCurrentTime().slice(0, 2));
  if (hour >= 5 && hour < 12) return "breakfast";
  if (hour >= 12 && hour < 15) return "lunch";
  if (hour >= 18 && hour < 22) return "dinner";
  return "snack";
}

const date = ref(entryDate);
const time = ref(entryTime);
const mealType = ref<MealType>(props.entry?.meal_type ?? defaultMealType());
const notes = ref(props.entry?.notes ?? "");

function itemToRow(item: MealEntry["items"][number]): ItemRow {
  if (item.source === "cook_event") {
    return {
      kind: "cook_event",
      uid: nextUid(),
      cookEventId: item.cook_event_id,
      portions: item.portions ?? 1,
    };
  }
  if (item.source === "ingredient") {
    return {
      kind: "ingredient",
      uid: nextUid(),
      ingredientId: item.ingredient_id,
      quantity: item.quantity ?? 0,
    };
  }
  return {
    kind: "manual",
    uid: nextUid(),
    name: item.name,
    macros: {
      kcal: item.macros.kcal ?? 0,
      protein_g: item.macros.protein_g ?? 0,
      carbs_g: item.macros.carbs_g ?? 0,
      fat_g: item.macros.fat_g ?? 0,
      fiber_g: item.macros.fiber_g ?? 0,
    },
  };
}

const rows = ref<ItemRow[]>(props.entry ? props.entry.items.map(itemToRow) : []);

const error = ref<string | null>(null);
const saving = ref(false);
const detailsOpen = ref(false);

const dateLabel = computed(() => {
  if (date.value === getToday()) return "Hoy";
  if (date.value === addDays(getToday(), -1)) return "Ayer";
  return capitalize(formatWeekdayAndDay(date.value));
});

const contextSummary = computed(
  () => `${dateLabel.value} ${time.value} · ${MEAL_TYPE_LABELS[mealType.value]}`,
);

function cookEventLabel(event: CookEvent): string {
  const remaining = event.remaining_portions ?? 0;
  const availability = remaining > 0 ? ` · ${Math.round(remaining)} porc.` : "";
  return `${recipeName(event.recipe_id, props.recipes)}${availability}`;
}

const cutoffDate = addDays(getToday(), -7);

const selectedCookEventIds = computed(() => {
  const ids = new Set<number>();
  for (const row of rows.value) {
    if (row.kind === "cook_event" && row.cookEventId != null) {
      ids.add(row.cookEventId);
    }
  }
  return ids;
});

const alreadyUsedCookEventIds = computed(() => {
  const ids = new Set<number>();
  for (const item of props.entry?.items ?? []) {
    if (item.source === "cook_event" && item.cook_event_id != null) {
      ids.add(item.cook_event_id);
    }
  }
  return ids;
});

const availableCookEvents = computed(() =>
  props.cookEvents.filter((ce) => {
    if (selectedCookEventIds.value.has(ce.id)) return true;
    return (ce.remaining_portions ?? 0) > 0 && ce.cooked_at.slice(0, 10) >= cutoffDate;
  }),
);

const stockByIngredient = computed(() => {
  const map = new Map<number, number>();
  for (const s of props.stock) map.set(s.ingredient_id, s.quantity);
  return map;
});

const unitLabels: Record<string, string> = {
  g: "g",
  ml: "ml",
  unit: "unidad",
  tablespoon: "cuchada",
};

function ingredientUnitLabel(row: IngredientRow): string {
  const ingredient = props.ingredients.find((i) => i.id === row.ingredientId);
  return ingredient ? (unitLabels[ingredient.unit] ?? ingredient.unit) : "";
}

function ingredientStock(row: IngredientRow): number | undefined {
  return row.ingredientId == null ? undefined : stockByIngredient.value.get(row.ingredientId);
}

function rowMacros(row: ItemRow): Record<string, number> {
  if (row.kind === "manual") {
    return row.macros;
  }
  if (row.kind === "ingredient") {
    const ingredient = props.ingredients.find((i) => i.id === row.ingredientId);
    const macros = ingredient?.macros;
    const factor = macros && row.quantity > 0 ? row.quantity / macros.serving_amount : 0;
    const out: Record<string, number> = {};
    for (const key of MACRO_KEYS) out[key] = Math.round((macros?.[key] ?? 0) * factor);
    return out;
  }
  const event = props.cookEvents.find((ce) => ce.id === row.cookEventId);
  const per = event?.macros?.per_portion ?? {};
  const factor = row.portions > 0 ? row.portions : 0;
  const out: Record<string, number> = {};
  for (const key of MACRO_KEYS) {
    out[key] = Math.round((per[key] ?? 0) * factor);
  }
  return out;
}

const totals = computed(() => {
  const out: Record<string, number> = { kcal: 0, protein_g: 0, carbs_g: 0, fat_g: 0, fiber_g: 0 };
  for (const row of rows.value) {
    const m = rowMacros(row);
    for (const key of MACRO_KEYS) out[key] += m[key];
  }
  return out;
});

function newCookEventRow(): ItemRow {
  return {
    kind: "cook_event",
    uid: nextUid(),
    cookEventId: null,
    portions: 1,
  };
}

function newIngredientRow(): ItemRow {
  return {
    kind: "ingredient",
    uid: nextUid(),
    ingredientId: null,
    quantity: 0,
  };
}

function newManualRow(): ItemRow {
  return {
    kind: "manual",
    uid: nextUid(),
    name: "",
    macros: { kcal: 0, protein_g: 0, carbs_g: 0, fat_g: 0, fiber_g: 0 },
  };
}

const kindLabels: Record<ItemRow["kind"], string> = {
  cook_event: "Cocción",
  ingredient: "Ingrediente",
  manual: "Manual",
};

const kindIcons: Record<ItemRow["kind"], string> = {
  cook_event: icons.pot,
  ingredient: icons.measuringCup,
  manual: icons.pencil,
};

const addOptions = (Object.keys(kindLabels) as ItemRow["kind"][]).map((kind) => ({
  kind,
  label: kindLabels[kind],
  icon: kindIcons[kind],
}));

function addRow(kind: ItemRow["kind"]) {
  if (kind === "cook_event") rows.value.push(newCookEventRow());
  else if (kind === "ingredient") rows.value.push(newIngredientRow());
  else rows.value.push(newManualRow());
}

function hasAnyMacro(row: ManualRow): boolean {
  return MACRO_KEYS.some((key) => (row.macros[key] ?? 0) > 0);
}

function removeRow(row: ItemRow) {
  rows.value.splice(rows.value.indexOf(row), 1);
}

function buildPayloadItems(): MealEntryItemInput[] {
  const items: MealEntryItemInput[] = [];
  for (const row of rows.value) {
    if (row.kind === "cook_event") {
      if (row.cookEventId == null || row.portions <= 0) continue;
      items.push({
        source: "cook_event",
        cook_event_id: row.cookEventId,
        portions: row.portions,
      });
    } else if (row.kind === "ingredient") {
      const ingredient = props.ingredients.find((i) => i.id === row.ingredientId);
      if (row.ingredientId == null || row.quantity <= 0 || !ingredient) continue;
      items.push({
        source: "ingredient",
        ingredient_id: row.ingredientId,
        quantity: row.quantity,
        unit: ingredient.unit,
      });
    } else {
      if (!row.name.trim() || !hasAnyMacro(row)) continue;
      items.push({
        source: "manual",
        name: row.name.trim(),
        macros: row.macros,
      });
    }
  }
  return items;
}

async function submit() {
  error.value = null;

  if (!date.value.trim()) {
    error.value = "La fecha es obligatoria.";
    detailsOpen.value = true;
    return;
  }

  if (date.value > getToday()) {
    error.value = "La fecha no puede ser posterior a hoy.";
    detailsOpen.value = true;
    return;
  }

  if (date.value === getToday() && time.value && time.value > getCurrentTime()) {
    error.value = "La hora no puede ser posterior a la actual.";
    detailsOpen.value = true;
    return;
  }

  for (const row of rows.value) {
    if (row.kind === "cook_event") {
      if (row.cookEventId == null) {
        error.value = "Debes seleccionar una cocción.";
        return;
      }
      if (row.portions <= 0) {
        error.value = "Las porciones deben ser mayores que 0.";
        return;
      }
    } else if (row.kind === "ingredient") {
      if (row.ingredientId == null) {
        error.value = "Debes seleccionar un ingrediente.";
        return;
      }
      if (row.quantity <= 0) {
        error.value = "La cantidad debe ser mayor que 0.";
        return;
      }
    } else {
      if (!row.name.trim()) {
        error.value = "El nombre del alimento es obligatorio.";
        return;
      }
      if (!hasAnyMacro(row)) {
        error.value = "Define al menos un macro para el alimento.";
        return;
      }
    }
  }

  const items = buildPayloadItems();
  if (items.length === 0) {
    error.value = "Agrega al menos un alimento a la comida.";
    return;
  }

  const requestedByEvent = new Map<number, number>();
  for (const row of rows.value) {
    if (row.kind === "cook_event" && row.cookEventId != null) {
      requestedByEvent.set(
        row.cookEventId,
        (requestedByEvent.get(row.cookEventId) ?? 0) + row.portions,
      );
    }
  }

  for (const [eventId, requested] of requestedByEvent) {
    const cookEvent = props.cookEvents.find((ce) => ce.id === eventId);
    if (!cookEvent) {
      error.value = "La cocción seleccionada ya no existe.";
      return;
    }
    const ownConsumed = isEdit
      ? (props.entry?.items ?? [])
          .filter((item) => item.cook_event_id === eventId)
          .reduce((sum, item) => sum + (item.portions ?? 0), 0)
      : 0;
    const available = (cookEvent.remaining_portions ?? 0) + ownConsumed;
    if (
      !alreadyUsedCookEventIds.value.has(eventId) &&
      cookEvent.cooked_at.slice(0, 10) < cutoffDate
    ) {
      error.value = "La cocción seleccionada tiene más de 7 días.";
      return;
    }
    if (requested > available + 0.000001) {
      error.value = `No quedan suficientes porciones: solo hay ${Math.round(available)} disponible(s).`;
      return;
    }
  }

  const payload = {
    eaten_at: `${date.value} ${time.value || "12:00"}`,
    meal_type: mealType.value,
    notes: notes.value.trim() || null,
    items,
  };

  saving.value = true;
  try {
    if (props.entry) {
      await foodApi.updateMeal(props.entry.id, payload);
    } else {
      await foodApi.createMeal(payload);
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
  <Modal :title="isEdit ? 'Editar comida' : 'Registrar comida'" size="lg" @close="emit('close')">
    <form class="space-y-4" @submit.prevent="submit">
      <div class="rounded-lg border border-slate-200 bg-slate-50/60">
        <button
          type="button"
          class="flex h-11 w-full items-center gap-2 px-3 text-left text-sm font-medium text-slate-800 transition-colors active:bg-slate-100"
          :aria-expanded="detailsOpen"
          @click="detailsOpen = !detailsOpen"
        >
          <span class="min-w-0 flex-1 truncate">{{ contextSummary }}</span>
          <span v-if="notes" class="shrink-0 truncate text-xs text-slate-400">{{ notes }}</span>
          <Icon
            :path="detailsOpen ? icons.chevronUp : icons.pencil"
            :size="15"
            class="shrink-0 text-slate-400"
          />
        </button>

        <Transition
          enter-from-class="opacity-0"
          leave-to-class="opacity-0"
          enter-active-class="transition-opacity duration-150"
          leave-active-class="transition-opacity duration-100"
        >
          <div v-if="detailsOpen" class="space-y-3 border-t border-slate-200 p-3">
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="mb-1 block text-xs font-medium text-slate-500">Fecha</label>
                <DateInput v-model="date" :max="getToday()" />
              </div>
              <div>
                <label class="mb-1 block text-xs font-medium text-slate-500">Hora</label>
                <input
                  v-model="time"
                  type="time"
                  :max="maxTime"
                  class="w-full rounded-lg border border-slate-200 bg-white h-11 px-3 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
                />
              </div>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="mb-1 block text-xs font-medium text-slate-500">Tipo de comida</label>
                <select
                  v-model="mealType"
                  class="w-full rounded-lg border border-slate-200 bg-white h-11 px-3 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
                >
                  <option v-for="t in mealTypes" :key="t.value" :value="t.value">
                    {{ t.label }}
                  </option>
                </select>
              </div>
              <div>
                <label class="mb-1 block text-xs font-medium text-slate-500">Notas (Opcional)</label>
                <input
                  v-model="notes"
                  type="text"
                  placeholder="Casa de la Nonna…"
                  class="w-full rounded-lg border border-slate-200 bg-white h-11 px-3 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
                />
              </div>
            </div>
          </div>
        </Transition>
      </div>

      <div>
        <h4 class="mb-2 text-sm font-medium text-slate-800">¿Qué comiste?</h4>
        <div class="mb-3 grid grid-cols-3 gap-2">
          <button
            v-for="option in addOptions"
            :key="option.kind"
            type="button"
            class="flex h-[52px] flex-col items-center justify-center gap-1 rounded-lg border border-slate-200 text-xs font-medium text-slate-600 transition active:scale-[0.98] active:bg-slate-50"
            @click="addRow(option.kind)"
          >
            <Icon :path="option.icon" :size="18" class="text-slate-400" />
            {{ option.label }}
          </button>
        </div>
        <div class="space-y-3">
          <p
            v-if="rows.length === 0"
            class="py-6 text-center text-sm text-slate-500"
          >
            Aún no has agregado alimentos.
          </p>
          <div
            v-for="row in rows"
            :key="row.uid"
            class="rounded-lg border border-slate-100 bg-slate-50/50 p-3"
          >
            <div class="flex items-center gap-2">
              <Icon :path="kindIcons[row.kind]" :size="14" class="shrink-0 text-slate-400" />
              <span class="text-xs font-medium text-slate-500">
                {{ kindLabels[row.kind] }}
              </span>
              <span class="ml-auto text-xs tabular-nums text-slate-400">
                {{ Math.round(rowMacros(row).kcal) }}kcal
              </span>
              <button
                type="button"
                class="shrink-0 rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-500"
                @click="removeRow(row)"
              >
                <Icon :path="icons.trash" :size="14" />
              </button>
            </div>

            <div v-if="row.kind === 'cook_event'" class="mt-2 flex items-center gap-2">
              <select
                v-model="row.cookEventId"
                class="min-w-0 flex-1 rounded-lg border border-slate-200 h-11 px-3 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
              >
                <option :value="null" disabled>
                  {{
                    availableCookEvents.length
                      ? "Selecciona una cocción"
                      : "No hay cocciones disponibles"
                  }}
                </option>
                <option
                  v-for="ce in availableCookEvents"
                  :key="ce.id"
                  :value="ce.id"
                >
                  {{ cookEventLabel(ce) }}
                </option>
              </select>
              <input
                v-model.number="row.portions"
                type="number"
                min="0.5"
                step="0.5"
                class="w-16 rounded-lg border border-slate-200 h-11 px-3 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100 [appearance:textfield] [&::-webkit-inner-spin-button]:m-0 [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
              />
              <span class="text-xs text-slate-400">porc.</span>
            </div>
            <p
              v-if="row.kind === 'cook_event' && availableCookEvents.length === 0"
              class="mt-1 text-xs text-slate-500"
            >
            Todas las cocciones ya se consumieron o tienen más de 7 días de antigüedad.
            </p>

            <div v-else-if="row.kind === 'manual'" class="mt-2 space-y-2">
              <input
                v-model="row.name"
                type="text"
                placeholder="Nombre del alimento"
                class="w-full rounded-lg border border-slate-200 h-11 px-3 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
              />
              <div class="grid grid-cols-5 gap-2">
                <div v-for="key in MACRO_KEYS" :key="key">
                  <label class="mb-0.5 block text-[10px] text-slate-400">
                    {{ key === "kcal" ? "kcal*" : MACRO_SHORT_LABELS[key] }}
                  </label>
                  <input
                    v-model.number="row.macros[key]"
                    type="number"
                    min="0"
                    step="any"
                    class="w-full rounded-lg border border-slate-200 h-10 px-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100 [appearance:textfield] [&::-webkit-inner-spin-button]:m-0 [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
                  />
                </div>
              </div>
            </div>

            <div v-else-if="row.kind === 'ingredient'" class="mt-2 flex items-center gap-2">
              <select
                v-model="row.ingredientId"
                class="min-w-0 flex-1 rounded-lg border border-slate-200 h-11 px-3 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
              >
                <option :value="null" disabled>Selecciona un ingrediente</option>
                <option v-for="ing in ingredients" :key="ing.id" :value="ing.id">
                  {{ ing.name }}
                </option>
              </select>
              <input
                v-model.number="row.quantity"
                type="number"
                min="0"
                step="any"
                class="w-24 rounded-lg border border-slate-200 h-11 px-3 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100 [appearance:textfield] [&::-webkit-inner-spin-button]:m-0 [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
              />
              <span class="text-xs text-slate-400">{{ ingredientUnitLabel(row) }}</span>
            </div>
            <p
              v-if="row.kind === 'ingredient' && ingredientStock(row) != null"
              class="mt-1 text-xs text-slate-500"
            >
              Stock disponible: {{ ingredientStock(row) }}{{ ingredientUnitLabel(row) }}
            </p>
          </div>
        </div>
      </div>

      <div>
        <h4 class="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
          Macros totales
        </h4>
        <MacroGrid :macros="{ total: totals, per_portion: totals }" />
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
          {{ saving ? "Guardando…" : isEdit ? "Guardar" : "Registrar" }}
        </button>
      </div>
    </form>
  </Modal>
</template>
