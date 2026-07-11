<script setup lang="ts">
import Icon from "./Icon.vue";
import type { ModuleDef } from "../modules";

defineProps<{
  modules: ModuleDef[];
  activeId: string;
}>();

defineEmits<{
  select: [id: string];
}>();
</script>

<template>
  <aside class="flex w-60 shrink-0 flex-col border-r border-slate-200 bg-slate-50">
    <div class="flex items-center gap-2.5 px-4 py-3.5">
      <div
        class="flex h-6 w-6 items-center justify-center rounded-md bg-slate-900 text-[11px] font-bold text-white"
      >
        H
      </div>
      <span class="text-sm font-semibold text-slate-800">HomeOS</span>
    </div>

    <nav class="px-3 pt-2">
      <p
        class="px-2 pb-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400"
      >
        Módulos
      </p>
      <button
        v-for="m in modules"
        :key="m.id"
        class="flex w-full items-center gap-2.5 rounded-md px-2.5 py-1.5 text-left text-[13px] font-medium transition-colors"
        :class="
          m.id === activeId
            ? 'bg-white text-slate-900 shadow-sm ring-1 ring-slate-200'
            : 'text-slate-600 hover:bg-slate-200/60'
        "
        @click="$emit('select', m.id)"
      >
        <Icon :path="m.icon" :size="15" class="text-slate-400" />
        {{ m.label }}
      </button>
    </nav>
  </aside>
</template>
