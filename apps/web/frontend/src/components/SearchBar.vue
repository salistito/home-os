<script setup lang="ts">
import { icons } from "../lib/icons";
import Icon from "./Icon.vue";

const modelValue = defineModel<string>({ required: true });

withDefaults(
  defineProps<{ placeholder?: string }>(),
  { placeholder: "Buscar…" },
);
</script>

<template>
  <div class="relative flex-1 min-w-0">
    <Icon
      :path="icons.search"
      :size="16"
      class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
    />
    <input
      type="text"
      :value="modelValue"
      :placeholder="placeholder"
      class="h-9 w-full rounded-lg border border-slate-200 pl-9 pr-8 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
      @input="modelValue = ($event.target as HTMLInputElement).value"
    />
    <button
      v-if="modelValue"
      type="button"
      class="absolute right-2 top-1/2 -translate-y-1/2 rounded p-0.5 text-slate-400 hover:text-slate-600"
      @click="modelValue = ''"
    >
      <Icon :path="icons.close" :size="14" />
    </button>
  </div>
</template>
