<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { ApiRequestError } from "../../api/client";
import { fitnessApi } from "../../api/fitness";
import Icon from "../../components/Icon.vue";
import IconButton from "../../components/IconButton.vue";
import Modal from "../../components/Modal.vue";
import MonthPicker from "../../components/MonthPicker.vue";
import WidgetCard from "../../components/WidgetCard.vue";
import { addDays, daysOfWeek, getToday, isoWeek, startOfWeek } from "../../lib/date";
import {
  capitalize,
  formatWeekdayAndDay,
  formatWeekdayAndDayShort,
  formatWeekdayShort,
  formatYearMonth,
} from "../../lib/format";
import { icons } from "../../lib/icons";
import { pushToast } from "../../lib/toast";
import type {
  FitnessStats,
  SetBreakdownRow,
  WorkoutEntry,
} from "../../types";
import WorkoutEntriesFormModal from "./WorkoutEntriesFormModal.vue";
import WorkoutEntriesTabSkeleton from "./WorkoutEntriesTabSkeleton.vue";

const props = defineProps<{ loading: boolean }>();
const emit = defineEmits<{ reload: [] }>();

const today = getToday();
const viewMode = ref<"day" | "week">("week");
const selectedDate = ref(getToday());

const workoutEntries = ref<WorkoutEntry[]>([]);
const fitnessStats = ref<FitnessStats | null>(null);
const loading = ref(true);
const revealed = ref(false);
const error = ref<string | null>(null);

const calendarOpen = ref(false);
const topOpen = ref(false);
const breakdownOpen = ref(false);
const formOpen = ref(false);
const editing = ref<WorkoutEntry | null>(null);
const deleting = ref<WorkoutEntry | null>(null);
const deleteBusy = ref(false);

function dayLabelFor(day: string): string {
  if (day === today) return "Hoy";
  if (day === addDays(today, -1)) return "Ayer";
  if (day === addDays(today, 1)) return "Mañana";
  return capitalize(formatWeekdayAndDay(day));
}
const dayLabel = computed(() => dayLabelFor(selectedDate.value));
const weekStart = computed(() => startOfWeek(selectedDate.value));
const weekDays = computed(() => daysOfWeek(selectedDate.value));
const weekLabel = computed(() =>
  `${formatYearMonth(weekStart.value.slice(0, 7))} - Semana ${isoWeek(weekStart.value)}`,
);

interface WorkoutEntriesStats {
  minutes: number;
  kcal: number;
  volume: number;
  reps: number;
}

function calculateWorkoutEntriesStats(entries: WorkoutEntry[]): WorkoutEntriesStats {
  const out: WorkoutEntriesStats = { minutes: 0, kcal: 0, volume: 0, reps: 0 };
  for (const entry of entries) {
    out.minutes += entry.duration_min ?? 0;
    out.kcal += entry.calories_burned ?? 0;
    out.volume += entry.volume_kg ?? 0;
    out.reps += entry.total_reps ?? 0;
  }
  return out;
}

const selectedDayEntries = computed(() =>
  workoutEntries.value.filter((e) => e.performed_at.slice(0, 10) === selectedDate.value),
);
const dayTotals = computed(() => calculateWorkoutEntriesStats(selectedDayEntries.value));
const weekTotals = computed(() => calculateWorkoutEntriesStats(workoutEntries.value));
const activeTotals = computed(() =>
  viewMode.value === "day"
    ? { stats: dayTotals.value, count: selectedDayEntries.value.length }
    : { stats: weekTotals.value, count: workoutEntries.value.length },
);
const visibleCount = computed(() =>
  viewMode.value === "day"
    ? selectedDayEntries.value.length
    : workoutEntries.value.length,
);
const dayEntryCounts = computed(() => {
  const counts = new Map<string, number>();
  for (const entry of workoutEntries.value) {
    const day = entry.performed_at.slice(0, 10);
    counts.set(day, (counts.get(day) ?? 0) + 1);
  }
  return counts;
});

