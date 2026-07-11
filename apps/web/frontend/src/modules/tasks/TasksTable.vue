<script setup lang="ts">
import { onMounted, ref } from "vue";
import Icon from "../../components/Icon.vue";
import WidgetCard from "../../components/WidgetCard.vue";
import { icons } from "../../lib/icons";
import { formatDate } from "../../lib/format";
import { tasksApi } from "../../api/tasks";
import type { Task } from "../../types";

const tasks = ref<Task[]>([]);
const error = ref<string | null>(null);
const loading = ref(true);

onMounted(async () => {
  try {
    tasks.value = await tasksApi.list();
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Error inesperado";
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <WidgetCard title="Tareas" :count="!loading && !error ? tasks.length : undefined">
    <p v-if="loading" class="px-4 py-6 text-sm text-slate-400">
      Cargando tareas…
    </p>

    <p v-else-if="error" class="px-4 py-6 text-sm text-red-600">{{ error }}</p>

    <p
      v-else-if="tasks.length === 0"
      class="px-4 py-10 text-center text-sm text-slate-500"
    >
      Todavía no hay tareas. Crea la primera para empezar a repartir.
    </p>

    <div v-else>
      <div
        class="grid grid-cols-[1fr_5rem_7rem_6rem] items-center gap-3 border-b border-slate-100 bg-slate-50/60 px-4 py-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400"
      >
        <span>Tarea</span>
        <span>Puntos</span>
        <span>Frecuencia</span>
        <span>Próxima</span>
      </div>

      <ul class="divide-y divide-slate-100">
        <li
          v-for="task in tasks"
          :key="task.id"
          class="grid grid-cols-[1fr_5rem_7rem_6rem] items-center gap-3 px-4 py-2.5 transition-colors hover:bg-slate-50"
        >
          <span class="truncate text-[13px] font-medium text-slate-800">
            {{ task.name }}
          </span>

          <span>
            <span
              class="inline-flex items-center gap-1 rounded-md bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700 ring-1 ring-amber-100"
            >
              <Icon :path="icons.star" :size="12" />
              {{ task.points }}
            </span>
          </span>

          <span>
            <span
              v-if="task.frequency_days"
              class="inline-flex items-center gap-1 rounded-md border border-slate-200 px-2 py-0.5 text-xs text-slate-600"
            >
              <Icon :path="icons.repeat" :size="12" class="text-slate-400" />
              cada {{ task.frequency_days }}d
            </span>
            <span v-else class="block text-center text-xs text-slate-300">—</span>
          </span>

          <span
            v-if="task.next_due_date"
            class="inline-flex items-center gap-1 text-xs text-slate-400"
          >
            <Icon :path="icons.calendar" :size="12" />
            {{ formatDate(task.next_due_date) }}
          </span>
          <span v-else class="block text-center text-xs text-slate-300">—</span>
        </li>
      </ul>
    </div>
  </WidgetCard>
</template>
