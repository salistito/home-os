<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Tooltip,
} from "chart.js";
import { Bar } from "vue-chartjs";
import WidgetCard from "../../components/WidgetCard.vue";
import { colorsByUser } from "../../lib/colors";
import { tasksApi } from "../../api/tasks";
import type { DailyScoresResponse } from "../../types";

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend);

const data = ref<DailyScoresResponse | null>(null);
const error = ref<string | null>(null);
const loading = ref(true);

const hasData = computed(
  () => data.value !== null && Object.keys(data.value.daily).length > 0,
);

const monthNames = [
  "enero",
  "febrero",
  "marzo",
  "abril",
  "mayo",
  "junio",
  "julio",
  "agosto",
  "septiembre",
  "octubre",
  "noviembre",
  "diciembre",
];

const title = computed(() => {
  const days = data.value ? Object.keys(data.value.daily) : [];
  if (days.length === 0) return "Ranking diario";
  const month = Number(days.sort()[0].split("-")[1]);
  return `Ranking diario de ${monthNames[month - 1]}`;
});

const chartData = computed(() => {
  if (!data.value) return { labels: [], datasets: [] };
  const days = Object.keys(data.value.daily).sort();
  const colors = colorsByUser(data.value.users.map((u) => u.id));
  return {
    labels: days.map((d) => Number(d.split("-")[2])),
    datasets: data.value.users.map((user) => ({
      label: user.name,
      backgroundColor: colors[user.id].solid,
      borderRadius: 3,
      maxBarThickness: 18,
      data: days.map((d) => data.value!.daily[d][user.id] ?? 0),
    })),
  };
});

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    x: {
      stacked: true,
      grid: { display: false },
      ticks: { color: "#94a3b8", font: { size: 11 } },
    },
    y: {
      stacked: true,
      border: { display: false },
      grid: { color: "#f1f5f9" },
      ticks: { color: "#94a3b8", font: { size: 11 }, precision: 0 },
    },
  },
  plugins: {
    legend: {
      position: "bottom" as const,
      labels: { color: "#475569", boxWidth: 12, font: { size: 12 } },
    },
    tooltip: { boxPadding: 4 },
  },
};

onMounted(async () => {
  try {
    data.value = await tasksApi.dailyScores();
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Error inesperado";
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <WidgetCard :title="title">
    <div class="flex h-full flex-col px-4 py-4">
      <p v-if="loading" class="py-16 text-center text-sm text-slate-400">
        Cargando…
      </p>

      <p v-else-if="error" class="py-16 text-center text-sm text-red-600">
        {{ error }}
      </p>

      <p
        v-else-if="!hasData"
        class="py-16 text-center text-sm text-slate-500"
      >
        Aún no hay puntos registrados este mes.
      </p>

      <div v-else class="min-h-64 flex-1">
        <Bar :data="chartData" :options="chartOptions" />
      </div>
    </div>
  </WidgetCard>
</template>
