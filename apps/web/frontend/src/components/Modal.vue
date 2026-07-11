<script setup lang="ts">
import { onMounted, onUnmounted } from "vue";
import Icon from "./Icon.vue";
import { icons } from "../lib/icons";

const props = defineProps<{ title: string }>();
const emit = defineEmits<{ close: [] }>();

function onKey(e: KeyboardEvent) {
  if (e.key === "Escape") emit("close");
}

onMounted(() => document.addEventListener("keydown", onKey));
onUnmounted(() => document.removeEventListener("keydown", onKey));
</script>

<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4"
      @click.self="emit('close')"
    >
      <div class="w-full max-w-md rounded-xl border border-slate-200 bg-white shadow-xl">
        <header
          class="flex items-center justify-between border-b border-slate-100 px-5 py-3.5"
        >
          <h3 class="text-sm font-semibold text-slate-900">{{ props.title }}</h3>
          <button
            type="button"
            class="rounded-md p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600"
            aria-label="Cerrar"
            @click="emit('close')"
          >
            <Icon :path="icons.close" :size="16" />
          </button>
        </header>
        <div class="px-5 py-4">
          <slot />
        </div>
      </div>
    </div>
  </Teleport>
</template>
