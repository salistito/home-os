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
    <main
      class="flex-1 overflow-auto bg-slate-50/50 px-4 py-4 sm:px-6 sm:py-6"
    >
      <component :is="activeModule.component" />
    </main>
    <Toasts />
  </div>
</template>
