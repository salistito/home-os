<script setup lang="ts">
import { computed, ref } from "vue";
import { ApiRequestError } from "../../api/client";
import { foodApi } from "../../api/food";
import DateInput from "../../components/DateInput.vue";
import Icon from "../../components/Icon.vue";
import Modal from "../../components/Modal.vue";
import { getCurrentTime, getToday } from "../../lib/date";
import { recipeName, MACRO_SHORT_LABELS } from "../../lib/food";
import { icons } from "../../lib/icons";
import { MACRO_KEYS, MEAL_TYPE_LABELS } from "../../types";
import type {
  CookEvent,
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

interface ManualRow {
  kind: "manual";
  uid: number;
  name: string;
  macros: Record<MacroKey, number>;
}

type ItemRow = CookEventRow | ManualRow;

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

const rows = ref<ItemRow[]>(
  props.entry
    ? props.entry.items.map((item) =>
        item.source === "cook_event"
          ? {
              kind: "cook_event",
              uid: nextUid(),
              cookEventId: item.cook_event_id,
              portions: item.portions ?? 1,
            }
          : {
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
            },
      )
    : [],
);

const error = ref<string | null>(null);
const saving = ref(false);

function cookEventLabel(event: CookEvent): string {
  const macro = event.macros?.per_portion.kcal;
  const kcal = macro != null ? ` · ${Math.round(macro)}kcal/porc.` : "";
  return `${recipeName(event.recipe_id, props.recipes)}${kcal}`;
}

function rowMacros(row: ItemRow): Record<string, number> {
  if (row.kind === "manual") {
    return row.macros;
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

function newManualRow(): ItemRow {
  return {
    kind: "manual",
    uid: nextUid(),
    name: "",
    macros: { kcal: 0, protein_g: 0, carbs_g: 0, fat_g: 0, fiber_g: 0 },
  };
}

function addCookEventRow() {
  rows.value.push(newCookEventRow());
}

function addManualRow() {
  rows.value.push(newManualRow());
}

function setRowKind(row: ItemRow, kind: ItemRow["kind"]) {
  const i = rows.value.indexOf(row);
  if (i === -1 || row.kind === kind) return;
  rows.value[i] = kind === "manual" ? newManualRow() : newCookEventRow();
}

function changeRowKind(row: ItemRow, event: Event) {
  setRowKind(row, (event.target as HTMLSelectElement).value as ItemRow["kind"]);
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
    return;
  }

  if (date.value > getToday()) {
    error.value = "La fecha no puede ser posterior a hoy.";
    return;
  }

  if (date.value === getToday() && time.value && time.value > getCurrentTime()) {
    error.value = "La hora no puede ser posterior a la actual.";
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
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
          />
        </div>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">Tipo de comida</label>
          <select
            v-model="mealType"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
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
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
          />
        </div>
      </div>

      <div class="border-t border-slate-100 pt-4">
        <div class="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <h4 class="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Alimentos
          </h4>
          <div class="flex items-center gap-1.5">
            <span class="text-xs font-medium text-slate-500">Ingresar:</span>
            <button
              type="button"
              class="inline-flex items-center gap-1 rounded-md border border-slate-200 px-2 py-0.5 text-xs font-medium text-slate-500 transition-colors hover:bg-slate-50"
              @click="addCookEventRow"
            >
              <Icon :path="icons.plus" :size="12" />
              De una cocción
            </button>
            <button
              type="button"
              class="inline-flex items-center gap-1 rounded-md border border-slate-200 px-2 py-0.5 text-xs font-medium text-slate-500 transition-colors hover:bg-slate-50"
              @click="addManualRow"
            >
              <Icon :path="icons.plus" :size="12" />
              Manual
            </button>
          </div>
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
              <span
                class="flex shrink-0 items-center rounded-md bg-slate-100 px-1.5 py-0.5 text-[11px] font-semibold text-slate-500"
              >
                Alimento {{ rows.indexOf(row) + 1 }}
              </span>
              <select
                :value="row.kind"
                class="rounded-md border border-slate-200 bg-white px-2 py-1 text-xs font-medium text-slate-600 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
                @change="changeRowKind(row, $event)"
              >
                <option value="cook_event">Cocción</option>
                <option value="manual">Manual</option>
              </select>
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
                class="min-w-0 flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
              >
                <option :value="null" disabled>Selecciona una cocción</option>
                <option
                  v-for="ce in props.cookEvents"
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
                class="w-8 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100 [appearance:textfield] [&::-webkit-inner-spin-button]:m-0 [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
              />
              <span class="text-xs text-slate-400">porc.</span>
            </div>

            <div v-else class="mt-2 space-y-2">
              <input
                v-model="row.name"
                type="text"
                placeholder="Nombre del alimento"
                class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
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
                    class="w-full rounded-lg border border-slate-200 px-2 py-1.5 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100 [appearance:textfield] [&::-webkit-inner-spin-button]:m-0 [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
                  />
                </div>
              </div>
            </div>
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
