<script setup lang="ts">
import { computed, ref } from "vue";
import { ApiRequestError } from "../../api/client";
import { remindersApi } from "../../api/reminders";
import DateInput from "../../components/DateInput.vue";
import Modal from "../../components/Modal.vue";
import { getToday } from "../../lib/date";
import { capitalize, formatDate } from "../../lib/format";
import { CUSTOM_RECURRENCE_UNITS, parseCustomRecurrence, recurrenceLabel } from "../../lib/recurrence";
import type { Reminder, ReminderRecurrence } from "../../types";

const props = defineProps<{ reminder?: Reminder | null }>();
const emit = defineEmits<{ close: []; saved: [] }>();

const isEdit = computed(() => props.reminder != null);

const message = ref(props.reminder?.message ?? "");
const triggerAt = ref(props.reminder?.trigger_at ?? getToday());
const triggerTime = ref(props.reminder?.trigger_time ?? "");

const parsedCustomRecurrence = props.reminder ? parseCustomRecurrence(props.reminder.recurrence) : null;
const customAmount = ref<string | number>(parsedCustomRecurrence ? String(parsedCustomRecurrence.amount) : "");
const customUnit = ref<string>(parsedCustomRecurrence?.unit ?? "d");
const recurrence = ref<string>(parsedCustomRecurrence ? "custom" : (props.reminder?.recurrence ?? "none"));

const summary = computed(() => {
  const reminderMessage = message.value.trim();
  if (!reminderMessage) return null
  const lead = `El recordatorio "${reminderMessage}" se activará`

  if (!triggerAt.value) return null;
  const timeParts = [`el ${formatDate(triggerAt.value)}`];
  if (triggerTime.value) timeParts.push(`a las ${triggerTime.value}`);
  const base = `${lead} ${timeParts.join(" ")}`;

  if (recurrence.value === "none") return `${base} y no se repetirá.`;
  else if (recurrence.value === "custom") {
    const custom = parseCustomRecurrence(`${customAmount.value}${customUnit.value}`);
    if (!custom) return null;
    return `${base} y se repetirá cada ${recurrenceLabel(`${custom.amount}${custom.unit}`)}.`;
  }
  return `${base} y su frecuencia será ${recurrenceLabel(recurrence.value)}.`;
});

const error = ref<string | null>(null);
const saving = ref(false);

async function submit() {
  error.value = null;

  if (!message.value.trim()) {
    error.value = "El mensaje del recordatorio es obligatorio.";
    return;
  }
  if (!triggerAt.value) {
    error.value = "La fecha es obligatoria.";
    return;
  }
  if (triggerAt.value < getToday()) {
    error.value = "La fecha no puede estar en el pasado.";
    return;
  }

  let recurrenceValue: ReminderRecurrence = recurrence.value;
  if (recurrenceValue === "custom") {
    const customRecurrence = parseCustomRecurrence(`${customAmount.value}${customUnit.value}`);
    if (!customRecurrence) {
      error.value = "La cantidad debe ser un número entero mayor que 0.";
      return;
    }
    recurrenceValue = `${customRecurrence.amount}${customRecurrence.unit}`;
    if (customRecurrence.unit === "h" && !triggerTime.value) {
      error.value = "Para fijar una frecuencia en horas primero debes definir una hora explicita de ejecución para el recordatorio.";
      return;
    }
  }

  const payload = {
    message: message.value.trim(),
    trigger_at: triggerAt.value,
    trigger_time: triggerTime.value || null,
    recurrence: recurrenceValue,
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

      <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">Fecha</label>
          <DateInput v-model="triggerAt" :min="getToday()" />
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">Hora (Opcional)</label>
          <input
            v-model="triggerTime"
            type="time"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
          />
        </div>
      </div>

      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">Frecuencia</label>
        <select
          v-model="recurrence"
          class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
        >
          <option value="none">Una vez</option>
          <option value="daily">Diario</option>
          <option value="weekly">Semanal</option>
          <option value="monthly">Mensual</option>
          <option value="yearly">Anual</option>
          <option value="custom">Personalizada</option>
        </select>
        <div v-if="recurrence === 'custom'" class="mt-4 grid grid-cols-2 gap-3">
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-500">Cantidad</label>
            <input
              v-model.number="customAmount"
              type="number"
              min="1"
              step="1"
              inputmode="numeric"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
            />
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-500">Unidad</label>
            <select
              v-model="customUnit"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
            >
              <option v-for="unit in CUSTOM_RECURRENCE_UNITS" :key="unit.value" :value="unit.value">
                {{ capitalize(unit.label) }}
              </option>
            </select>
          </div>
        </div>
        <p v-if="summary" class="mt-4 text-xs text-slate-400">
          {{ summary }}
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
          {{ saving ? "Guardando\u2026" : isEdit ? "Guardar" : "Crear" }}
        </button>
      </div>
    </form>
  </Modal>
</template>
