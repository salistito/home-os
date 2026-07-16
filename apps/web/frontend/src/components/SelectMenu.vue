<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import Icon from "./Icon.vue";
import { icons } from "../lib/icons";

export interface SelectOption {
  value: string;
  label: string;
  dot?: string;
}

const props = defineProps<{
  modelValue: string;
  options: SelectOption[];
  placeholder?: string;
  disabled?: boolean;
}>();
const emit = defineEmits<{ "update:modelValue": [value: string] }>();

const root = ref<HTMLElement | null>(null);
const open = ref(false);

const selected = computed(
  () => props.options.find((o) => o.value === props.modelValue) ?? null,
);

function pick(value: string) {
  emit("update:modelValue", value);
  open.value = false;
}

function toggle() {
  if (!props.disabled) open.value = !open.value;
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
  <div ref="root" class="relative">
    <button
      type="button"
      :disabled="disabled"
      class="flex w-full items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-left text-sm text-slate-800 transition-colors hover:bg-slate-50 focus:border-amber-400 focus:outline-none focus:ring-2 focus:ring-amber-100 disabled:cursor-not-allowed disabled:opacity-50"
      @click="toggle"
    >
      <span
        v-if="selected?.dot"
        class="h-2.5 w-2.5 shrink-0 rounded-full"
        :style="{ backgroundColor: selected.dot }"
      />
      <span :class="{ 'text-slate-400': !selected }">
        {{ selected?.label ?? placeholder ?? "Seleccionar" }}
      </span>
      <Icon
        :path="icons.chevronRight"
        :size="14"
        class="ml-auto rotate-90 text-slate-400 transition-transform"
        :class="{ '-rotate-90': open }"
      />
    </button>

    <div
      v-if="open"
      class="absolute left-0 top-full z-20 mt-1 max-h-60 w-full overflow-auto rounded-lg border border-slate-200 bg-white py-1 shadow-lg"
    >
      <button
        v-for="opt in options"
        :key="opt.value"
        type="button"
        class="flex w-full items-center gap-2 px-3 py-1.5 text-left text-sm transition-colors hover:bg-slate-50"
        :class="
          opt.value === modelValue
            ? 'font-medium text-slate-900'
            : 'text-slate-600'
        "
        @click="pick(opt.value)"
      >
        <span
          v-if="opt.dot"
          class="h-2.5 w-2.5 shrink-0 rounded-full"
          :style="{ backgroundColor: opt.dot }"
        />
        {{ opt.label }}
      </button>
    </div>
  </div>
</template>
