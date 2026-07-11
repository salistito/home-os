<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import Icon from "../../components/Icon.vue";
import WidgetCard from "../../components/WidgetCard.vue";
import { icons } from "../../lib/icons";
import { colorsByUser, initials } from "../../lib/colors";
import { tasksApi } from "../../api/tasks";
import type { ScoreEntry } from "../../types";

const ranking = ref<ScoreEntry[]>([]);
const error = ref<string | null>(null);
const loading = ref(true);

const leader = computed(() =>
  ranking.value.length > 0 ? ranking.value[0].points : 0,
);

const colors = computed(() =>
  colorsByUser(ranking.value.map((entry) => entry.user_id)),
);

onMounted(async () => {
  try {
    ranking.value = (await tasksApi.scores()).ranking;
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Error inesperado";
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <WidgetCard title="Ranking del mes">
    <p v-if="loading" class="px-4 py-6 text-sm text-slate-400">Cargando…</p>

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
          class="flex h-8 w-8 items-center justify-center rounded-full text-xs font-semibold"
          :class="[colors[entry.user_id].bg, colors[entry.user_id].text]"
        >
          {{ initials(entry.name) }}
        </span>
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
