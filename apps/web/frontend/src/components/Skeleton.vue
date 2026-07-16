<script setup lang="ts">
withDefaults(
  defineProps<{
    width: string;
    height?: string;
    text?: boolean;
  }>(),
  {
    height: "0.875rem",
    text: false,
  },
);
</script>

<template>
  <span v-if="text" class="flex h-5 items-center">
    <span
      class="block animate-pulse rounded-full bg-slate-200"
      :style="{ width, height }"
    />
  </span>
  <span
    v-else
    class="block animate-pulse rounded-full bg-slate-200"
    :style="{ width, height }"
  />
</template>
