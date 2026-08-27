<script setup lang="ts">
import { computed, ref } from "vue";
import {
  CategoryScale,
  Chart as ChartJS,
  Filler,
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
import { addDays, getToday } from "../../lib/date";
import { formatDelta, formatWeight } from "../../lib/fitness";
import { capitalize, formatDate, formatDateShort, formatDateYear, formatYearMonth } from "../../lib/format";
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
  Filler,
);

const props = defineProps<{ loading: boolean }>();
const emit = defineEmits<{ reload: [] }>();

const today = getToday();
const range = ref<"30" | "90" | "all">("90");
const rangeOptions = [
  { id: "30", label: "30d" },
  { id: "90", label: "90d" },
  { id: "all", label: "Todo" },
] as const;

const weightEntries = ref<WeightEntry[]>([]);
const fitnessStats = ref<FitnessStats | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);

const formOpen = ref(false);
const editing = ref<WeightEntry | null>(null);
const deleting = ref<WeightEntry | null>(null);
const deleteBusy = ref(false);

async function load() {
  loading.value = true;
  error.value = null;
  try {
    const [entries, stats] = await Promise.all([
      fitnessApi.listWeightsEntries(),
      fitnessApi.getStats(),
    ]);
    weightEntries.value = entries;
    fitnessStats.value = stats;
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

function openEdit(entry: WeightEntry) {
  editing.value = entry;
  formOpen.value = true;
}

function onSaved() {
  formOpen.value = false;
  editing.value = null;
  void load();
  emit("reload");
  pushToast("Peso guardado");
}

async function confirmDelete() {
  if (!deleting.value || deleteBusy.value) return;
  deleteBusy.value = true;
  try {
    await fitnessApi.deleteWeightEntry(deleting.value.id);
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

const hasEntries = computed(() => weightEntries.value.length > 0);

const sortedAsc = computed(() =>
  [...weightEntries.value].sort((a, b) => a.measured_at.localeCompare(b.measured_at)),
);

const filteredAsc = computed(() => {
  if (range.value === "all") return sortedAsc.value;
  const cutoff = addDays(today, -Number(range.value));
  return sortedAsc.value.filter((e) => e.measured_at.slice(0, 10) >= cutoff);
});

interface ScriptableContext {
  chart: {
    ctx: CanvasRenderingContext2D;
    chartArea?: { top: number; bottom: number };
  };
}

const chartData = computed(() => ({
  labels: filteredAsc.value.map((e) => formatDateYear(e.measured_at)),
  datasets: [
    {
      label: "Peso (kg)",
      borderColor: "#0f172a",
      pointRadius: 2.5,
      pointHoverRadius: 5,
      pointBackgroundColor: "#0f172a",
      tension: 0.3,
      fill: true,
      backgroundColor: (context: ScriptableContext) => {
        const { ctx, chartArea } = context.chart;
        if (!chartArea) return "rgba(15, 23, 42, 0.06)";
        const gradient = ctx.createLinearGradient(
          0,
          chartArea.top,
          0,
          chartArea.bottom,
        );
        gradient.addColorStop(0, "rgba(15, 23, 42, 0.12)");
        gradient.addColorStop(1, "rgba(15, 23, 42, 0)");
        return gradient;
      },
      data: filteredAsc.value.map((e) => e.weight_kg),
    },
  ],
}));

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
      grace: "8%" as const,
      grid: { color: "#f1f5f9" },
      ticks: { color: "#94a3b8", font: { size: 11 }, callback: (val: number | string) => `${val} kg` },
    },
  },
  plugins: {
    legend: { display: false },
    tooltip: {
      boxPadding: 4,
      displayColors: false,
      titleFont: { weight: "bold" as const },
      callbacks: {
        title: (items: { dataIndex: number }[]) => {
          const entry = filteredAsc.value[items[0]?.dataIndex];
          return entry ? `${formatDateYear(entry.measured_at)}:` : "";
        },
        label: (ctx: { parsed: { y: number | null } }) =>
          `\u2022 ${ctx.parsed.y ?? 0} kg`,
      },
    },
  },
}));

