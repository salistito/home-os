<script setup lang="ts">
import { computed, ref } from "vue";
import { ApiRequestError } from "../../api/client";
import { fitnessApi } from "../../api/fitness";
import Icon from "../../components/Icon.vue";
import IconButton from "../../components/IconButton.vue";
import Modal from "../../components/Modal.vue";
import SearchBar from "../../components/SearchBar.vue";
import WidgetCard from "../../components/WidgetCard.vue";
import { color } from "../../lib/colors";
import { icons } from "../../lib/icons";
import { pushToast } from "../../lib/toast";
import type { Exercise, Routine } from "../../types";
import RoutinesFormModal from "./RoutinesFormModal.vue";

const props = defineProps<{ loading: boolean }>();
const emit = defineEmits<{ reload: [] }>();

const routines = ref<Routine[]>([]);
const exercises = ref<Exercise[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);

const searchQuery = ref("");
const expandedId = ref<number | null>(null);

const formOpen = ref(false);
const editing = ref<Routine | null>(null);
const deleting = ref<Routine | null>(null);
const deleteBusy = ref(false);

async function load() {
  loading.value = true;
  error.value = null;
  try {
    const [r, e] = await Promise.all([
      fitnessApi.listRoutines(),
      fitnessApi.listExercises(),
    ]);
    routines.value = r;
    exercises.value = e;
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Error inesperado";
  } finally {
    loading.value = false;
  }
}

const hasRoutines = computed(() => routines.value.length > 0);

function openCreate() {
  formOpen.value = true;
  editing.value = null;
}

function openEdit(routine: Routine) {
  formOpen.value = true;
  editing.value = routine;
}

function onSaved() {
  formOpen.value = false;
  void load();
  emit("reload");
  pushToast("Rutina guardada");
}

async function confirmDelete() {
  if (!deleting.value || deleteBusy.value) return;
  deleteBusy.value = true;
  try {
    await fitnessApi.deleteRoutine(deleting.value.id);
    deleting.value = null;
    void load();
    emit("reload");
    pushToast("Rutina eliminada");
  } catch (e) {
    pushToast(
      e instanceof ApiRequestError ? e.message : "Error al eliminar",
      "error",
    );
  } finally {
    deleteBusy.value = false;
  }
}

const filteredRoutines = computed(() => {
  const query = searchQuery.value.trim().toLowerCase();
  if (!query) return routines.value;
  return routines.value.filter(
    (r) =>
      r.name.toLowerCase().includes(query) ||
      (r.description ?? "").toLowerCase().includes(query) ||
      (r.category ?? "").toLowerCase().includes(query),
  );
});

function toggleExpand(id: number) {
  expandedId.value = expandedId.value === id ? null : id;
}

const exerciseNameMap = computed(() => {
  const map: Record<number, string> = {};
  for (const e of exercises.value) {
    map[e.id] = e.name;
  }
  return map;
});

void load();

defineExpose({ openCreate });
</script>

