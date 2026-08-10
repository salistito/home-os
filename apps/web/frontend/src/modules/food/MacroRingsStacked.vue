<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

interface Ring {
  key: string;
  label: string;
  consumed: number;
  target: number;
  unit: string;
  color: string;
}

const props = defineProps<{ rings: readonly Ring[] }>();

const RADII = [46, 35, 24];
const STROKE = 8.5;

const revealed = ref(false);

const tracks = computed(() =>
  props.rings.slice(0, RADII.length).map((ring, index) => {
    const radius = RADII[index];
    const circumference = 2 * Math.PI * radius;
    const pct = ring.target > 0 ? Math.round((ring.consumed / ring.target) * 100) : 0;
    return {
      ...ring,
      radius,
      circumference,
      pct,
      offset: revealed.value ? circumference * (1 - Math.min(pct, 100) / 100) : circumference,
      delay: index * 120,
      over: ring.target > 0 && ring.consumed > ring.target,
    };
  }),
);

onMounted(() => {
  requestAnimationFrame(() => {
    revealed.value = true;
  });
});
</script>

<template>
  <div class="flex items-center gap-4">
    <div class="h-[120px] w-[120px] shrink-0">
      <svg viewBox="0 0 100 100" class="h-full w-full -rotate-90">
        <circle
          v-for="track in tracks"
          :key="`bg-${track.key}`"
          cx="50"
          cy="50"
          :r="track.radius"
          fill="none"
          stroke="#f1f5f9"
          :stroke-width="STROKE"
        />
        <circle
          v-for="track in tracks"
          :key="track.key"
          cx="50"
          cy="50"
          :r="track.radius"
          fill="none"
          :stroke="track.color"
          :stroke-width="STROKE"
          stroke-linecap="round"
          :stroke-dasharray="track.circumference"
          :stroke-dashoffset="track.offset"
          class="transition-[stroke-dashoffset] duration-700 ease-out"
          :style="{ transitionDelay: `${track.delay}ms` }"
        />
      </svg>
    </div>

    <ul class="min-w-0 flex-1 space-y-2">
      <li v-for="track in tracks" :key="`legend-${track.key}`" class="min-w-0">
        <div class="flex items-baseline gap-1.5">
          <span
            class="h-2 w-2 shrink-0 rounded-full"
            :style="{ backgroundColor: track.color }"
          />
          <span class="truncate text-xs font-medium text-slate-800">
            {{ track.label }}
          </span>
          <span
            class="ml-auto shrink-0 text-xs font-semibold tabular-nums"
            :class="track.over ? 'text-red-600' : 'text-slate-500'"
          >
            {{ track.pct }}%
          </span>
        </div>
        <p class="pl-3.5 text-xs tabular-nums text-slate-500">
          <span :class="track.over ? 'text-red-600' : ''">
            {{ Math.round(track.consumed) }}
          </span>
          / {{ Math.round(track.target) }} {{ track.unit }}
        </p>
      </li>
    </ul>
  </div>
</template>
