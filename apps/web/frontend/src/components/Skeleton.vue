<script setup lang="ts">
withDefaults(
  defineProps<{
    width: string;
    height?: string;
    rounded?: boolean;
    text?: boolean;
  }>(),
  {
    height: "0.875rem",
    rounded: false,
    text: false,
  },
);
</script>

<template>
  <span v-if="text" class="flex h-5 items-center">
    <span
      class="block animate-pulse bg-slate-200"
      :class="rounded ? 'rounded-md' : 'rounded-full'"
      :style="{ width, height }"
    />
  </span>
  <span
    v-else
    class="block animate-pulse bg-slate-200"
    :class="rounded ? 'rounded-md' : 'rounded-full'"
    :style="{ width, height }"
  />
</template>
