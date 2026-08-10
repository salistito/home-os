<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { ApiRequestError } from "../../api/client";
import { foodApi } from "../../api/food";
import Icon from "../../components/Icon.vue";
import IconButton from "../../components/IconButton.vue";
import Modal from "../../components/Modal.vue";
import WidgetCard from "../../components/WidgetCard.vue";
import { addDays, daysOfWeek, getToday, isoWeek, startOfWeek } from "../../lib/date";
import { capitalize, formatWeekdayAndDay, formatWeekdayShort, formatYearMonth } from "../../lib/format";
import { icons } from "../../lib/icons";
import { pushToast } from "../../lib/toast";
import { MEAL_TYPE_LABELS } from "../../types";
import type {
  CookEvent,
  Ingredient,
  IngredientStock,
  MealEntry,
  MealEntryItem,
  MealType,
  NutritionGoals,
  Recipe,
} from "../../types";
import GoalsModal from "./GoalsModal.vue";
import MacroRingsStacked from "./MacroRingsStacked.vue";
import MealFormModal from "./MealFormModal.vue";
import MonthPicker from "./MonthPicker.vue";
import ProgressRing from "./ProgressRing.vue";

const props = defineProps<{
  recipes: Recipe[];
  stock: IngredientStock[];
  ingredients: Ingredient[];
}>();

const emit = defineEmits<{ reload: [] }>();

const mealTypeIcons: Record<MealType, string> = {
  breakfast: icons.coffee,
  lunch: icons.bowlChopsticks,
  dinner: icons.soup,
  snack: icons.cookie,
};

const mealOrder: MealType[] = ["breakfast", "lunch", "dinner", "snack"];

const today = getToday();
const selectedDate = ref(getToday());
const goals = ref<NutritionGoals | null>(null);
const cookEvents = ref<CookEvent[]>([]);
const entries = ref<MealEntry[]>([]);
const loading = ref(true);
const revealed = ref(false);
const error = ref<string | null>(null);

const calendarOpen = ref(false);
const goalsOpen = ref(false);
const formOpen = ref(false);
const editing = ref<MealEntry | null>(null);
const deleting = ref<{ entry: MealEntry; item: MealEntryItem } | null>(null);
const deleteBusy = ref(false);

const dayLabel = computed(() => {
  if (selectedDate.value === today) return "Hoy";
  if (selectedDate.value === addDays(today, -1)) return "Ayer";
  if (selectedDate.value === addDays(today, 1)) return "Mañana";
  return capitalize(formatWeekdayAndDay(selectedDate.value));
});
const weekStart = computed(() => startOfWeek(selectedDate.value));
const weekDays = computed(() => daysOfWeek(selectedDate.value));
const weekLabel = computed(() =>
  `${formatYearMonth(weekStart.value.slice(0, 7))} - Semana ${isoWeek(weekStart.value)}`,
);

const selectedDayEntries = computed(() =>
  entries.value.filter((e) => e.eaten_at.slice(0, 10) === selectedDate.value),
);
const selectedDayMacros = computed(() => {
  const out: Record<string, number> = { kcal: 0, protein_g: 0, carbs_g: 0, fat_g: 0, fiber_g: 0 };
  for (const entry of selectedDayEntries.value) {
    for (const key of Object.keys(out)) out[key] += entry.macros[key] ?? 0;
  }
  return out;
});

const kcalConsumed = computed(() => selectedDayMacros.value.kcal);
const kcalTarget = computed(() => goals.value?.kcal_target ?? 0);
const kcalPct = computed(() =>
  kcalTarget.value > 0 ? Math.round((kcalConsumed.value / kcalTarget.value) * 100) : 0,
);
const kcalRemaining = computed(() => kcalTarget.value - kcalConsumed.value);

const ringDefs = [
  { key: "protein_g", label: "Proteínas", unit: "g", color: "#06b6d4" },
  { key: "carbs_g", label: "Carbohidratos", unit: "g", color: "#f97316" },
  { key: "fat_g", label: "Grasas", unit: "g", color: "#22c55e" },
] as const;

const rings = computed(() =>
  ringDefs
    .filter((r) => goals.value?.[`${r.key}_target`] != null)
    .map((r) => {
      const target = goals.value![`${r.key}_target`] as number;
      return { ...r, consumed: selectedDayMacros.value[r.key], target };
    }),
);

