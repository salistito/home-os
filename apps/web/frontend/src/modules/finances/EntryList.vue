<script setup lang="ts">
import { computed, ref, watch } from "vue";
import IconButton from "../../components/IconButton.vue";
import Modal from "../../components/Modal.vue";
import SelectMenu, {
  type SelectOption,
} from "../../components/SelectMenu.vue";
import { color, type Color } from "../../lib/colors";
import { icons } from "../../lib/icons";
import type { FinanceEntry, UserRef } from "../../types";
import EntryRow from "./EntryRow.vue";

const props = defineProps<{
  title: string;
  entries: FinanceEntry[];
  users: UserRef[];
  colors: Record<number, Color>;
  busyEntryId: number | null;
  hideOwnerTag?: boolean;
  hideSharedTag?: boolean;
}>();

const emit = defineEmits<{
  confirm: [id: number];
  edit: [id: number];
  delete: [id: number];
}>();

const sort = ref<string>("default");
const tag = ref<string>("all");
const sortDraft = ref<string>("default");
const tagDraft = ref<string>("all");
const filtersActive = computed(() => tag.value !== "all");
const showFilters = ref(false);

const sortOptions: SelectOption[] = [
  { value: "default", label: "Por defecto" },
  { value: "name_asc", label: "Nombre A-Z" },
  { value: "name_desc", label: "Nombre Z-A" },
  { value: "amount_asc", label: "Monto menor a mayor" },
  { value: "amount_desc", label: "Monto mayor a menor" },
];

const tagOptions = computed<SelectOption[]>(() => {
  const opts: SelectOption[] = [{ value: "all", label: "Todos los tags" }];
  if (!props.hideOwnerTag) {
    const ownerIds = [...new Set(props.entries.map((e) => e.owner_id))];
    for (const id of ownerIds) {
      const name = props.users.find((u) => u.id === id)?.name ?? `User_${id}`;
      opts.push({ value: `user_${id}`, label: name, dot: props.colors[id]?.solid });
    }
  }
  const hasShared = props.entries.some((e) => e.scope === "shared");
  const hasPersonal = props.entries.some((e) => e.scope === "personal");
  if (hasShared && hasPersonal) {
    opts.push({ value: "shared", label: "Compartido", dot: color('slate').solid });
  }
  if (props.entries.some((e) => e.status === "pending")) {
    opts.push({ value: "pending", label: "Pendientes", dot: color('amber').solid });
  }
  const seen = new Set<number>();
  for (const entry of props.entries) {
    const allTags = [...entry.tags, ...entry.details.flatMap((d) => d.tags)];
    for (const t of allTags) {
      if (seen.has(t.id)) continue;
      seen.add(t.id);
      opts.push({ value: `tag_${t.id}`, label: t.name, dot: color(t.color).solid });
    }
  }
  return opts;
});

const matchesTag = (entry: FinanceEntry): boolean => {
  const value = tag.value;
  if (value === "all") return true;
  if (value.startsWith("user_")) return entry.owner_id === Number(value.slice(5));
  if (value === "shared") return entry.scope === "shared";
  if (value === "pending") return entry.status === "pending";
  if (value.startsWith("tag_")) {
    const tagId = Number(value.slice(4));
    return (
      entry.tags.some((t) => t.id === tagId) ||
      entry.details.some((d) => d.tags.some((t) => t.id === tagId))
    );
  }
  return true;
};

const detailAmountFor = (entry: FinanceEntry, tagId: number): number =>
  entry.details
    .filter((d) => d.tags.some((t) => t.id === tagId))
    .reduce((sum, d) => sum + (d.amount || 0), 0);

const displayAmountFor = (entry: FinanceEntry): number | null => {
  const value = tag.value;
  if (!value.startsWith("tag_")) return entry.amount;
  const tagId = Number(value.slice(4));
  if (entry.tags.some((t) => t.id === tagId)) return entry.amount;
  return detailAmountFor(entry, tagId);
};

const visibleEntries = computed(() => {
  const list = props.entries.filter(matchesTag);
  if (sort.value === "name_asc" || sort.value === "name_desc") {
    const factor = sort.value === "name_asc" ? 1 : -1;
    return [...list].sort(
      (a, b) => a.label.localeCompare(b.label, "es", { sensitivity: "base" }) * factor,
    );
  }
  if (sort.value === "amount_asc" || sort.value === "amount_desc") {
    const factor = sort.value === "amount_asc" ? 1 : -1;
    const withAmount = list
      .filter((e) => displayAmountFor(e) !== null)
      .sort((a, b) => ((displayAmountFor(a) ?? 0) - (displayAmountFor(b) ?? 0)) * factor);
    return [...withAmount, ...list.filter((e) => displayAmountFor(e) === null)];
  }
  return list;
});

watch(tagOptions, (opts) => {
  if (tag.value !== "all" && !opts.some((o) => o.value === tag.value)) {
    tag.value = "all";
  }
});

function emitConfirm(id: number) {
  emit("confirm", id);
}
function emitEdit(id: number) {
  emit("edit", id);
}
function emitDelete(id: number) {
  emit("delete", id);
}

function openFilters() {
  sortDraft.value = sort.value;
  tagDraft.value = tag.value;
  showFilters.value = true;
}

function applyFilters() {
  sort.value = sortDraft.value;
  tag.value = tagDraft.value;
  showFilters.value = false;
}

function cancelFilters() {
  showFilters.value = false;
}
</script>

<template>
  <section class="pt-4">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <h4 class="text-xs font-semibold uppercase tracking-wider text-slate-400">
        {{ title }}
      </h4>
      <div class="flex flex-wrap items-center gap-2">
        <span class="relative">
          <IconButton
            :icon="icons.filter"
            label="Filtros"
            @click="openFilters"
          />
          <span
            v-if="filtersActive"
            class="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-amber-500"
          />
        </span>
      </div>
    </div>

    <ul class="divide-y divide-slate-100 pt-1">
      <li
        v-if="visibleEntries.length === 0"
        class="py-6 text-center text-sm text-slate-500"
      >
        Ningún movimiento coincide con el filtro.
      </li>
      <EntryRow
        v-for="entry in visibleEntries"
        :key="entry.id"
        :entry="entry"
        :owner-name="
          users.find((u) => u.id === entry.owner_id)?.name ?? `User_${entry.owner_id}`
        "
        :dot-color="colors[entry.owner_id]?.solid ?? null"
        :tag-filter="tag"
        :display-amount="displayAmountFor(entry)"
        :busy="busyEntryId === entry.id"
        :hide-owner-tag="hideOwnerTag"
        :hide-shared-tag="hideSharedTag"
        @confirm="emitConfirm(entry.id)"
        @edit="emitEdit(entry.id)"
        @delete="emitDelete(entry.id)"
      />
    </ul>

    <Modal
      v-if="showFilters"
      title="Filtros"
      size="lg"
      @close="cancelFilters"
    >
      <div class="space-y-4">
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">Orden</label>
          <SelectMenu
            v-model="sortDraft"
            :options="sortOptions"
            placeholder="Orden"
            menu-position="static"
          />
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">Tag</label>
          <SelectMenu
            v-model="tagDraft"
            :options="tagOptions"
            placeholder="Tag"
            menu-position="static"
          />
        </div>
      </div>
      <template #footer>
        <button
          type="button"
          class="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100"
          @click="cancelFilters"
        >
          Cancelar
        </button>
        <button
          type="button"
          class="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-700"
          @click="applyFilters"
        >
          Confirmar
        </button>
      </template>
    </Modal>
  </section>
</template>
