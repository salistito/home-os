<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { ApiRequestError } from "../../api/client";
import { fitnessApi } from "../../api/fitness";
import DateInput from "../../components/DateInput.vue";
import Icon from "../../components/Icon.vue";
import Modal from "../../components/Modal.vue";
import SelectMenu, { type SelectOption } from "../../components/SelectMenu.vue";
import { getToday } from "../../lib/date";
import { icons } from "../../lib/icons";
import type {
  Exercise,
  ExerciseEntry,
  ExerciseMetrics,
  Routine,
  SetBreakdownRow,
} from "../../types";

const MAX_EXERCISE_SET_ROWS = 50;
const MAX_SET_NAME_LEN = 60;
const MAX_WEIGHT_KG = 500;
const MAX_REPS = 1000;
const MAX_SETS = 100;

const MAX_METRICS_KEYS = 15;
const MAX_METRIC_KEY_LEN = 40;
const MAX_METRIC_STR_LEN = 50;

const props = defineProps<{ exerciseEntry?: ExerciseEntry | null }>();
const emit = defineEmits<{ close: []; saved: [] }>();

const exercises = ref<Exercise[]>([]);
const routines = ref<Routine[]>([]);
const entryMode = ref<"exercise" | "routine">(
  props.exerciseEntry ? (props.exerciseEntry.routine_id ? "routine" : "exercise") : "routine",
);

const exerciseOptions = computed<SelectOption[]>(() =>
  exercises.value.map((e) => ({
    value: String(e.id),
    label: e.kind ? `${e.name} (${e.kind})` : e.name,
  })),
);

const routineOptions = computed<SelectOption[]>(() =>
  routines.value.map((r) => ({
    value: String(r.id),
    label: r.category ? `${r.name} (${r.category})` : r.name,
  })),
);

const routineExerciseOptions = computed<SelectOption[]>(() => {
  const routine = routines.value.find((r) => String(r.id) === routineId.value);
  if (!routine) return [];
  return routine.exercises.map((re) => {
    const exercise = exercises.value.find((e) => e.id === re.exercise_id);
    const name = re.exercise_name ?? exercise?.name ?? `#${re.exercise_id}`;
    return { value: name, label: name };
  });
});

const exerciseId = ref(
  props.exerciseEntry?.routine_id ? "" : String(props.exerciseEntry?.exercise_id ?? ""),
);
const routineId = ref(
  props.exerciseEntry?.routine_id ? String(props.exerciseEntry.routine_id) : "",
);

const durationMin = ref<number | null>(
  props.exerciseEntry ? (props.exerciseEntry.duration_min ?? null) : 30,
);
const caloriesBurned = ref<number | null>(props.exerciseEntry?.calories_burned ?? null);
const performedAt = ref(props.exerciseEntry?.performed_at ?? getToday());
const notes = ref(props.exerciseEntry?.notes ?? "");

interface SetFormRow {
  id: number;
  name: string;
  weightKg: number | null;
  reps: number | null;
  sets: number | null;
}

interface MetricFormRow {
  id: number;
  key: string;
  value: string;
}

function onBreakdownExerciseChange(row: SetFormRow, exerciseName: string) {
  row.name = exerciseName;
  if (!exerciseName) return;
  const routine = routines.value.find((r) => String(r.id) === routineId.value);
  if (!routine) return;
  const re = routine.exercises.find((e) => {
    const exercise = exercises.value.find((ex) => ex.id === e.exercise_id);
    const name = e.exercise_name ?? exercise?.name ?? `#${e.exercise_id}`;
    return name === exerciseName;
  });
  if (re) {
    row.weightKg = re.weight_kg;
    row.reps = re.reps;
    row.sets = re.sets;
  }
}

let nextRowId = 1;

const initialSets = props.exerciseEntry?.sets_breakdown ?? [];

const setRows = ref<SetFormRow[]>(
  initialSets.map((s) => ({
    id: nextRowId++,
    name: s.name ?? "",
    weightKg: s.weight_kg,
    reps: s.reps,
    sets: s.sets,
  })),
);

const metricRows = ref<MetricFormRow[]>(
  Object.entries(props.exerciseEntry?.metrics ?? {}).map(([key, value]) => ({
    id: nextRowId++,
    key,
    value: String(value),
  })),
);

