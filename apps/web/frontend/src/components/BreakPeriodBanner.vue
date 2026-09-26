<script setup lang="ts">
import { computed } from "vue";
import {
  breakModuleHint,
  breakPeriodsOnDay,
  formatBreakPeriodsTooltip,
} from "../lib/breaks";
import { getToday } from "../lib/date";
import type { BreakPeriodInfo } from "../types";

const props = withDefaults(
  defineProps<{
    module: "food" | "fitness";
    breakPeriods: BreakPeriodInfo[];
    day?: string;
  }>(),
  { day: () => getToday() },
);

const activePeriods = computed(() => breakPeriodsOnDay(props.breakPeriods, props.day));
</script>

<template>
  <div
    v-if="activePeriods.length"
    class="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 ring-1 ring-amber-100"
    :title="formatBreakPeriodsTooltip(activePeriods)"
  >
    <p class="font-semibold">🌴 Módulo incluido en un período de receso. </p>
    <p class="text-amber-700">{{ breakModuleHint(module) }}</p>
  </div>
</template>
