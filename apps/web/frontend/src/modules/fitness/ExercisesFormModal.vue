<script setup lang="ts">
import { computed, ref } from "vue";
import { ApiRequestError } from "../../api/client";
import { fitnessApi } from "../../api/fitness";
import Modal from "../../components/Modal.vue";
import type { Exercise } from "../../types";

const MAX_NAME_LEN = 80;
const MAX_KIND_LEN = 40;

const props = defineProps<{ exercise?: Exercise | null }>();
const emit = defineEmits<{ close: []; saved: [] }>();

const isEdit = computed(() => props.exercise != null);

const name = ref(props.exercise?.name ?? "");
const kind = ref(props.exercise?.kind ?? "");

const error = ref<string | null>(null);
const saving = ref(false);

async function submit() {
  error.value = null;

  if (!name.value.trim()) {
    error.value = "El nombre del ejercicio es obligatorio.";
    return;
  }

  saving.value = true;
  try {
    if (props.exercise) {
      await fitnessApi.updateExercise(props.exercise.id, {
        name: name.value.trim(),
        kind: kind.value.trim() || null,
      });
    } else {
      await fitnessApi.createExercise({
        name: name.value.trim(),
        kind: kind.value.trim() || undefined,
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
    :title="isEdit ? 'Editar ejercicio' : 'Nuevo ejercicio'"
    @close="emit('close')"
  >
    <form class="space-y-4" @submit.prevent="submit">
      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">Nombre</label>
        <input
          v-model="name"
          type="text"
          :maxlength="MAX_NAME_LEN"
          placeholder="Press banca"
          class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
        />
      </div>

      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">
          Tipo
          <span class="font-normal text-slate-400">(Opcional)</span>
        </label>
        <input
          v-model="kind"
          type="text"
          :maxlength="MAX_KIND_LEN"
          placeholder="Fuerza, Cardio o Pecho, Espalda, Pierna…"
          class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
        />
        <p class="mt-1 text-xs text-slate-400">
          Sirve para categorizar tus ejercicios al elegirlos en una sesión de entrenamiento.
        </p>
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