const hasGoals = computed(() => kcalTarget.value > 0 || rings.value.length > 0);

interface MealRow {
  item: MealEntryItem;
  entry: MealEntry;
}

const selectedDayItemCount = computed(() =>
  selectedDayEntries.value.reduce((sum, e) => sum + e.items.length, 0),
);

const groupedItems = computed(() =>
  mealOrder
    .map((type) => ({
      type,
      rows: selectedDayEntries.value
        .filter((e) => e.meal_type === type)
        .flatMap((entry) => entry.items.map((item) => ({ item, entry }) as MealRow))
        .sort((a, b) => a.entry.eaten_at.localeCompare(b.entry.eaten_at)),
    }))
    .filter((group) => group.rows.length > 0),
);

function barColor(pct: number): string {
  if (pct > 100) return "bg-red-500";
  if (pct === 100) return "bg-green-500";
  if (pct >= 66) return "bg-amber-500";
  return "bg-blue-500";
}

function selectDate(date: string) {
  selectedDate.value = date;
}

function dayNumber(iso: string): number {
  return Number(iso.slice(8, 10));
}

function shiftDay(delta: number) {
  selectedDate.value = addDays(selectedDate.value, delta);
}

function shiftWeek(delta: number) {
  selectedDate.value = addDays(weekStart.value, delta * 7);
}

function onCalendarSelect(date: string) {
  calendarOpen.value = false;
  selectedDate.value = date;
}

function goToday() {
  selectedDate.value = getToday();
}

function macroSummary(macros: Record<string, number>): string {
  const parts: string[] = [];
  if (macros.kcal != null) parts.push(`${Math.round(macros.kcal)}kcal`);
  if (macros.protein_g != null) parts.push(`${Math.round(macros.protein_g)}P`);
  if (macros.carbs_g != null) parts.push(`${Math.round(macros.carbs_g)}C`);
  if (macros.fat_g != null) parts.push(`${Math.round(macros.fat_g)}G`);
  if (macros.fiber_g != null) parts.push(`${Math.round(macros.fiber_g)}F`);
  return parts.join(" · ") || "—";
}

function groupKcal(rows: MealRow[]): number {
  return Math.round(rows.reduce((sum, r) => sum + (r.item.macros.kcal ?? 0), 0));
}

function mealTime(entry: MealEntry): string {
  return entry.eaten_at.length >= 16 ? entry.eaten_at.slice(11, 16) : "";
}

function openCreate() {
  editing.value = null;
  formOpen.value = true;
}

function openEdit(entry: MealEntry) {
  editing.value = entry;
  formOpen.value = true;
}

function editFromDelete() {
  if (!deleting.value) return;
  openEdit(deleting.value.entry);
  deleting.value = null;
}

async function onSaved() {
  formOpen.value = false;
  await loadWeek();
  pushToast("Comida guardada");
}

async function onGoalsSaved() {
  goalsOpen.value = false;
  await reloadGoals();
  pushToast("Objetivos guardados");
}

function askDelete(entry: MealEntry, item: MealEntryItem) {
  deleting.value = { entry, item };
}

async function confirmDelete() {
  if (!deleting.value) return;
  deleteBusy.value = true;
  try {
    await foodApi.deleteMeal(deleting.value.entry.id);
    deleting.value = null;
    await loadWeek();
    pushToast("Comida eliminada");
  } catch (e) {
    pushToast(
      e instanceof ApiRequestError ? e.message : "No se pudo eliminar la comida.",
      "error",
    );
  } finally {
    deleteBusy.value = false;
  }
}

async function reloadGoals() {
  try {
    goals.value = await foodApi.getNutritionGoals();
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Error inesperado";
  }
}

async function loadWeek() {
  try {
    entries.value = await foodApi.listMeals({
      from_date: weekStart.value,
      to_date: weekDays.value[6],
    });
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Error inesperado";
  }
}

async function load() {
  loading.value = true;
  error.value = null;
  try {
    const [nutritionGoals, cookedEvents, meals] = await Promise.all([

      foodApi.getNutritionGoals(),
      foodApi.listCookEvents(),
      foodApi.listMeals({
        from_date: weekStart.value,
        to_date: weekDays.value[6],
      }),
    ]);
    goals.value = nutritionGoals;
    cookEvents.value = cookedEvents;
    entries.value = meals;
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Error inesperado";
  } finally {
    loading.value = false;
  }
}

