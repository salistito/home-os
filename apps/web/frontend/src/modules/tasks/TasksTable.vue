<script setup lang="ts">
import { onMounted, ref } from "vue";
import Icon from "../../components/Icon.vue";
import Modal from "../../components/Modal.vue";
import WidgetCard from "../../components/WidgetCard.vue";
import TaskFormModal from "./TaskFormModal.vue";
import { icons } from "../../lib/icons";
import { formatDate } from "../../lib/format";
import { tasksApi } from "../../api/tasks";
import { ApiRequestError } from "../../api/client";
import { pushToast } from "../../lib/toast";
import type { Task } from "../../types";

const tasks = ref<Task[]>([]);
const error = ref<string | null>(null);
const loading = ref(true);

const formOpen = ref(false);
const editing = ref<Task | null>(null);

const deleting = ref<Task | null>(null);
const deleteError = ref<string | null>(null);
const deleteBusy = ref(false);

async function load() {
  try {
    tasks.value = await tasksApi.list();
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

function openEdit(task: Task) {
  editing.value = task;
  formOpen.value = true;
}

async function onSaved() {
  const wasEdit = editing.value != null;
  formOpen.value = false;
  await load();
  pushToast(wasEdit ? "Tarea actualizada" : "Tarea creada");
}

function askDelete(task: Task) {
  deleting.value = task;
  deleteError.value = null;
}

async function confirmDelete() {
  if (!deleting.value) return;
  deleteBusy.value = true;
  try {
    await tasksApi.remove(deleting.value.id);
    deleting.value = null;
    await load();
    pushToast("Tarea borrada");
  } catch (e) {
    deleteError.value =
      e instanceof ApiRequestError ? e.message : "No se pudo borrar la tarea.";
  } finally {
    deleteBusy.value = false;
  }
}

onMounted(load);
</script>

<template>
  <WidgetCard title="Tareas" :count="!loading && !error ? tasks.length : undefined">
    <template #actions>
      <button
        type="button"
        class="inline-flex items-center gap-1 rounded-lg bg-slate-900 px-2.5 py-1.5 text-xs font-medium text-white transition-colors hover:bg-slate-700"
        @click="openCreate"
      >
        <Icon :path="icons.plus" :size="14" />
        Nueva tarea
      </button>
    </template>

    <p v-if="loading" class="px-4 py-6 text-sm text-slate-400">
      Cargando tareas…
    </p>

    <p v-else-if="error" class="px-4 py-6 text-sm text-red-600">{{ error }}</p>

    <p
      v-else-if="tasks.length === 0"
      class="px-4 py-10 text-center text-sm text-slate-500"
    >
      Todavía no hay tareas. Crea la primera para empezar a repartir.
    </p>

    <div v-else>
      <div
        class="grid grid-cols-[1fr_5rem_7rem_4.25rem_2.25rem] items-center gap-3 border-b border-slate-100 bg-slate-50/60 px-4 py-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400"
      >
        <span>Tarea</span>
        <span>Puntos</span>
        <span>Frecuencia</span>
        <span>Próxima</span>
        <span></span>
      </div>

      <ul class="divide-y divide-slate-100">
        <li
          v-for="task in tasks"
          :key="task.id"
          class="group grid grid-cols-[1fr_5rem_7rem_4.25rem_2.25rem] items-center gap-3 px-4 py-2.5 transition-colors hover:bg-slate-50"
        >
          <span class="truncate text-[13px] font-medium text-slate-800">
            {{ task.name }}
          </span>

          <span>
            <span
              class="inline-flex items-center gap-1 rounded-md bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700 ring-1 ring-amber-100"
            >
              <Icon :path="icons.star" :size="12" />
              {{ task.points }}
            </span>
          </span>

          <span>
            <span
              v-if="task.frequency_days"
              class="inline-flex items-center gap-1 rounded-md border border-slate-200 px-2 py-0.5 text-xs text-slate-600"
            >
              <Icon :path="icons.repeat" :size="12" class="text-slate-400" />
              cada {{ task.frequency_days }}d
            </span>
            <span v-else class="block text-center text-xs text-slate-300">—</span>
          </span>

          <span
            v-if="task.next_due_date"
            class="inline-flex items-center gap-1 text-xs text-slate-400"
          >
            <Icon :path="icons.calendar" :size="12" />
            {{ formatDate(task.next_due_date) }}
          </span>
          <span v-else class="block text-center text-xs text-slate-300">—</span>

          <span
            class="flex items-center justify-end gap-0.5 opacity-0 transition-opacity group-hover:opacity-100"
          >
            <button
              type="button"
              class="rounded-md p-1 text-slate-400 transition-colors hover:bg-slate-200 hover:text-slate-700"
              aria-label="Editar"
              @click="openEdit(task)"
            >
              <Icon :path="icons.pencil" :size="14" />
            </button>
            <button
              type="button"
              class="rounded-md p-1 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-600"
              aria-label="Borrar"
              @click="askDelete(task)"
            >
              <Icon :path="icons.trash" :size="14" />
            </button>
          </span>
        </li>
      </ul>
    </div>
  </WidgetCard>

  <TaskFormModal
    v-if="formOpen"
    :task="editing"
    @close="formOpen = false"
    @saved="onSaved"
  />

  <Modal v-if="deleting" title="Borrar tarea" @close="deleting = null">
    <p class="text-sm text-slate-600">
      ¿Seguro que quieres borrar
      <span class="font-medium text-slate-900">{{ deleting.name }}</span>?
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
        {{ deleteBusy ? "Borrando…" : "Borrar" }}
      </button>
    </div>
  </Modal>
</template>
