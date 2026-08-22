<script setup lang="ts">
import { computed, ref } from "vue";
import { ApiRequestError } from "../../api/client";
import { fitnessApi } from "../../api/fitness";
import Icon from "../../components/Icon.vue";
import IconButton from "../../components/IconButton.vue";
import Modal from "../../components/Modal.vue";
import WidgetCard from "../../components/WidgetCard.vue";
import { INTENSITY_LABELS, INTENSITY_STYLES } from "../../lib/fitness";
import { formatDateShort } from "../../lib/format";
import { icons } from "../../lib/icons";
import { pushToast } from "../../lib/toast";
import type { ExerciseEntry, FitnessStats } from "../../types";
import ExerciseFormModal from "./ExerciseFormModal.vue";
import ExerciseTabSkeleton from "./ExerciseTabSkeleton.vue";

const props = defineProps<{ loading: boolean }>();
const emit = defineEmits<{ reload: [] }>();

defineExpose({ openCreate });

const stats = ref<FitnessStats | null>(null);
const entries = ref<ExerciseEntry[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);

const formOpen = ref(false);
const editing = ref<ExerciseEntry | null>(null);
const deleting = ref<ExerciseEntry | null>(null);
const deleteBusy = ref(false);

void load();

async function load() {
  loading.value = true;
  error.value = null;
  try {
    const [s, list] = await Promise.all([
      fitnessApi.getStats(),
      fitnessApi.listExercises({ limit: 60 }),
    ]);
    stats.value = s;
    entries.value = list;
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

function openEdit(entry: ExerciseEntry) {
  editing.value = entry;
  formOpen.value = true;
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
    pushToast("Registro eliminado");
  } catch (e) {
    pushToast(
      e instanceof ApiRequestError ? e.message : "Error al eliminar",
      "error",
    );
  } finally {
    deleteBusy.value = false;
  }
}

const hasEntries = computed(() => entries.value.length > 0);

const topTypes = computed(() =>
  Object.entries(stats.value?.by_type_last_30d ?? {}).slice(0, 3),
);
</script>

<template>
  <div>
    <ExerciseTabSkeleton v-if="props.loading || loading" />

    <template v-else>
      <p
        v-if="error"
        class="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-600"
      >
        {{ error }}
      </p>

      <template v-else>
        <div class="grid grid-cols-3 gap-3">
          <div class="rounded-xl border border-slate-200 bg-white p-4">
            <p class="text-xs font-medium text-slate-400">Últimos 7 días</p>
            <p class="mt-1 text-2xl font-semibold text-slate-900">
              {{ stats?.minutes_last_7d ?? 0 }}
              <span class="text-sm font-normal text-slate-400">min</span>
            </p>
            <p class="mt-0.5 text-xs text-slate-400">
              {{ stats?.sessions_last_7d ?? 0 }} sesiones
            </p>
          </div>
          <div class="rounded-xl border border-slate-200 bg-white p-4">
            <p class="text-xs font-medium text-slate-400">Últimos 30 días</p>
            <p class="mt-1 text-2xl font-semibold text-slate-900">
              {{ stats?.minutes_last_30d ?? 0 }}
              <span class="text-sm font-normal text-slate-400">min</span>
            </p>
            <p class="mt-0.5 text-xs text-slate-400">
              {{ stats?.sessions_last_30d ?? 0 }} sesiones
            </p>
          </div>
          <div class="rounded-xl border border-slate-200 bg-white p-4">
            <p class="text-xs font-medium text-slate-400">Top 30 días</p>
            <div v-if="topTypes.length" class="mt-1.5 space-y-1">
              <p
                v-for="[type, minutes] in topTypes"
                :key="type"
                class="flex items-center justify-between gap-2 text-sm"
              >
                <span class="truncate capitalize text-slate-700">{{
                  type
                }}</span>
                <span class="shrink-0 text-xs text-slate-400"
                  >{{ minutes }} min</span
                >
              </p>
            </div>
            <p v-else class="mt-1 text-sm text-slate-400">—</p>
          </div>
        </div>

        <WidgetCard title="Sesiones" :count="entries.length">
          <div
            v-if="!hasEntries"
            class="px-4 py-10 text-center text-sm text-slate-500"
          >
            Registra tu primer ejercicio para ver el historial.
          </div>
          <ul v-else class="divide-y divide-slate-100">
            <li
              v-for="entry in entries"
              :key="entry.id"
              class="flex items-center gap-3 px-4 py-3"
            >
              <span class="w-20 shrink-0 text-sm text-slate-500">{{
                formatDateShort(entry.performed_at)
              }}</span>
              <span
                class="truncate text-sm font-semibold capitalize text-slate-900"
                >{{ entry.exercise_type }}</span
              >
              <span
                v-if="entry.intensity"
                class="shrink-0 rounded-full px-2 py-0.5 text-[11px] font-medium"
                :class="INTENSITY_STYLES[entry.intensity]"
              >
                {{ INTENSITY_LABELS[entry.intensity] }}
              </span>
              <span class="ml-auto shrink-0 text-sm text-slate-600"
                >{{ entry.duration_min }} min</span
              >
              <span
                v-if="entry.calories_burned !== null"
                class="w-16 shrink-0 text-right text-xs text-slate-400"
              >
                {{ entry.calories_burned }} kcal
              </span>
              <span class="flex shrink-0 items-center gap-1">
                <IconButton
                  :icon="icons.pencil"
                  label="Editar"
                  @click="openEdit(entry)"
                />
                <IconButton
                  :icon="icons.trash"
                  label="Eliminar"
                  @click="deleting = entry"
                />
              </span>
            </li>
          </ul>
        </WidgetCard>
      </template>
    </template>

    <ExerciseFormModal
      v-if="formOpen"
      :entry="editing"
      @close="formOpen = false"
      @saved="onSaved"
    />

    <Modal v-if="deleting" title="Eliminar registro" @close="deleting = null">
      <p class="text-sm text-slate-600">
        ¿Eliminar la sesión de {{ deleting.exercise_type }} del
        {{ formatDateShort(deleting.performed_at) }}?
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
