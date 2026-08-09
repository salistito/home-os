<script setup lang="ts">
import { computed, ref, watch } from "vue";
import IconButton from "../../components/IconButton.vue";
import Modal from "../../components/Modal.vue";
import SelectMenu, {
  type SelectOption,
} from "../../components/SelectMenu.vue";
import { color, type Color } from "../../lib/colors";
import { icons } from "../../lib/icons";
import type {
  FinanceEntry,
  FinanceEntryDeletePayload,
  FinanceSharedItem,
  FinanceTag,
  UserRef,
} from "../../types";
import EntryRow from "./EntryRow.vue";

type Row =
  | { mode: "entry"; key: string; entry: FinanceEntry; label: string; amount: number | null; tags: FinanceTag[] }
  | { mode: "item"; key: string; entry: FinanceEntry; label: string; amount: number; tags: FinanceTag[] };

const props = defineProps<{
  title: string;
  entries: FinanceEntry[];
  items?: FinanceSharedItem[];
  users: UserRef[];
  colors: Record<number, Color>;
  busyEntryId: number | null;
  expandEntryId?: number | null;
  hideOwnerTag?: boolean;
  hideSharedTag?: boolean;
  sharedOnly?: boolean;
}>();

const emit = defineEmits<{
  confirm: [id: number];
  edit: [id: number];
  delete: [payload: FinanceEntryDeletePayload];
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

const isEntryMode = computed(() => props.items === undefined);

const rows = computed<Row[]>(() => [
  ...props.entries.map((e) => ({
    mode: "entry" as const,
    key: String(e.id),
    entry: e,
    label: e.label,
    amount: e.amount,
    tags: e.tags,
  })),
  ...(props.items ?? []).map((it) => ({
    mode: "item" as const,
    key: it.key,
    entry: it.entry,
    label: it.label,
    amount: it.amount,
    tags: it.tags,
  })),
]);

const tagOptions = computed<SelectOption[]>(() => {
  const opts: SelectOption[] = [{ value: "all", label: "Todos los tags" }];
  if (!props.hideOwnerTag) {
    const ownerIds = [...new Set(rows.value.map((r) => r.entry.owner_id))];
    for (const id of ownerIds) {
      const name = props.users.find((u) => u.id === id)?.name ?? `User_${id}`;
      opts.push({ value: `user_${id}`, label: name, dot: props.colors[id]?.solid });
    }
  }
  if (isEntryMode.value) {
    const isSharedEntry = (entry: FinanceEntry): boolean =>
      entry.scope === "shared" ||
      entry.details.some((d) => d.scope === "shared");
    const hasShared = props.entries.some(isSharedEntry);
    const hasPersonal = props.entries.some((e) => e.scope === "personal");
    if (hasShared && hasPersonal) {
      opts.push({ value: "shared", label: "Compartido", dot: color('slate').solid });
    }
  }
  if (rows.value.some((r) => r.entry.status === "pending")) {
    opts.push({ value: "pending", label: "Pendientes", dot: color('amber').solid });
  }
  const seen = new Set<number>();
  for (const row of rows.value) {
    const allTags =
      row.mode === "entry"
        ? [...row.entry.tags, ...row.entry.details.flatMap((d) => d.tags)]
        : row.tags;
    for (const t of allTags) {
      if (seen.has(t.id)) continue;
      seen.add(t.id);
      opts.push({ value: `tag_${t.id}`, label: t.name, dot: color(t.color).solid });
    }
  }
  return opts;
});

const matchesTag = (row: Row): boolean => {
  const value = tag.value;
  if (value === "all") return true;
  if (value.startsWith("user_")) return row.entry.owner_id === Number(value.slice(5));
  if (value === "shared") {
    return (
      row.entry.scope === "shared" ||
      row.entry.details.some((d) => d.scope === "shared")
    );
  }
  if (value === "pending") return row.entry.status === "pending";
  if (value.startsWith("tag_")) {
    const tagId = Number(value.slice(4));
    if (row.mode === "item") return row.tags.some((t) => t.id === tagId);
    return (
      row.entry.tags.some((t) => t.id === tagId) ||
      row.entry.details.some((d) => d.tags.some((t) => t.id === tagId))
    );
  }
  return true;
};

const detailAmountFor = (entry: FinanceEntry, tagId: number): number =>
  entry.details
    .filter((d) => d.tags.some((t) => t.id === tagId))
    .reduce((sum, d) => sum + (d.amount || 0), 0);

const displayAmountFor = (row: Row): number | null => {
  if (row.mode === "item") return row.amount;
  const entry = row.entry;
  if (props.sharedOnly || tag.value === "shared") return entry.shared_amount;
  const value = tag.value;
  if (!value.startsWith("tag_")) return entry.amount;
  const tagId = Number(value.slice(4));
  if (entry.tags.some((t) => t.id === tagId)) return entry.amount;
  return detailAmountFor(entry, tagId);
};

const visibleRows = computed(() => {
  const list = rows.value.filter(matchesTag);
  if (sort.value === "name_asc" || sort.value === "name_desc") {
    const factor = sort.value === "name_asc" ? 1 : -1;
    return [...list].sort(
      (a, b) => a.label.localeCompare(b.label, "es", { sensitivity: "base" }) * factor,
    );
  }
  if (sort.value === "amount_asc" || sort.value === "amount_desc") {
    const factor = sort.value === "amount_asc" ? 1 : -1;
    const withAmount = list
      .filter((r) => displayAmountFor(r) !== null)
      .sort((a, b) => ((displayAmountFor(a) ?? 0) - (displayAmountFor(b) ?? 0)) * factor);
    return [...withAmount, ...list.filter((r) => displayAmountFor(r) === null)];
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
function emitDelete(row: Row) {
  emit("delete", {
    id: row.entry.id,
    itemLabel: row.mode === "item" ? row.label : undefined,
  });
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
        v-if="visibleRows.length === 0"
        class="py-6 text-center text-sm text-slate-500"
      >
        Ningún movimiento coincide con el filtro.
      </li>
      <EntryRow
        v-for="row in visibleRows"
        :key="row.key"
        :entry="row.entry"
        :owner-name="
          users.find((u) => u.id === row.entry.owner_id)?.name ?? `User_${row.entry.owner_id}`
        "
        :dot-color="colors[row.entry.owner_id]?.solid ?? null"
        :busy="busyEntryId === row.entry.id"
        :tag-filter="tag"
        :parent-label="row.mode === 'item' ? row.entry.label : undefined"
        :display-label="row.mode === 'item' ? row.label : undefined"
        :display-amount="displayAmountFor(row)"
        :display-tags="row.mode === 'item' ? row.tags : undefined"
        :hide-shared-tag="hideSharedTag"
        :hide-owner-tag="hideOwnerTag"
        :hide-details="row.mode === 'item'"
        :shared-only-details="sharedOnly"
        :expand-entry-id="expandEntryId"
        @confirm="emitConfirm(row.entry.id)"
        @edit="emitEdit(row.entry.id)"
        @delete="emitDelete(row)"
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
