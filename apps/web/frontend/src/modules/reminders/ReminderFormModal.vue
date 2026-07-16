<script setup lang="ts">
import { computed, ref } from "vue";
import Modal from "../../components/Modal.vue";
import { remindersApi } from "../../api/reminders";
import { ApiRequestError } from "../../api/client";
import type { Reminder, ReminderRecurrence } from "../../types";

const props = defineProps<{ reminder?: Reminder | null }>();
const emit = defineEmits<{ close: []; saved: [] }>();

const isEdit = computed(() => props.reminder != null);

const message = ref(props.reminder?.message ?? "");
const triggerAt = ref(props.reminder?.trigger_at ?? today());
const triggerTime = ref(props.reminder?.trigger_time ?? "");
const recurrence = ref<ReminderRecurrence>(props.reminder?.recurrence ?? "none");

const error = ref<string | null>(null);
const saving = ref(false);

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

async function submit() {
  error.value = null;

  if (!message.value.trim()) {
    error.value = "El mensaje es obligatorio.";
    return;
  }
  if (!triggerAt.value) {
    error.value = "La fecha es obligatoria.";
    return;
  }
  if (triggerAt.value < today()) {
    error.value = "La fecha no puede estar en el pasado.";
    return;
  }

  const payload = {
    message: message.value.trim(),
    trigger_at: triggerAt.value,
    trigger_time: triggerTime.value || null,
    recurrence: recurrence.value,
  };

  saving.value = true;
  try {
    if (props.reminder) {
      await remindersApi.update(props.reminder.id, payload);
    } else {
      await remindersApi.create(payload);
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
  <Modal :title="isEdit ? 'Editar recordatorio' : 'Nuevo recordatorio'" @close="emit('close')">
    <form class="space-y-4" @submit.prevent="submit">
      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">Mensaje</label>
        <input
          v-model="message"
          type="text"
          placeholder="Tomar medicación"
          class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
        />
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">Fecha</label>
          <input
            v-model="triggerAt"
            type="date"
            :min="today()"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
          />
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">Hora (opcional)</label>
          <input
            v-model="triggerTime"
            type="time"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
          />
        </div>
      </div>

      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">Recurrencia</label>
        <select
          v-model="recurrence"
          class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
        >
          <option value="none">Una vez</option>
          <option value="daily">Diario</option>
          <option value="weekly">Semanal</option>
          <option value="monthly">Mensual</option>
          <option value="yearly">Anual</option>
        </select>
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
          {{ saving ? "Guardando\u2026" : isEdit ? "Guardar" : "Crear" }}
        </button>
      </div>
    </form>
  </Modal>
</template>
