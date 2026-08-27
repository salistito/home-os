<script setup lang="ts">
import { computed, ref } from "vue";
import { ApiRequestError } from "../../api/client";
import { fitnessApi } from "../../api/fitness";
import Icon from "../../components/Icon.vue";
import Modal from "../../components/Modal.vue";
import SelectMenu, { type SelectOption } from "../../components/SelectMenu.vue";
import { icons } from "../../lib/icons";
import type { Exercise, Routine } from "../../types";

const MAX_ROUTINE_NAME_LEN = 80;
const MAX_ROUTINE_CATEGORY_LEN = 40;
const MAX_ROUTINE_DESCRIPTION_LEN = 500;

const MAX_WEIGHT_KG = 500;
const MAX_REPS = 1000;
const MAX_SETS = 100;

const props = defineProps<{ routine?: Routine | null; exercises: Exercise[] }>();
const emit = defineEmits<{ close: []; saved: [] }>();

const isEdit = computed(() => props.routine != null);

const name = ref(props.routine?.name ?? "");
const category = ref(props.routine?.category ?? "");
const description = ref(props.routine?.description ?? "");

interface RoutineExerciseFormRow {
  id: number;
  exerciseId: string;
  weightKg: number | null;
  reps: number | null;
  sets: number | null;
}

let nextRowId = 1;

const exerciseRows = ref<RoutineExerciseFormRow[]>(
  [...(props.routine?.exercises ?? [])]
    .sort((a, b) => a.position - b.position)
    .map((re) => ({
      id: nextRowId++,
      exerciseId: String(re.exercise_id),
      weightKg: re.weight_kg,
      reps: re.reps,
      sets: re.sets,
    })),
);

const exerciseOptions = computed<SelectOption[]>(() =>
  props.exercises.map((e) => ({
    value: String(e.id),
    label: e.kind ? `${e.name} (${e.kind})` : e.name,
  })),
);

function addExerciseRow() {
  exerciseRows.value.push({
    id: nextRowId++,
    exerciseId: "",
    weightKg: null,
    reps: null,
    sets: null,
  });
}

function moveExerciseRow(row: RoutineExerciseFormRow, dir: -1 | 1) {
  const idx = exerciseRows.value.findIndex((r) => r.id === row.id);
  const target = idx + dir;
  if (target < 0 || target >= exerciseRows.value.length) return;
  const temp = exerciseRows.value[idx];
  exerciseRows.value[idx] = exerciseRows.value[target];
  exerciseRows.value[target] = temp;
}

function removeExerciseRow(row: RoutineExerciseFormRow) {
  exerciseRows.value = exerciseRows.value.filter((r) => r.id !== row.id);
}

const error = ref<string | null>(null);
const saving = ref(false);

