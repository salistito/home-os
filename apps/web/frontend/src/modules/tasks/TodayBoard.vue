<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import Icon from "../../components/Icon.vue";
import Skeleton from "../../components/Skeleton.vue";
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
    <div v-if="loading" class="divide-y divide-slate-100">
      <div v-for="n in 2" :key="n" class="px-4 py-3">
        <div class="mb-2 flex h-5 items-center gap-2">
          <Skeleton width="0.625rem" height="0.625rem" />
          <Skeleton width="6rem" />
        </div>
        <ul class="space-y-1.5 pl-[18px]">
          <li
            v-for="(w, i) in ['10rem', '8rem']"
            :key="i"
            class="flex items-center gap-2"
          >
            <span class="block h-[14px] w-[14px] shrink-0 animate-pulse rounded bg-slate-200" />
            <Skeleton text :width="w" />
          </li>
        </ul>
      </div>
    </div>

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
        </div>

        <ul v-if="user.tasks.length" class="space-y-1.5 pl-[18px]">
          <li
            v-for="task in user.tasks"
            :key="task.task_id"
            class="flex items-center gap-2 text-[13px]"
          >
            <span
              class="shrink-0"
              :class="task.done ? 'text-emerald-500' : 'text-slate-300'"
            >
              <Icon :path="task.done ? icons.checkSquare : icons.square" :size="14" />
            </span>
            <span
              class="truncate"
              :class="task.done ? 'text-slate-400 line-through' : 'text-slate-700'"
            >
              {{ task.name }}
            </span>
          </li>
        </ul>
        <p v-else class="pl-[18px] text-xs text-slate-400">Sin tareas asignadas.</p>
      </div>
    </div>
  </WidgetCard>
</template>
