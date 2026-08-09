<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import Icon from "./Icon.vue";
import { auth } from "../lib/auth";
import { icons } from "../lib/icons";
import type { ModuleDef } from "../modules";

defineProps<{
  modules: ModuleDef[];
  activeId: string;
}>();

defineEmits<{
  select: [id: string];
}>();

const WIDTH_KEY = "homeos:sidebar-width";
const MIN_WIDTH = 180;
const MAX_WIDTH = 360;
const RAIL_WIDTH = 60;
const SNAP_POINT = 150;

const stored = Number(localStorage.getItem(WIDTH_KEY));
const width = ref(stored >= RAIL_WIDTH && stored <= MAX_WIDTH ? stored : 240);
const resizing = ref(false);
const isDesktop = ref(false);
const collapsed = computed(() => isDesktop.value && width.value <= RAIL_WIDTH);

const desktopQuery = window.matchMedia("(min-width: 1024px)");

function syncDesktop(e: MediaQueryList | MediaQueryListEvent) {
  isDesktop.value = e.matches;
}

function onPointerMove(e: PointerEvent) {
  const x = e.clientX;
  width.value = x < SNAP_POINT ? RAIL_WIDTH : Math.min(Math.max(x, MIN_WIDTH), MAX_WIDTH);
}

function stopResize() {
  resizing.value = false;
  document.body.style.userSelect = "";
  document.body.style.cursor = "";
  localStorage.setItem(WIDTH_KEY, String(width.value));
  window.removeEventListener("pointermove", onPointerMove);
  window.removeEventListener("pointerup", stopResize);
}

function startResize() {
  resizing.value = true;
  document.body.style.userSelect = "none";
  document.body.style.cursor = "col-resize";
  window.addEventListener("pointermove", onPointerMove);
  window.addEventListener("pointerup", stopResize);
}

function toggleCollapse() {
  width.value = collapsed.value ? 240 : RAIL_WIDTH;
  localStorage.setItem(WIDTH_KEY, String(width.value));
}

onMounted(() => {
  syncDesktop(desktopQuery);
  desktopQuery.addEventListener("change", syncDesktop);
});

onUnmounted(() => {
  desktopQuery.removeEventListener("change", syncDesktop);
  stopResize();
});
</script>

<template>
  <aside
    class="relative hidden shrink-0 flex-col bg-slate-50 lg:flex"
    :style="{ width: `${width}px` }"
  >
    <div
      class="flex items-center gap-2.5 py-3.5"
      :class="collapsed ? 'justify-center px-0' : 'pl-[18px] pr-4'"
    >
      <img
        src="/homeos-logo.png"
        alt="HomeOS"
        class="h-6 w-6 shrink-0 rounded-md object-cover"
      />
      <span v-if="!collapsed" class="truncate text-sm font-semibold text-slate-800"
        >HomeOS</span
      >
    </div>

    <nav class="flex flex-col gap-0.5 px-3 pt-2">
      <p
        class="overflow-hidden px-2 pb-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400"
        :class="collapsed ? 'invisible' : ''"
      >
        Módulos
      </p>
      <button
        v-for="m in modules"
        :key="m.id"
        class="flex h-9 w-full items-center gap-2.5 rounded-lg text-left text-sm font-medium transition-colors"
        :class="[
          collapsed ? 'justify-center px-0' : 'px-2.5',
          m.id === activeId
            ? 'bg-slate-200/70 text-slate-900'
            : 'text-slate-600 hover:bg-slate-200/40',
        ]"
        :title="collapsed ? m.label : undefined"
        @click="$emit('select', m.id)"
      >
        <Icon
          :path="m.icon"
          :size="16"
          class="shrink-0"
          :class="m.id === activeId ? 'text-slate-700' : 'text-slate-400'"
        />
        <span v-if="!collapsed" class="truncate">{{ m.label }}</span>
      </button>
    </nav>

    <button
      class="mt-auto mb-3 mx-3 flex h-9 items-center gap-2.5 rounded-lg text-left text-sm font-medium text-slate-600 transition-colors hover:bg-slate-200/40"
      :class="collapsed ? 'justify-center px-0' : 'px-2.5'"
      :title="collapsed ? 'Cerrar sesión' : undefined"
      @click="auth.logout()"
    >
      <Icon :path="icons.logout" :size="16" class="shrink-0 text-slate-400" />
      <span v-if="!collapsed" class="truncate">Cerrar sesión</span>
    </button>

    <div
      v-if="isDesktop"
      class="group absolute -right-1.5 bottom-7 top-5 z-10 hidden w-3 cursor-col-resize lg:block"
      title="Arrastra para redimensionar, doble click para colapsar"
      @pointerdown.prevent="startResize"
      @dblclick="toggleCollapse"
    >
      <div
        class="mx-auto h-full w-0.5 rounded-full transition-colors"
        :class="resizing ? 'bg-slate-400' : 'bg-transparent group-hover:bg-slate-300'"
      />
    </div>
  </aside>
</template>
