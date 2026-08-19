<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { foodApi } from "../../api/food";
import FilterModal from "../../components/FilterModal.vue";
import Icon from "../../components/Icon.vue";
import IconButton from "../../components/IconButton.vue";
import Modal from "../../components/Modal.vue";
import SearchBar from "../../components/SearchBar.vue";
import WidgetCard from "../../components/WidgetCard.vue";
import { colorsByUser } from "../../lib/colors";
import { addDays, daysOfWeek, getToday, isoWeek, startOfWeek } from "../../lib/date";
import { cookEventPortions, recipeName } from "../../lib/food";
import { formatWeekdayShort, formatYearMonth } from "../../lib/format";
import { icons } from "../../lib/icons";
import type { CookEvent, Ingredient, IngredientStock, Recipe, UserRef } from "../../types";
import CookEventDetailModal from "./CookEventDetailModal.vue";
import CookEventsTabSkeleton from "./CookEventsTabSkeleton.vue";
import CookRecipeModal from "./CookRecipeModal.vue";
import MonthPicker from "./MonthPicker.vue";

const props = defineProps<{
  recipes: Recipe[];
  ingredients: Ingredient[];
  stock: IngredientStock[];
  users: UserRef[];
  loading: boolean;
}>();
const emit = defineEmits<{ reload: [] }>();

const cookEvents = ref<CookEvent[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);

const searchQuery = ref("");
const recipeFilter = ref("all");
const chefFilter = ref("all");
const showFilters = ref(false);

const recipeSearch = ref("");
const recipePickerOpen = ref(false);

const cookRecipe = ref<Recipe | null>(null);
const detailEvent = ref<CookEvent | null>(null);

const today = getToday();
const selectedDate = ref(today);
const cutoffDate = addDays(today, -7);
const calendarOpen = ref(false);

const weekStart = computed(() => startOfWeek(selectedDate.value));
const weekDays = computed(() => daysOfWeek(selectedDate.value));
const weekLabel = computed(() =>
  `${formatYearMonth(weekStart.value.slice(0, 7))} - Semana ${isoWeek(weekStart.value)}`,
);

const dayRecipes = computed(() => {
  const seen = new Set<number>();
  const out: { id: number; name: string }[] = [];
  for (const ev of cookEvents.value) {
    if (ev.cooked_at.slice(0, 10) !== selectedDate.value) continue;
    if (!seen.has(ev.recipe_id)) {
      seen.add(ev.recipe_id);
      out.push({ id: ev.recipe_id, name: recipeName(ev.recipe_id, props.recipes) });
    }
  }
  return out.sort((a, b) => a.name.localeCompare(b.name, undefined, { sensitivity: "base" }));
});

const dayChefs = computed(() => {
  const seen = new Set<number>();
  const out: { id: number; name: string }[] = [];
  for (const ev of cookEvents.value) {
    if (ev.cooked_at.slice(0, 10) !== selectedDate.value) continue;
    if (!seen.has(ev.user_id)) {
      seen.add(ev.user_id);
      out.push({ id: ev.user_id, name: ev.user_name });
    }
  }
  return out.sort((a, b) => a.name.localeCompare(b.name, undefined, { sensitivity: "base" }));
});

const recipeOptions = computed(() => [
  { value: "all", label: "Todas las recetas" },
  ...dayRecipes.value.map((r) => ({ value: String(r.id), label: r.name })),
]);

const chefOptions = computed(() => [
  { value: "all", label: "Todos los chefs" },
  ...dayChefs.value.map((c) => ({ value: String(c.id), label: c.name })),
]);

const filtersActive = computed(() => recipeFilter.value !== "all" || chefFilter.value !== "all");

const colors = computed(() => {
  const ids = [...new Set(cookEvents.value.map((ev) => ev.user_id))];
  return colorsByUser(ids.map((id) => ({ id })));
});

const dayCounts = computed(() => {
  const counts = new Map<string, number>();
  for (const ev of cookEvents.value) {
    const day = ev.cooked_at.slice(0, 10);
    counts.set(day, (counts.get(day) ?? 0) + 1);
  }
  return counts;
});

