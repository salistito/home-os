<script setup lang="ts">
defineProps<{ title: string; count?: number }>();
</script>

<template>
  <section
    class="flex flex-col overflow-hidden rounded-xl border border-slate-200 bg-white"
  >
    <header
      class="flex items-baseline gap-2 border-b border-slate-100 px-4 py-3"
    >
      <h3 class="text-sm font-semibold text-slate-900">{{ title }}</h3>
      <span v-if="count !== undefined" class="text-xs text-slate-400">
        ({{ count }})
      </span>
      <div class="ml-auto flex items-center gap-2">
        <slot name="actions" />
      </div>
    </header>
    <div class="flex-1">
      <slot />
    </div>
  </section>
</template>
