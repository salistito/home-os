<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import Icon from "../../components/Icon.vue";
import WidgetCard from "../../components/WidgetCard.vue";
import { icons } from "../../lib/icons";
import { colorsByUser } from "../../lib/colors";
import { tasksApi } from "../../api/tasks";
import type { TodayUser } from "../../types";

const users = ref<TodayUser[]>([]);
const error = ref<string | null>(null);
const loading = ref(true);

const colors = computed(() => colorsByUser(users.value.map((u) => u.id)));

onMounted(async () => {
  try {
    users.value = (await tasksApi.today()).users;
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Error inesperado";
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <WidgetCard title="Hoy">
    <p v-if="loading" class="px-4 py-6 text-sm text-slate-400">Cargando…</p>

    <p v-else-if="error" class="px-4 py-6 text-sm text-red-600">{{ error }}</p>

    <div v-else class="divide-y divide-slate-100">
      <div v-for="user in users" :key="user.id" class="px-4 py-3">
        <div class="mb-2 flex items-center gap-2">
          <span
            class="h-2.5 w-2.5 shrink-0 rounded-full"
            :style="{ backgroundColor: colors[user.id].solid }"
          />
          <span class="text-[13px] font-medium text-slate-800">
            {{ user.name }}
          </span>
          <span
            v-if="user.tasks.length"
            class="ml-auto inline-flex items-center gap-1 text-xs font-semibold text-amber-700"
          >
            <Icon :path="icons.star" :size="12" />
            {{ user.total }}
          </span>
        </div>

        <ul v-if="user.tasks.length" class="space-y-1 pl-[18px]">
          <li
            v-for="task in user.tasks"
            :key="task.task_id"
            class="flex items-center gap-2 text-[13px] text-slate-600"
          >
            <span class="h-1 w-1 rounded-full bg-slate-300" />
            <span class="truncate">{{ task.name }}</span>
            <span class="text-xs text-slate-400">· {{ task.points }}</span>
          </li>
        </ul>
        <p v-else class="pl-[18px] text-xs text-slate-400">Sin tareas asignadas.</p>
      </div>
    </div>
  </WidgetCard>
</template>
