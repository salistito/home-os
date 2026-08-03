<script setup lang="ts">
import { computed, ref } from "vue";
import Icon from "../../components/Icon.vue";
import IconButton from "../../components/IconButton.vue";
import { tagColor } from "../../lib/colors";
import { icons } from "../../lib/icons";
import { formatMoney } from "../../lib/money";
import type { FinanceEntry } from "../../types";

const props = defineProps<{
  entry: FinanceEntry;
  ownerName: string;
  color: string | null;
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

const hasTags = computed(
  () =>
    !props.hideOwnerTag ||
    (props.entry.scope === "shared" && !props.hideSharedTag) ||
    props.entry.status === "pending" ||
    props.entry.tags.length > 0,
);
</script>

<template>
  <li class="group py-3 transition-colors hover:bg-slate-50 sm:py-2.5">
    <div class="grid grid-cols-[auto_minmax(0,1fr)_auto_auto] items-center gap-x-3">
      <button
        type="button"
        class="shrink-0 rounded-md p-1 transition-colors"
        :class="
          entry.details.length > 0
            ? 'text-slate-400 hover:bg-slate-100 hover:text-slate-600'
            : 'invisible pointer-events-none'
        "
        :disabled="entry.details.length === 0"
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

      <span class="flex min-w-0 items-center">
        <span
          class="min-w-0 truncate text-[13px] font-medium"
          :class="entry.status === 'pending' ? 'text-slate-400' : 'text-slate-800'"
        >{{ entry.label }}</span>
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
        v-if="hasTags"
        class="col-start-2 col-end-4 flex flex-wrap items-center gap-1.5 pt-1"
      >
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
          class="shrink-0 rounded-md border border-slate-200 px-2 py-0.5 text-xs text-slate-600"
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
          class="shrink-0 rounded-md px-2 py-0.5 text-xs"
          :class="[tagColor(tag.color).bg, tagColor(tag.color).text]"
        >
          {{ tag.name }}
        </span>
      </div>

      <div v-if="expanded" class="col-start-2 col-end-4 pt-2">
        <ul class="space-y-1.5">
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
