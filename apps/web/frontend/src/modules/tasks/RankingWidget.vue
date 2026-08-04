<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { tasksApi } from "../../api/tasks";
import Icon from "../../components/Icon.vue";
import IconButton from "../../components/IconButton.vue";
import Skeleton from "../../components/Skeleton.vue";
import WidgetCard from "../../components/WidgetCard.vue";
import { colorsByUser } from "../../lib/colors";
import { addMonths, getCurrentYearMonth } from "../../lib/date";
import { formatYearMonth } from "../../lib/format";
import { icons } from "../../lib/icons";
import { taskToggled } from "../../lib/refresh";
import type { MonthlyRankingEntry } from "../../types";

const props = defineProps<{ month: string }>();
const emit = defineEmits<{ "update:month": [month: string] }>();

const ranking = ref<MonthlyRankingEntry[]>([]);
const error = ref<string | null>(null);
const loading = ref(true);

const currentYearMonth = getCurrentYearMonth();
const isCurrentMonth = computed(() => props.month === currentYearMonth);
const isPastMonth = computed(() => props.month < currentYearMonth);

const title = computed(() => `Ranking (${formatYearMonth(props.month)})`);

const rankingWithPoints = computed(() =>
  ranking.value.filter((e) => e.points > 0),
);

const leader = computed(() =>
  rankingWithPoints.value.length > 0 ? rankingWithPoints.value[0].points : 0,
);

const winners = computed(() => {
  if (!isPastMonth.value || rankingWithPoints.value.length === 0) return [];
  const top = rankingWithPoints.value[0].points;
  return rankingWithPoints.value.filter((e) => e.points === top);
});

const winnerIds = computed(() => new Set(winners.value.map((w) => w.user_id)));

const winnersText = computed(() => {
  const names = winners.value.map((w) => w.name);
  if (names.length === 1) {
    return `¡${names[0]} se lleva la victoria!`;
  }
  const subjects =
    names.length === 2
      ? names.join(" y ")
      : `${names.slice(0, -1).join(", ")} y ${names[names.length - 1]}`;
  return `¡${subjects} comparten la victoria!`;
});

const colors = computed(() => colorsByUser(ranking.value.map((entry) => ({ id: entry.user_id}))));

function goPrevMonth() {
  emit("update:month", addMonths(props.month, -1));
}

function goNextMonth() {
  if (!isCurrentMonth.value) {
    emit("update:month", addMonths(props.month, 1));
  }
}

async function loadRanking() {
  loading.value = true;
  error.value = null;
  try {
    ranking.value = (await tasksApi.getMonthlyRanking(props.month)).ranking;
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Error inesperado";
  } finally {
    loading.value = false;
  }
}

watch(() => props.month, loadRanking);
watch(taskToggled, loadRanking);

onMounted(loadRanking);
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
    <div
      v-if="!loading && !error && winners.length"
      class="flex items-center gap-3 border-b border-amber-100 bg-amber-50 px-2.5 py-4"
    >
      <Icon :path="icons.trophy" :size="18" class="shrink-0 text-amber-500" />
      <p class="text-[13px] font-semibold text-amber-800">{{ winnersText }}</p>
    </div>
    <ol v-if="loading" class="divide-y divide-slate-100">
      <li v-for="n in 2" :key="n" class="flex items-center gap-3 px-4 py-3">
        <Skeleton width="1rem" />
        <Skeleton width="0.625rem" height="0.625rem" />
        <div class="min-w-0 flex-1">
          <Skeleton text width="6rem" />
          <Skeleton class="mt-1" width="100%" height="0.375rem" />
        </div>
        <Skeleton width="2rem" />
      </li>
    </ol>

    <p v-else-if="error" class="px-4 py-6 text-sm text-red-600">{{ error }}</p>

    <p
      v-else-if="rankingWithPoints.length === 0"
      class="flex flex-1 items-center justify-center px-4 py-12 text-sm text-slate-500"
    >
      {{ isPastMonth ? "Nadie sumó puntos este mes." : "Aún nadie ha sumado puntos este mes." }}
    </p>

    <ol v-else class="divide-y divide-slate-100">
      <li
        v-for="(entry, index) in rankingWithPoints"
        :key="entry.user_id"
        class="flex items-center gap-3 px-4 py-3"
        :class="winnerIds.has(entry.user_id) ? 'bg-amber-50' : ''"
      >
        <span class="w-4 text-sm font-semibold text-slate-400">
          {{ index + 1 }}
        </span>
        <span
          class="h-2.5 w-2.5 shrink-0 rounded-full"
          :style="{ backgroundColor: colors[entry.user_id].solid }"
        />
        <div class="min-w-0 flex-1">
          <p class="truncate text-[13px] font-medium text-slate-800">
            {{ entry.name }}<span v-if="winnerIds.has(entry.user_id)"> 👑</span>
          </p>
          <div class="mt-1 h-1.5 overflow-hidden rounded-full bg-slate-100">
            <div
              class="h-full rounded-full bg-amber-400"
              :style="{ width: `${leader ? (entry.points / leader) * 100 : 0}%` }"
            />
          </div>
        </div>
        <span
          class="inline-flex items-center gap-1 text-sm font-semibold text-amber-700"
        >
          <Icon :path="icons.star" :size="13" />
          {{ entry.points }}
        </span>
      </li>
    </ol>
  </WidgetCard>
</template>
