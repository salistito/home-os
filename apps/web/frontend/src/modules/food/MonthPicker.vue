<script setup lang="ts">
import { computed, ref } from "vue";
import IconButton from "../../components/IconButton.vue";
import { addDays, addMonths, getCurrentYearMonth, getToday, startOfWeek } from "../../lib/date";
import { WEEKDAYS_SHORT, formatYearMonth } from "../../lib/format";
import { icons } from "../../lib/icons";

const props = defineProps<{ selected: string }>();
const emit = defineEmits<{ select: [date: string]; close: [] }>();

const WEEKDAY_LABELS = [...WEEKDAYS_SHORT.slice(1), WEEKDAYS_SHORT[0]];

const today = getToday();

const yearMonth = ref(
  props.selected
    ? `${props.selected.slice(0, 4)}-${props.selected.slice(5, 7)}`
    : getCurrentYearMonth(),
);

const cells = computed(() => {
  const gridStart = startOfWeek(`${yearMonth.value}-01`);
  return Array.from({ length: 42 }, (_, i) => addDays(gridStart, i));
});

function inMonth(date: string): boolean {
  return date.startsWith(yearMonth.value);
}

function dayNumber(date: string): number {
  return Number(date.slice(8, 10));
}

function cellClass(date: string): string[] {
  const base = "flex h-8 w-8 items-center justify-center rounded-full text-xs transition-colors";
  if (!inMonth(date)) return [base, "text-slate-300 hover:bg-slate-50"];
  if (date === props.selected) return [base, "bg-slate-900 font-semibold text-white"];
  if (date === today) return [base, "font-semibold text-amber-600 ring-2 ring-amber-400 hover:bg-slate-100"];
  return [base, "text-slate-700 hover:bg-slate-100"];
}

function select(date: string) {
  emit("select", date);
}
</script>

<template>
  <div class="w-72 rounded-xl border border-slate-200 bg-white p-3 shadow-lg">
    <div class="mb-2 flex items-center justify-between">
      <IconButton
        :icon="icons.chevronLeft"
        label="Mes anterior"
        @click="yearMonth = addMonths(yearMonth, -1)"
      />
      <h4 class="text-sm font-semibold text-slate-900">{{ formatYearMonth(yearMonth) }}</h4>
      <IconButton
        :icon="icons.chevronRight"
        label="Mes siguiente"
        @click="yearMonth = addMonths(yearMonth, 1)"
      />
    </div>
    <div class="grid grid-cols-7 gap-1">
      <span
        v-for="label in WEEKDAY_LABELS"
        :key="label"
        class="py-1 text-center text-[10px] font-medium uppercase tracking-wide text-slate-400"
      >
        {{ label }}
      </span>
    </div>
    <div class="grid grid-cols-7 gap-1">
      <div
        v-for="date in cells"
        :key="date"
        class="flex justify-center"
      >
        <button
          type="button"
          :class="cellClass(date)"
          @click="select(date)"
        >
          {{ dayNumber(date) }}
        </button>
      </div>
    </div>
  </div>
</template>
