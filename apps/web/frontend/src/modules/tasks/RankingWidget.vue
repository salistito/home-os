<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { tasksApi } from "../../api/tasks";
import Icon from "../../components/Icon.vue";
import Skeleton from "../../components/Skeleton.vue";
import WidgetCard from "../../components/WidgetCard.vue";
import { colorsByUser } from "../../lib/colors";
import { getCurrentMonth } from "../../lib/date";
import { formatMonth } from "../../lib/format";
import { icons } from "../../lib/icons";
import type { MonthlyRankingEntry } from "../../types";

const ranking = ref<MonthlyRankingEntry[]>([]);
const error = ref<string | null>(null);
const loading = ref(true);

const title = computed(() => `Ranking del mes (${formatMonth(getCurrentMonth())})`);

const leader = computed(() =>
  ranking.value.length > 0 ? ranking.value[0].points : 0,
);

const colors = computed(() => colorsByUser(ranking.value.map((entry) => ({ id: entry.user_id}))));

onMounted(async () => {
  try {
    ranking.value = (await tasksApi.getMonthlyRanking()).ranking;
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Error inesperado";
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <WidgetCard :title="title">
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
      v-else-if="ranking.length === 0"
      class="px-4 py-6 text-sm text-slate-500"
    >
      Nadie ha sumado puntos este mes todavía.
    </p>

    <ol v-else class="divide-y divide-slate-100">
      <li
        v-for="(entry, index) in ranking"
        :key="entry.user_id"
        class="flex items-center gap-3 px-4 py-3"
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
            {{ entry.name }}
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
