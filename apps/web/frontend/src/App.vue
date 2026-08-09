<script setup lang="ts">
import { computed, ref } from "vue";
import BottomNav from "./components/BottomNav.vue";
import Sidebar from "./components/Sidebar.vue";
import Login from "./components/Login.vue";
import Toasts from "./components/Toasts.vue";
import { modules } from "./modules";
import { auth } from "./lib/auth";
import { usePullToRefresh } from "./lib/pullToRefresh";

const ACTIVE_KEY = "homeos:active-module";

const storedId = localStorage.getItem(ACTIVE_KEY);
const activeId = ref(
  modules.some((m) => m.id === storedId) ? (storedId as string) : modules[0].id,
);
const scroller = ref<HTMLElement | null>(null);
const refreshKey = ref(0);
const pull = usePullToRefresh(scroller, () => {
  refreshKey.value++;
});
const visibleModules = computed(() =>
  modules.filter((m) => !m.requiresAdmin || auth.isAdmin.value),
);
const activeModule = computed(
  () => visibleModules.value.find((m) => m.id === activeId.value) ?? visibleModules.value[0],
);

function selectModule(id: string) {
  activeId.value = id;
  localStorage.setItem(ACTIVE_KEY, id);
  scroller.value?.scrollTo({ top: 0 });
}
</script>

<template>
  <Login v-if="!auth.isAuthenticated.value" />
  <div
    v-else
    class="flex h-screen flex-col bg-slate-50 font-sans text-slate-900 antialiased lg:flex-row"
  >
    <header
      class="flex items-center gap-2.5 bg-slate-50 px-4 pb-2 pt-3 lg:hidden"
    >
      <img src="/homeos-logo.png" alt="HomeOS" class="h-6 w-6 rounded-md object-cover" />
      <span class="text-sm font-semibold text-slate-800">
        {{ activeModule.label }}
      </span>
    </header>

    <Sidebar :modules="visibleModules" :active-id="activeModule.id" @select="selectModule" />
    <div
      class="relative mx-2 flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden rounded-xl border border-slate-200/80 bg-white shadow-sm lg:mx-0 lg:mr-2 lg:mb-4 lg:mt-2"
    >
      <div
        v-if="pull.active.value"
        class="pointer-events-none absolute inset-x-0 top-0 z-10 flex items-center justify-center overflow-hidden"
        :style="{ height: `${pull.distance.value}px` }"
      >
        <svg
          class="h-6 w-6 text-slate-400"
          :class="pull.refreshing.value ? 'animate-spin' : ''"
          viewBox="0 0 24 24"
          fill="none"
        >
          <circle
            cx="12"
            cy="12"
            r="9"
            stroke="currentColor"
            stroke-width="2.5"
            class="opacity-20"
          />
          <circle
            cx="12"
            cy="12"
            r="9"
            stroke="currentColor"
            stroke-width="2.5"
            stroke-linecap="round"
            transform="rotate(-90 12 12)"
            :stroke-dasharray="56.5"
            :stroke-dashoffset="
              pull.refreshing.value ? 42 : 56.5 * (1 - pull.progress.value)
            "
          />
        </svg>
      </div>
      <main
        ref="scroller"
        class="flex-1 overflow-auto overscroll-y-contain px-4 py-4 sm:px-6 sm:py-6"
        :class="pull.dragging.value ? '' : 'transition-transform duration-200'"
        :style="{ transform: `translateY(${pull.distance.value}px)` }"
      >
        <component :is="activeModule.component" :key="refreshKey" />
      </main>
    </div>
    <div id="module-action-bar" class="shrink-0 px-2 pt-2 empty:hidden lg:hidden" />
    <BottomNav :modules="visibleModules" :active-id="activeModule.id" @select="selectModule" />
    <Toasts />
  </div>
</template>