const dayHasAvailable = computed(() => {
  const available = new Map<string, boolean>();
  for (const ev of cookEvents.value) {
    const day = ev.cooked_at.slice(0, 10);
    if (!available.has(day)) available.set(day, false);
    if (ev.cooked_at.slice(0, 10) >= cutoffDate && (ev.remaining_portions ?? 0) > 0) {
      available.set(day, true);
    }
  }
  return available;
});

const selectedDayEvents = computed(() =>
  cookEvents.value.filter((ev) => {
    if (ev.cooked_at.slice(0, 10) !== selectedDate.value) return false;
    if (recipeFilter.value !== "all" && String(ev.recipe_id) !== recipeFilter.value) return false;
    if (chefFilter.value !== "all" && String(ev.user_id) !== chefFilter.value) return false;
    return true;
  }),
);

const filteredEvents = computed(() => {
  const term = searchQuery.value.trim().toLowerCase();
  if (!term) return selectedDayEvents.value;
  return selectedDayEvents.value.filter((ev) =>
    recipeName(ev.recipe_id, props.recipes).toLowerCase().includes(term),
  );
});

const searchableRecipes = computed(() => {
  const term = recipeSearch.value.trim().toLowerCase();
  const list = [...props.recipes].sort((a, b) => a.name.localeCompare(b.name));
  return term ? list.filter((r) => r.name.toLowerCase().includes(term)) : list;
});

function openFilters() {
  showFilters.value = true;
}

function applyFilter({ key, value }: { key: string; value: string }) {
  if (key === "recipe") recipeFilter.value = value;
  if (key === "chef") chefFilter.value = value;
}

function selectDate(date: string) {
  selectedDate.value = date;
}

function dayNumber(iso: string): number {
  return Number(iso.slice(8, 10));
}

function shiftWeek(delta: number) {
  selectedDate.value = addDays(weekStart.value, delta * 7);
}

function onCalendarSelect(date: string) {
  calendarOpen.value = false;
  selectedDate.value = date;
}

function goToday() {
  selectedDate.value = today;
}

function openCreate() {
  recipeSearch.value = "";
  recipePickerOpen.value = true;
}

function pickRecipe(recipe: Recipe) {
  recipePickerOpen.value = false;
  cookRecipe.value = recipe;
}

function backToPicker() {
  cookRecipe.value = null;
  recipePickerOpen.value = true;
}

function macroSummary(macros: { per_portion: Record<string, number> }): string {
  const p = macros.per_portion;
  const parts: string[] = [];
  if (p.kcal != null) parts.push(`${Math.round(p.kcal)}kcal`);
  if (p.protein_g != null) parts.push(`${Math.round(p.protein_g)}P`);
  if (p.carbs_g != null) parts.push(`${Math.round(p.carbs_g)}C`);
  if (p.fat_g != null) parts.push(`${Math.round(p.fat_g)}G`);
  if (p.fiber_g != null) parts.push(`${Math.round(p.fiber_g)}F`);
  return parts.join(" · ") || "—";
}

async function loadWeek() {
  loading.value = true;
  error.value = null;
  try {
    cookEvents.value = await foodApi.listCookEvents({
      from_date: weekStart.value,
      to_date: weekDays.value[6],
    });
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Error inesperado";
    cookEvents.value = [];
  } finally {
    loading.value = false;
  }
}

async function onCookSaved() {
  cookRecipe.value = null;
  emit("reload");
  await loadWeek();
}

defineExpose({ openCreate });

watch(selectedDate, () => {
  recipeFilter.value = "all";
  chefFilter.value = "all";
  searchQuery.value = "";
});
watch(weekStart, loadWeek);
void loadWeek();
</script>

