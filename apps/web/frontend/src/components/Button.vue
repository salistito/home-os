<script setup lang="ts">
import { computed } from "vue";

type Variant = "primary" | "ghost" | "danger";
type Size = "sm" | "md";

const props = withDefaults(
  defineProps<{
    variant?: Variant;
    size?: Size;
    type?: "button" | "submit";
    loading?: boolean;
    disabled?: boolean;
    iconOnly?: boolean;
  }>(),
  {
    variant: "primary",
    size: "md",
    type: "button",
    loading: false,
    disabled: false,
    iconOnly: false,
  },
);

const emit = defineEmits<{ click: [] }>();

const isDisabled = computed(() => props.disabled || props.loading);

const VARIANTS: Record<Variant, string> = {
  primary: "bg-slate-900 text-white hover:bg-slate-700",
  ghost: "text-slate-600 hover:bg-slate-100",
  danger: "bg-red-600 text-white hover:bg-red-500",
};

const SIZES: Record<Size, string> = {
  sm: "px-2.5 py-1.5 text-xs",
  md: "px-4 py-2 text-sm",
};

const ICON_SIZES: Record<Size, string> = {
  sm: "p-1.5",
  md: "p-2",
};

const classes = computed(() => [
  "inline-flex items-center justify-center gap-1 rounded-lg font-medium outline-none transition-colors disabled:opacity-50",
  VARIANTS[props.variant],
  props.iconOnly ? ICON_SIZES[props.size] : SIZES[props.size],
  props.loading ? "cursor-wait" : "disabled:cursor-not-allowed",
]);

function onClick() {
  if (!isDisabled.value) emit("click");
}
</script>

<template>
  <button :type="type" :disabled="isDisabled" :class="classes" @click="onClick">
    <svg
      v-if="loading"
      class="h-3.5 w-3.5 animate-spin"
      viewBox="0 0 24 24"
      fill="none"
    >
      <circle
        class="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        stroke-width="4"
      />
      <path
        class="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 0 1 8-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
    <slot />
  </button>
</template>
