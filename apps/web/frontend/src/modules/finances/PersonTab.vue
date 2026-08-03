<script setup lang="ts">
import { computed } from "vue";
import Button from "../../components/Button.vue";
import Icon from "../../components/Icon.vue";
import type { UserColor } from "../../lib/colors";
import { icons } from "../../lib/icons";
import { formatMoney } from "../../lib/money";
import type { FinanceEntry, FinancePersonSummary, UserRef } from "../../types";
import EntryList from "./EntryList.vue";

const props = defineProps<{
  ownerId: number;
  entries: FinanceEntry[];
  summary: FinancePersonSummary | null;
  users: UserRef[];
  colors: Record<number, UserColor>;
  busyEntryId: number | null;
  closed?: boolean;
}>();

defineEmits<{
  add: [];
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
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-wrap gap-2">
      <div class="flex-1 rounded-lg border border-slate-200 bg-emerald-50 px-3 py-2">
        <p class="text-xs text-slate-500">Ingresos</p>
        <p class="mt-1 text-sm font-semibold text-emerald-700 tabular-nums">
          {{ formatMoney(summary?.income ?? 0) }}
        </p>
      </div>
      <div class="flex-1 rounded-lg border border-slate-200 bg-rose-50 px-3 py-2">
        <p class="text-xs text-slate-500">Egresos</p>
        <p class="mt-1 text-sm font-semibold text-rose-700 tabular-nums">
          {{ formatMoney(summary?.expense ?? 0) }}
        </p>
      </div>
      <div class="flex-1 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
        <p class="text-xs text-slate-500">Lo que queda</p>
        <p
          class="mt-1 text-sm font-semibold tabular-nums"
          :class="balance < 0 ? 'text-rose-700' : 'text-slate-900'"
        >
          {{ formatMoney(balance) }}
        </p>
      </div>
    </div>

    <div class="relative">
      <div class="flex items-center justify-between gap-2">
        <h4 class="text-xs font-semibold uppercase tracking-wider text-slate-400">Movimientos</h4>
        <Button size="sm" @click="$emit('add')">
          <Icon :path="icons.plus" :size="14" />
          Agregar
        </Button>
      </div>

      <p
        v-if="mine.length === 0"
        class="py-10 text-center text-sm text-slate-500"
      >
        {{
          closed
            ? "No hubo movimientos registrados para esta persona."
            : "Todavía no hay movimientos registrados para esta persona."
        }}
      </p>

      <template v-else>
        <EntryList
          v-if="income.length > 0"
          title="Ingresos"
          :entries="income"
          :users="users"
          :colors="colors"
          :busy-entry-id="busyEntryId"
          hide-owner-tag
          @confirm="$emit('confirm', $event)"
          @edit="$emit('edit', $event)"
          @delete="$emit('delete', $event)"
        />

        <EntryList
          v-if="expense.length > 0"
          title="Egresos"
          :entries="expense"
          :users="users"
          :colors="colors"
          :busy-entry-id="busyEntryId"
          hide-owner-tag
          @confirm="$emit('confirm', $event)"
          @edit="$emit('edit', $event)"
          @delete="$emit('delete', $event)"
        />
      </template>

      <div
        v-if="closed"
        class="pointer-events-none absolute -inset-2 z-1 rounded-xl bg-slate-100/25"
        aria-hidden="true"
      />
    </div>
  </div>
</template>
