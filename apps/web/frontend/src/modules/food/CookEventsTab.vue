<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { foodApi } from "../../api/food";
import WidgetCard from "../../components/WidgetCard.vue";
import type { CookEvent, Recipe } from "../../types";

const props = defineProps<{ recipes: Recipe[] }>();

const cookEvents = ref<CookEvent[]>([]);
const expanded = ref<Set<number>>(new Set());

type SortColumn = "recipe" | "portions" | "macros" | "chef" | "date";
const sortBy = ref<SortColumn>("date");
const sortDesc = ref(true);

function recipeName(id: number): string {
  return props.recipes.find((r) => r.id === id)?.name ?? `#${id}`;
}

function fmtDate(iso: string): string {
  const [y, m, d] = iso.split("-");
  return `${d}/${m}/${y}`;
}

function macroSummary(macros: { per_portion: Record<string, number> }) {
  const p = macros.per_portion;
  const parts: string[] = [];
  if (p.kcal) parts.push(`${Math.round(p.kcal)}kcal`);
  if (p.protein_g) parts.push(`${Math.round(p.protein_g)}P`);
  if (p.carbs_g) parts.push(`${Math.round(p.carbs_g)}C`);
  if (p.fat_g) parts.push(`${Math.round(p.fat_g)}G`);
  return parts.join(" · ") || "—";
}

function toggleExpand(id: number) {
  const next = new Set(expanded.value);
  if (next.has(id)) {
    next.delete(id);
  } else {
    next.add(id);
  }
  expanded.value = next;
}

function setSort(col: SortColumn) {
  if (sortBy.value === col) {
    sortDesc.value = !sortDesc.value;
  } else {
    sortBy.value = col;
    sortDesc.value = false;
  }
}

const sortedCookEvents = computed(() => {
  const dir = sortDesc.value ? -1 : 1;
  return [...cookEvents.value].sort((a, b) => {
    let cmp = 0;
    switch (sortBy.value) {
      case "recipe":
        cmp = recipeName(a.recipe_id).localeCompare(
          recipeName(b.recipe_id),
          undefined,
          { sensitivity: "base" },
        );
        break;
      case "portions":
        cmp = a.portions - b.portions;
        break;
      case "macros": {
        const ka = a.macros?.per_portion.kcal ?? 0;
        const kb = b.macros?.per_portion.kcal ?? 0;
        cmp = ka - kb;
        break;
      }
      case "chef":
        cmp = (a.user_name ?? "").localeCompare(
          b.user_name ?? "",
          undefined,
          { sensitivity: "base" },
        );
        break;
      case "date":
        cmp = a.cooked_at.localeCompare(b.cooked_at);
        break;
    }
    return cmp * dir;
  });
});

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
      <div class="flex items-center gap-2 px-4 py-3 sm:hidden">
        <select
          v-model="sortBy"
          class="rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs text-slate-700 outline-none focus:border-slate-400"
        >
          <option value="recipe">Receta</option>
          <option value="portions">Porciones</option>
          <option value="macros">Macros por porción</option>
          <option value="chef">Chef</option>
          <option value="date">Fecha de cocción</option>
        </select>
        <button
          type="button"
          class="inline-flex items-center rounded-lg border border-slate-200 px-2 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-50"
          @click="sortDesc = !sortDesc"
        >
          {{ sortDesc ? "↓ DESC" : "↑ ASC" }}
        </button>
      </div>

      <div
        class="hidden grid-cols-[1fr_5rem_11rem_8rem_8rem] items-center gap-2 border-b border-slate-100 bg-slate-50/60 px-4 py-2 text-xs font-semibold tracking-wider text-slate-400 sm:grid"
      >
        <button type="button" class="flex items-center gap-1 text-left" @click="setSort('recipe')">
          Receta
          <span v-if="sortBy === 'recipe'">{{ sortDesc ? "↓" : "↑" }}</span>
        </button>
        <button type="button" class="flex items-center gap-1" @click="setSort('portions')">
          Porciones
          <span v-if="sortBy === 'portions'">{{ sortDesc ? "↓" : "↑" }}</span>
        </button>
        <button type="button" class="flex items-center gap-1" @click="setSort('macros')">
          Macros por porción
          <span v-if="sortBy === 'macros'">{{ sortDesc ? "↓" : "↑" }}</span>
        </button>
        <button type="button" class="flex items-center gap-1" @click="setSort('chef')">
          Chef
          <span v-if="sortBy === 'chef'">{{ sortDesc ? "↓" : "↑" }}</span>
        </button>
        <button type="button" class="flex items-center gap-1" @click="setSort('date')">
          Fecha de cocción
          <span v-if="sortBy === 'date'">{{ sortDesc ? "↓" : "↑" }}</span>
        </button>
      </div>

      <ul class="divide-y divide-slate-100">
        <li
          v-for="ev in sortedCookEvents"
          :key="ev.id"
        >
          <button
            type="button"
            class="group flex w-full cursor-pointer items-start gap-3 px-4 py-3 text-left transition-colors sm:grid sm:grid-cols-[1fr_5rem_11rem_8rem_8rem] sm:items-center sm:gap-2 sm:py-2.5 hover:bg-slate-50"
            @click="toggleExpand(ev.id)"
          >
            <div class="min-w-0 flex-1 sm:contents">
              <span class="block truncate text-[13px] font-medium text-slate-800">
                {{ recipeName(ev.recipe_id) }}
              </span>
              <span class="mt-1 block text-xs tabular-nums text-slate-500 sm:mt-0">
                {{ ev.portions }} porc.
              </span>
              <span class="mt-1 block truncate whitespace-nowrap text-xs tabular-nums text-slate-500 sm:mt-0">
                {{ ev.macros ? macroSummary(ev.macros) : "—" }}
              </span>
              <span class="mt-1 block truncate text-xs text-slate-500 sm:mt-0">
                {{ ev.user_name }}
              </span>
              <span class="mt-1 block text-xs text-slate-500 sm:mt-0">
                {{ fmtDate(ev.cooked_at) }}
              </span>
            </div>
          </button>

          <div
            v-if="expanded.has(ev.id) && ev.ingredients.length"
            class="border-t border-slate-50 bg-slate-50/40 px-4 py-2"
          >
            <p class="mb-1 text-xs font-medium text-slate-500">Ingredientes utilizados:</p>
            <ul>
              <li
                v-for="ing in ev.ingredients"
                :key="ing.id"
              >
                <span class="text-xs font-medium text-slate-700">· {{ ing.ingredient_name }}:&nbsp;</span>
                <span class="text-xs tabular-nums text-slate-400">
                  {{ ing.quantity }}{{ ing.unit }}
                  <template v-if="ing.macros">
                    <span class="text-xs text-slate-400"> | </span>
                    {{ Math.round(ing.macros.kcal ?? 0) }}kcal
                    · {{ Math.round(ing.macros.protein_g ?? 0) }}P
                    · {{ Math.round(ing.macros.carbs_g ?? 0) }}C
                    · {{ Math.round(ing.macros.fat_g ?? 0) }}G
                  </template>
                </span>
              </li>
            </ul>
          </div>
        </li>
      </ul>
    </div>
  </WidgetCard>
</template>
