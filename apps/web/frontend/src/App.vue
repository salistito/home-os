<script setup lang="ts">
import { computed, ref } from "vue";
import Sidebar from "./components/Sidebar.vue";
import Login from "./components/Login.vue";
import Toasts from "./components/Toasts.vue";
import Icon from "./components/Icon.vue";
import { icons } from "./lib/icons";
import { modules } from "./modules";
import { auth } from "./lib/auth";

const activeId = ref(modules[0].id);
const mobileNavOpen = ref(false);
const activeModule = computed(
  () => modules.find((m) => m.id === activeId.value) ?? modules[0],
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
        <div
          class="flex h-6 w-6 items-center justify-center rounded-md bg-slate-900 text-[11px] font-bold text-white"
        >
          H
        </div>
        <span class="text-sm font-semibold text-slate-800">HomeOS</span>
      </div>
    </header>

    <Sidebar
      :modules="modules"
      :active-id="activeId"
      :open="mobileNavOpen"
      @select="selectModule"
      @close="mobileNavOpen = false"
    />
    <main
      class="flex-1 overflow-auto bg-slate-50/50 px-4 py-4 sm:px-6 sm:py-6"
    >
      <component :is="activeModule.component" />
    </main>
    <Toasts />
  </div>
</template>