<template>
  <div class="space-y-4">
    <div v-if="props.loading || loading" class="space-y-3">
      <div v-for="i in 3" :key="i" class="h-16 animate-pulse rounded-xl bg-slate-100" />
    </div>

    <template v-else>
      <p v-if="error" class="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-600">
        {{ error }}
      </p>

      <WidgetCard
        v-else
        title="Rutinas"
        :count="filteredRoutines.length"
      >
        <template #actions>
          <button
            type="button"
            class="hidden items-center gap-1 rounded-lg bg-slate-900 px-2.5 py-1.5 text-xs font-medium text-white transition-colors hover:bg-slate-700 lg:inline-flex"
            @click="openCreate"
          >
            <Icon :path="icons.plus" :size="14" />
            Nueva rutina
          </button>
        </template>

        <template #filter>
          <SearchBar
            v-model="searchQuery"
            placeholder="Buscar rutina…"
          />
        </template>

        <p
          v-if="!hasRoutines"
          class="px-4 py-10 text-center text-sm text-slate-500"
        >
          Crea tu primera rutina de ejercicios para registrar entrenamientos más rápido.
        </p>
        <p
          v-else-if="!filteredRoutines.length"
          class="px-4 py-10 text-center text-sm text-slate-500"
        >
          No hay rutinas que coincidan con la búsqueda.
        </p>

        <ul v-else class="divide-y divide-slate-100">
          <li
            v-for="routine in filteredRoutines"
            :key="routine.id"
            class="group"
          >
            <div
              class="flex items-start gap-3 px-4 py-3 transition-colors hover:bg-slate-50"
            >
              <div
                class="min-w-0 flex-1 cursor-pointer"
                @click="toggleExpand(routine.id)"
              >
                <div class="flex items-center gap-2">
                  <span class="truncate text-[13px] font-medium text-slate-800">
                    {{ routine.name }}
                  </span>
                  <span
                    v-if="routine.category"
                    class="inline-flex shrink-0 items-center rounded-md px-2 py-0.5 text-xs font-medium ring-1"
                    :class="[
                      color(routine.category).bg,
                      color(routine.category).text,
                      color(routine.category).ring,
                    ]"
                  >
                    {{ routine.category }}
                  </span>
                </div>
                <p
                  v-if="routine.description"
                  class="mt-0.5 truncate text-xs text-slate-400"
                >
                  {{ routine.description }}
                </p>
                <p class="mt-0.5 text-xs text-slate-400">
                  {{ routine.exercises.length }}
                  {{ routine.exercises.length === 1 ? "ejercicio" : "ejercicios" }}
                </p>
              </div>

              <div class="flex shrink-0 items-center gap-1" @click.stop>
                <IconButton
                  :icon="icons.pencil"
                  label="Editar"
                  @click="openEdit(routine)"
                />
                <IconButton
                  :icon="icons.trash"
                  label="Eliminar"
                  variant="danger"
                  @click="deleting = routine"
                />
                <button
                  type="button"
                  class="rounded-md p-1 text-slate-400 transition-colors hover:bg-slate-200 hover:text-slate-700"
                  @click="toggleExpand(routine.id)"
                >
                  <Icon
                    :path="expandedId === routine.id ? icons.chevronUp : icons.chevronDown"
                    :size="16"
                  />
                </button>
              </div>
            </div>

            <div
              v-if="expandedId === routine.id && routine.exercises.length"
              class="border-t border-slate-50 bg-slate-50/50 px-4 py-2"
            >
              <div
                v-for="re in routine.exercises"
                :key="re.id"
                class="flex items-center gap-3 border-b border-slate-100 py-1.5 text-xs last:border-0"
              >
                <span class="w-5 text-center font-medium text-slate-400">
                  {{ re.position + 1 }}
                </span>
                <span class="min-w-0 flex-1 truncate text-slate-700">
                  {{ exerciseNameMap[re.exercise_id] ?? `#${re.exercise_id}` }}
                </span>
                <span class="tabular-nums text-slate-500">
                  <template v-if="re.weight_kg != null">{{ re.weight_kg }} kg × </template>
                  {{ re.reps }} reps × {{ re.sets }} sets
                </span>
              </div>
            </div>
          </li>
        </ul>
      </WidgetCard>
    </template>

    <RoutinesFormModal
      v-if="formOpen"
      :routine="editing"
      :exercises="exercises"
      @saved="onSaved"
      @close="formOpen = false"
    />

    <Modal v-if="deleting" title="Eliminar rutina" @close="deleting = null">
      <p class="text-sm text-slate-600">
        ¿Seguro que quieres eliminar la rutina
        <span class="font-medium text-slate-900">{{ deleting.name }}</span>?
      </p>
      <p class="mt-2 text-xs text-slate-400">
        Los entrenamientos registrados conservarán el nombre de la rutina,
        pero ya no se podrá registrar nuevos entrenamientos asociados a ella.
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
  </div>
</template>
