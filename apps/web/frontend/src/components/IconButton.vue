<script setup lang="ts">
import { computed } from "vue";
import Icon from "./Icon.vue";

type Variant = "neutral" | "danger";

const props = withDefaults(
  defineProps<{
    icon: string;
    label: string;
    variant?: Variant;
    size?: number;
    disabled?: boolean;
  }>(),
  { variant: "neutral", size: 14, disabled: false },
);

const emit = defineEmits<{ click: [] }>();

const VARIANTS: Record<Variant, string> = {
  neutral: "hover:bg-slate-200 hover:text-slate-700",
  danger: "hover:bg-red-50 hover:text-red-600",
};

const classes = computed(() => [
  "rounded-md p-1 text-slate-400 transition-colors disabled:opacity-50",
  VARIANTS[props.variant],
]);

function onClick() {
  if (!props.disabled) emit("click");
}
</script>

<template>
  <button
    type="button"
    :class="classes"
    :disabled="disabled"
    :aria-label="label"
    :title="label"
    @click="onClick"
  >
    <Icon :path="icon" :size="size" />
  </button>
</template>
