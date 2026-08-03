<script setup lang="ts">
import { computed, ref, watch } from "vue";
import SelectMenu, {
  type SelectOption,
} from "../../components/SelectMenu.vue";
import { COLORS, type UserColor } from "../../lib/colors";
import type { FinanceEntry, UserRef } from "../../types";
import EntryRow from "./EntryRow.vue";

const props = defineProps<{
  title: string;
  entries: FinanceEntry[];
  users: UserRef[];
  colors: Record<number, UserColor>;
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

const sortOptions: SelectOption[] = [
  { value: "default", label: "Por defecto" },
  { value: "name_asc", label: "Nombre A-Z" },
  { value: "name_desc", label: "Nombre Z-A" },
  { value: "amount_asc", label: "Monto menor a mayor" },
  { value: "amount_desc", label: "Monto mayor a menor" },
];

const tagSolid = (color: string): string =>
  (COLORS as Record<string, { solid: string }>)[color.toLowerCase()]?.solid ??
  COLORS.neutral.solid;

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
    opts.push({ value: "shared", label: "Compartido", dot: COLORS.slate.solid });
  }
  if (props.entries.some((e) => e.status === "pending")) {
    opts.push({ value: "pending", label: "Pendientes", dot: COLORS.amber.solid });
  }
  const seen = new Set<number>();
  for (const entry of props.entries) {
    for (const t of entry.tags) {
      if (seen.has(t.id)) continue;
      seen.add(t.id);
      opts.push({ value: `tag_${t.id}`, label: t.name, dot: tagSolid(t.color) });
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
  if (value.startsWith("tag_")) return entry.tags.some((t) => t.id === Number(value.slice(4)));
  return true;
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
      .filter((e) => e.amount !== null)
      .sort((a, b) => ((a.amount ?? 0) - (b.amount ?? 0)) * factor);
    return [...withAmount, ...list.filter((e) => e.amount === null)];
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
</script>

<template>
  <section class="pt-4">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <h4 class="text-xs font-semibold uppercase tracking-wider text-slate-400">
        {{ title }}
      </h4>
      <div class="flex flex-wrap items-center gap-2">
        <div class="w-56">
          <SelectMenu v-model="sort" :options="sortOptions" placeholder="Orden" />
        </div>
        <div class="w-44">
          <SelectMenu v-model="tag" :options="tagOptions" placeholder="Tag" />
        </div>
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
        :color="colors[entry.owner_id]?.solid ?? null"
        :busy="busyEntryId === entry.id"
        :hide-owner-tag="hideOwnerTag"
        :hide-shared-tag="hideSharedTag"
        @confirm="emitConfirm(entry.id)"
        @edit="emitEdit(entry.id)"
        @delete="emitDelete(entry.id)"
      />
    </ul>
  </section>
</template>
