<script setup lang="ts">
import { computed, ref } from "vue";
import Sidebar from "./components/Sidebar.vue";
import Login from "./components/Login.vue";
import Toasts from "./components/Toasts.vue";
import Icon from "./components/Icon.vue";
import { icons } from "./lib/icons";
import { modules } from "./modules";
import { auth } from "./lib/auth";
import { usePullToRefresh } from "./lib/pullToRefresh";

const activeId = ref(modules[0].id);
const mobileNavOpen = ref(false);
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
  mobileNavOpen.value = false;
}
</script>

<template>
  <Login v-if="!auth.isAuthenticated.value" />
  <div
    v-else
    class="flex h-screen flex-col bg-white font-sans text-slate-900 antialiased lg:flex-row"
  >
    <header
      class="flex items-center gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 lg:hidden"
    >
      <button
        class="flex h-8 w-8 items-center justify-center rounded-md text-slate-600 hover:bg-slate-200/60"
        aria-label="Abrir menú"
        @click="mobileNavOpen = true"
      >
        <Icon :path="icons.menu" :size="18" />
      </button>
      <div class="flex items-center gap-2.5">
        <img
          src="/homeos-logo.png"
          alt="HomeOS"
          class="h-6 w-6 rounded-md object-cover"
        />
        <span class="text-sm font-semibold text-slate-800">HomeOS</span>
      </div>
    </header>

    <Sidebar
      :modules="visibleModules"
      :active-id="activeId"
      :open="mobileNavOpen"
      @select="selectModule"
      @close="mobileNavOpen = false"
    />
    <div class="relative flex min-h-0 min-w-0 flex-1 flex-col">
      <div
        v-if="pull.active.value"
        class="pointer-events-none absolute inset-x-0 top-0 z-20 flex justify-center"
        :style="{ transform: `translateY(${pull.distance.value}px)` }"
      >
        <div
          class="mt-2 flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-500 shadow-sm"
          :class="pull.refreshing.value ? 'animate-spin' : ''"
          :style="
            pull.refreshing.value
              ? undefined
              : {
                  transform: `rotate(${pull.progress.value * 270}deg)`,
                  opacity: pull.progress.value,
                }
          "
        >
          <Icon :path="icons.refresh" :size="16" />
        </div>
      </div>
      <main
        ref="scroller"
        class="flex-1 overflow-auto overscroll-y-contain bg-slate-50/50 px-4 py-4 sm:px-6 sm:py-6"
      >
        <component :is="activeModule.component" :key="refreshKey" />
      </main>
    </div>
    <Toasts />
  </div>
</template>
