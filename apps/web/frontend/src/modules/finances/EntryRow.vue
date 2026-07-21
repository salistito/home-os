<script setup lang="ts">
import IconButton from "../../components/IconButton.vue";
import { icons } from "../../lib/icons";
import { formatMoney } from "../../lib/format";
import { tagColor } from "../../lib/colors";
import type { FinanceEntry } from "../../types";

defineProps<{
  entry: FinanceEntry;
  ownerName: string;
  color: string | null;
  busy: boolean;
  hideSharedTag?: boolean;
  hideOwnerTag?: boolean;
}>();

defineEmits<{ confirm: []; edit: []; delete: [] }>();
</script>

<template>
  <li class="group py-2.5">
    <div class="flex items-center gap-3">
      <span
        class="w-16 rounded-md px-1.5 py-0.5 text-center text-xs font-medium"
        :class="
          entry.kind === 'income'
            ? 'bg-emerald-50 text-emerald-700'
            : 'bg-rose-50 text-rose-700'
        "
      >
        {{ entry.kind === "income" ? "ingreso" : "gasto" }}
      </span>
      <span
        class="text-sm"
        :class="entry.status === 'pending' ? 'text-slate-400' : 'text-slate-800'"
      >{{ entry.label }}</span>
      <span
        v-if="!hideOwnerTag"
        class="flex items-center gap-1.5 text-xs text-slate-400"
      >
        <span
          v-if="color"
          class="h-2.5 w-2.5 shrink-0 rounded-full"
          :style="{ backgroundColor: color }"
        />
        {{ ownerName }}
      </span>
      <span
        v-if="entry.scope === 'shared' && !hideSharedTag"
        class="rounded-md bg-slate-100 px-1.5 py-0.5 text-xs text-slate-500"
      >
        compartido
      </span>
      <span
        v-for="tag in entry.tags"
        :key="tag.id"
        class="rounded-md px-1.5 py-0.5 text-xs"
        :class="[tagColor(tag.color).bg, tagColor(tag.color).text]"
      >
        {{ tag.name }}
      </span>
      <span
        v-if="entry.status === 'pending'"
        class="rounded-md bg-amber-50 px-1.5 py-0.5 text-xs font-medium text-amber-700"
      >
        pendiente
      </span>
      <span
        class="ml-auto text-sm font-medium"
        :class="entry.status === 'pending' ? 'text-slate-400' : 'text-slate-900'"
      >
        {{ entry.amount === null ? "—" : formatMoney(entry.amount) }}
      </span>
      <span
        class="flex w-20 shrink-0 justify-end gap-0.5 transition-opacity sm:opacity-0 sm:group-hover:opacity-100"
      >
        <IconButton
          v-if="entry.status === 'pending'"
          :icon="icons.check"
          :label="entry.amount === null ? 'Agrega un monto para confirmar' : 'Confirmar'"
          :disabled="busy || entry.amount === null"
          @click="$emit('confirm')"
        />
        <IconButton
          :icon="icons.pencil"
          label="Editar"
          :disabled="busy"
          @click="$emit('edit')"
        />
        <IconButton
          :icon="icons.trash"
          label="Eliminar"
          variant="danger"
          :disabled="busy"
          @click="$emit('delete')"
        />
      </span>
    </div>

    <ul
      v-if="entry.details.length > 0"
      class="mt-1 space-y-0.5 border-l border-slate-100 pl-4 ml-16"
    >
      <li
        v-for="d in entry.details"
        :key="d.id"
        class="flex items-center gap-3 text-xs text-slate-500"
      >
        <span>{{ d.label }}</span>
        <span class="ml-auto">{{ formatMoney(d.amount) }}</span>
        <span class="w-20 shrink-0" aria-hidden="true" />
      </li>
    </ul>
  </li>
</template>