const rangeDelta = computed(() => {
  const list = filteredAsc.value;
  if (list.length < 2) return null;
  const first = list[0].weight_kg;
  const last = list[list.length - 1].weight_kg;
  return Math.round((last - first) * 10) / 10;
});

function deltaClass(value: number): string {
  return value <= 0 ? "text-emerald-600" : "text-amber-600";
}

interface MonthGroup {
  key: string;
  label: string;
  delta: number | null;
  weightEntries: WeightEntry[];
}

const monthGroups = computed<MonthGroup[]>(() => {
  const sortedDesc = [...weightEntries.value].sort((a, b) =>
    b.measured_at.localeCompare(a.measured_at),
  );
  const byMonth = new Map<string, WeightEntry[]>();
  for (const entry of sortedDesc) {
    const key = entry.measured_at.slice(0, 7);
    const list = byMonth.get(key);
    if (list) list.push(entry);
    else byMonth.set(key, [entry]);
  }
  return Array.from(byMonth.entries()).map(([key, list]) => ({
    key,
    label: capitalize(formatYearMonth(key)),
    delta:
      list.length > 1
        ? Math.round(
            (list[0].weight_kg - list[list.length - 1].weight_kg) * 10,
          ) / 10
        : null,
    weightEntries: list,
  }));
});

const deltaByEntryId = computed(() => {
  const map = new Map<number, number>();
  const asc = sortedAsc.value;
  for (let i = 1; i < asc.length; i++) {
    map.set(
      asc[i].id,
      Math.round((asc[i].weight_kg - asc[i - 1].weight_kg) * 10) / 10,
    );
  }
  return map;
});

void load();

defineExpose({ openCreate });
</script>

