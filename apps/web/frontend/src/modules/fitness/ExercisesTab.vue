<script setup lang="ts">
import { computed, ref } from "vue";
import { ApiRequestError } from "../../api/client";
import { fitnessApi } from "../../api/fitness";
import FilterModal from "../../components/FilterModal.vue";
import Icon from "../../components/Icon.vue";
import IconButton from "../../components/IconButton.vue";
import Modal from "../../components/Modal.vue";
import SearchBar from "../../components/SearchBar.vue";
import WidgetCard from "../../components/WidgetCard.vue";
import { color } from "../../lib/colors";
import { icons } from "../../lib/icons";
import { pushToast } from "../../lib/toast";
import type { Exercise, FitnessStats } from "../../types";
import ExerciseFormModal from "./ExercisesFormModal.vue";
import ExercisesTabSkeleton from "./ExercisesTabSkeleton.vue";

const props = defineProps<{ loading: boolean }>();
const emit = defineEmits<{ reload: [] }>();

const exercises = ref<Exercise[]>([]);
const stats = ref<FitnessStats | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);

const searchQuery = ref("");
const sortBy = ref("pct");
const sortOrder = ref("desc");
const kindFilter = ref("all");
const showFilters = ref(false);

const formOpen = ref(false);
const editing = ref<Exercise | null>(null);
const deleting = ref<Exercise | null>(null);
const deleteBusy = ref(false);

void load();

async function load() {
  loading.value = true;
  error.value = null;
  try {
    const [list, s] = await Promise.all([
      fitnessApi.listExercises(),
      fitnessApi.getStats(),
    ]);
    exercises.value = list;
    stats.value = s;
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Error inesperado";
  } finally {
    loading.value = false;
  }
}

function openCreate() {
  formOpen.value = true;
  editing.value = null;
}

function openEdit(exercise: Exercise) {
  formOpen.value = true;
  editing.value = exercise;
}

function onSaved() {
  formOpen.value = false;
  void load();
  emit("reload");
  pushToast("Ejercicio guardado");
}

async function confirmDelete() {
  if (!deleting.value || deleteBusy.value) return;
  deleteBusy.value = true;
  try {
    await fitnessApi.deleteExercise(deleting.value.id);
    deleting.value = null;
    void load();
    emit("reload");
    pushToast("Ejercicio eliminado");
  } catch (e) {
    pushToast(
      e instanceof ApiRequestError ? e.message : "Error al eliminar",
      "error",
    );
  } finally {
    deleteBusy.value = false;
  }
}

const hasExercises = computed(() => exercises.value.length > 0);

const usageByExerciseName = computed<Record<string, number>>(() => {
  const map: Record<string, number> = {};
  for (const [exerciseName, minutes] of Object.entries(
    stats.value?.by_exercise_last_30d ?? {},
  )) {
    map[exerciseName.toLowerCase()] = minutes;
  }
  return map;
});

const totalUsage = computed(() =>
  Object.values(usageByExerciseName.value).reduce((sum, minutes) => sum + minutes, 0),
);

function usageOf(exercise: Exercise): number {
  return usageByExerciseName.value[exercise.name.toLowerCase()] ?? 0;
}

function usagePct(exercise: Exercise): number {
  return totalUsage.value
    ? Math.round((usageOf(exercise) / totalUsage.value) * 100)
    : 0;
}

const sortColumns = [
  { value: "name", label: "Nombre" },
  { value: "kind", label: "Tipo" },
  { value: "usage", label: "Minutos" },
  { value: "pct", label: "% de entrenamientos" },
];

function applySort({ sortBy: by, sortOrder: order }: { sortBy: string; sortOrder: string }) {
  sortBy.value = by;
  sortOrder.value = order;
}

function setSort(col: string) {
  if (sortBy.value === col) {
    sortOrder.value = sortOrder.value === "asc" ? "desc" : "asc";
  } else {
    sortBy.value = col;
    sortOrder.value = col === "usage" || col === "pct" ? "desc" : "asc";
  }
}

const kindOptions = computed(() => [
  { value: "all", label: "Todos los tipos" },
  ...[...new Set(
    exercises.value
      .map((exercise) => exercise.kind)
      .filter((kind): kind is string => Boolean(kind)),
  )]
    .sort((a, b) => a.localeCompare(b))
    .map((kind) => ({ value: kind, label: kind })),
]);

const filtersActive = computed(() => kindFilter.value !== "all");

