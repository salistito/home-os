<script setup lang="ts">
import { computed, ref } from "vue";
import Icon from "../../components/Icon.vue";
import IconButton from "../../components/IconButton.vue";
import { color } from "../../lib/colors";
import { icons } from "../../lib/icons";
import { formatMoney } from "../../lib/money";
import type { FinanceEntry } from "../../types";

const props = defineProps<{
  entry: FinanceEntry;
  ownerName: string;
  dotColor: string | null;
  busy: boolean;
  hideSharedTag?: boolean;
  hideOwnerTag?: boolean;
}>();

defineEmits<{ confirm: []; edit: []; delete: [] }>();

const expanded = ref(false);

const amountClass = computed(() => {
  if (props.entry.status === "pending") return "text-slate-400";
  return props.entry.kind === "income" ? "text-emerald-700" : "text-rose-700";
});
</script>

<template>
  <li class="group py-2.5 transition-colors hover:bg-slate-50 sm:py-2">
    <div class="grid grid-cols-[minmax(0,1fr)_auto_auto] items-center gap-x-3">
      <span class="flex min-w-0 items-center gap-1">
        <span
          class="min-w-0 truncate text-[13px] font-medium"
          :class="entry.status === 'pending' ? 'text-slate-400' : 'text-slate-800'"
        >{{ entry.label }}</span>
        <button
          v-if="entry.details.length > 0"
          type="button"
          class="shrink-0 rounded-md p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600"
          :aria-label="expanded ? 'Ocultar desglose' : 'Ver desglose'"
          :aria-expanded="expanded"
          @click="expanded = !expanded"
        >
          <Icon
            :path="expanded ? icons.chevronUp : icons.chevronDown"
            :size="16"
            class="transition-transform"
          />
        </button>
      </span>

      <span
        class="text-sm font-semibold tabular-nums"
        :class="amountClass"
      >
        {{ entry.amount === null ? "—" : formatMoney(entry.amount) }}
      </span>

      <span
        class="flex w-[72px] shrink-0 items-center justify-end gap-0.5 transition-opacity sm:opacity-0 sm:group-hover:opacity-100"
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

      <div
        class="col-start-1 col-end-3 flex min-h-5 flex-wrap items-center gap-1.5 pt-1"
      >
        <span
          v-if="!hideOwnerTag"
          class="flex items-center gap-1.5 text-xs text-slate-400"
        >
          <span
            v-if="dotColor"
            class="h-2.5 w-2.5 shrink-0 rounded-full"
            :style="{ backgroundColor: dotColor }"
          />
          {{ ownerName }}
        </span>
        <span
          v-if="entry.scope === 'shared' && !hideSharedTag"
          class="shrink-0 rounded-md px-2 py-0.5 text-xs font-medium ring-1"
          :class="[
            color('slate').bg,
            color('slate').text,
            color('slate').ring,
          ]"
        >
          Compartido
        </span>
        <span
          v-if="entry.status === 'pending'"
          class="shrink-0 rounded-md bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700 ring-1 ring-amber-100"
        >
          Pendiente
        </span>
        <span
          v-for="tag in entry.tags"
          :key="tag.id"
          class="shrink-0 rounded-md px-2 py-0.5 text-xs font-medium ring-1"
          :class="[
            color(tag.color).bg,
            color(tag.color).text,
            color(tag.color).ring,
          ]"
        >
          {{ tag.name }}
        </span>
      </div>

      <div v-if="expanded" class="col-start-1 col-end-3 pt-2 pl-2">
        <ul class="space-y-1.5 border-l border-slate-200 pl-2">
          <li
            v-for="d in entry.details"
            :key="d.id"
            class="flex items-center gap-3 text-xs text-slate-500"
          >
            <span class="min-w-0 flex-1 truncate">{{ d.label }}</span>
            <span class="shrink-0 tabular-nums">{{ formatMoney(d.amount) }}</span>
          </li>
        </ul>
      </div>
    </div>
  </li>
</template>
