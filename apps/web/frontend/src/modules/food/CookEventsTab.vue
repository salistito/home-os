<script setup lang="ts">
import { onMounted, ref } from "vue";
import { foodApi } from "../../api/food";
import WidgetCard from "../../components/WidgetCard.vue";
import type { CookEvent, Recipe } from "../../types";

const props = defineProps<{ recipes: Recipe[] }>();

const cookEvents = ref<CookEvent[]>([]);

function recipeName(id: number): string {
  return props.recipes.find((r) => r.id === id)?.name ?? `#${id}`;
}

function fmtDate(iso: string): string {
  const [y, m, d] = iso.split("-");
  return `${d}/${m}/${y}`;
}

onMounted(async () => {
  try {
    cookEvents.value = await foodApi.listCookEvents();
  } catch {
    cookEvents.value = [];
  }
});
</script>

<template>
  <WidgetCard title="Historial de cocciones" :count="cookEvents.length">
    <p
      v-if="!cookEvents.length"
      class="px-4 py-10 text-center text-sm text-slate-500"
    >
      Todavía no hay cocciones registradas.
    </p>

    <div v-else>
      <div
        class="hidden grid-cols-[1fr_4rem_7rem] items-center gap-3 border-b border-slate-100 bg-slate-50/60 px-4 py-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400 sm:grid"
      >
        <span>Receta</span>
        <span class="text-right">Porciones</span>
        <span>Fecha</span>
      </div>
      <ul class="divide-y divide-slate-100">
        <li
          v-for="ev in cookEvents"
          :key="ev.id"
          class="grid grid-cols-[1fr_4rem_7rem] items-center gap-3 px-4 py-2.5 text-sm transition-colors hover:bg-slate-50"
        >
          <span class="truncate text-slate-700">{{ recipeName(ev.recipe_id) }}</span>
          <span class="text-right tabular-nums text-slate-500">{{ ev.portions }}</span>
          <span class="text-xs text-slate-400">{{ fmtDate(ev.cooked_at) }}</span>
        </li>
      </ul>
    </div>
  </WidgetCard>
</template>
