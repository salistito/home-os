<script setup lang="ts">
import { ref, watch } from "vue";
import Modal from "./Modal.vue";
import SelectMenu, { type SelectOption } from "./SelectMenu.vue";

export interface FilterField {
  key: string;
  label: string;
  options: SelectOption[];
}

const props = withDefaults(
  defineProps<{
    show: boolean;
    title?: string;
    columns: SelectOption[];
    currentSortBy: string;
    currentSortOrder: string;
    showSort?: boolean;
    filters?: FilterField[];
    currentFilters?: Record<string, string>;
  }>(),
  { title: "Filtros", showSort: true, filters: () => [], currentFilters: () => ({}) },
);

const emit = defineEmits<{
  "update:show": [value: boolean];
  "apply:sort": [value: { sortBy: string; sortOrder: string }];
  "apply:filter": [value: { key: string; value: string }];
}>();

const sortByDraft = ref(props.currentSortBy);
const sortOrderDraft = ref(props.currentSortOrder);
const filterDrafts = ref<Record<string, string>>({});

watch(
  () => props.show,
  (visible) => {
    if (visible) {
      sortByDraft.value = props.currentSortBy;
      sortOrderDraft.value = props.currentSortOrder;
      const drafts: Record<string, string> = {};
      for (const f of props.filters) {
        drafts[f.key] = props.currentFilters[f.key] ?? f.options[0]?.value ?? "all";
      }
      filterDrafts.value = drafts;
    }
  },
);

function apply() {
  emit("apply:sort", { sortBy: sortByDraft.value, sortOrder: sortOrderDraft.value });
  for (const key of Object.keys(filterDrafts.value)) {
    emit("apply:filter", { key, value: filterDrafts.value[key] });
  }
  emit("update:show", false);
}

function cancel() {
  emit("update:show", false);
}
</script>

<template>
  <Modal v-if="show" :title="title" @close="cancel">
    <div class="space-y-4">
      <div v-if="showSort">
        <label class="mb-1 block text-xs font-medium text-slate-500">Ordenar por</label>
        <div class="flex items-center gap-2">
          <SelectMenu
            v-model="sortByDraft"
            :options="columns"
            menu-position="static"
            class="min-w-0 flex-1"
          />
          <button
            type="button"
            class="inline-flex shrink-0 items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-50"
            @click="sortOrderDraft = sortOrderDraft === 'asc' ? 'desc' : 'asc'"
          >
            {{ sortOrderDraft === 'asc' ? "↑ Ascendente" : "↓ Descendente" }}
          </button>
        </div>
      </div>

      <div v-for="filter in filters" :key="filter.key">
        <label class="mb-1 block text-xs font-medium text-slate-500">{{ filter.label }}</label>
        <SelectMenu
          v-model="filterDrafts[filter.key]"
          :options="filter.options"
          menu-position="static"
        />
      </div>
    </div>

    <template #footer>
      <button
        type="button"
        class="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100"
        @click="cancel"
      >
        Cancelar
      </button>
      <button
        type="button"
        class="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-700"
        @click="apply"
      >
        Confirmar
      </button>
    </template>
  </Modal>
</template>
