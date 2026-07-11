<script setup lang="ts">
import { computed, ref } from "vue";
import Sidebar from "./components/Sidebar.vue";
import { modules } from "./modules";

const activeId = ref(modules[0].id);
const activeModule = computed(
  () => modules.find((m) => m.id === activeId.value) ?? modules[0],
);
</script>

<template>
  <div class="flex h-screen bg-white font-sans text-slate-900 antialiased">
    <Sidebar
      :modules="modules"
      :active-id="activeId"
      @select="activeId = $event"
    />
    <main class="flex-1 overflow-auto bg-slate-50/50 px-6 py-6">
      <component :is="activeModule.component" />
    </main>
  </div>
</template>
