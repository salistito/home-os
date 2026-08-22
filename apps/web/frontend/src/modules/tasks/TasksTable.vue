<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { ApiRequestError } from "../../api/client";
import { tasksApi } from "../../api/tasks";
import FilterModal from "../../components/FilterModal.vue";
import Icon from "../../components/Icon.vue";
import IconButton from "../../components/IconButton.vue";
import Modal from "../../components/Modal.vue";
import SearchBar from "../../components/SearchBar.vue";
import Skeleton from "../../components/Skeleton.vue";
import WidgetCard from "../../components/WidgetCard.vue";
import { formatDate } from "../../lib/format";
import { icons } from "../../lib/icons";
import { taskToggled } from "../../lib/refresh";
import { pushToast } from "../../lib/toast";
import type { Task } from "../../types";
import TaskFormModal from "./TaskFormModal.vue";

const tasks = ref<Task[]>([]);
const error = ref<string | null>(null);
const loading = ref(true);

const searchQuery = ref("");
const showFilters = ref(false);

type SortColumn = "name" | "points" | "frequency" | "nextDue";
const sortBy = ref<SortColumn>("nextDue");
const sortOrder = ref<"asc" | "desc">("asc");
const sortColumns = [
  { value: "name", label: "Nombre" },
  { value: "points", label: "Puntos" },
  { value: "frequency", label: "Frecuencia" },
  { value: "nextDue", label: "Próxima" },
];

const formOpen = ref(false);
const editing = ref<Task | null>(null);

const deleting = ref<Task | null>(null);
const deleteError = ref<string | null>(null);
const deleteBusy = ref(false);

function openFilters() {
  showFilters.value = true;
}

function applySort(value: { sortBy: string; sortOrder: string }) {
  sortBy.value = value.sortBy as SortColumn;
  sortOrder.value = value.sortOrder as "asc" | "desc";
}

function setSort(col: SortColumn) {
  if (sortBy.value === col) {
    sortOrder.value = sortOrder.value === "asc" ? "desc" : "asc";
  } else {
    sortBy.value = col;
    sortOrder.value = "asc";
  }
}

function compareNullable<T>(
  a: T | null,
  b: T | null,
  compare: (x: T, y: T) => number,
  dir: number,
): number {
  if (a === null && b === null) return 0;
  if (a === null) return 1;
  if (b === null) return -1;
  return compare(a, b) * dir;
}

const filteredBySearch = computed(() => {
  const term = searchQuery.value.trim().toLowerCase();
  if (!term) return tasks.value;
  return tasks.value.filter((t) => t.name.toLowerCase().includes(term));
});

const sortedTasks = computed(() => {
  const dir = sortOrder.value === "asc" ? 1 : -1;
  return [...filteredBySearch.value].sort((a, b) => {
    switch (sortBy.value) {
      case "name":
        return a.name.localeCompare(b.name, undefined, { sensitivity: "base" }) * dir;
      case "points":
        return (a.points - b.points) * dir;
      case "frequency":
        return compareNullable(
          a.frequency_days ?? null,
          b.frequency_days ?? null,
          (x, y) => x - y,
          dir,
        );
      case "nextDue":
        return compareNullable(
          a.next_due_date ?? null,
          b.next_due_date ?? null,
          (x, y) => x.localeCompare(y),
          dir,
        );
    }
    return 0;
  });
});

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
    await tasksApi.delete(deleting.value.id);
    deleting.value = null;
    await load();
    pushToast("Tarea eliminada");
  } catch (e) {
    deleteError.value =
      e instanceof ApiRequestError ? e.message : "No se pudo eliminar la tarea.";
  } finally {
    deleteBusy.value = false;
  }
}

