<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import Icon from "../../components/Icon.vue";
import Button from "../../components/Button.vue";
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

const root = ref<HTMLElement | null>(null);
const open = ref(false);

const index = computed(() =>
  props.periods.findIndex((p) => p.id === props.modelValue),
);
const selected = computed(() => props.periods[index.value] ?? null);
const hasNewer = computed(() => index.value > 0);
const hasOlder = computed(
  () => index.value >= 0 && index.value < props.periods.length - 1,
);

function step(direction: "older" | "newer") {
  const i = index.value + (direction === "older" ? 1 : -1);
  if (i >= 0 && i < props.periods.length) {
    emit("update:modelValue", props.periods[i].id);
  }
}

function pick(id: number) {
  emit("update:modelValue", id);
  open.value = false;
}

function onDocClick(e: MouseEvent) {
  if (root.value && !root.value.contains(e.target as Node)) open.value = false;
}
function onKey(e: KeyboardEvent) {
  if (e.key === "Escape") open.value = false;
}

onMounted(() => {
  document.addEventListener("click", onDocClick);
  document.addEventListener("keydown", onKey);
});
onUnmounted(() => {
  document.removeEventListener("click", onDocClick);
  document.removeEventListener("keydown", onKey);
});
</script>

<template>
  <div class="flex items-center gap-2">
    <div
      ref="root"
      class="relative inline-flex items-center rounded-lg border border-slate-200 bg-white"
    >
      <button
        type="button"
        :disabled="!hasOlder"
        class="rounded-l-lg px-2 py-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-800 disabled:opacity-25 disabled:hover:bg-transparent"
        aria-label="Mes anterior"
        @click="step('older')"
      >
        <Icon :path="icons.chevronLeft" :size="16" />
      </button>

      <button
        type="button"
        class="flex min-w-36 items-center justify-center gap-1.5 border-x border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-800 transition-colors hover:bg-slate-50"
        @click="open = !open"
      >
        <span
          v-if="selected?.status === 'open'"
          class="h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500"
        />
        {{ selected?.label ?? "—" }}
        <Icon
          :path="icons.chevronRight"
          :size="14"
          class="rotate-90 text-slate-400 transition-transform"
          :class="{ '-rotate-90': open }"
        />
      </button>

      <button
        type="button"
        :disabled="!hasNewer"
        class="rounded-r-lg px-2 py-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-800 disabled:opacity-25 disabled:hover:bg-transparent"
        aria-label="Mes siguiente"
        @click="step('newer')"
      >
        <Icon :path="icons.chevronRight" :size="16" />
      </button>

      <div
        v-if="open"
        class="absolute left-0 top-full z-20 mt-1 max-h-72 w-full min-w-40 overflow-auto rounded-lg border border-slate-200 bg-white py-1 shadow-lg"
      >
        <button
          v-for="p in periods"
          :key="p.id"
          type="button"
          class="flex w-full items-center gap-2 px-3 py-1.5 text-left text-sm transition-colors hover:bg-slate-50"
          :class="
            p.id === modelValue
              ? 'font-medium text-slate-900'
              : 'text-slate-600'
          "
          @click="pick(p.id)"
        >
          <span
            class="h-1.5 w-1.5 shrink-0 rounded-full"
            :class="p.status === 'open' ? 'bg-emerald-500' : 'bg-transparent'"
          />
          {{ p.label }}
        </button>
      </div>
    </div>

    <Button
      size="sm"
      :loading="busy"
      class="ml-auto"
      @click="emit('openNew')"
    >
      <Icon v-if="!busy" :path="icons.plus" :size="14" />
      {{ busy ? "Abriendo…" : "Abrir mes nuevo" }}
    </Button>
  </div>
</template>
