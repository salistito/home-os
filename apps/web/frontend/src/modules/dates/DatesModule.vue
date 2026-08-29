<script setup lang="ts">
import { computed, ref } from "vue";
import ActionBar from "../../components/ActionBar.vue";
import Icon from "../../components/Icon.vue";
import { icons } from "../../lib/icons";
import CouplesTab from "./CouplesTab.vue";
import EventsTab from "./EventsTab.vue";

const tabs = [
  { id: "events", label: "Citas" },
  { id: "couples", label: "Parejas" },
];

const primaryActions: Record<string, string> = {
  events: "Nueva cita",
  couples: "Nueva pareja",
};

const activeTab = ref("events");
const activeTabRef = ref<{ openCreate: () => void } | null>(null);
const primaryAction = computed(() => primaryActions[activeTab.value]);
const loading = ref(false);

function runPrimaryAction() {
  activeTabRef.value?.openCreate();
}
</script>

<template>
  <div class="mx-auto max-w-5xl space-y-4">
    <nav class="flex gap-5 overflow-x-auto overflow-y-hidden border-b border-slate-200 sm:gap-6">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="-mb-px flex shrink-0 items-center gap-1.5 border-b-2 py-2.5 text-sm transition-colors sm:pb-2 sm:pt-0"
        :class="
          activeTab === tab.id
            ? 'border-slate-900 font-medium text-slate-900'
            : 'border-transparent text-slate-400 hover:text-slate-600'
        "
        @click="activeTab = tab.id"
      >
        {{ tab.label }}
      </button>
    </nav>

    <Transition
      mode="out-in"
      enter-from-class="opacity-0"
      leave-to-class="opacity-0"
      enter-active-class="transition-opacity duration-150"
      leave-active-class="transition-opacity duration-75"
    >
      <div :key="activeTab">
        <EventsTab v-if="activeTab === 'events'" ref="activeTabRef" :loading="loading" />
        <CouplesTab v-else ref="activeTabRef" :loading="loading" />
      </div>
    </Transition>

    <ActionBar>
      <Transition
        appear
        enter-from-class="translate-y-3 opacity-0"
        enter-active-class="transition duration-300 ease-out"
      >
        <button
          v-if="!loading && primaryAction"
          type="button"
          class="flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-slate-900 text-sm font-semibold text-white shadow-sm transition active:scale-[0.98] active:bg-slate-700"
          @click="runPrimaryAction"
        >
          <Icon :path="icons.plus" :size="18" />
          <Transition
            mode="out-in"
            enter-from-class="opacity-0"
            leave-to-class="opacity-0"
            enter-active-class="transition-opacity duration-100"
            leave-active-class="transition-opacity duration-75"
          >
            <span :key="primaryAction">{{ primaryAction }}</span>
          </Transition>
        </button>
      </Transition>
    </ActionBar>
  </div>
</template>