onMounted(load);
watch(taskToggled, load);
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

    <template #filter>
      <SearchBar v-model="searchQuery" placeholder="Buscar tarea…" />
      <span class="relative">
        <IconButton :icon="icons.filter" label="Filtros" @click="openFilters" />
      </span>
    </template>

    <p v-if="error" class="px-4 py-6 text-sm text-red-600">{{ error }}</p>

    <p
      v-else-if="!loading && tasks.length === 0"
      class="px-4 py-10 text-center text-sm text-slate-500"
    >
      Todavía no hay tareas registradas.
    </p>

    <div v-else>
      <div
        class="hidden grid-cols-[1fr_5rem_8rem_7rem_2.25rem] items-center gap-3 border-b border-slate-100 bg-slate-50/60 px-4 py-2 text-xs font-semibold tracking-wider text-slate-400 sm:grid"
      >
        <button
          type="button"
          class="flex items-center gap-1 text-left"
          @click="setSort('name')"
        >
          Nombre
          <span v-if="sortBy === 'name'">{{ sortOrder === "asc" ? "↑": "↓" }}</span>
        </button>
        <button
          type="button"
          class="flex items-center gap-1"
          @click="setSort('points')"
        >
          Puntos
          <span v-if="sortBy === 'points'">{{ sortOrder === "asc" ? "↑": "↓" }}</span>
        </button>
        <button
          type="button"
          class="flex items-center gap-1"
          @click="setSort('frequency')"
        >
          Frecuencia
          <span v-if="sortBy === 'frequency'">{{ sortOrder === "asc" ? "↑": "↓" }}</span>
        </button>
        <button
          type="button"
          class="flex items-center gap-1"
          @click="setSort('nextDue')"
        >
          Próxima
          <span v-if="sortBy === 'nextDue'">{{ sortOrder === "asc" ? "↑": "↓" }}</span>
        </button>
        <span></span>
      </div>

      <ul class="divide-y divide-slate-100">
        <template v-if="loading">
          <li
            v-for="n in 4"
            :key="n"
            class="flex items-center gap-3 px-4 py-3 sm:grid sm:grid-cols-[1fr_5rem_8rem_7rem_2.25rem] sm:items-center sm:py-2.5"
          >
            <Skeleton width="10rem" />
            <Skeleton width="2.5rem" height="1.25rem" rounded />
            <Skeleton width="6rem" height="1.25rem" rounded />
            <Skeleton width="6rem" />
            <span></span>
          </li>
        </template>

        <template v-else>
          <li
            v-for="task in sortedTasks"
            :key="task.id"
            class="group flex items-start gap-3 px-4 py-3 transition-colors hover:bg-slate-50 sm:grid sm:grid-cols-[1fr_5rem_8rem_7rem_2.25rem] sm:items-center sm:py-2.5"
          >
          <div class="min-w-0 flex-1 sm:contents">
            <span
              class="block truncate text-[13px] font-medium text-slate-800"
            >
              {{ task.name }}
            </span>

            <div
              class="mt-1.5 flex flex-wrap items-center gap-1.5 sm:contents"
            >
              <span
                class="inline-flex items-center gap-1 rounded-md bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700 ring-1 ring-amber-100 sm:justify-self-start"
              >
                <Icon :path="icons.star" :size="12" />
                {{ task.points }}
              </span>

              <span
                v-if="task.frequency_days"
                class="inline-flex items-center gap-1 rounded-md border border-slate-200 px-2 py-0.5 text-xs text-slate-600 sm:justify-self-start"
              >
                <Icon :path="icons.repeat" :size="12" class="text-slate-400" />
                cada {{ task.frequency_days }} días
              </span>
              <span
                v-else
                class="hidden text-xs text-slate-300 sm:block sm:justify-self-start"
                >—</span
              >

              <span
                v-if="task.next_due_date"
                class="inline-flex items-center gap-1 text-xs text-slate-400 sm:justify-self-start"
              >
                <Icon :path="icons.calendar" :size="12" />
                {{ formatDate(task.next_due_date) }}
              </span>
              <span
                v-else
                class="hidden text-xs text-slate-300 sm:block sm:justify-self-start"
                >—</span
              >
            </div>
          </div>

          <span
            class="flex shrink-0 items-center justify-end gap-0.5 transition-opacity sm:opacity-0 sm:group-hover:opacity-100"
          >
            <IconButton
              :icon="icons.pencil"
              label="Editar"
              @click="openEdit(task)"
            />
            <IconButton
              :icon="icons.trash"
              label="Eliminar"
              variant="danger"
              @click="askDelete(task)"
            />
          </span>
          </li>
        </template>
      </ul>
    </div>
  </WidgetCard>

  <TaskFormModal
    v-if="formOpen"
    :task="editing"
    @close="formOpen = false"
    @saved="onSaved"
  />

  <Modal v-if="deleting" title="Eliminar tarea" @close="deleting = null">
    <p class="text-sm text-slate-600">
      ¿Seguro que quieres eliminar la tarea
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
        {{ deleteBusy ? "Eliminando…" : "Eliminar" }}
      </button>
    </div>
  </Modal>

  <FilterModal
    :show="showFilters"
    title="Filtros de tareas"
    :columns="sortColumns"
    :current-sort-by="sortBy"
    :current-sort-order="sortOrder"
    @update:show="showFilters = $event"
    @apply:sort="applySort"
  />
</template>
