<script setup lang="ts">
import Icon from "../../components/Icon.vue";
import Button from "../../components/Button.vue";
import { icons } from "../../lib/icons";
import { formatMoney } from "../../lib/format";
import type { FinanceEntry } from "../../types";

defineProps<{
  entry: FinanceEntry;
  ownerName: string;
  color: string | null;
  busy: boolean;
}>();

defineEmits<{ confirm: []; reject: [] }>();
</script>

<template>
  <li class="flex items-center gap-3 py-2.5">
    <span
      class="rounded-md px-1.5 py-0.5 text-xs font-medium"
      :class="
        entry.kind === 'income'
          ? 'bg-emerald-50 text-emerald-700'
          : 'bg-rose-50 text-rose-700'
      "
    >
      {{ entry.kind === "income" ? "ingreso" : "gasto" }}
    </span>
    <span class="text-sm text-slate-800">{{ entry.label }}</span>
    <span
      v-if="entry.scope === 'shared'"
      class="rounded-md bg-slate-100 px-1.5 py-0.5 text-xs text-slate-500"
    >
      compartido
    </span>
    <span class="flex items-center gap-1.5 text-xs text-slate-400">
      <span
        v-if="color"
        class="h-2.5 w-2.5 shrink-0 rounded-full"
        :style="{ backgroundColor: color }"
      />
      {{ ownerName }}
    </span>
    <span
      v-if="entry.status === 'pending'"
      class="rounded-md bg-amber-50 px-1.5 py-0.5 text-xs font-medium text-amber-700"
    >
      pendiente
    </span>
    <span class="ml-auto text-sm font-medium text-slate-900">
      {{ formatMoney(entry.amount) }}
    </span>
    <div v-if="entry.status === 'pending'" class="flex items-center gap-1">
      <Button
        variant="ghost"
        size="sm"
        icon-only
        :loading="busy"
        @click="$emit('confirm')"
      >
        <Icon :path="icons.check" :size="14" />
      </Button>
      <Button
        variant="ghost"
        size="sm"
        icon-only
        :disabled="busy"
        @click="$emit('reject')"
      >
        <Icon :path="icons.close" :size="14" />
      </Button>
    </div>
  </li>
</template>
