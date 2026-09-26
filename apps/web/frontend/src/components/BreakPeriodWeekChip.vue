<script setup lang="ts">
import { formatBreakPeriodsTooltip } from "../lib/breaks";
import type { BreakPeriodInfo } from "../types";

const props = defineProps<{ breakPeriods: BreakPeriodInfo[] }>();
</script>

<template>
  <span
    v-if="props.breakPeriods.length"
    class="inline-block rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 text-[10px] font-medium text-amber-700"
    :title="formatBreakPeriodsTooltip(props.breakPeriods, { includeLabel: true })"
  >
    🌴 Semana con días en receso
  </span>
</template>
