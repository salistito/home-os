<script setup lang="ts">
import { computed } from "vue";
import Button from "../../components/Button.vue";
import Icon from "../../components/Icon.vue";
import { COLORS, type UserColor } from "../../lib/colors";
import { icons } from "../../lib/icons";
import { formatMoney } from "../../lib/money";
import type { FinanceEntry, FinancePeriodSummary, UserRef } from "../../types";
import EntryRow from "./EntryRow.vue";

const props = defineProps<{
  entries: FinanceEntry[];
  summary: FinancePeriodSummary;
  users: UserRef[];
  colors: Record<number, UserColor>;
  busyEntryId: number | null;
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

const userName = (id: number) =>
  props.users.find((u) => u.id === id)?.name ?? `User_${id}`
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-wrap gap-2">
      <div
        v-for="user in users"
        :key="user.id"
        class="flex-1 rounded-lg border border-slate-200 px-3 py-2"
      >
        <div class="flex items-center gap-1.5 text-xs text-slate-500">
          <span
            class="h-2.5 w-2.5 shrink-0 rounded-full"
            :style="{ backgroundColor: colors[user.id]?.solid ?? COLORS.neutral.solid }"
          />
          {{ user.name }}
        </div>
        <p class="mt-1 text-sm font-semibold text-slate-900">
          {{ formatMoney(summary.contributions[user.id] ?? 0) }}
        </p>
      </div>
      <div class="flex-1 rounded-lg bg-slate-50 px-3 py-2">
        <p class="text-xs text-slate-500">Total compartido</p>
        <p class="mt-1 text-sm font-semibold text-slate-900">
          {{ formatMoney(summary.shared_total) }}
        </p>
      </div>
    </div>

    <div class="flex items-center justify-between gap-2">
      <h4 class="text-xs font-semibold uppercase tracking-wider text-slate-400">Movimientos</h4>
      <Button size="sm" @click="$emit('add')">
        <Icon :path="icons.plus" :size="14" />
        Agregar
      </Button>
    </div>

    <p
      v-if="shared.length === 0"
      class="py-10 text-center text-sm text-slate-400"
    >
      Todavía no hay cuentas compartidas en este mes.
    </p>

    <section v-else class="pt-4">
      <h4 class="text-xs font-semibold uppercase tracking-wider text-slate-400">Egresos</h4>
      <ul class="divide-y divide-slate-100 pt-1">
        <EntryRow
          v-for="entry in shared"
          :key="entry.id"
          :entry="entry"
          :owner-name="userName(entry.owner_id)"
          :color="colors[entry.owner_id]?.solid ?? null"
          :busy="busyEntryId === entry.id"
          hide-shared-tag
          @confirm="$emit('confirm', entry.id)"
          @edit="$emit('edit', entry.id)"
          @delete="$emit('delete', entry.id)"
        />
      </ul>
    </section>
  </div>
</template>