function addSetRow() {
  setRows.value.push({
    id: nextRowId++,
    name: "",
    weightKg: null,
    reps: null,
    sets: null,
  });
}

function removeSetRow(row: SetFormRow) {
  setRows.value = setRows.value.filter((r) => r.id !== row.id);
}

function addMetricRow() {
  metricRows.value.push({ id: nextRowId++, key: "", value: "" });
}

function removeMetricRow(row: MetricFormRow) {
  metricRows.value = metricRows.value.filter((r) => r.id !== row.id);
}

function rowWeight(row: SetFormRow): number | null {
  return typeof row.weightKg === "number" && Number.isFinite(row.weightKg)
    ? row.weightKg
    : null;
}

function isValidSetRow(row: SetFormRow): boolean {
  const weight = rowWeight(row);
  return (
    (weight === null || (weight > 0 && weight <= MAX_WEIGHT_KG)) &&
    Number.isInteger(row.reps) &&
    (row.reps ?? 0) > 0 &&
    (row.reps ?? 0) <= MAX_REPS &&
    Number.isInteger(row.sets) &&
    row.sets !== null &&
    row.sets >= 1 &&
    row.sets <= MAX_SETS &&
    row.name.trim().length <= MAX_SET_NAME_LEN
  );
}

const filledSetRows = computed(() =>
  setRows.value.filter((r) => {
    const weight = rowWeight(r);
    return (
      r.name.trim() !== "" ||
      (weight !== null && weight !== 0) ||
      (r.reps !== null && r.reps !== 0)
    );
  }),
);

const totalReps = computed(() => {
  let reps = 0;
  for (const row of filledSetRows.value) {
    if (isValidSetRow(row)) {
      reps += (row.reps ?? 0) * (row.sets || 1);
    }
  }
  return reps;
});

const totalVolume = computed(() => {
  let volume = 0;
  for (const row of filledSetRows.value) {
    if (isValidSetRow(row)) {
      const weight = rowWeight(row);
      if (weight !== null) {
        volume += weight * (row.reps ?? 0) * (row.sets || 1);
      }
    }
  }
  return Math.round(volume * 10) / 10;
});

function validateExtraFields(): string | null {
  if (filledSetRows.value.length > MAX_EXERCISE_SET_ROWS) {
    return `Máximo ${MAX_EXERCISE_SET_ROWS} filas de desglose.`;
  }
  for (const row of filledSetRows.value) {
    if (row.name.trim().length > MAX_SET_NAME_LEN) {
      return `El nombre del ejercicio no puede superar los ${MAX_SET_NAME_LEN} caracteres.`;
    }
    const weight = rowWeight(row);
    if (weight !== null && weight <= 0) {
      return "El peso debe ser nulo o mayor a 0.";
    }
    if (weight !== null && weight > MAX_WEIGHT_KG) {
      return `El peso máximo es ${MAX_WEIGHT_KG} kg.`;
    }
    if (!Number.isInteger(row.reps) || (row.reps ?? 0) <= 0) {
      return "Las repeticiones deben ser un entero mayor a 0.";
    }
    if ((row.reps ?? 0) > MAX_REPS) {
      return `El máximo de repeticiones es ${MAX_REPS}.`;
    }
    if (row.sets === null ||!Number.isInteger(row.sets) || row.sets < 1) {
      return "Las series deben ser un entero mayor o igual a 1.";
    }
    if (row.sets > MAX_SETS) {
      return `El máximo de series es ${MAX_SETS}.`;
    }
  }

  const filledMetrics = metricRows.value.filter(
    (m) => m.key.trim() !== "" || m.value.trim() !== "",
  );
  if (filledMetrics.length > MAX_METRICS_KEYS) {
    return `Máximo ${MAX_METRICS_KEYS} métricas por entrenamiento.`;
  }
  for (const row of filledMetrics) {
    const key = row.key.trim();
    const value = row.value.trim();
    if (!key) {
      return "Cada métrica necesita una clave.";
    }
    if (key.length > MAX_METRIC_KEY_LEN) {
      return `La clave de la métrica no puede superar los ${MAX_METRIC_KEY_LEN} caracteres.`;
    }
    if (!value) {
      return `La métrica "${key}" necesita un valor.`;
    }
    if (value.length > MAX_METRIC_STR_LEN) {
      return `El valor de "${key}" no puede superar los ${MAX_METRIC_STR_LEN} caracteres.`;
    }
  }
  return null;
}