const topExercises = computed(() =>
  Object.entries(fitnessStats.value?.by_exercise_last_30d ?? {})
    .sort((a, b) => b[1].count - a[1].count)
    .slice(0, 5)
    .map(([name, { count, minutes }]) => ({ name, count, minutes })),
);

interface DayBar {
  day: string;
  minutes: number;
  kcal: number;
  pct: number;
  hasEntries: boolean;
}

const dayBars = computed<DayBar[]>(() => {
  const weekStats = weekDays.value.map((day) => {
    const dayEntries = workoutEntries.value.filter(
      (e) => e.performed_at.slice(0, 10) === day,
    );
    const stats = calculateWorkoutEntriesStats(dayEntries);
    return {
      day,
      minutes: Math.round(stats.minutes),
      kcal: Math.round(stats.kcal),
      pct: 0,
      hasEntries: dayEntries.length > 0,
    };
  });
  const maxMinutes = Math.max(1, ...weekStats.map((b) => b.minutes));
  return weekStats.map((b) => ({ ...b, pct: Math.round((b.minutes / maxMinutes) * 100) }));
});

function barFillHeight(bar: DayBar): string {
  if (!revealed.value) return "0%";
  if (bar.minutes > 0) return `${Math.max(bar.pct, 10)}%`;
  if (bar.hasEntries) return "100%";
  return "0%";
}

interface WorkoutGroup {
  day: string;
  label: string;
  stats: WorkoutEntriesStats;
  workoutEntries: WorkoutEntry[];
}

const workoutGroup = computed<WorkoutGroup[]>(() => {
  const visible =
    viewMode.value === "day" ? selectedDayEntries.value : workoutEntries.value;
  const sortedEntries = [...visible].sort((a, b) =>
    b.performed_at.localeCompare(a.performed_at),
  );
  const byDay = new Map<string, WorkoutEntry[]>();
  for (const entry of sortedEntries) {
    const day = entry.performed_at.slice(0, 10);
    const workoutEntries = byDay.get(day);
    if (workoutEntries) workoutEntries.push(entry);
    else byDay.set(day, [entry]);
  }
  return Array.from(byDay.entries()).map(([day, workoutEntries]) => ({
    day,
    label: dayLabelFor(day),
    stats: calculateWorkoutEntriesStats(workoutEntries),
    workoutEntries,
  }));
});

function setsOf(entry: WorkoutEntry): SetBreakdownRow[] {
  return entry.sets_breakdown ?? [];
}

function otherMetricsOf(entry: WorkoutEntry): [string, string | number][] {
  const result: [string, string | number][] = [];
  for (const [key, value] of Object.entries(entry.metrics)) {
    if (typeof value === "number" || typeof value === "string") {
      result.push([key, value]);
    }
  }
  return result;
}

function formatNumber(value: number): string {
  return String(Math.round(value * 100) / 100);
}

function setBreakdownRowLabel(row: SetBreakdownRow): string {
  const weight = row.weight_kg !== null ? `${formatNumber(row.weight_kg)} kg` : "";
  const reps = row.reps !== null ? `${row.weight_kg !== null ? ` × ${row.reps}` : ` ${row.reps}`} reps` : "";
  const sets = row.sets > 1 ? `${row.weight_kg !== null || row.reps !== null ? ` × ${row.sets}` : ` ${row.sets}`} sets` : "";
  return `${row.exercise_name}: ${weight}${reps}${sets}`;
}

function dayNumber(iso: string): number {
  return Number(iso.slice(8, 10));
}

function selectDate(date: string) {
  selectedDate.value = date;
}

function shiftDay(delta: number) {
  selectedDate.value = addDays(selectedDate.value, delta);
}

function shiftWeek(delta: number) {
  selectedDate.value = addDays(weekStart.value, delta * 7);
}