function applyFilter({ key, value }: { key: string; value: string }) {
  if (key === "kind") kindFilter.value = value;
}

function compareExercises(a: Exercise, b: Exercise): number {
  if (sortBy.value === "name") {
    return a.name.localeCompare(b.name);
  }
  if (sortBy.value === "kind") {
    return (
      (a.kind ?? "").localeCompare(b.kind ?? "") || a.name.localeCompare(b.name)
    );
  }
  const usageDiff = usageOf(a) - usageOf(b);
  if (usageDiff !== 0) return usageDiff;
  return a.name.localeCompare(b.name);
}

const filteredExercises = computed(() =>
  exercises.value
    .filter((exercise) => {
      if (kindFilter.value !== "all" && exercise.kind !== kindFilter.value) {
        return false;
      }
      const query = searchQuery.value.trim().toLowerCase();
      if (!query) return true;
      return (
        exercise.name.toLowerCase().includes(query) ||
        (exercise.kind ?? "").toLowerCase().includes(query)
      );
    })
    .sort((a, b) =>
      sortOrder.value === "desc"
        ? -compareExercises(a, b)
        : compareExercises(a, b),
    ),
);

defineExpose({ openCreate });
</script>

<template>
  <div class="space-y-4">
    <ExercisesTabSkeleton v-if="props.loading || loading" />

    <template v-else>
      <p v-if="error" class="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-600">
        {{ error }}
      </p>

      <WidgetCard
        v-else
        title="Ejercicios"
        :count="filteredExercises.length"
      >
        <template #actions>
          <button
            type="button"
            class="hidden items-center gap-1 rounded-lg bg-slate-900 px-2.5 py-1.5 text-xs font-medium text-white transition-colors hover:bg-slate-700 lg:inline-flex"
            @click="openCreate"
          >
            <Icon :path="icons.plus" :size="14" />
            Nuevo ejercicio
          </button>
        </template>

        <template #filter>
          <SearchBar
            v-model="searchQuery"
            placeholder="Buscar ejercicio…"
          />
          <span class="relative">
            <IconButton
              :icon="icons.filter"
              label="Filtros"
              @click="showFilters = true"
            />
            <span
              v-if="filtersActive"
              class="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-amber-500"
            />
          </span>
        </template>

        <p
          v-if="!hasExercises"
          class="px-4 py-10 text-center text-sm text-slate-500"
        >
          Crea tu primer ejercicio para poder registrarlo en tus sesiones de entrenamiento.
        </p>
        <p
          v-else-if="!filteredExercises.length"
          class="px-4 py-10 text-center text-sm text-slate-500"
        >
          {{
            searchQuery
              ? `No hay ejercicios que coincidan con la búsqueda.`
              : "No hay ejercicios que coincidan con los filtros."
          }}
        </p>

        <div v-else>
          <div
            class="hidden grid-cols-[minmax(0,1fr)_6rem_9rem_10rem_4.75rem] items-center gap-3 border-b border-slate-100 bg-slate-50/60 px-4 py-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400 sm:grid"
          >
            <button
              type="button"
              class="flex items-center gap-1 text-left"
              @click="setSort('name')"
            >
              Ejercicio
              <span v-if="sortBy === 'name'">{{ sortOrder === "asc" ? "↑" : "↓" }}</span>
            </button>
            <button
              type="button"
              class="flex items-center justify-center gap-1 text-center"
              @click="setSort('kind')"
            >
              Tipo
              <span v-if="sortBy === 'kind'">{{ sortOrder === "asc" ? "↑" : "↓" }}</span>
            </button>
            <button
              type="button"
              class="flex items-center justify-center gap-1 text-center"
              @click="setSort('usage')"
            >
              <span>
                <span class="block">Minutos</span>
                <span class="block">(Últimos 30 días)</span>
              </span>
              <span v-if="sortBy === 'usage'">{{ sortOrder === "asc" ? "↑" : "↓" }}</span>
            </button>
            <button
              type="button"
              class="flex items-center justify-center gap-1 text-center"
              @click="setSort('pct')"
            >
              <span>
                <span class="block">% de Entrenamientos</span>
                <span class="block">(Últimos 30 días)</span>
              </span>
              <span v-if="sortBy === 'pct'">{{ sortOrder === "asc" ? "↑" : "↓" }}</span>
            </button>
            <span></span>
          </div>

          <ul class="divide-y divide-slate-100">
            <li
              v-for="exercise in filteredExercises"
              :key="exercise.id"
              class="group flex items-start gap-3 px-4 py-3 transition-colors hover:bg-slate-50 sm:grid sm:grid-cols-[minmax(0,1fr)_6rem_9rem_10rem_4.75rem] sm:items-center sm:py-2.5"
            >
              <div class="min-w-0 flex-1 sm:contents">
                <span
                  class="block truncate text-[13px] font-medium capitalize text-slate-800"
                >
                  {{ exercise.name }}
                </span>
                <div
                  class="mt-1.5 flex flex-wrap items-center gap-1.5 sm:contents"
                >
                  <span
                    v-if="exercise.kind"
                    class="inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium capitalize ring-1 sm:justify-self-center"
                    :class="[
                      color(exercise.kind).bg,
                      color(exercise.kind).text,
                      color(exercise.kind).ring,
                    ]"
                  >
                    {{ exercise.kind }}
                  </span>
                  <span
                    v-else
                    class="hidden text-xs text-slate-300 sm:block sm:text-center"
                  >—</span>

                  <p class="w-full text-xs tabular-nums text-slate-400 sm:hidden">
                    <template v-if="usageOf(exercise) > 0">
                      <span>Últimos 30 días:</span>
                      {{ usageOf(exercise) }} min · {{ usagePct(exercise) }}% del total de
                      entrenamientos
                    </template>
                    <template v-else>Sin sesiones de entrenamiento con duración en los últimos 30 días</template>
                  </p>

                  <span
                    v-if="usageOf(exercise) > 0"
                    class="hidden items-center gap-1 text-xs tabular-nums text-slate-600 sm:inline-flex sm:justify-self-center"
                  >
                    <Icon :path="icons.clock" :size="12" class="shrink-0 text-slate-400" />
                    {{ usageOf(exercise) }} min
                  </span>
                  <span v-else class="hidden text-xs text-slate-300 sm:block sm:text-center">—</span>

                  <div
                    v-if="usageOf(exercise) > 0"
                    class="relative hidden h-4 items-center overflow-hidden rounded-full bg-slate-100 sm:flex"
                  >
                    <div
                      class="h-full bg-emerald-500 transition-[width] duration-500 ease-out"
                      :style="{ width: `${usagePct(exercise)}%` }"
                    />
                    <span
                      class="absolute inset-0 flex items-center justify-center text-[10px] font-semibold tabular-nums text-slate-900"
                    >
                      {{ usagePct(exercise) }}%
                    </span>
                  </div>
                  <span v-else class="hidden text-xs text-slate-300 sm:block sm:text-center">—</span>
                </div>
              </div>

              <span
                class="flex shrink-0 items-center justify-end gap-1 transition-opacity sm:opacity-0 sm:group-hover:opacity-100"
              >
                <IconButton
                  :icon="icons.pencil"
                  label="Editar"
                  @click="openEdit(exercise)"
                />
                <IconButton
                  :icon="icons.trash"
                  label="Eliminar"
                  variant="danger"
                  @click="deleting = exercise"
                />
              </span>
            </li>
          </ul>
        </div>
      </WidgetCard>
    </template>

    <ExerciseFormModal
      v-if="formOpen"
      :exercise="editing"
      @saved="onSaved"
      @close="formOpen = false"
    />

    <Modal v-if="deleting" title="Eliminar ejercicio" @close="deleting = null">
      <p class="text-sm text-slate-600">
        ¿Seguro que quieres eliminar el ejercicio
        <span class="font-medium capitalize text-slate-900">{{ deleting.name }}</span>?
      </p>
      <p class="mt-2 text-xs text-slate-400">
        Los entrenamientos registrados conservarán el nombre del ejercicio,
        pero ya no se podrá registrar nuevos entrenamientos asociados a él.
      </p>
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
          class="flex items-center gap-1.5 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-500 disabled:opacity-50"
          @click="confirmDelete"
        >
          <Icon :path="icons.trash" :size="14" />
          {{ deleteBusy ? "Eliminando…" : "Eliminar" }}
        </button>
      </div>
    </Modal>

    <FilterModal
      :show="showFilters"
      title="Filtros de ejercicios"
      :columns="sortColumns"
      :current-sort-by="sortBy"
      :current-sort-order="sortOrder"
      :filters="[{ key: 'kind', label: 'Tipo', options: kindOptions }]"
      :current-filters="{ kind: kindFilter }"
      @update:show="showFilters = $event"
      @apply:sort="applySort"
      @apply:filter="applyFilter"
    />
  </div>
</template>
