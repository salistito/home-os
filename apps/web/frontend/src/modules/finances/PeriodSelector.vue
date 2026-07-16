<script setup lang="ts">
import { computed } from "vue";
import Icon from "../../components/Icon.vue";
import { icons } from "../../lib/icons";
import type { FinancePeriod } from "../../types";

const props = defineProps<{
  periods: FinancePeriod[];
  modelValue: number | null;
  busy?: boolean;
}>();
const emit = defineEmits<{
  "update:modelValue": [id: number];
  openNew: [];
}>();

const index = computed(() =>
  props.periods.findIndex((p) => p.id === props.modelValue),
);
const hasNewer = computed(() => index.value > 0);
const hasOlder = computed(
  () => index.value >= 0 && index.value < props.periods.length - 1,
);

function go(delta: number) {
  const i = index.value + delta;
  if (i >= 0 && i < props.periods.length) {
    emit("update:modelValue", props.periods[i].id);
  }
}

function onSelect(e: Event) {
  emit("update:modelValue", Number((e.target as HTMLSelectElement).value));
}
</script>

<template>
  <div class="flex items-center gap-2">
    <div class="flex items-center gap-1">
      <button
        type="button"
        :disabled="!hasNewer"
        class="rounded-md p-1.5 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-800 disabled:opacity-30"
        aria-label="Mes más nuevo"
        @click="go(-1)"
      >
        <Icon :path="icons.chevronLeft" :size="16" />
      </button>

      <div class="relative">
        <select
          class="appearance-none rounded-lg border border-slate-200 bg-white py-1.5 pl-3 pr-8 text-sm font-medium text-slate-800"
          :value="modelValue ?? ''"
          @change="onSelect"
        >
          <option v-for="p in periods" :key="p.id" :value="p.id">
            {{ p.label }}{{ p.status === "open" ? " · abierto" : "" }}
          </option>
        </select>
        <Icon
          :path="icons.chevronRight"
          :size="14"
          class="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 rotate-90 text-slate-400"
        />
      </div>

      <button
        type="button"
        :disabled="!hasOlder"
        class="rounded-md p-1.5 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-800 disabled:opacity-30"
        aria-label="Mes más antiguo"
        @click="go(1)"
      >
        <Icon :path="icons.chevronRight" :size="16" />
      </button>
    </div>

    <button
      type="button"
      :disabled="busy"
      class="ml-auto inline-flex items-center gap-1 rounded-lg bg-slate-900 px-2.5 py-1.5 text-xs font-medium text-white transition-colors hover:bg-slate-700 disabled:opacity-50"
      @click="emit('openNew')"
    >
      <Icon :path="icons.plus" :size="14" />
      {{ busy ? "Abriendo…" : "Abrir mes nuevo" }}
    </button>
  </div>
</template>
