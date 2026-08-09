<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

const props = defineProps<{
  label: string;
  consumed: number;
  target: number;
  unit: string;
  color: string;
}>();

const radius = 42;
const circumference = 2 * Math.PI * radius;

const revealed = ref(false);

onMounted(() => {
  requestAnimationFrame(() => {
    revealed.value = true;
  });
});

const pct = computed(() =>
  props.target > 0 ? Math.round((props.consumed / props.target) * 100) : 0,
);
const offset = computed(() =>
  revealed.value ? circumference * (1 - Math.min(pct.value, 100) / 100) : circumference,
);
const over = computed(() => props.target > 0 && props.consumed > props.target);
</script>

<template>
  <div class="flex flex-col items-center gap-1.5">
    <div class="relative h-24 w-24">
      <svg viewBox="0 0 100 100" class="h-full w-full -rotate-90">
        <circle
          cx="50"
          cy="50"
          :r="radius"
          fill="none"
          stroke="#f1f5f9"
          stroke-width="10"
        />
        <circle
          cx="50"
          cy="50"
          :r="radius"
          fill="none"
          :stroke="color"
          stroke-width="10"
          stroke-linecap="round"
          :stroke-dasharray="circumference"
          :stroke-dashoffset="offset"
          class="transition-[stroke-dashoffset] duration-700 ease-out"
        />
      </svg>
      <div class="absolute inset-0 flex items-center justify-center">
        <span
          class="text-base font-bold tabular-nums"
          :class="over ? 'text-red-600' : 'text-slate-800'"
        >
          {{ pct }}%
        </span>
      </div>
    </div>
    <p class="text-xs font-medium text-slate-800">{{ label }}</p>
    <p class="-mt-0.5 text-xs font-medium tabular-nums text-slate-500">
      <span :class="over ? 'text-red-600' : 'text-slate-500'">
        {{ Math.round(consumed) }} {{ unit }}
      </span>
      / {{ Math.round(target) }} {{ unit }}
    </p>
  </div>
</template>
