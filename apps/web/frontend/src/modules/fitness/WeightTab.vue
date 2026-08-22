<script setup lang="ts">
import { computed, ref } from "vue";
import {
  CategoryScale,
  Chart as ChartJS,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from "chart.js";
import { Line } from "vue-chartjs";
import { ApiRequestError } from "../../api/client";
import { fitnessApi } from "../../api/fitness";
import Icon from "../../components/Icon.vue";
import IconButton from "../../components/IconButton.vue";
import Modal from "../../components/Modal.vue";
import WidgetCard from "../../components/WidgetCard.vue";
import { formatDelta, formatWeight } from "../../lib/fitness";
import { formatDateShort } from "../../lib/format";
import { icons } from "../../lib/icons";
import { pushToast } from "../../lib/toast";
import type { FitnessStats, WeightEntry } from "../../types";
import WeightFormModal from "./WeightFormModal.vue";
import WeightTabSkeleton from "./WeightTabSkeleton.vue";

ChartJS.register(
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Tooltip,
);

const props = defineProps<{ loading: boolean }>();
const emit = defineEmits<{ reload: [] }>();

defineExpose({ openCreate });

const stats = ref<FitnessStats | null>(null);
const entries = ref<WeightEntry[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);

const formOpen = ref(false);
const deleting = ref<WeightEntry | null>(null);
const deleteBusy = ref(false);

void load();

async function load() {
  loading.value = true;
  error.value = null;
  try {
    const [s, list] = await Promise.all([
      fitnessApi.getStats(),
      fitnessApi.listWeights(),
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
  formOpen.value = true;
}

function onSaved() {
  formOpen.value = false;
  void load();
  emit("reload");
  pushToast("Peso guardado");
}

const hasEntries = computed(() => entries.value.length > 0);

const chartData = computed(() => {
  const points = [...entries.value].sort((a, b) =>
    a.measured_at.localeCompare(b.measured_at),
  );
  return {
    labels: points.map((e) => formatDateShort(e.measured_at)),
    datasets: [
      {
        label: "Peso (kg)",
        borderColor: "#0f172a",
        backgroundColor: "#0f172a",
        pointRadius: 3,
        pointHoverRadius: 5,
        tension: 0.25,
        data: points.map((e) => e.weight_kg),
      },
    ],
  };
});

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  animation: { duration: 600, easing: "easeOutQuart" as const },
  scales: {
    x: {
      grid: { display: false },
      ticks: { color: "#94a3b8", font: { size: 11 }, maxTicksLimit: 10 },
    },
    y: {
      border: { display: false },
      grid: { color: "#f1f5f9" },
      ticks: { color: "#94a3b8", font: { size: 11 } },
    },
  },
  plugins: {
    legend: { display: false },
    tooltip: {
      boxPadding: 4,
      displayColors: false,
      callbacks: {
        label: (ctx: { parsed: { y: number | null } }) =>
          `${ctx.parsed.y ?? 0} kg`,
      },
    },
  },
}));

async function confirmDelete() {
  if (!deleting.value || deleteBusy.value) return;
  deleteBusy.value = true;
  try {
    await fitnessApi.deleteWeight(deleting.value.id);
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
</script>

<template>
  <div>
    <WeightTabSkeleton v-if="props.loading || loading" />

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
            <p class="text-xs font-medium text-slate-400">Peso actual</p>
            <p class="mt-1 text-2xl font-semibold text-slate-900">
              {{ formatWeight(stats?.latest_weight_kg ?? null) }}
              <span class="text-sm font-normal text-slate-400">kg</span>
            </p>
            <p
              v-if="stats?.latest_measured_at"
              class="mt-0.5 text-xs text-slate-400"
            >
              {{ formatDateShort(stats.latest_measured_at) }}
            </p>
          </div>
          <div class="rounded-xl border border-slate-200 bg-white p-4">
            <p class="text-xs font-medium text-slate-400">Δ 7 días</p>
            <p
              class="mt-1 text-2xl font-semibold"
              :class="
                (stats?.weight_delta_7d ?? 0) <= 0
                  ? 'text-emerald-600'
                  : 'text-amber-600'
              "
            >
              {{ formatDelta(stats?.weight_delta_7d ?? null) }}
            </p>
          </div>
          <div class="rounded-xl border border-slate-200 bg-white p-4">
            <p class="text-xs font-medium text-slate-400">Δ 30 días</p>
            <p
              class="mt-1 text-2xl font-semibold"
              :class="
                (stats?.weight_delta_30d ?? 0) <= 0
                  ? 'text-emerald-600'
                  : 'text-amber-600'
              "
            >
              {{ formatDelta(stats?.weight_delta_30d ?? null) }}
            </p>
          </div>
        </div>

        <WidgetCard title="Evolución">
          <div class="px-4 py-4">
            <div
              v-if="!hasEntries"
              class="py-16 text-center text-sm text-slate-500"
            >
              Aún no hay registros de peso.
            </div>
            <div v-else class="relative h-64">
              <Line :data="chartData" :options="chartOptions" />
            </div>
          </div>
        </WidgetCard>

        <WidgetCard title="Historial" :count="entries.length">
          <div
            v-if="!hasEntries"
            class="px-4 py-10 text-center text-sm text-slate-500"
          >
            Registra tu peso para ver el historial.
          </div>
          <ul v-else class="divide-y divide-slate-100">
            <li
              v-for="entry in entries.slice(0, 30)"
              :key="entry.id"
              class="flex items-center gap-3 px-4 py-3"
            >
              <span class="w-24 text-sm text-slate-500">{{
                formatDateShort(entry.measured_at)
              }}</span>
              <span class="text-sm font-semibold text-slate-900"
                >{{ entry.weight_kg }} kg</span
              >
              <span
                v-if="entry.notes"
                class="truncate text-xs text-slate-400"
                >{{ entry.notes }}</span
              >
              <IconButton
                class="ml-auto"
                :icon="icons.trash"
                label="Eliminar registro"
                @click="deleting = entry"
              />
            </li>
          </ul>
        </WidgetCard>
      </template>
    </template>

    <WeightFormModal
      v-if="formOpen"
      @close="formOpen = false"
      @saved="onSaved"
    />

    <Modal v-if="deleting" title="Eliminar registro" @close="deleting = null">
      <p class="text-sm text-slate-600">
        ¿Eliminar el peso de {{ formatDateShort(deleting.measured_at) }} ({{
          deleting.weight_kg
        }}
        kg)?
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
