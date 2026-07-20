<script setup lang="ts">
import { computed } from "vue";
import EntryRow from "./EntryRow.vue";
import { formatMoney } from "../../lib/format";
import type { UserColor } from "../../lib/colors";
import type { FinanceEntry, FinancePersonSummary, UserRef } from "../../types";

const props = defineProps<{
  ownerId: number;
  entries: FinanceEntry[];
  summary: FinancePersonSummary | null;
  users: UserRef[];
  colors: Record<string, UserColor>;
  busyEntryId: number | null;
}>();

defineEmits<{
  confirm: [id: number];
  edit: [id: number];
  delete: [id: number];
}>();

const mine = computed(() =>
  props.entries.filter((e) => e.owner_id === props.ownerId),
);
const income = computed(() => mine.value.filter((e) => e.kind === "income"));
const expense = computed(() => mine.value.filter((e) => e.kind === "expense"));

const balance = computed(() => props.summary?.balance ?? 0);

const userName = (id: number) =>
  props.users.find((u) => u.id === id)?.name ?? `User_${id}`
</script>

<template>
  <div class="space-y-4">
    <div class="grid grid-cols-3 gap-2">
      <div class="rounded-lg border border-slate-200 px-3 py-2">
        <p class="text-xs text-slate-500">Ingresos</p>
        <p class="mt-1 text-sm font-semibold text-emerald-700">
          {{ formatMoney(summary?.income ?? 0) }}
        </p>
      </div>
      <div class="rounded-lg border border-slate-200 px-3 py-2">
        <p class="text-xs text-slate-500">Egresos</p>
        <p class="mt-1 text-sm font-semibold text-rose-700">
          {{ formatMoney(summary?.expense ?? 0) }}
        </p>
      </div>
      <div class="rounded-lg bg-slate-50 px-3 py-2">
        <p class="text-xs text-slate-500">Lo que queda</p>
        <p
          class="mt-1 text-sm font-semibold"
          :class="balance < 0 ? 'text-rose-700' : 'text-slate-900'"
        >
          {{ formatMoney(balance) }}
        </p>
      </div>
    </div>

    <p
      v-if="mine.length === 0"
      class="py-10 text-center text-sm text-slate-400"
    >
      Todavía no hay movimientos de esta persona.
    </p>

    <template v-else>
      <section v-if="income.length > 0">
        <h4 class="text-xs font-medium uppercase tracking-wide text-slate-400">
          Ingresos
        </h4>
        <ul class="divide-y divide-slate-100 pt-1">
          <EntryRow
            v-for="entry in income"
            :key="entry.id"
            :entry="entry"
            :owner-name="userName(entry.owner_id)"
            :color="colors[entry.owner_id]?.solid ?? null"
            :busy="busyEntryId === entry.id"
            hide-owner-tag
            @confirm="$emit('confirm', entry.id)"
            @edit="$emit('edit', entry.id)"
            @delete="$emit('delete', entry.id)"
          />
        </ul>
      </section>

      <section v-if="expense.length > 0">
        <h4 class="text-xs font-medium uppercase tracking-wide text-slate-400">
          Egresos
        </h4>
        <ul class="divide-y divide-slate-100 pt-1">
          <EntryRow
            v-for="entry in expense"
            :key="entry.id"
            :entry="entry"
            :owner-name="userName(entry.owner_id)"
            :color="colors[entry.owner_id]?.solid ?? null"
            :busy="busyEntryId === entry.id"
            hide-owner-tag
            @confirm="$emit('confirm', entry.id)"
            @edit="$emit('edit', entry.id)"
            @delete="$emit('delete', entry.id)"
          />
        </ul>
      </section>
    </template>
  </div>
</template>