watch(weekStart, loadWeek);

defineExpose({ openCreate });

void load();

onMounted(() => {
  requestAnimationFrame(() => {
    revealed.value = true;
  });
});
</script>

<template>
  <div class="space-y-4">
    <p v-if="error" class="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-600">
      {{ error }}
    </p>

    <div class="hidden rounded-xl border border-slate-200 bg-white p-3 lg:block">
      <div class="relative mb-3 flex items-center justify-between gap-2">
        <div class="flex min-w-0 items-center gap-1">
          <IconButton dense :icon="icons.chevronLeft" label="Semana anterior" @click="shiftWeek(-1)" />
          <h3 class="whitespace-nowrap text-sm font-semibold text-slate-900">
            {{ weekLabel }}
          </h3>
          <IconButton dense :icon="icons.chevronRight" label="Semana siguiente" @click="shiftWeek(1)" />
        </div>
        <div class="flex shrink-0 items-center gap-1">
          <button
            v-if="selectedDate !== today"
            type="button"
            class="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-50"
            @click="goToday"
          >
            Hoy
          </button>
          <IconButton
            :icon="icons.calendar"
            label="Cambiar fecha"
            @click="calendarOpen = !calendarOpen"
          />
        </div>
        <div v-if="calendarOpen" class="fixed inset-0 z-10" @click="calendarOpen = false" />
        <div v-if="calendarOpen" class="absolute left-1/2 top-full z-20 mt-2 -translate-x-1/2">
          <MonthPicker
            :selected="selectedDate"
            @select="onCalendarSelect"
            @close="calendarOpen = false"
          />
        </div>
      </div>
      <div class="grid grid-cols-7 gap-1.5">
        <button
          v-for="day in weekDays"
          :key="day"
          type="button"
          class="flex flex-col items-center gap-1 rounded-lg px-1 py-2 text-xs transition-colors hover:bg-slate-50"
          :class="day === selectedDate ? 'bg-slate-100' : ''"
          @click="selectDate(day)"
        >
          <span
            class="text-[11px]"
            :class="day === selectedDate ? 'font-semibold text-slate-900' : 'text-slate-400'"
          >
            {{ formatWeekdayShort(day) }}
          </span>
          <span
            class="flex h-8 w-8 items-center justify-center rounded-full text-sm transition-colors"
            :class="[
              day === selectedDate
                ? 'bg-slate-900 font-semibold text-white'
                : day === today
                  ? 'font-semibold text-amber-600 ring-2 ring-amber-400'
                  : 'text-slate-700',
            ]"
          >
            {{ dayNumber(day) }}
          </span>
        </button>
      </div>
    </div>

    <div class="rounded-xl border border-slate-200 bg-white p-4">
      <div
        class="relative -mx-1 flex items-center justify-between gap-1 border-b border-slate-100 pb-3 lg:hidden"
      >
        <div class="flex min-w-0 items-center">
          <IconButton dense :icon="icons.chevronLeft" label="Día anterior" @click="shiftDay(-1)" />
          <button
            type="button"
            class="min-w-0 truncate rounded-lg px-1.5 py-1 text-sm font-semibold text-slate-900 transition-colors active:bg-slate-100"
            @click="calendarOpen = !calendarOpen"
          >
            {{ dayLabel }}
          </button>
          <IconButton dense :icon="icons.chevronRight" label="Día siguiente" @click="shiftDay(1)" />
        </div>
        <div class="flex shrink-0 items-center gap-0.5">
          <button
            v-if="selectedDate !== today"
            type="button"
            class="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-50"
            @click="goToday"
          >
            Hoy
          </button>
          <IconButton
            :icon="icons.calendar"
            label="Cambiar fecha"
            @click="calendarOpen = !calendarOpen"
          />
          <IconButton :icon="icons.pencil" label="Editar objetivos" @click="goalsOpen = true" />
        </div>
        <div v-if="calendarOpen" class="fixed inset-0 z-10" @click="calendarOpen = false" />
        <Transition
          enter-from-class="scale-95 opacity-0"
          leave-to-class="scale-95 opacity-0"
          enter-active-class="origin-top transition duration-150"
          leave-active-class="origin-top transition duration-100"
        >
          <div v-if="calendarOpen" class="absolute left-1/2 top-full z-20 mt-2 -translate-x-1/2">
            <MonthPicker
              :selected="selectedDate"
              @select="onCalendarSelect"
              @close="calendarOpen = false"
            />
          </div>
        </Transition>
      </div>

      <div class="hidden items-center justify-between lg:flex">
        <h3 class="text-sm font-semibold text-slate-900">Calorías y Macronutrientes</h3>
        <IconButton :icon="icons.pencil" label="Editar objetivos" @click="goalsOpen = true" />
      </div>

      <p v-if="!hasGoals" class="py-6 text-center text-sm text-slate-500">
        Para poder medir tu progreso primero debes definir tus objetivos nutricionales de calorías y macronutrientes.
      </p>

      <template v-else>
        <template v-if="kcalTarget > 0">
          <div class="mt-4 flex items-end gap-1">
            <span
              class="text-3xl font-bold tabular-nums"
              :class="kcalRemaining < 0 ? 'text-red-600' : 'text-slate-900'"
            >
              {{ Math.round(kcalConsumed) }}
            </span>
            <span class="pb-1 text-sm font-medium tabular-nums text-slate-500">
              kcal / {{ Math.round(kcalTarget) }} kcal
            </span>
          </div>
          <div class="mt-1 h-2 overflow-hidden rounded-full bg-slate-100">
            <div
              class="h-full rounded-full transition-[width,background-color] duration-700 ease-out"
              :class="barColor(kcalPct)"
              :style="{ width: revealed ? `${Math.min(kcalPct, 100)}%` : '0%' }"
            />
          </div>
          <p
            class="mt-3 text-right text-xs font-medium tabular-nums"
            :class="kcalRemaining > 0 ? 'text-slate-500' : 'text-red-600'"
          >
            {{ kcalPct }}% ·
            <span v-if="kcalRemaining > 0">
              {{ Math.round(kcalRemaining) }} kcal restantes
            </span>
            <span v-else>
              {{ Math.round(-kcalRemaining) }} kcal de exceso
            </span>
          </p>
        </template>
        <p v-else class="pt-4 text-center text-sm text-slate-500">
          Para poder medir tu progreso diario de calorías primero debes definir tus objetivos nutricionales.
        </p>

        <template v-if="rings.length">
          <MacroRingsStacked
            class="mt-4 border-t border-slate-100 pt-4 sm:hidden"
            :rings="rings"
          />
          <div class="mt-4 hidden grid-cols-3 gap-3 border-t border-slate-100 pt-4 sm:grid">
            <ProgressRing
              v-for="ring in rings"
              :key="ring.key"
              :label="ring.label"
              :consumed="ring.consumed"
              :target="ring.target"
              :unit="ring.unit"
              :color="ring.color"
            />
          </div>
        </template>
        <p v-else class="mt-4 border-t border-slate-100 pt-4 text-center text-sm text-slate-500">
          Para poder medir tu progreso diario de proteínas, carbohidratos y grasas primero debes definir tus objetivos nutricionales.
        </p>
      </template>
    </div>

    <WidgetCard title="Registro de comidas" :count="selectedDayItemCount">
      <template #actions>
        <button
          type="button"
          class="hidden items-center gap-1 rounded-lg bg-slate-900 px-2.5 py-1.5 text-xs font-medium text-white transition-colors hover:bg-slate-700 lg:inline-flex"
          @click="openCreate"
        >
          <Icon :path="icons.plus" :size="14" />
          Registrar
        </button>
      </template>

      <p
        v-if="!loading && !selectedDayEntries.length"
        class="px-4 py-10 text-center text-sm text-slate-500"
      >
        No hay comidas registradas este día.
      </p>

      <div v-else class="divide-y divide-slate-100">
        <div v-for="group in groupedItems" :key="group.type">
          <div class="flex items-center justify-between bg-slate-100/50 px-4 py-2">
            <h4 class="text-xs font-semibold tracking-wider text-slate-900">
              {{ MEAL_TYPE_LABELS[group.type] }}
            </h4>
            <span class="text-xs font-semibold tabular-nums text-slate-900">
              {{ groupKcal(group.rows) }} kcal
            </span>
          </div>
          <ul class="divide-y divide-slate-100">
            <li
              v-for="row in group.rows"
              :key="row.item.id"
              class="group flex items-center gap-3 px-4 py-3 transition-colors hover:bg-slate-50"
            >
              <span
                class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-slate-100 text-slate-500"
              >
                <Icon :path="mealTypeIcons[row.entry.meal_type]" :size="16" />
              </span>
              <div class="min-w-0 flex-1">
                <div class="flex flex-wrap items-center gap-x-1">
                  <span class="text-[13px] font-medium text-slate-800">
                    {{ row.item.name }}
                  </span>
                </div>
                <div class="mt-1 flex flex-wrap items-center gap-2">
                  <span
                    v-if="row.item.portions != null"
                    class="inline-flex items-center gap-1 rounded-md bg-slate-50 px-2 py-0.5 text-xs tabular-nums text-slate-700 ring-1 ring-slate-200"
                  >
                    <Icon :path="icons.utensils" :size="12" class="shrink-0 text-slate-400" />
                    {{ row.item.portions }} porc.
                  </span>
                  <span
                    v-if="mealTime(row.entry)"
                    class="inline-flex items-center gap-1 rounded-md bg-slate-50 px-2 py-0.5 text-xs tabular-nums text-slate-700 ring-1 ring-slate-200"
                  >
                    <Icon :path="icons.clock" :size="12" class="shrink-0 text-slate-400" />
                    {{ mealTime(row.entry) }}
                  </span>
                </div>
                <p class="mt-1 text-xs text-slate-600">
                  {{ macroSummary(row.item.macros) }}
                </p>
                <p v-if="row.entry.notes" class="mt-1 text-xs text-slate-500">
                  {{ row.entry.notes }}
                </p>
              </div>
              <span
                class="flex shrink-0 items-center gap-1 transition-opacity sm:opacity-0 sm:group-hover:opacity-100"
              >
                <IconButton
                  :icon="icons.pencil"
                  label="Editar"
                  @click="openEdit(row.entry)"
                />
                <IconButton
                  :icon="icons.trash"
                  label="Eliminar"
                  variant="danger"
                  @click="askDelete(row.entry, row.item)"
                />
              </span>
            </li>
          </ul>
        </div>
      </div>
    </WidgetCard>

    <GoalsModal
      v-if="goalsOpen"
      :goals="goals"
      @close="goalsOpen = false"
      @saved="onGoalsSaved"
    />
    
    <MealFormModal
      v-if="formOpen"
      :entry="editing"
      :cook-events="cookEvents"
      :recipes="props.recipes"
      :stock="props.stock"
      :ingredients="props.ingredients"
      :default-date="selectedDate"
      @close="formOpen = false"
      @saved="onSaved"
      @reload="emit('reload')"
    />

    <Modal v-if="deleting" title="Eliminar comida" @close="deleting = null">
      <div v-if="deleting.entry.items.length > 1" class="space-y-3 text-sm">
        <p class="text-slate-600">
          <span class="font-medium text-slate-900">{{ deleting.item.name }}</span>
          pertenece a un registro de comida con múltiples alimentos.
        </p>
        <div class="rounded-lg bg-amber-50 px-3 py-2 text-amber-700 ring-1 ring-amber-100">
          <p class="font-medium">
            Al eliminar, se borrará la comida completa con todos sus alimentos, no solo esta entrada.
          </p>
        </div>
        <p class="text-slate-600">
          Si solo quieres eliminar
          <span class="font-medium text-slate-900">{{ deleting.item.name }}</span>,
          edita la comida para quitar ese alimento desde ahí.
        </p>
      </div>
      <p v-else class="text-sm text-slate-600">
        ¿Seguro que quieres eliminar esta comida?
      </p>
      <div
        class="mt-5 flex gap-2"
        :class="deleting.entry.items.length > 1 ? 'flex-col sm:flex-row sm:justify-end' : 'justify-end'"
      >
        <button
          type="button"
          class="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100"
          @click="deleting = null"
        >
          Cancelar
        </button>
        <button
          v-if="deleting.entry.items.length > 1"
          type="button"
          class="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50"
          @click="editFromDelete"
        >
          Editar comida
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
  </div>
</template>
