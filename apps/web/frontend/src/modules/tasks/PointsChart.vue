<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Tooltip,
} from "chart.js";
import { Bar } from "vue-chartjs";
import { tasksApi } from "../../api/tasks";
import IconButton from "../../components/IconButton.vue";
import WidgetCard from "../../components/WidgetCard.vue";
import { colorsByUser } from "../../lib/colors";
import { addMonths, getCurrentYearMonth } from "../../lib/date";
import { formatCookingAssignmentName } from "../../lib/food";
import { formatWeekdayAndDay, formatWeekdayAndDayShort, formatYearMonth } from "../../lib/format";
import { icons } from "../../lib/icons";
import { taskToggled } from "../../lib/refresh";
import type { DailyBreakdownResponse, DailyBreakdownTaskEntry } from "../../types";

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend);

const props = defineProps<{ month: string }>();
const emit = defineEmits<{ "update:month": [month: string] }>();

const data = ref<DailyBreakdownResponse | null>(null);
const error = ref<string | null>(null);
const loading = ref(true);

const currentYearMonth = getCurrentYearMonth();
const isCurrentMonth = computed(() => props.month === currentYearMonth);
const isPastMonth = computed(() => props.month < currentYearMonth);

const title = computed(() => `Ranking diario (${formatYearMonth(props.month)})`);

const formatTaskLabel = (task: DailyBreakdownTaskEntry): string => {
  if (task.source === "cooking" && task.source_entity_details) {
    return `• ${formatCookingAssignmentName(task.source_entity_details)} [${task.points} pts]`;
  }
  return `• ${task.name} [${task.points} pts]`;
}

const hasData = computed(
  () => data.value !== null && Object.keys(data.value.daily).length > 0,
);

const sortedDays = computed(() =>
  data.value ? Object.keys(data.value.daily).sort() : [],
);

const chartData = computed(() => {
  if (!data.value) return { labels: [], datasets: [] };
  const days = sortedDays.value;
  const colors = colorsByUser(data.value.users.map((user) => ({id: user.id})));
  return {
    labels: days.map((d) => formatWeekdayAndDayShort(d)),
    datasets: data.value.users.map((user) => ({
      label: user.name,
      backgroundColor: colors[user.id].solid,
      borderRadius: 3,
      maxBarThickness: 18,
      data: days.map((d) => data.value!.daily[d][user.id] ?? 0),
    })),
  };
});

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  animation: { duration: 800, easing: "easeOutQuart" as const },
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
    tooltip: {
      boxPadding: 4,
      displayColors: false,
      callbacks: {
        title: (items: { dataIndex: number }[]) => {
          const day = sortedDays.value[items[0]?.dataIndex];
          return day ? `${formatWeekdayAndDay(day)}:` : "";
        },
        label: (ctx: { dataIndex: number; datasetIndex: number }) => {
          const day = sortedDays.value[ctx.dataIndex];
          const userId = data.value?.users[ctx.datasetIndex]?.id;
          if (!day || !userId) return [];
          const tasks = data.value?.tasks?.[day]?.[userId] ?? [];
          return tasks.map((t) => formatTaskLabel(t));
        },
      },
    },
  },
}));

function goPrevMonth() {
  emit("update:month", addMonths(props.month, -1));
}

function goNextMonth() {
  if (!isCurrentMonth.value) {
    emit("update:month", addMonths(props.month, 1));
  }
}

async function loadBreakdown() {
  loading.value = true;
  error.value = null;
  try {
    data.value = await tasksApi.getDailyBreakdown(props.month);
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Error inesperado";
  } finally {
    loading.value = false;
  }
}

watch(() => props.month, loadBreakdown);
watch(taskToggled, loadBreakdown);

onMounted(loadBreakdown);
</script>

<template>
  <WidgetCard :title="title">
    <template #actions>
      <IconButton :icon="icons.chevronLeft" label="Mes anterior" @click="goPrevMonth" />
      <IconButton
        :icon="icons.chevronRight"
        label="Mes siguiente"
        :disabled="isCurrentMonth"
        @click="goNextMonth"
      />
    </template>
    <div class="flex h-full flex-col px-4 py-4">
      <p v-if="error" class="py-16 text-center text-sm text-red-600">
        {{ error }}
      </p>

      <p
        v-else-if="!loading && !hasData"
        class="py-16 text-center text-sm text-slate-500"
      >
        {{ isPastMonth ? "No hay puntos registrados este mes." : "Aún no hay puntos registrados este mes." }}
      </p>

      <div v-else class="relative min-h-64 flex-1">
        <div
          v-if="loading"
          class="absolute inset-0 z-10 flex items-center justify-center bg-white"
        >
          <span
            class="h-8 w-8 animate-spin rounded-full border-2 border-slate-200 border-t-slate-500"
          />
        </div>
        <Bar :data="chartData" :options="chartOptions" />
      </div>
    </div>
  </WidgetCard>
</template>