function buildSets(): SetBreakdownRow[] {
  return filledSetRows.value.map((row) => {
    const weight = rowWeight(row);
    return {
      name: row.name.trim() || null,
      weight_kg: weight !== null ? Math.round(weight * 100) / 100 : null,
      reps: row.reps ?? 0,
      sets: row.sets || 1,
    };
  });
}

function buildMetrics(): ExerciseMetrics | undefined {
  const metrics: ExerciseMetrics = {};
  for (const row of metricRows.value) {
    const key = row.key.trim();
    const raw = row.value.trim();
    if (!key || !raw) continue;
    const num = Number(raw.replace(",", "."));
    metrics[key] = Number.isFinite(num) ? Math.round(num * 100) / 100 : raw;
  }
  return Object.keys(metrics).length ? metrics : undefined;
}

const error = ref<string | null>(null);
const saving = ref(false);

async function submit() {
  error.value = null;

  if (entryMode.value === "exercise") {
    if (!exerciseId.value || Number.isNaN(Number(exerciseId.value))) {
      error.value = "Selecciona un ejercicio.";
      return;
    }
  } else {
    if (!routineId.value || Number.isNaN(Number(routineId.value))) {
      error.value = "Selecciona una rutina.";
      return;
    }
  }

  const rawDuration = durationMin.value;
  const hasValidDuration =
    typeof rawDuration === "number" &&
    Number.isFinite(rawDuration) &&
    rawDuration > 0;
  if (
    rawDuration !== null &&
    typeof rawDuration === "number" &&
    (!Number.isFinite(rawDuration) || rawDuration <= 0)
  ) {
    error.value = "La duración debe ser mayor a 0 minutos.";
    return;
  }

  const sets = buildSets();
  if (!hasValidDuration && !sets.length) {
    error.value = "Registra una duración o al menos un desglose.";
    return;
  }

  const metricsError = validateExtraFields();
  if (metricsError) {
    error.value = metricsError;
    return;
  }

  saving.value = true;
  try {
    const basePayload = {
      calories_burned:
        caloriesBurned.value !== null && !Number.isNaN(caloriesBurned.value)
          ? caloriesBurned.value
          : undefined,
      metrics: buildMetrics(),
      notes: notes.value.trim() || undefined,
      performed_at: performedAt.value,
    };

    if (props.exerciseEntry) {
      await fitnessApi.updateExerciseEntry(props.exerciseEntry.id, {
        ...basePayload,
        exercise_id: entryMode.value === "exercise" ? Number(exerciseId.value) : undefined,
        routine_id: entryMode.value === "routine" ? Number(routineId.value) : undefined,
        duration_min: hasValidDuration ? Math.round(rawDuration as number) : null,
        sets_breakdown: sets,
      });
    } else {
      if (entryMode.value === "exercise") {
        await fitnessApi.logExerciseEntry({
          ...basePayload,
          exercise_id: Number(exerciseId.value),
          ...(hasValidDuration ? { duration_min: Math.round(rawDuration as number) } : {}),
          ...(sets.length ? { sets_breakdown: sets } : {}),
        });
      } else {
        await fitnessApi.logExerciseEntry({
          ...basePayload,
          routine_id: Number(routineId.value),
          ...(hasValidDuration ? { duration_min: Math.round(rawDuration as number) } : {}),
          ...(sets.length ? { sets_breakdown: sets } : {}),
        });
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

watch(entryMode, () => {
  setRows.value = [];
});

onMounted(async () => {
  try {
    const [e, r] = await Promise.all([
      fitnessApi.listExercises(),
      fitnessApi.listRoutines(),
    ]);
    exercises.value = e;
    routines.value = r;
  } catch {
    exercises.value = [];
    routines.value = [];
  }
});
</script>

<template>
  <Modal
    :title="exerciseEntry ? 'Editar entrenamiento' : 'Registrar entrenamiento'"
    @close="emit('close')"
  >
    <form class="space-y-4" @submit.prevent="submit">
      <div class="flex rounded-lg border border-slate-200 bg-slate-50 p-0.5">
        <button
          type="button"
          class="flex-1 rounded-md px-3 py-1.5 text-xs font-medium transition-colors"
          :class="
            entryMode === 'routine'
              ? 'bg-white text-slate-900 shadow-sm'
              : 'text-slate-500 hover:text-slate-700'
          "
          @click="entryMode = 'routine'"
        >
          Rutina completa
        </button>
        <button
          type="button"
          class="flex-1 rounded-md px-3 py-1.5 text-xs font-medium transition-colors"
          :class="
            entryMode === 'exercise'
              ? 'bg-white text-slate-900 shadow-sm'
              : 'text-slate-500 hover:text-slate-700'
          "
          @click="entryMode = 'exercise'"
        >
          Ejercicio individual
        </button>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div v-if="entryMode === 'exercise'">
          <label class="mb-1 block text-xs font-medium text-slate-500">
            Ejercicio
          </label>
          <SelectMenu
            v-model="exerciseId"
            :options="exerciseOptions"
            placeholder="Elegir ejercicio…"
          />
        </div>
        <div v-else>
          <label class="mb-1 block text-xs font-medium text-slate-500">
            Rutina
          </label>
          <SelectMenu
            v-model="routineId"
            :options="routineOptions"
            placeholder="Elegir rutina…"
          />
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">
            Duración (Opcional)
          </label>
          <div class="flex h-11 items-center gap-1.5">
            <input
              v-model.number="durationMin"
              type="number"
              min="1"
              step="1"
              class="min-w-0 flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
            />
            <span
              class="shrink-0 rounded-md bg-slate-100 px-2 py-1.5 text-xs font-medium text-slate-500">
              min
            </span>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">
            Calorías (Opcional)
          </label>
          <div class="flex h-11 items-center gap-1.5">
            <input
              v-model.number="caloriesBurned"
              type="number"
              min="0"
              step="any"
              class="min-w-0 flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
            />
            <span
              class="shrink-0 rounded-md bg-slate-100 px-2 py-1.5 text-xs font-medium text-slate-500">
              kcal
            </span>
          </div>
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">
            Fecha del entrenamiento
          </label>
          <DateInput v-model="performedAt" :max="getToday()" />
        </div>
      </div>

      <div class="rounded-lg border border-slate-100 bg-slate-50/50">
        <div class="flex items-center justify-between gap-2 px-3 py-2.5">
          <div class="flex min-w-0 items-center gap-2">
            <span
              class="shrink-0 text-xs font-semibold tracking-wider text-slate-400"
            >
              Desglose y Volumen (Opcional)
            </span>
          </div>
          <button
            type="button"
            class="shrink-0 rounded-md border border-slate-200 bg-white px-2 py-0.5 text-xs font-medium text-slate-500 transition-colors hover:bg-slate-50"
            @click="addSetRow"
          >
            + Añadir
          </button>
        </div>
        <div class="border-t border-slate-100 px-3 py-3">
          <p class="mb-3 text-xs text-slate-500">
            Desglosa tu entrenamiento en peso, reps y series por ejercicio para registrar repeticiones totales o calcular el volumen del entrenamiento. 
          </p>
          <p
            v-if="!setRows.length"
            class="text-center text-xs text-slate-400"
          >
          <span>Reps totales = Reps × Series</span><br />
          <span>Volumen entrenamiento = Peso × Reps × Series</span>
          </p>
          <div v-else class="space-y-3">
            <div
              v-for="(row, index) in setRows"
              :key="row.id"
              class="space-y-2 rounded-lg border border-slate-100 bg-white p-2"
            >
              <div class="flex items-center justify-between">
                <span
                  class="flex items-center rounded-md bg-slate-100 px-1.5 py-0.5 text-[11px] font-semibold text-slate-500"
                >
                  Desglose {{ index + 1 }}
                </span>
                <button
                  type="button"
                  class="shrink-0 rounded-lg p-1 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-500"
                  @click="removeSetRow(row)"
                >
                  <Icon :path="icons.trash" :size="14" />
                </button>
              </div>
              <div>
                <div class="grid grid-cols-[minmax(0,1fr)_2rem] gap-2 px-1 text-[10px] font-medium uppercase tracking-wider text-slate-400">
                  <span>Ejercicio</span>
                  <span></span>
                </div>
                <SelectMenu
                  v-if="entryMode === 'routine' && routineExerciseOptions.length"
                  :modelValue="row.name"
                  @update:modelValue="onBreakdownExerciseChange(row, $event)"
                  :options="routineExerciseOptions"
                  placeholder="Elegir ejercicio…"
                />
                <input
                  v-else
                  v-model="row.name"
                  placeholder="Curl de bíceps"
                  class="min-w-0 w-full rounded-lg border border-slate-200 px-2 py-1.5 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
                />
              </div>
              <div>
                <div class="grid grid-cols-[1fr_2.5rem_1fr_1fr] gap-2 px-1 text-[10px] font-medium uppercase tracking-wider text-slate-400">
                  <span>Peso</span>
                  <span></span>
                  <span>Reps</span>
                  <span>Series</span>
                </div>
                <div class="flex items-center gap-2">
                  <input
                    v-model.number="row.weightKg"
                    type="number"
                    min="0"
                    step="any"
                    placeholder="12"
                    class="min-w-0 w-full rounded-lg border border-slate-200 px-2 py-1.5 text-sm tabular-nums text-slate-800 outline-none transition-colors [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
                  />
                  <span
                    class="shrink-0 rounded-md bg-slate-100 px-2 py-1.5 text-xs font-medium text-slate-500"
                    >kg</span
                  >
                  <input
                    v-model.number="row.reps"
                    type="number"
                    min="1"
                    step="1"
                    placeholder="15"
                    class="min-w-0 w-full rounded-lg border border-slate-200 px-2 py-1.5 text-sm tabular-nums text-slate-800 outline-none transition-colors [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
                  />
                  <input
                    v-model.number="row.sets"
                    type="number"
                    min="1"
                    step="1"
                    placeholder="3"
                    class="min-w-0 w-full rounded-lg border border-slate-200 px-2 py-1.5 text-sm tabular-nums text-slate-800 outline-none transition-colors [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
                  />
                </div>
              </div>
            </div>
          </div>
          <div
            v-if="totalReps > 0"
            class="mt-2 flex items-center justify-between rounded-lg bg-slate-100 px-3 py-2 text-sm"
          >
            <span class="text-slate-500">Repeticiones totales:</span>
            <span class="font-medium tabular-nums text-slate-900">{{ totalReps }} reps</span>
          </div>
          <div
            v-if="totalVolume > 0"
            class="mt-2 flex items-center justify-between rounded-lg bg-slate-100 px-3 py-2 text-sm"
          >
            <span class="text-slate-500">Volumen del entrenamiento:</span>
            <span class="font-medium tabular-nums text-slate-900">{{ totalVolume }} kg</span>
          </div>
        </div>
      </div>

      <div class="rounded-lg border border-slate-100 bg-slate-50/50">
        <div class="flex items-center justify-between gap-2 px-3 py-2.5">
          <span
            class="shrink-0 text-xs font-semibold tracking-wider text-slate-400"
          >
            Otras métricas (Opcional)
          </span>
          <button
            type="button"
            class="shrink-0 rounded-md border border-slate-200 bg-white px-2 py-0.5 text-xs font-medium text-slate-500 transition-colors hover:bg-slate-50"
            @click="addMetricRow"
          >
            + Añadir
          </button>
        </div>
        <div class="border-t border-slate-100 px-3 py-3">
          <p class="mb-3 text-xs text-slate-500">
            Cualquier información adicional del entrenamiento definida como pares clave-valor.
          </p>
          <p
            v-if="!metricRows.length"
            class="text-center text-xs text-slate-400"
          >
            ej: Esfuerzo, Distancia, Ritmo, etc…
          </p>
          <div v-else class="space-y-2">
            <div
              v-for="row in metricRows"
              :key="row.id"
              class="flex items-center gap-2"
            >
              <input
                v-model="row.key"
                maxlength="40"
                placeholder="Esfuerzo"
                class="w-5/12 min-w-0 shrink-0 rounded-lg border border-slate-200 px-2 py-1.5 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
              />
              <input
                v-model="row.value"
                maxlength="50"
                placeholder="5 - Moderado"
                class="min-w-0 flex-1 rounded-lg border border-slate-200 px-2 py-1.5 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
              />
              <button
                type="button"
                class="shrink-0 rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-500"
                @click="removeMetricRow(row)"
              >
                <Icon :path="icons.trash" :size="14" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500"
          >Notas (Opcional)</label
        >
        <textarea
          v-model="notes"
          rows="2"
          placeholder="We're cool for the summer…"
          class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
        />
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
          {{ saving ? "Guardando…" : "Guardar" }}
        </button>
      </div>
    </form>
  </Modal>
</template>
