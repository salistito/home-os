<script setup lang="ts">
import { computed, ref } from "vue";
import Modal from "../../components/Modal.vue";
import { tasksApi } from "../../api/tasks";
import { ApiRequestError } from "../../api/client";
import type { Task } from "../../types";

const props = defineProps<{ task?: Task | null }>();
const emit = defineEmits<{ close: []; saved: [] }>();

const isEdit = computed(() => props.task != null);

const name = ref(props.task?.name ?? "");
const points = ref<number>(props.task?.points ?? 1);
const recurrent = ref(props.task?.frequency_days != null);
const frequencyDays = ref<number>(props.task?.frequency_days ?? 7);
const nextDueDate = ref(props.task?.next_due_date ?? today());

const error = ref<string | null>(null);
const saving = ref(false);

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

async function submit() {
  error.value = null;

  if (!name.value.trim()) {
    error.value = "El nombre es obligatorio.";
    return;
  }
  if (!Number.isInteger(points.value) || points.value <= 0) {
    error.value = "Los puntos deben ser un entero mayor que cero.";
    return;
  }
  if (recurrent.value) {
    if (!Number.isInteger(frequencyDays.value) || frequencyDays.value <= 0) {
      error.value = "La frecuencia debe ser un entero mayor que cero.";
      return;
    }
    if (!nextDueDate.value) {
      error.value = "Indica la fecha de la próxima vez.";
      return;
    }
  }

  const payload = {
    name: name.value.trim(),
    points: points.value,
    frequency_days: recurrent.value ? frequencyDays.value : null,
    next_due_date: recurrent.value ? nextDueDate.value : null,
  };

  saving.value = true;
  try {
    if (props.task) {
      await tasksApi.update(props.task.id, payload);
    } else {
      await tasksApi.create(payload);
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
  <Modal :title="isEdit ? 'Editar tarea' : 'Nueva tarea'" @close="emit('close')">
    <form class="space-y-4" @submit.prevent="submit">
      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">Nombre</label>
        <input
          v-model="name"
          type="text"
          placeholder="Lavar la loza"
          class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
        />
      </div>

      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">Puntos</label>
        <input
          v-model.number="points"
          type="number"
          min="1"
          class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
        />
      </div>

      <label class="flex items-center gap-2 text-sm text-slate-700">
        <input
          v-model="recurrent"
          type="checkbox"
          class="h-4 w-4 rounded border-slate-300 text-amber-500 focus:ring-amber-200"
        />
        Tarea recurrente
      </label>

      <div v-if="recurrent" class="grid grid-cols-2 gap-3">
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">
            Frecuencia (en días)
          </label>
          <input
            v-model.number="frequencyDays"
            type="number"
            min="1"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
          />
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">
            Próxima ocurrencia
          </label>
          <input
            v-model="nextDueDate"
            type="date"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
          />
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
