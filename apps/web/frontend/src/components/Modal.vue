<script setup lang="ts">
import { onMounted, onUnmounted } from "vue";
import Icon from "./Icon.vue";
import { icons } from "../lib/icons";

const props = withDefaults(
  defineProps<{ title: string; size?: "md" | "lg" }>(),
  { size: "md" },
);
const emit = defineEmits<{ close: [] }>();

let savedBodyOverflow = "";
let savedHtmlOverflow = "";

function onKey(e: KeyboardEvent) {
  if (e.key === "Escape") emit("close");
}

onMounted(() => {
  savedBodyOverflow = document.body.style.overflow;
  savedHtmlOverflow = document.documentElement.style.overflow;
  document.body.style.overflow = "hidden";
  document.documentElement.style.overflow = "hidden";
  document.addEventListener("keydown", onKey);
});
onUnmounted(() => {
  document.body.style.overflow = savedBodyOverflow;
  document.documentElement.style.overflow = savedHtmlOverflow;
  document.removeEventListener("keydown", onKey);
});
</script>

<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 z-50 flex items-center justify-center overscroll-contain bg-slate-900/40 p-4"
    >
      <div
        class="flex max-h-[calc(100vh-2rem)] w-full flex-col overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xl"
        :class="size === 'lg' ? 'max-w-lg' : 'max-w-md'"
      >
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
        <div class="min-h-0 overflow-y-auto px-5 py-4">
          <slot />
        </div>
        <footer
          v-if="$slots.footer"
          class="flex justify-end gap-2 border-t border-slate-100 px-5 py-3.5"
        >
          <slot name="footer" />
        </footer>
      </div>
    </div>
  </Teleport>
</template>