<template>
  <CookEventsTabSkeleton v-if="props.loading || loading" />
  <div v-else class="space-y-4">
    <p v-if="error" class="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-600">
      {{ error }}
    </p>

    <div class="rounded-xl border border-slate-200 bg-white p-3">
      <div class="relative mb-3 flex items-center justify-between gap-2">
        <div class="flex min-w-0 items-center gap-1">
          <IconButton dense :icon="icons.chevronLeft" label="Semana anterior" @click="shiftWeek(-1)" />
          <h3 class="whitespace-nowrap text-sm font-semibold text-slate-900">
            {{ weekLabel }}
          </h3>
          <IconButton dense :icon="icons.chevronRight" label="Semana siguiente" @click="shiftWeek(1)" />
        </div>
        <div class="flex shrink-0 items-center gap-1">
          <button
            v-if="selectedDate !== today"
            type="button"
            class="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-50"
            @click="goToday"
          >
            Hoy
          </button>
          <IconButton
            :icon="icons.calendar"
            label="Cambiar fecha"
            @click="calendarOpen = !calendarOpen"
          />
        </div>
        <div v-if="calendarOpen" class="fixed inset-0 z-10" @click="calendarOpen = false" />
        <div v-if="calendarOpen" class="absolute left-1/2 top-full z-20 mt-2 -translate-x-1/2">
          <MonthPicker
            :selected="selectedDate"
            @select="onCalendarSelect"
            @close="calendarOpen = false"
          />
        </div>
      </div>

      <div class="grid grid-cols-7 gap-1.5">
        <button
          v-for="day in weekDays"
          :key="day"
          type="button"
          class="flex flex-col items-center gap-1 rounded-lg px-1 py-2 text-xs transition-colors hover:bg-slate-50"
          :class="day === selectedDate ? 'bg-slate-100' : ''"
          @click="selectDate(day)"
        >
          <span
            class="text-[11px]"
            :class="day === selectedDate ? 'font-semibold text-slate-900' : 'text-slate-400'"
          >
            {{ formatWeekdayShort(day) }}
          </span>
          <span
            class="flex h-8 w-8 items-center justify-center rounded-full text-sm transition-colors"
            :class="[
              day === selectedDate
                ? 'bg-slate-900 font-semibold text-white'
                : day === today
                  ? 'font-semibold text-amber-600 ring-2 ring-amber-400'
                  : 'text-slate-700',
            ]"
          >
            {{ dayNumber(day) }}
          </span>
          <span class="h-3.5 text-[9px] leading-3">
            <span
              v-if="(dayCounts.get(day) ?? 0) > 0"
              class="inline-flex h-3.5 min-w-3.5 items-center justify-center rounded-full px-1 font-semibold tabular-nums"
              :class="dayHasAvailable.get(day)
                ? 'bg-amber-400 text-amber-900'
                : 'bg-slate-300 text-slate-600'"
            >
              {{ dayCounts.get(day) }}
            </span>
          </span>
        </button>
      </div>
    </div>

    <WidgetCard title="Registro de cocciones" :count="filteredEvents.length">
    <template #actions>
      <button
        type="button"
        class="hidden items-center gap-1 rounded-lg bg-slate-900 px-2.5 py-1.5 text-xs font-medium text-white transition-colors hover:bg-slate-700 lg:inline-flex"
        @click="openCreate"
      >
        <Icon :path="icons.plus" :size="14" />
        Registrar cocción
      </button>
    </template>

    <template #filter>
      <SearchBar v-model="searchQuery" placeholder="Buscar cocción…" />
      <span class="relative">
        <IconButton :icon="icons.filter" label="Filtros" @click="openFilters" />
        <span
          v-if="filtersActive"
          class="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-amber-500"
        />
      </span>
    </template>

      <p
        v-if="!loading && !cookEvents.length"
        class="px-4 py-10 text-center text-sm text-slate-500"
      >
        No hay cocciones registradas este día.
      </p>

      <p
        v-else-if="!loading && !filteredEvents.length"
        class="px-4 py-10 text-center text-sm text-slate-500"
      >
        {{ searchQuery
          ? "No hay cocciones que coincidan con la búsqueda."
          : filtersActive
            ? "No hay cocciones que coincidan con los filtros."
            : "No hay cocciones registradas este día." }}
      </p>

      <div v-else>
        <ul class="divide-y divide-slate-100">
          <li
            v-for="ev in filteredEvents"
            :key="ev.id"
          >
            <button
              type="button"
              class="group flex w-full cursor-pointer items-start gap-3 px-4 py-3 text-left transition-colors hover:bg-slate-50"
              @click="detailEvent = ev"
            >
              <div class="min-w-0 flex-1">
                <span class="block truncate text-[13px] font-medium text-slate-800">
                  {{ recipeName(ev.recipe_id, props.recipes) }}
                </span>

                <p class="mt-1.5 text-xs text-slate-600">
                  {{ ev.macros ? macroSummary(ev.macros) : "—" }}
                </p>

                <div class="mt-1.5 flex flex-wrap items-center gap-2">
                  <span
                    class="inline-flex items-center gap-1 rounded-md bg-slate-50 px-2 py-0.5 text-xs tabular-nums text-slate-700 ring-1 ring-slate-200"
                  >
                    <Icon :path="icons.pot" :size="12" class="shrink-0 text-slate-400" />
                    {{ ev.portions }} porc.
                  </span>
                  <span
                    class="inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium ring-1"
                    :class="[colors[ev.user_id].bg, colors[ev.user_id].text, colors[ev.user_id].ring]"
                  >
                    <Icon :path="icons.users" :size="12" />
                    {{ ev.user_name }}
                  </span>
                </div>
              </div>

              <span class="flex shrink-0 items-center gap-1.5">
                <span
                  class="inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium"
                  :class="cookEventPortions(ev, cutoffDate).classes"
                >
                  <Icon
                    v-if="cookEventPortions(ev, cutoffDate).icon"
                    :path="cookEventPortions(ev, cutoffDate).icon!"
                    :size="12"
                    class="shrink-0"
                  />
                  {{ cookEventPortions(ev, cutoffDate).label }}
                </span>
                <Icon
                  :path="icons.chevronRight"
                  :size="14"
                  class="text-slate-300 transition-colors group-hover:text-slate-500"
                />
              </span>
            </button>
          </li>
        </ul>
      </div>
    </WidgetCard>

    <CookEventDetailModal
      v-if="detailEvent"
      :event="detailEvent"
      :name="recipeName(detailEvent.recipe_id, props.recipes)"
      :chef-color="colors[detailEvent.user_id]"
      :cutoff-date="cutoffDate"
      @close="detailEvent = null"
    />

    <FilterModal
      :show="showFilters"
      title="Filtros de cocciones"
      :columns="[]"
      current-sort-by=""
      current-sort-order="asc"
      :show-sort="false"
      :filters="[
        { key: 'recipe', label: 'Receta', options: recipeOptions },
        { key: 'chef', label: 'Chef', options: chefOptions },
      ]"
      :current-filters="{ recipe: recipeFilter, chef: chefFilter }"
      @update:show="showFilters = $event"
      @apply:filter="applyFilter"
    />

    <Modal v-if="recipePickerOpen" title="¿Qué cocinaste?" @close="recipePickerOpen = false">
      <input
        v-model="recipeSearch"
        type="text"
        placeholder="Buscar receta…"
        class="h-11 w-full rounded-lg border border-slate-200 px-3 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
      />
      <p v-if="!searchableRecipes.length" class="py-8 text-center text-sm text-slate-500">
        {{ recipes.length ? "Ninguna receta coincide con la búsqueda." : "Todavía no hay recetas registradas." }}
      </p>
      <ul v-else class="mt-2 max-h-72 divide-y divide-slate-100 overflow-auto">
        <li v-for="recipe in searchableRecipes" :key="recipe.id">
          <button
            type="button"
            class="flex h-12 w-full items-center gap-2 px-1 text-left text-sm text-slate-800 transition-colors active:bg-slate-50"
            @click="pickRecipe(recipe)"
          >
            <span class="min-w-0 flex-1 truncate">{{ recipe.name }}</span>
            <Icon :path="icons.chevronRight" :size="14" class="shrink-0 text-slate-300" />
          </button>
        </li>
      </ul>
    </Modal>

    <CookRecipeModal
      v-if="cookRecipe"
      :recipe="cookRecipe"
      :ingredients="ingredients"
      :stock="stock"
      :users="users"
      show-back
      @reload="emit('reload')"
      @saved="onCookSaved"
      @back="backToPicker"
      @close="cookRecipe = null"
    />
  </div>
</template>
