<script setup lang="ts">
import { computed, ref } from "vue";
import ActionBar from "../../components/ActionBar.vue";
import Icon from "../../components/Icon.vue";
import { icons } from "../../lib/icons";
import ExercisesTab from "./ExercisesTab.vue";
import RoutinesTab from "./RoutinesTab.vue";
import WeightTab from "./WeightTab.vue";
import WorkoutEntriesTab from "./WorkoutEntriesTab.vue";

const tabs = [
  { id: "workouts", label: "Entrenamientos" },
  { id: "routines", label: "Rutinas" },
  { id: "exercises", label: "Ejercicios" },
  { id: "weight", label: "Peso" },
];

const primaryActions: Record<string, string> = {
  workouts: "Registrar entrenamiento",
  routines: "Nueva rutina",
  exercises: "Nuevo ejercicio",
  weight: "Registrar peso",
};

const activeTab = ref("workouts");
const activeTabRef = ref<{ openCreate: () => void } | null>(null);
const primaryAction = computed(() => primaryActions[activeTab.value]);

function runPrimaryAction() {
  activeTabRef.value?.openCreate();
}
const loading = ref(false);
</script>

<template>
  <div class="mx-auto max-w-5xl space-y-4">
    <nav
      class="flex gap-5 overflow-x-auto overflow-y-hidden border-b border-slate-200 sm:gap-6"
    >
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
        <WorkoutEntriesTab
          v-if="activeTab === 'workouts'"
          ref="activeTabRef"
          :loading="loading"
        />
        <RoutinesTab
          v-else-if="activeTab === 'routines'"
          ref="activeTabRef"
          :loading="loading"
        />
        <ExercisesTab
          v-else-if="activeTab === 'exercises'"
          ref="activeTabRef"
          :loading="loading"
        />
        <WeightTab
          v-else-if="activeTab === 'weight'"
          ref="activeTabRef"
          :loading="loading"
        />
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
