<script setup lang="ts">
import { computed } from "vue";
import Button from "../../components/Button.vue";
import Icon from "../../components/Icon.vue";
import { COLORS, type UserColor } from "../../lib/colors";
import { icons } from "../../lib/icons";
import { formatMoney } from "../../lib/money";
import type { FinanceEntry, FinancePeriodSummary, UserRef } from "../../types";
import EntryList from "./EntryList.vue";

const props = defineProps<{
  entries: FinanceEntry[];
  summary: FinancePeriodSummary;
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

const shared = computed(() =>
  props.entries.filter((e) => e.scope === "shared"),
);
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-wrap gap-2">
      <div
        v-for="user in users"
        :key="user.id"
        class="flex-1 rounded-lg border border-slate-200 px-3 py-2"
        :class="colors[user.id]?.bg ?? 'bg-slate-50'"
      >
        <div class="flex items-center gap-1.5 text-xs text-slate-500">
          <span
            class="h-2.5 w-2.5 shrink-0 rounded-full"
            :style="{ backgroundColor: colors[user.id]?.solid ?? COLORS.neutral.solid }"
          />
          {{ user.name }}
        </div>
        <p class="mt-1 text-sm font-semibold text-slate-900 tabular-nums">
          {{ formatMoney(summary.contributions[user.id] ?? 0) }}
        </p>
      </div>
      <div class="flex-1 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
        <p class="text-xs text-slate-500">Total compartido</p>
        <p class="mt-1 text-sm font-semibold text-slate-900 tabular-nums">
          {{ formatMoney(summary.shared_total) }}
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
        v-if="shared.length === 0"
        class="py-10 text-center text-sm text-slate-500"
      >
        {{
          closed
            ? "No hubo cuentas compartidas en este mes."
            : "Todavía no hay cuentas compartidas en este mes."
        }}
      </p>

      <EntryList
        v-else
        title="Egresos"
        :entries="shared"
        :users="users"
        :colors="colors"
        :busy-entry-id="busyEntryId"
        hide-shared-tag
        @confirm="$emit('confirm', $event)"
        @edit="$emit('edit', $event)"
        @delete="$emit('delete', $event)"
      />

      <div
        v-if="closed"
        class="pointer-events-none absolute -inset-2 z-1 rounded-xl bg-slate-100/25"
        aria-hidden="true"
      />
    </div>
  </div>
</template>