<template>
  <div class="space-y-4">
    <WeightTabSkeleton v-if="props.loading || loading" />

    <template v-else>
      <p v-if="error" class="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-600">
        {{ error }}
      </p>

      <template v-else>
        <div class="grid grid-cols-3 gap-3">
          <div class="flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-4 text-center">
            <p class="text-xs font-medium text-slate-400">Peso actual</p>
            <p class="mt-1 text-2xl font-semibold text-slate-900">
              {{ formatWeight(fitnessStats?.latest_weight_kg ?? null) }} kg
            </p>
          </div>
          <div class="flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-4 text-center">
            <p class="text-xs font-medium text-slate-400">Δ 7 días</p>
            <p
              class="mt-1 text-2xl font-semibold"
              :class="
                (fitnessStats?.weight_delta_7d ?? 0) <= 0
                  ? 'text-emerald-600'
                  : 'text-amber-600'
              "
            >
              {{ formatDelta(fitnessStats?.weight_delta_7d ?? null) }}
            </p>
          </div>
          <div class="flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-4 text-center">
            <p class="text-xs font-medium text-slate-400">Δ 30 días</p>
            <p
              class="mt-1 text-2xl font-semibold"
              :class="
                (fitnessStats?.weight_delta_30d ?? 0) <= 0
                  ? 'text-emerald-600'
                  : 'text-amber-600'
              "
            >
              {{ formatDelta(fitnessStats?.weight_delta_30d ?? null) }}
            </p>
          </div>
        </div>

        <WidgetCard title="Evolución">
          <template #actions>
            <div class="flex rounded-lg bg-slate-100 p-0.5">
              <button
                v-for="option in rangeOptions"
                :key="option.id"
                type="button"
                class="rounded-md px-2 py-1 text-xs font-medium transition-colors"
                :class="
                  range === option.id
                    ? 'bg-white text-slate-900 shadow-sm'
                    : 'text-slate-500'
                "
                @click="range = option.id"
              >
                {{ option.label }}
              </button>
            </div>
          </template>

          <div class="px-4 py-4">
            <div
              v-if="!hasEntries"
              class="py-16 text-center text-sm text-slate-500"
            >
              Aún no hay pesos registrados.
            </div>
            <div
              v-else-if="!filteredAsc.length"
              class="py-16 text-center text-sm text-slate-500"
            >
              No hay pesos registrados en este período.
            </div>
            <template v-else>
              <div
                v-if="filteredAsc.length >= 2"
                class="mb-3 flex flex-wrap items-center justify-between gap-x-3 gap-y-1"
              >
                <span class="text-xs font-medium tabular-nums text-slate-500">
                  {{ filteredAsc.length }} registros en el período
                </span>
                <span
                  class="text-xs font-semibold tabular-nums"
                  :class="deltaClass(rangeDelta ?? 0)"
                >
                  {{ formatDelta(rangeDelta) }} en el período
                </span>
              </div>
              <div class="relative h-64">
                <Line :data="chartData" :options="chartOptions" />
              </div>
            </template>
          </div>
        </WidgetCard>

        <WidgetCard title="Histórico" icon="flame" :count="weightEntries.length">
          <template #actions>
            <button
              type="button"
              class="hidden items-center gap-1 rounded-lg bg-slate-900 px-2.5 py-1.5 text-xs font-medium text-white transition-colors hover:bg-slate-700 lg:inline-flex"
              @click="openCreate"
            >
              <Icon :path="icons.plus" :size="14" />
              Registrar peso
            </button>
          </template>
          <div
            v-if="!hasEntries"
            class="px-4 py-10 text-center text-sm text-slate-500"
          >
            Aún no hay pesos registrados.
          </div>
          <div v-else class="divide-y divide-slate-100">
            <div v-for="group in monthGroups" :key="group.key">
              <div class="flex items-center justify-between bg-slate-100/50 px-4 py-2">
                <h4 class="text-xs font-semibold tracking-wider text-slate-900">
                  {{ group.label }}
                </h4>
                <span
                  v-if="group.delta !== null"
                  class="text-xs font-semibold tabular-nums"
                  :class="deltaClass(group.delta)"
                >
                  {{ formatDelta(group.delta) }}
                </span>
              </div>
              <ul class="divide-y divide-slate-100">
                <li
                  v-for="entry in group.weightEntries"
                  :key="entry.id"
                  class="group flex items-center gap-3 px-4 py-3 transition-colors hover:bg-slate-50"
                >
                  <span class="w-10 shrink-0 text-sm text-slate-500">
                    {{ formatDateShort(entry.measured_at) }}
                  </span>
                  <span class="inline-flex shrink-0 items-baseline gap-1">
                    <span class="text-sm font-semibold tabular-nums text-slate-900">
                      {{ entry.weight_kg }} kg
                    </span>
                    <span
                      v-if="deltaByEntryId.has(entry.id)"
                      class="text-xs font-medium tabular-nums"
                      :class="deltaClass(deltaByEntryId.get(entry.id)!)"
                    >
                      ({{ formatDelta(deltaByEntryId.get(entry.id)!) }})
                    </span>
                  </span>
                  <span
                    v-if="entry.notes"
                    class="min-w-0 truncate text-xs text-slate-400"
                  >
                    {{ entry.notes }}
                  </span>
                  <span
                    class="ml-auto flex shrink-0 items-center gap-1 transition-opacity sm:opacity-0 sm:group-hover:opacity-100"
                  >
                    <IconButton
                      :icon="icons.pencil"
                      label="Editar registro"
                      @click="openEdit(entry)"
                    />
                    <IconButton
                      :icon="icons.trash"
                      label="Eliminar registro"
                      variant="danger"
                      @click="deleting = entry"
                    />
                  </span>
                </li>
              </ul>
            </div>
          </div>
        </WidgetCard>
      </template>
    </template>

    <WeightFormModal
      v-if="formOpen"
      :weightEntry="editing"
      @saved="onSaved"
      @close="
        formOpen = false;
        editing = null;
      "
    />

    <Modal v-if="deleting" title="Eliminar peso" @close="deleting = null">
      <p class="text-sm text-slate-600">
        ¿Seguro que quieres eliminar el peso registrado el {{ formatDate(deleting.measured_at) }}?
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