async function submit() {
  error.value = null;

  if (!name.value.trim()) {
    error.value = "El nombre de la rutina es obligatorio.";
    return;
  }
  if (name.value.trim().length > MAX_ROUTINE_NAME_LEN) {
    error.value = `El nombre no puede superar los ${MAX_ROUTINE_NAME_LEN} caracteres.`;
    return;
  }
  if (category.value.trim().length > MAX_ROUTINE_CATEGORY_LEN) {
    error.value = `La categoría no puede superar los ${MAX_ROUTINE_CATEGORY_LEN} caracteres.`;
    return;
  }
  if (description.value.trim().length > MAX_ROUTINE_DESCRIPTION_LEN) {
    error.value = `La descripción no puede superar los ${MAX_ROUTINE_DESCRIPTION_LEN} caracteres.`;
    return;
  }

  const filled = exerciseRows.value.filter((r) => r.exerciseId);
  if (!filled.length) {
    error.value = "Agrega al menos un ejercicio a la rutina.";
    return;
  }
  for (const row of filled) {
    if (row.weightKg !== null && row.weightKg !== undefined) {
      if (row.weightKg <= 0 || row.weightKg > MAX_WEIGHT_KG) {
        error.value = `El peso debe estar entre 0 y ${MAX_WEIGHT_KG} kg.`;
        return;
      }
    }
    if (row.reps === null || !Number.isInteger(row.reps) || row.reps <= 0) {
      error.value = "Las repeticiones deben ser un entero mayor a 0.";
      return;
    }
    if (row.reps > MAX_REPS) {
      error.value = `El máximo de repeticiones es ${MAX_REPS}.`;
      return;
    }
    if (row.sets === null || !Number.isInteger(row.sets) || row.sets < 1) {
      error.value = "Las series deben ser un entero mayor o igual a 1.";
      return;
    }
    if (row.sets > MAX_SETS) {
      error.value = `El máximo de series es ${MAX_SETS}.`;
      return;
    }
  }

  const seen = new Set<string>();
  for (const row of filled) {
    if (seen.has(row.exerciseId)) {
      error.value = "No puedes agregar el mismo ejercicio dos veces.";
      return;
    }
    seen.add(row.exerciseId);
  }

  saving.value = true;
  try {
    const exercisesPayload = filled.map((row, i) => ({
      exercise_id: Number(row.exerciseId),
      weight_kg: row.weightKg ?? undefined,
      reps: row.reps!,
      sets: row.sets ?? 1,
      position: i,
    }));

    if (props.routine) {
      await fitnessApi.updateRoutine(props.routine.id, {
        name: name.value.trim(),
        category: category.value.trim() || null,
        description: description.value.trim() || null,
      });
      await fitnessApi.replaceRoutineExercises(props.routine.id, {
        exercises: exercisesPayload,
      });
    } else {
      await fitnessApi.createRoutine({
        name: name.value.trim(),
        category: category.value.trim() || undefined,
        description: description.value.trim() || undefined,
        exercises: exercisesPayload,
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
  <Modal
    :title="isEdit ? 'Editar rutina' : 'Nueva rutina'"
    @close="emit('close')"
  >
    <form class="space-y-4" @submit.prevent="submit">
      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">Nombre</label>
        <input
          v-model="name"
          type="text"
          :maxlength="MAX_ROUTINE_NAME_LEN"
          placeholder="Full body, Tren superior, Tren inferior, Hiit…"
          class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
        />
      </div>

      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">
          Categoría
          <span class="font-normal text-slate-400">(Opcional)</span>
        </label>
        <input
          v-model="category"
          type="text"
          :maxlength="MAX_ROUTINE_CATEGORY_LEN"
          placeholder="Fuerza, Cardio, Movilidad…"
          class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
        />
      </div>

      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">
          Descripción
          <span class="font-normal text-slate-400">(Opcional)</span>
        </label>
        <textarea
          v-model="description"
          rows="2"
          :maxlength="MAX_ROUTINE_DESCRIPTION_LEN"
          placeholder="Rutina de fuerza para todo el cuerpo…"
          class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
        />
      </div>

      <div class="rounded-lg border border-slate-100 bg-slate-50/50">
        <div class="flex items-center justify-between gap-2 px-3 py-2.5">
          <span class="text-xs font-semibold tracking-wider text-slate-400">
            Ejercicios
          </span>
          <button
            type="button"
            class="shrink-0 rounded-md border border-slate-200 bg-white px-2 py-0.5 text-xs font-medium text-slate-500 transition-colors hover:bg-slate-50"
            @click="addExerciseRow"
          >
            + Añadir
          </button>
        </div>

        <div class="border-t border-slate-100 px-3 py-3">
          <p
            v-if="!exerciseRows.length"
            class="text-center text-xs text-slate-400"
          >
            Añade ejercicios para definir la rutina.
          </p>

          <div v-else class="space-y-3">
            <div
              v-for="(row, index) in exerciseRows"
              :key="row.id"
              class="space-y-2 rounded-lg border border-slate-100 bg-white p-2"
            >
              <div class="flex items-center justify-between">
                <span
                  class="flex items-center rounded-md bg-slate-100 px-1.5 py-0.5 text-[11px] font-semibold text-slate-500"
                >
                  Ejercicio {{ index + 1 }}
                </span>
                <div class="flex items-center gap-1">
                  <button
                    type="button"
                    :disabled="index === 0"
                    class="rounded p-1 text-slate-400 transition-colors hover:bg-slate-100 disabled:opacity-30"
                    @click="moveExerciseRow(row, -1)"
                  >
                    <Icon :path="icons.chevronUp" :size="14" />
                  </button>
                  <button
                    type="button"
                    :disabled="index === exerciseRows.length - 1"
                    class="rounded p-1 text-slate-400 transition-colors hover:bg-slate-100 disabled:opacity-30"
                    @click="moveExerciseRow(row, 1)"
                  >
                    <Icon :path="icons.chevronDown" :size="14" />
                  </button>
                  <button
                    type="button"
                    class="rounded-lg p-1 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-500"
                    @click="removeExerciseRow(row)"
                  >
                    <Icon :path="icons.trash" :size="14" />
                  </button>
                </div>
              </div>

              <div>
                <div class="px-1 text-[10px] font-medium uppercase tracking-wider text-slate-400">
                  Ejercicio
                </div>
                <SelectMenu
                  v-model="row.exerciseId"
                  :options="exerciseOptions"
                  placeholder="Elegir ejercicio…"
                />
              </div>

              <div class="grid grid-cols-3 gap-2">
                <div>
                  <div class="px-1 text-[10px] font-medium uppercase tracking-wider text-slate-400">
                    Peso
                  </div>
                  <div class="flex items-center gap-1">
                    <input
                      v-model.number="row.weightKg"
                      type="number"
                      min="0"
                      step="any"
                      placeholder="12"
                      class="min-w-0 w-full rounded-lg border border-slate-200 px-2 py-1.5 text-sm tabular-nums text-slate-800 outline-none transition-colors [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
                    />
                    <span class="shrink-0 rounded-md bg-slate-100 px-1.5 py-1.5 text-[10px] font-medium text-slate-500">kg</span>
                  </div>
                </div>
                <div>
                  <div class="px-1 text-[10px] font-medium uppercase tracking-wider text-slate-400">
                    Reps
                  </div>
                  <input
                    v-model.number="row.reps"
                    type="number"
                    min="1"
                    step="1"
                    placeholder="15"
                    class="min-w-0 w-full rounded-lg border border-slate-200 px-2 py-1.5 text-sm tabular-nums text-slate-800 outline-none transition-colors [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
                  />
                </div>
                <div>
                  <div class="px-1 text-[10px] font-medium uppercase tracking-wider text-slate-400">
                    Series
                  </div>
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
