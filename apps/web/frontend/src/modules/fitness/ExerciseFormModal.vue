<script setup lang="ts">
import { ref } from "vue";
import { ApiRequestError } from "../../api/client";
import { fitnessApi } from "../../api/fitness";
import DateInput from "../../components/DateInput.vue";
import Modal from "../../components/Modal.vue";
import { getToday } from "../../lib/date";
import {
  EXERCISE_TYPE_SUGGESTIONS,
  INTENSITY_OPTIONS,
} from "../../lib/fitness";
import type { ExerciseEntry, ExerciseIntensity } from "../../types";

const props = defineProps<{ entry?: ExerciseEntry | null }>();
const emit = defineEmits<{ close: []; saved: [] }>();

const exerciseType = ref(props.entry?.exercise_type ?? "");
const durationMin = ref<number | null>(props.entry?.duration_min ?? 30);
const intensity = ref<ExerciseIntensity | "">(
  (props.entry?.intensity as ExerciseIntensity | undefined) ?? "",
);
const caloriesBurned = ref<number | null>(props.entry?.calories_burned ?? null);
const performedAt = ref(props.entry?.performed_at ?? getToday());
const notes = ref(props.entry?.notes ?? "");

const error = ref<string | null>(null);
const saving = ref(false);

async function submit() {
  error.value = null;

  if (!exerciseType.value.trim()) {
    error.value = "Ingresa el tipo de ejercicio.";
    return;
  }
  if (
    durationMin.value === null ||
    Number.isNaN(durationMin.value) ||
    durationMin.value <= 0
  ) {
    error.value = "La duración debe ser mayor a 0 minutos.";
    return;
  }

  saving.value = true;
  try {
    const payload = {
      exercise_type: exerciseType.value.trim().toLowerCase(),
      duration_min: Math.round(durationMin.value),
      intensity: intensity.value || undefined,
      calories_burned:
        caloriesBurned.value !== null && !Number.isNaN(caloriesBurned.value)
          ? caloriesBurned.value
          : undefined,
      performed_at: performedAt.value,
      notes: notes.value.trim() || undefined,
    };
    if (props.entry) {
      await fitnessApi.updateExercise(props.entry.id, payload);
    } else {
      await fitnessApi.createExercise(payload);
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
    :title="entry ? 'Editar ejercicio' : 'Registrar ejercicio'"
    @close="emit('close')"
  >
    <form class="space-y-4" @submit.prevent="submit">
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500"
            >Ejercicio</label
          >
          <input
            v-model="exerciseType"
            list="exercise-type-suggestions"
            placeholder="correr, gym…"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
          />
          <datalist id="exercise-type-suggestions">
            <option
              v-for="t in EXERCISE_TYPE_SUGGESTIONS"
              :key="t"
              :value="t"
            />
          </datalist>
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500"
            >Duración (min)</label
          >
          <input
            v-model.number="durationMin"
            type="number"
            min="1"
            step="1"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
          />
        </div>
      </div>

      <div class="grid grid-cols-3 gap-3">
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500"
            >Intensidad</label
          >
          <select
            v-model="intensity"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
          >
            <option value="">—</option>
            <option
              v-for="opt in INTENSITY_OPTIONS"
              :key="opt.value"
              :value="opt.value"
            >
              {{ opt.label }}
            </option>
          </select>
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500"
            >Calorías</label
          >
          <input
            v-model.number="caloriesBurned"
            type="number"
            min="0"
            step="any"
            placeholder="opcional"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
          />
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500"
            >Fecha</label
          >
          <DateInput v-model="performedAt" :max="getToday()" />
        </div>
      </div>

      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500"
          >Notas (Opcional)</label
        >
        <textarea
          v-model="notes"
          rows="2"
          placeholder="Pierna, 5km en 25min…"
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
