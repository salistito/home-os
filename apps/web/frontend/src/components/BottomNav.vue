<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from "vue";
import Icon from "./Icon.vue";
import { auth } from "../lib/auth";
import { icons } from "../lib/icons";
import type { ModuleDef } from "../modules";

const PRIMARY_COUNT = 3;

const props = defineProps<{
  modules: ModuleDef[];
  activeId: string;
}>();

const emit = defineEmits<{ select: [id: string] }>();

const sheetOpen = ref(false);

const primary = computed(() => props.modules.slice(0, PRIMARY_COUNT));
const activeIsPrimary = computed(() =>
  primary.value.some((m) => m.id === props.activeId),
);
const activeModule = computed(() => props.modules.find((m) => m.id === props.activeId));

let savedOverflow = "";

watch(sheetOpen, (open) => {
  if (open) {
    savedOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
  } else {
    document.body.style.overflow = savedOverflow;
  }
});

onUnmounted(() => {
  document.body.style.overflow = savedOverflow;
});

function select(id: string) {
  sheetOpen.value = false;
  emit("select", id);
}
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-from-class="opacity-0"
      leave-to-class="opacity-0"
      enter-active-class="transition-opacity"
      leave-active-class="transition-opacity"
    >
      <div
        v-if="sheetOpen"
        class="fixed inset-0 z-40 bg-slate-900/40 lg:hidden"
        @click="sheetOpen = false"
      />
    </Transition>

    <Transition
      enter-from-class="translate-y-full"
      leave-to-class="translate-y-full"
      enter-active-class="transition-transform duration-200"
      leave-active-class="transition-transform duration-200"
    >
      <div
        v-if="sheetOpen"
        class="fixed inset-x-0 bottom-0 z-50 rounded-t-2xl bg-white pb-[max(1rem,env(safe-area-inset-bottom))] shadow-2xl lg:hidden"
      >
        <div class="flex items-center justify-between px-5 pb-2 pt-4">
          <h2 class="text-sm font-semibold text-slate-900">Módulos</h2>
          <button
            type="button"
            class="flex h-9 w-9 items-center justify-center rounded-lg text-slate-500 transition-colors active:bg-slate-100"
            aria-label="Cerrar"
            @click="sheetOpen = false"
          >
            <Icon :path="icons.close" :size="18" />
          </button>
        </div>

        <div class="grid grid-cols-3 gap-3 px-5 pt-2">
          <button
            v-for="m in modules"
            :key="m.id"
            type="button"
            class="flex aspect-square flex-col items-center justify-center gap-2 rounded-2xl border transition active:scale-95"
            :class="
              m.id === activeId
                ? 'border-transparent bg-slate-200/70 text-slate-900'
                : 'border-slate-200 text-slate-600 active:bg-slate-200/40'
            "
            @click="select(m.id)"
          >
            <Icon
              :path="m.icon"
              :size="26"
              :class="m.id === activeId ? 'text-slate-700' : 'text-slate-400'"
            />
            <span class="px-1 text-center text-xs font-medium leading-tight">
              {{ m.label }}
            </span>
          </button>
        </div>

        <div class="px-5 pt-4">
          <button
            type="button"
            class="flex h-12 w-full items-center justify-center gap-2 rounded-lg text-sm font-medium text-slate-600 transition-colors active:bg-slate-200/40"
            @click="auth.logout()"
          >
            <Icon :path="icons.logout" :size="16" class="text-slate-400" />
            Cerrar sesión
          </button>
        </div>
      </div>
    </Transition>
  </Teleport>

  <nav
    class="shrink-0 bg-slate-50 pb-[env(safe-area-inset-bottom)] lg:hidden"
  >
    <div class="flex items-stretch px-1 pb-1 pt-1.5">
      <button
        v-for="m in primary"
        :key="m.id"
        type="button"
        class="flex flex-1 flex-col items-center justify-center gap-1 rounded-lg py-2 text-[11px] font-medium transition active:scale-95"
        :class="
          m.id === activeId
            ? 'bg-slate-200/70 text-slate-900'
            : 'text-slate-600 active:bg-slate-200/40'
        "
        @click="emit('select', m.id)"
      >
        <Icon
          :path="m.icon"
          :size="22"
          :class="m.id === activeId ? 'text-slate-700' : 'text-slate-400'"
        />
        <span class="leading-none">{{ m.label }}</span>
      </button>

      <button
        type="button"
        class="flex flex-1 flex-col items-center justify-center gap-1 rounded-lg py-2 text-[11px] font-medium transition active:scale-95"
        :class="
          !activeIsPrimary
            ? 'bg-slate-200/70 text-slate-900'
            : 'text-slate-600 active:bg-slate-200/40'
        "
        aria-label="Ver todos los módulos"
        @click="sheetOpen = true"
      >
        <Icon
          :path="!activeIsPrimary && activeModule ? activeModule.icon : icons.moreHorizontal"
          :size="22"
          :class="!activeIsPrimary ? 'text-slate-700' : 'text-slate-400'"
        />
        <span class="leading-none">
          {{ !activeIsPrimary && activeModule ? activeModule.label : "Más" }}
        </span>
      </button>
    </div>
  </nav>
</template>
