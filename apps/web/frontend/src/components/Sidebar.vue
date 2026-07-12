<script setup lang="ts">
import Icon from "./Icon.vue";
import { icons } from "../lib/icons";
import { auth } from "../lib/auth";
import type { ModuleDef } from "../modules";

defineProps<{
  modules: ModuleDef[];
  activeId: string;
  open: boolean;
}>();

defineEmits<{
  select: [id: string];
  close: [];
}>();
</script>

<template>
  <div
    v-if="open"
    class="fixed inset-0 z-30 bg-slate-900/40 lg:hidden"
    @click="$emit('close')"
  />
  <aside
    class="fixed inset-y-0 left-0 z-40 flex w-60 shrink-0 flex-col border-r border-slate-200 bg-slate-50 transition-transform lg:static lg:translate-x-0"
    :class="open ? 'translate-x-0' : '-translate-x-full'"
  >
    <div class="flex items-center gap-2.5 px-4 py-3.5">
      <div
        class="flex h-6 w-6 items-center justify-center rounded-md bg-slate-900 text-[11px] font-bold text-white"
      >
        H
      </div>
      <span class="text-sm font-semibold text-slate-800">HomeOS</span>
      <button
        class="ml-auto flex h-7 w-7 items-center justify-center rounded-md text-slate-500 hover:bg-slate-200/60 lg:hidden"
        aria-label="Cerrar menú"
        @click="$emit('close')"
      >
        <Icon :path="icons.close" :size="16" />
      </button>
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

    <button
      class="mt-auto mb-3 mx-3 flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-left text-[13px] font-medium text-slate-600 transition-colors hover:bg-slate-200/60"
      @click="auth.logout()"
    >
      <Icon :path="icons.logout" :size="15" class="text-slate-400" />
      Cerrar sesión
    </button>
  </aside>
</template>
