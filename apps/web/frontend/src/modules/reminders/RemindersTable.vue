<script setup lang="ts">
import { onMounted, ref } from "vue";
import Icon from "../../components/Icon.vue";
import Modal from "../../components/Modal.vue";
import Skeleton from "../../components/Skeleton.vue";
import WidgetCard from "../../components/WidgetCard.vue";
import ReminderFormModal from "./ReminderFormModal.vue";
import { icons } from "../../lib/icons";
import { formatDate } from "../../lib/format";
import { remindersApi } from "../../api/reminders";
import { ApiRequestError } from "../../api/client";
import { pushToast } from "../../lib/toast";
import type { Reminder, ReminderRecurrence } from "../../types";

const RECURRENCE_LABELS: Record<ReminderRecurrence, string> = {
  none: "Una vez",
  daily: "Diario",
  weekly: "Semanal",
  monthly: "Mensual",
  yearly: "Anual",
};

const reminders = ref<Reminder[]>([]);
const error = ref<string | null>(null);
const loading = ref(true);

const formOpen = ref(false);
const editing = ref<Reminder | null>(null);

const deleting = ref<Reminder | null>(null);
const deleteError = ref<string | null>(null);
const deleteBusy = ref(false);

async function load() {
  try {
    reminders.value = await remindersApi.list();
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Error inesperado";
  } finally {
    loading.value = false;
  }
}

function openCreate() {
  editing.value = null;
  formOpen.value = true;
}

function openEdit(reminder: Reminder) {
  editing.value = reminder;
  formOpen.value = true;
}

async function onSaved() {
  const wasEdit = editing.value != null;
  formOpen.value = false;
  await load();
  pushToast(wasEdit ? "Recordatorio actualizado" : "Recordatorio creado");
}

function askDelete(reminder: Reminder) {
  deleting.value = reminder;
  deleteError.value = null;
}

async function confirmDelete() {
  if (!deleting.value) return;
  deleteBusy.value = true;
  try {
    await remindersApi.remove(deleting.value.id);
    deleting.value = null;
    await load();
    pushToast("Recordatorio borrado");
  } catch (e) {
    deleteError.value =
      e instanceof ApiRequestError ? e.message : "No se pudo borrar el recordatorio.";
  } finally {
    deleteBusy.value = false;
  }
}

onMounted(load);
</script>

<template>
  <WidgetCard title="Recordatorios" :count="!loading && !error ? reminders.length : undefined">
    <template #actions>
      <button
        type="button"
        class="inline-flex items-center gap-1 rounded-lg bg-slate-900 px-2.5 py-1.5 text-xs font-medium text-white transition-colors hover:bg-slate-700"
        @click="openCreate"
      >
        <Icon :path="icons.plus" :size="14" />
        Nuevo recordatorio
      </button>
    </template>

    <p v-if="error" class="px-4 py-6 text-sm text-red-600">{{ error }}</p>

    <p
      v-else-if="!loading && reminders.length === 0"
      class="px-4 py-10 text-center text-sm text-slate-500"
    >
      No hay recordatorios. Crea el primero para empezar.
    </p>

    <div v-else>
      <div
        class="hidden grid-cols-[1fr_6rem_5rem_6rem_2.25rem] items-center gap-3 border-b border-slate-100 bg-slate-50/60 px-4 py-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400 sm:grid"
      >
        <span>Mensaje</span>
        <span>Fecha</span>
        <span>Hora</span>
        <span>Frecuencia</span>
        <span></span>
      </div>

      <ul class="divide-y divide-slate-100">
        <template v-if="loading">
          <li
            v-for="n in 4"
            :key="n"
            class="flex items-center gap-3 px-4 py-3 sm:grid sm:grid-cols-[1fr_6rem_5rem_6rem_2.25rem] sm:items-center sm:py-2.5"
          >
            <Skeleton width="12rem" />
            <Skeleton width="4rem" />
            <Skeleton width="3rem" />
            <Skeleton width="4rem" />
            <span></span>
          </li>
        </template>

        <template v-else>
          <li
            v-for="reminder in reminders"
            :key="reminder.id"
            class="group flex items-start gap-3 px-4 py-3 transition-colors hover:bg-slate-50 sm:grid sm:grid-cols-[1fr_6rem_5rem_6rem_2.25rem] sm:items-center sm:py-2.5"
          >
            <div class="min-w-0 flex-1 sm:contents">
              <span
                class="block truncate text-[13px] font-medium text-slate-800"
              >
                {{ reminder.message }}
              </span>

              <div
                class="mt-1.5 flex flex-wrap items-center gap-1.5 sm:contents"
              >
                <span
                  class="inline-flex items-center gap-1 text-xs text-slate-500 sm:justify-self-start"
                >
                  <Icon :path="icons.calendar" :size="12" class="text-slate-400" />
                  {{ formatDate(reminder.trigger_at) }}
                </span>

                <span
                  v-if="reminder.trigger_time"
                  class="inline-flex items-center text-xs text-slate-500 sm:justify-self-start"
                >
                  {{ reminder.trigger_time }}
                </span>
                <span
                  v-else
                  class="hidden text-xs text-slate-300 sm:block sm:justify-self-start"
                >—</span>

                <span
                  class="inline-flex items-center rounded-md border border-slate-200 px-2 py-0.5 text-xs text-slate-600 sm:justify-self-start"
                >
                  {{ RECURRENCE_LABELS[reminder.recurrence] }}
                </span>
              </div>
            </div>

            <span
              class="flex shrink-0 items-center justify-end gap-0.5 transition-opacity sm:opacity-0 sm:group-hover:opacity-100"
            >
              <button
                type="button"
                class="rounded-md p-1 text-slate-400 transition-colors hover:bg-slate-200 hover:text-slate-700"
                aria-label="Editar"
                @click="openEdit(reminder)"
              >
                <Icon :path="icons.pencil" :size="14" />
              </button>
              <button
                type="button"
                class="rounded-md p-1 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-600"
                aria-label="Borrar"
                @click="askDelete(reminder)"
              >
                <Icon :path="icons.trash" :size="14" />
              </button>
            </span>
          </li>
        </template>
      </ul>
    </div>
  </WidgetCard>

  <ReminderFormModal
    v-if="formOpen"
    :reminder="editing"
    @close="formOpen = false"
    @saved="onSaved"
  />

  <Modal v-if="deleting" title="Borrar recordatorio" @close="deleting = null">
    <p class="text-sm text-slate-600">
      ¿Seguro que quieres borrar
      <span class="font-medium text-slate-900">{{ deleting.message }}</span>?
    </p>
    <p v-if="deleteError" class="mt-3 text-sm text-red-600">{{ deleteError }}</p>
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
        class="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-500 disabled:opacity-50"
        @click="confirmDelete"
      >
        {{ deleteBusy ? "Borrando\u2026" : "Borrar" }}
      </button>
    </div>
  </Modal>
</template>
