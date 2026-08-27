<script setup lang="ts">
import { ref } from "vue";
import { ApiRequestError } from "../../api/client";
import { fitnessApi } from "../../api/fitness";
import DateInput from "../../components/DateInput.vue";
import Modal from "../../components/Modal.vue";
import { getToday } from "../../lib/date";
import type { WeightEntry } from "../../types";

const props = defineProps<{ weightEntry?: WeightEntry | null }>();
const emit = defineEmits<{ close: []; saved: [] }>();

const weight = ref<number | null>(props.weightEntry?.weight_kg ?? null);
const measuredAt = ref(props.weightEntry?.measured_at ?? getToday());
const notes = ref(props.weightEntry?.notes ?? "");

const error = ref<string | null>(null);
const saving = ref(false);

async function submit() {
  error.value = null;

  if (
    weight.value === null ||
    Number.isNaN(weight.value) ||
    weight.value <= 0
  ) {
    error.value = "Ingresa un peso válido mayor a 0.";
    return;
  }
  if (!measuredAt.value) {
    error.value = "Ingresa una fecha válida.";
    return;
  }

  saving.value = true;
  try {
    if (props.weightEntry) {
      await fitnessApi.updateWeightEntry(props.weightEntry.id, {
        weight_kg: Math.round(weight.value * 100) / 100,
        measured_at: measuredAt.value,
        notes: notes.value.trim() || null,
      });
    } else {
      await fitnessApi.logWeightEntry({
        weight_kg: Math.round(weight.value * 100) / 100,
        measured_at: measuredAt.value,
        notes: notes.value.trim() || undefined,
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
    :title="weightEntry ? 'Editar peso' : 'Registrar peso'"
    @close="emit('close')"
  >
    <form class="space-y-4" @submit.prevent="submit">
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">Peso</label>
          <div class="flex items-center gap-1.5">
            <input
              v-model.number="weight"
              type="number"
              min="0"
              step="0.1"
              class="h-11 min-w-0 flex-1 rounded-lg border border-slate-200 px-3 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
            />
            <span class="shrink-0 rounded-md bg-slate-100 px-2 py-1.5 text-xs font-medium text-slate-500">kg</span>
          </div>
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">Fecha</label>
          <DateInput v-model="measuredAt" :max="getToday()" />
          <p v-if="!weightEntry" class="mt-1 text-xs text-slate-400">
            Si ya existe un peso registrado para esta fecha se actualizará.
          </p>
        </div>
      </div>

      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">Notas (Opcional)</label>
        <textarea
          v-model="notes"
          rows="2"
          placeholder="En ayuno, Después de entrenar, etc…"
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