function shiftCurrent(delta: number) {
  if (viewMode.value === "day") shiftDay(delta);
  else shiftWeek(delta);
}

function onCalendarSelect(date: string) {
  calendarOpen.value = false;
  selectedDate.value = date;
}

function goToday() {
  selectedDate.value = getToday();
}

async function load() {
  loading.value = true;
  error.value = null;
  try {
    const [entries, stats] = await Promise.all([
      fitnessApi.listWorkoutEntries({
        from_date: weekStart.value,
        to_date: weekDays.value[6],
        limit: 200,
      }),
      fitnessApi.getStats(),
    ]);
    workoutEntries.value = entries;
    fitnessStats.value = stats;
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Error inesperado";
  } finally {
    loading.value = false;
  }
}

async function loadWeek() {
  try {
    workoutEntries.value = await fitnessApi.listWorkoutEntries({
      from_date: weekStart.value,
      to_date: weekDays.value[6],
      limit: 200,
    });
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Error inesperado";
  }
}

function openCreate() {
  editing.value = null;
  formOpen.value = true;
}

function openEdit(entry: WorkoutEntry) {
  editing.value = entry;
  formOpen.value = true;
}

function onSaved() {
  formOpen.value = false;
  void load();
  emit("reload");
  pushToast("Entrenamiento guardado");
}

async function confirmDelete() {
  if (!deleting.value || deleteBusy.value) return;
  deleteBusy.value = true;
  try {
    await fitnessApi.deleteWorkoutEntry(deleting.value.id);
    deleting.value = null;
    void load();
    emit("reload");
    pushToast("Entrenamiento eliminado");
  } catch (e) {
    pushToast(
      e instanceof ApiRequestError ? e.message : "Error al eliminar",
      "error",
    );
  } finally {
    deleteBusy.value = false;
  }
}

defineExpose({ openCreate });

void load();

watch(weekStart, loadWeek);

onMounted(() => {
  requestAnimationFrame(() => {
    revealed.value = true;
  });
});
</script>

