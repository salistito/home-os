<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ApiRequestError } from "../../api/client";
import { remindersApi } from "../../api/reminders";
import Button from "../../components/Button.vue";
import Icon from "../../components/Icon.vue";
import IconButton from "../../components/IconButton.vue";
import Modal from "../../components/Modal.vue";
import Skeleton from "../../components/Skeleton.vue";
import WidgetCard from "../../components/WidgetCard.vue";
import { capitalize, formatDate } from "../../lib/format";
import { icons } from "../../lib/icons";
import { recurrenceLabel, recurrenceRank } from "../../lib/recurrence";
import { pushToast } from "../../lib/toast";
import type { Reminder } from "../../types";
import ReminderFormModal from "./ReminderFormModal.vue";

const reminders = ref<Reminder[]>([]);
const error = ref<string | null>(null);
const loading = ref(true);

const formOpen = ref(false);
const editing = ref<Reminder | null>(null);

const deleting = ref<Reminder | null>(null);
const deleteError = ref<string | null>(null);
const deleteBusy = ref(false);

type SortColumn = "message" | "date" | "time" | "frequency";
const sortBy = ref<SortColumn>("date");
const sortDesc = ref(false);

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
    pushToast("Recordatorio eliminado");
  } catch (e) {
    deleteError.value =
      e instanceof ApiRequestError ? e.message : "No se pudo eliminar el recordatorio.";
  } finally {
    deleteBusy.value = false;
  }
}

const sortedReminders = computed(() => {
  const dir = sortDesc.value ? -1 : 1;
  return [...reminders.value].sort((a, b) => {
    let cmp = 0;
    switch (sortBy.value) {
      case "message":
        cmp = a.message.localeCompare(b.message, undefined, { sensitivity: "base" });
        break;
      case "date":
        cmp = a.trigger_at.localeCompare(b.trigger_at);
        break;
      case "time":
        cmp = (a.trigger_time ?? "").localeCompare(b.trigger_time ?? "");
        break;
      case "frequency":
        cmp = recurrenceRank(a.recurrence) - recurrenceRank(b.recurrence);
        if (cmp === 0) {
          cmp = recurrenceLabel(a.recurrence).localeCompare(recurrenceLabel(b.recurrence));
        }
        break;
    }
    return cmp * dir;
  });
});

function setSort(col: SortColumn) {
  if (sortBy.value === col) {
    sortDesc.value = !sortDesc.value;
  } else {
    sortBy.value = col;
    sortDesc.value = false;
  }
}

onMounted(load);
</script>

<template>
  <WidgetCard title="Recordatorios" :count="!loading && !error ? reminders.length : undefined">
    <template #actions>
      <Button size="sm" @click="openCreate">
        <Icon :path="icons.plus" :size="14" />
        Nuevo recordatorio
      </Button>
    </template>

    <p v-if="error" class="px-4 py-6 text-sm text-red-600">{{ error }}</p>

    <p
      v-else-if="!loading && reminders.length === 0"
      class="px-4 py-10 text-center text-sm text-slate-500"
    >
      No hay recordatorios. Crea el primero para empezar.
    </p>

    <div v-else>
      <div class="flex items-center gap-2 px-4 py-3 sm:hidden">
        <select
          v-model="sortBy"
          class="rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs text-slate-700 outline-none focus:border-slate-400"
        >
          <option value="message">Mensaje</option>
          <option value="date">Fecha</option>
          <option value="time">Hora</option>
          <option value="frequency">Frecuencia</option>
        </select>
        <button
          type="button"
          class="inline-flex items-center rounded-lg border border-slate-200 px-2 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-50"
          @click="sortDesc = !sortDesc"
        >
          {{ sortDesc ? "↓ DESC" : "↑ ASC" }}
        </button>
      </div>

      <div
        class="hidden grid-cols-[1fr_6rem_5rem_6rem_2.25rem] items-center gap-3 border-b border-slate-100 bg-slate-50/60 px-4 py-2 text-xs font-semibold tracking-wider text-slate-400 sm:grid"
      >
        <button type="button" class="flex items-center gap-1 text-left" @click="setSort('message')">
          Mensaje
          <span v-if="sortBy === 'message'">{{ sortDesc ? "↓" : "↑" }}</span>
        </button>
        <button type="button" class="flex items-center gap-1" @click="setSort('date')">
          Fecha
          <span v-if="sortBy === 'date'">{{ sortDesc ? "↓" : "↑" }}</span>
        </button>
        <button type="button" class="flex items-center gap-1" @click="setSort('time')">
          Hora
          <span v-if="sortBy === 'time'">{{ sortDesc ? "↓" : "↑" }}</span>
        </button>
        <button type="button" class="flex items-center gap-1" @click="setSort('frequency')">
          Frecuencia
          <span v-if="sortBy === 'frequency'">{{ sortDesc ? "↓" : "↑" }}</span>
        </button>
        <span></span>
      </div>

      <ul class="divide-y divide-slate-100">
        <template v-if="loading">
          <li
            v-for="n in 4"
            :key="n"
            class="flex items-start gap-3 px-4 py-3 sm:grid sm:grid-cols-[1fr_6rem_5rem_6rem_2.25rem] sm:items-center sm:py-2.5"
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
            v-for="reminder in sortedReminders"
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
                class="mt-1.5 flex flex-wrap items-center gap-2 sm:contents"
              >
                <span
                  class="inline-flex items-center gap-1 text-xs text-slate-600 sm:justify-self-start"
                >
                  <Icon :path="icons.calendar" :size="12" class="shrink-0 text-slate-400" />
                  {{ formatDate(reminder.trigger_at) }}
                </span>

                <span
                  v-if="reminder.trigger_time"
                  class="inline-flex items-center gap-1 text-xs text-slate-600 sm:justify-self-start"
                >
                  <Icon :path="icons.clock" :size="12" class="shrink-0 text-slate-400" />
                  {{ reminder.trigger_time }}
                </span>
                <span
                  v-else
                  class="hidden text-xs text-slate-400 sm:inline sm:ml-2.5"
                >—</span>

                <span
                  class="inline-flex items-center gap-1 rounded-md border border-slate-200 px-2 py-0.5 text-xs text-slate-600 sm:justify-self-start"
                >
                  <Icon :path="icons.repeat" :size="12" class="shrink-0 text-slate-400" />
                  {{ capitalize(recurrenceLabel(reminder.recurrence)) }}
                </span>
              </div>
            </div>

            <span
              class="flex shrink-0 items-center justify-end gap-0.5 transition-opacity sm:opacity-0 sm:group-hover:opacity-100"
            >
              <IconButton
                :icon="icons.pencil"
                label="Editar"
                @click="openEdit(reminder)"
              />
              <IconButton
                :icon="icons.trash"
                label="Eliminar"
                variant="danger"
                @click="askDelete(reminder)"
              />
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

  <Modal v-if="deleting" title="Eliminar recordatorio" @close="deleting = null">
    <p class="text-sm text-slate-600">
      ¿Seguro que quieres eliminar el recordatorio
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
        {{ deleteBusy ? "Eliminando\u2026" : "Eliminar" }}
      </button>
    </div>
  </Modal>
</template>