<template>
  <div class="space-y-4">
    <WorkoutEntriesTabSkeleton v-if="props.loading || loading" />

    <template v-else>
      <p v-if="error" class="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-600">
        {{ error }}
      </p>

      <template v-else>
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
                      ? 'font-semibold text-emerald-600 ring-2 ring-emerald-400'
                      : 'text-slate-700',
                ]"
              >
                {{ dayNumber(day) }}
              </span>
              <span class="h-3.5 text-[9px] leading-3">
                <span
                  v-if="(dayEntryCounts.get(day) ?? 0) > 0"
                  class="inline-flex h-3.5 min-w-3.5 items-center justify-center rounded-full bg-emerald-400 px-1 font-semibold tabular-nums text-emerald-900"
                >
                  {{ dayEntryCounts.get(day) }}
                </span>
              </span>
            </button>
          </div>
        </div>

        <div class="rounded-xl border border-slate-200 bg-white p-4">
          <div
            class="relative -mx-1 flex items-center justify-between gap-1 border-b border-slate-100 pb-3 lg:hidden"
          >
            <div class="flex min-w-0 items-center">
              <IconButton
                dense
                :icon="icons.chevronLeft"
                :label="viewMode === 'day' ? 'Día anterior' : 'Semana anterior'"
                @click="shiftCurrent(-1)"
              />
              <button
                type="button"
                class="min-w-0 truncate rounded-lg px-1.5 py-1 text-sm font-semibold text-slate-900 transition-colors active:bg-slate-100"
                @click="calendarOpen = !calendarOpen"
              >
                {{ viewMode === "day" ? dayLabel : weekLabel }}
              </button>
              <IconButton
                dense
                :icon="icons.chevronRight"
                :label="viewMode === 'day' ? 'Día siguiente' : 'Semana siguiente'"
                @click="shiftCurrent(1)"
              />
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

          <div class="mt-3 flex items-start justify-between gap-2 lg:hidden">
            <div class="flex min-w-0 items-center gap-2 max-[420px]:flex-wrap">
              <h3 class="text-sm font-semibold text-slate-900">Resumen de Actividad</h3>
              <div class="flex shrink-0 rounded-lg bg-slate-100 p-0.5">
                <button
                  type="button"
                  class="rounded-md px-2 py-1 text-xs font-medium transition-colors"
                  :class="viewMode === 'day' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'"
                  @click="viewMode = 'day'"
                >
                  Día
                </button>
                <button
                  type="button"
                  class="rounded-md px-2 py-1 text-xs font-medium transition-colors"
                  :class="viewMode === 'week' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'"
                  @click="viewMode = 'week'"
                >
                  Semana
                </button>
              </div>
            </div>
          </div>

          <div class="hidden items-center justify-between lg:flex">
            <div class="flex items-center gap-2">
              <h3 class="text-sm font-semibold text-slate-900">Resumen de Actividad</h3>
              <div class="flex rounded-lg bg-slate-100 p-0.5">
                <button
                  type="button"
                  class="rounded-md px-2.5 py-1 text-xs font-medium transition-colors"
                  :class="viewMode === 'day' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'"
                  @click="viewMode = 'day'"
                >
                  Día
                </button>
                <button
                  type="button"
                  class="rounded-md px-2.5 py-1 text-xs font-medium transition-colors"
                  :class="viewMode === 'week' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'"
                  @click="viewMode = 'week'"
                >
                  Semana
                </button>
              </div>
            </div>
          </div>

          <p
            v-if="!visibleCount"
            class="mt-4 py-6 text-center text-sm text-slate-500"
          >
            No hay entrenamientos registrados
            {{ viewMode === "day" ? "este día" : "esta semana" }}.
          </p>

          <template v-else>
            <div class="mt-4 flex flex-wrap items-center gap-2">
              <span
                class="inline-flex items-center gap-2 rounded-xl bg-slate-50 px-3.5 py-2.5 ring-1 ring-slate-200"
              >
                <Icon :path="icons.fitness" :size="18" class="shrink-0 text-slate-400" />
                <span class="text-base font-semibold tabular-nums text-slate-800">
                  {{ visibleCount }}
                  {{ visibleCount === 1 ? "entrenamiento" : "entrenamientos" }}
                </span>
              </span>
              <span
                class="inline-flex items-center gap-2 rounded-xl bg-slate-50 px-3.5 py-2.5 ring-1 ring-slate-200"
              >
                <Icon :path="icons.clock" :size="18" class="shrink-0 text-slate-400" />
                <span class="text-base font-semibold tabular-nums text-slate-800">
                  {{
                    activeTotals.stats.minutes === 0
                      ? "Sin info"
                      : `${Math.round(activeTotals.stats.minutes)} min`
                  }}
                </span>
              </span>
              <span
                v-if="activeTotals.stats.kcal > 0"
                class="inline-flex items-center gap-2 rounded-xl bg-slate-50 px-3.5 py-2.5 ring-1 ring-slate-200"
              >
                <Icon :path="icons.flame" :size="18" class="shrink-0 text-slate-400" />
                <span class="text-base font-semibold tabular-nums text-slate-800">
                  {{ Math.round(activeTotals.stats.kcal) }} kcal
                </span>
              </span>
              <span
                v-if="activeTotals.stats.volume > 0"
                class="inline-flex items-center gap-2 rounded-xl bg-slate-50 px-3.5 py-2.5 ring-1 ring-slate-200"
              >
                <Icon :path="icons.dumbbell" :size="18" class="shrink-0 text-slate-400" />
                <span class="text-base font-semibold tabular-nums text-slate-800">
                  Vol {{ formatNumber(activeTotals.stats.volume) }} kg
                </span>
              </span>
              <span
                v-if="activeTotals.stats.volume === 0 && activeTotals.stats.reps > 0"
                class="inline-flex items-center gap-2 rounded-xl bg-slate-50 px-3.5 py-2.5 ring-1 ring-slate-200"
              >
                <Icon :path="icons.repeat" :size="18" class="shrink-0 text-slate-400" />
                <span class="text-base font-semibold tabular-nums text-slate-800">
                  {{ Math.round(activeTotals.stats.reps) }} reps
                </span>
              </span>
            </div>

            <div v-if="topExercises.length" class="mt-4 border-t border-slate-100 pt-4">
              <button
                type="button"
                class="flex w-full items-center justify-between text-left"
                @click="topOpen = !topOpen"
              >
                <h4 class="text-xs font-semibold text-slate-900">Ejercicios más entrenados</h4>
                <span class="flex items-center gap-2">
                  <span class="text-xs text-slate-400">Últimos 30 días</span>
                  <Icon
                    :path="topOpen ? icons.chevronUp : icons.chevronDown"
                    :size="16"
                    class="shrink-0 text-slate-400"
                  />
                </span>
              </button>
              <ol v-show="topOpen" class="mt-3 space-y-2.5">
                <li
                  v-for="(exercise, index) in topExercises"
                  :key="exercise.name"
                  class="flex items-center gap-2.5"
                >
                  <span
                    class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold tabular-nums"
                    :class="
                      index === 0 ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'
                    "
                  >
                    {{ index + 1 }}
                  </span>
                  <span
                    class="min-w-0 flex-1 truncate text-[13px] font-medium capitalize text-slate-800"
                  >
                    {{ exercise.name }}
                  </span>
                  <span
                    class="inline-flex shrink-0 items-center gap-1 rounded-md bg-slate-50 px-2 py-0.5 text-xs tabular-nums text-slate-700 ring-1 ring-slate-200"
                  >
                    {{ exercise.count }} {{ exercise.count === 1 ? "sesión" : "sesiones" }}
                  </span>
                </li>
              </ol>
            </div>

            <div v-if="viewMode === 'week'" class="mt-4 border-t border-slate-100 pt-4">
              <button
                type="button"
                class="flex w-full items-center justify-between text-left"
                @click="breakdownOpen = !breakdownOpen"
              >
                <h4 class="text-xs font-semibold text-slate-900">Desglose por día</h4>
                <Icon
                  :path="breakdownOpen ? icons.chevronUp : icons.chevronDown"
                  :size="16"
                  class="text-slate-400"
                />
              </button>
              <div v-show="breakdownOpen">
                <div class="mt-3 flex flex-wrap justify-center gap-2 sm:grid sm:grid-cols-7 sm:gap-1.5">
                  <div
                    v-for="bar in dayBars"
                    :key="bar.day"
                    class="flex w-[calc(25%-0.375rem)] flex-col items-center gap-1 sm:w-auto"
                  >
                    <div class="relative flex h-16 w-full items-end overflow-hidden rounded-md bg-slate-100">
                      <div
                        class="absolute inset-x-0 bottom-0 rounded-md bg-emerald-500 transition-[height] duration-700 ease-out"
                        :style="{ height: barFillHeight(bar) }"
                      />
                      <span
                        v-if="bar.minutes > 0"
                        class="absolute inset-0 flex items-center justify-center text-xs font-semibold tabular-nums text-slate-900"
                      >
                        {{ bar.minutes }} min
                      </span>
                      <span
                        v-else-if="bar.hasEntries"
                        class="absolute inset-0 flex items-center justify-center text-xs font-semibold text-slate-900"
                      >
                        Sin info
                      </span>
                      <span
                        v-else
                        class="absolute inset-0 flex items-center justify-center text-xs tabular-nums text-slate-300"
                      >
                        0 min
                      </span>
                    </div>
                    <span class="whitespace-nowrap text-center text-xs font-medium leading-tight text-slate-800">
                      {{ formatWeekdayAndDayShort(bar.day) }}
                    </span>
                    <span
                      v-if="bar.kcal > 0 || bar.hasEntries"
                      class="inline-flex items-center gap-1 whitespace-nowrap text-xs font-medium leading-tight tabular-nums text-slate-500"
                    >
                      <Icon :path="icons.flame" :size="12" class="shrink-0 text-slate-400" />
                      <template v-if="bar.kcal > 0">{{ bar.kcal }} kcal</template>
                      <template v-else>Sin info</template>
                    </span>
                    <span
                      v-else
                      class="whitespace-nowrap text-center text-xs font-medium leading-tight tabular-nums text-slate-300"
                    >—</span>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>

        <WidgetCard title="Entrenamientos" :count="visibleCount">
          <template #actions>
            <button
              type="button"
              class="hidden items-center gap-1 rounded-lg bg-slate-900 px-2.5 py-1.5 text-xs font-medium text-white transition-colors hover:bg-slate-700 lg:inline-flex"
              @click="openCreate"
            >
              <Icon :path="icons.plus" :size="14" />
              Registrar entrenamiento
            </button>
          </template>

          <p
            v-if="!visibleCount"
            class="px-4 py-10 text-center text-sm text-slate-500"
          >
            {{
              viewMode === "day"
                ? "No hay entrenamientos registrados este día."
                : "No hay entrenamientos registrados esta semana."
            }}
          </p>

          <div v-else class="divide-y divide-slate-100">
            <div v-for="group in workoutGroup" :key="group.day">
              <div class="flex items-center justify-between bg-slate-100/50 px-4 py-2">
                <h4 class="text-xs font-semibold tracking-wider text-slate-900">
                  {{ group.label }}
                </h4>
                <span
                  class="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs font-semibold tabular-nums text-slate-900"
                >
                  <span class="inline-flex items-center gap-1">
                    <Icon :path="icons.clock" :size="12" class="shrink-0 text-slate-400" />
                    <template v-if="group.stats.minutes > 0">
                      {{ Math.round(group.stats.minutes) }} min
                    </template>
                    <template v-else>Sin info</template>
                  </span>
                  <span
                    v-if="group.stats.kcal > 0"
                    class="inline-flex items-center gap-1"
                  >
                    <Icon :path="icons.flame" :size="12" class="shrink-0 text-slate-400" />
                    {{ Math.round(group.stats.kcal) }} kcal
                  </span>
                  <span
                    v-if="group.stats.volume > 0"
                    class="inline-flex items-center gap-1"
                  >
                    <Icon :path="icons.dumbbell" :size="12" class="shrink-0 text-slate-400" />
                    Vol {{ Math.round(group.stats.volume) }} kg
                  </span>
                  <span
                    v-else-if="group.stats.reps > 0"
                    class="inline-flex items-center gap-1"
                  >
                    <Icon :path="icons.repeat" :size="12" class="shrink-0 text-slate-400" />
                    {{ Math.round(group.stats.reps) }} reps
                  </span>
                </span>
              </div>
              <ul class="divide-y divide-slate-100">
                <li
                  v-for="entry in group.workoutEntries"
                  :key="entry.id"
                  class="group flex items-center gap-3 pl-4 pr-1 py-3 transition-colors hover:bg-slate-50"
                >
                  <span class="hidden h-9 w-9 shrink-0 items-center justify-center rounded-full bg-slate-100 text-slate-500 sm:flex">
                    <Icon :path="icons.fitness" :size="16" />
                  </span>
                  <div class="min-w-0 flex-1">
                    <span class="text-[13px] font-medium capitalize text-slate-800">
                      {{ entry.routine_name ?? entry.exercise_name ?? `#${entry.exercise_id}` }}
                    </span>
                    <div class="mt-1 flex flex-wrap items-center gap-2">
                      <span
                        v-if="entry.duration_min !== null"
                        class="inline-flex items-center gap-1 rounded-md bg-slate-50 px-2 py-0.5 text-xs tabular-nums text-slate-700 ring-1 ring-slate-200"
                      >
                        <Icon :path="icons.clock" :size="12" class="shrink-0 text-slate-400" />
                        {{ entry.duration_min }} min
                      </span>
                      <span
                        v-if="entry.calories_burned !== null"
                        class="inline-flex items-center gap-1 rounded-md bg-slate-50 px-2 py-0.5 text-xs tabular-nums text-slate-700 ring-1 ring-slate-200"
                      >
                        <Icon :path="icons.flame" :size="12" class="shrink-0 text-slate-400" />
                        {{ entry.calories_burned }} kcal
                      </span>
                      <span
                        v-if="entry.volume_kg !== null"
                        class="inline-flex items-center gap-1 rounded-md bg-slate-50 px-2 py-0.5 text-xs tabular-nums text-slate-700 ring-1 ring-slate-200"
                      >
                        <Icon :path="icons.dumbbell" :size="12" class="shrink-0 text-slate-400" />
                        Vol {{ formatNumber(entry.volume_kg) }} kg
                      </span>
                      <span
                        v-else-if="entry.total_reps !== null"
                        class="inline-flex items-center gap-1 rounded-md bg-slate-50 px-2 py-0.5 text-xs tabular-nums text-slate-700 ring-1 ring-slate-200"
                      >
                        <Icon :path="icons.repeat" :size="12" class="shrink-0 text-slate-400" />
                        {{ entry.total_reps }} reps
                      </span>
                    </div>
                    <p v-if="setsOf(entry).length" class="mt-1 whitespace-pre-line text-xs tabular-nums text-slate-600">
                      {{ setsOf(entry).map(setBreakdownRowLabel).join("\n") }}
                    </p>
                    <div
                      v-if="otherMetricsOf(entry).length"
                      class="mt-1 flex flex-wrap gap-1.5"
                    >
                      <span
                        v-for="[key, value] in otherMetricsOf(entry)"
                        :key="key"
                        class="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600"
                      >
                        {{ key }}: {{ value }}
                      </span>
                    </div>
                    <p v-if="entry.notes" class="mt-1 text-xs text-slate-500">
                      {{ entry.notes }}
                    </p>
                  </div>
                  <span
                    class="flex shrink-0 items-center transition-opacity sm:opacity-0 sm:group-hover:opacity-100"
                  >
                    <IconButton
                      :icon="icons.pencil"
                      label="Editar"
                      @click="openEdit(entry)"
                    />
                    <IconButton
                      :icon="icons.trash"
                      label="Eliminar"
                      variant="danger"
                      @click="deleting = entry"
                    />
                  </span>
                </li>
              </ul>
            </div>
          </div>
        </WidgetCard>
      </template>
    </template>

    <WorkoutEntriesFormModal
      v-if="formOpen"
      :workoutEntry="editing"
      @saved="onSaved"
      @close="formOpen = false"
    />

    <Modal v-if="deleting" title="Eliminar entrenamiento" @close="deleting = null">
      <p class="text-sm text-slate-600">
        <template v-if="deleting.routine_name || deleting.exercise_name">
          ¿Seguro que quieres eliminar la sesión de entrenamiento de
          <span class="font-medium capitalize text-slate-900">{{ deleting.routine_name ?? deleting.exercise_name }}</span>?
        </template>
        <template v-else>
          ¿Seguro que quieres eliminar esta sesión de entrenamiento?
        </template>
      </p>
      <div class="mt-5 flex justify-end gap-2">
        <button
          type="button"
          class="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100"
          @click="deleting = null"
        >
          Cancelar
        </button>
        <button
          type="button"
          :disabled="deleteBusy"
          class="flex items-center gap-1.5 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-500 disabled:opacity-50"
          @click="confirmDelete"
        >
          <Icon :path="icons.trash" :size="14" />
          {{ deleteBusy ? "Eliminando…" : "Eliminar" }}
        </button>
      </div>
    </Modal>
  </div>
</template>
