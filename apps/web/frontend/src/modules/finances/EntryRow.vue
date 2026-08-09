<script setup lang="ts">
import { computed, ref, watch } from "vue";
import Icon from "../../components/Icon.vue";
import IconButton from "../../components/IconButton.vue";
import { color } from "../../lib/colors";
import { icons } from "../../lib/icons";
import { formatMoney } from "../../lib/money";
import type { FinanceEntry, FinanceTag } from "../../types";

const props = defineProps<{
  entry: FinanceEntry;
  ownerName: string;
  dotColor: string | null;
  busy: boolean;
  tagFilter?: string;
  parentLabel?: string;
  displayLabel?: string;
  displayAmount?: number | null;
  displayTags?: FinanceTag[];
  hideSharedTag?: boolean;
  hideOwnerTag?: boolean;
  hideDetails?: boolean;
  sharedOnlyDetails?: boolean;
  expandEntryId?: number | null;
}>();

defineEmits<{ confirm: []; edit: []; delete: [] }>();

const expanded = ref(false);

watch(
  () => props.expandEntryId,
  (id) => {
    if (id != null && id === props.entry.id) expanded.value = true;
  },
  { immediate: true },
);

const hasTags = computed(
  () =>
    !props.hideOwnerTag ||
    (props.entry.scope === "shared" && !props.hideSharedTag) ||
    props.entry.status === "pending" ||
    (props.displayTags ?? props.entry.tags).length > 0,
);

const shownAmount = computed(() =>
  props.displayAmount !== undefined ? props.displayAmount : props.entry.amount,
);

const visibleDetails = computed(() => {
  const tagFilter = props.tagFilter;
  let details = props.entry.details;
  if (props.sharedOnlyDetails || tagFilter === "shared") {
    details = details.filter((d) => (d.scope ?? props.entry.scope) === "shared");
  }
  if (!tagFilter || !tagFilter.startsWith("tag_")) return details;
  const tagId = Number(tagFilter.slice(4));
  if (props.entry.tags.some((t) => t.id === tagId)) return details;
  return details.filter((d) => d.tags.some((t) => t.id === tagId));
});

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
        >{{ displayLabel ?? entry.label }}</span>
        <button
          v-if="!hideDetails && entry.details.length > 0"
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
        {{ shownAmount === null ? "—" : formatMoney(shownAmount) }}
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
        class="col-start-1 col-end-3 flex flex-wrap items-center gap-1.5 pt-1"
        :class="hasTags || !expanded ? 'min-h-5' : ''"
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
          v-if="parentLabel"
          class="flex shrink-0 items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium ring-1"
          :class="[
            color('slate').bg,
            color('slate').text,
            color('slate').ring,
          ]"
        >
          <Icon :path="icons.repeat" :size="12" />
          De {{ parentLabel }}
        </span>
        <span
          v-if="entry.scope === 'shared' && !hideSharedTag"
          class="flex shrink-0 items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium ring-1"
          :class="[
            color('slate').bg,
            color('slate').text,
            color('slate').ring,
          ]"
        >
          <Icon :path="icons.users" :size="12" />
          Compartido
        </span>
        <span
          v-if="entry.status === 'pending'"
          class="shrink-0 rounded-md bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700 ring-1 ring-amber-100"
        >
          Pendiente
        </span>
        <span
          v-for="tag in displayTags ?? entry.tags"
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

      <div v-if="!hideDetails && expanded" class="col-start-1 col-end-3 pt-2 pl-2">
        <ul class="space-y-1.5 border-l border-slate-200 pl-2">
          <li
            v-for="d in visibleDetails"
            :key="d.id"
            class="flex items-center gap-3 text-xs text-slate-500"
          >
            <span class="flex min-w-0 flex-1 items-center gap-1.5">
              <span class="truncate">{{ d.label }}</span>
              <span
                v-if="entry.scope !== 'shared' && d.scope === 'shared'"
                class="flex shrink-0 items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium ring-1"
                :class="[
                  color('slate').bg,
                  color('slate').text,
                  color('slate').ring,
                ]"
              >
                <Icon :path="icons.users" :size="12" />
                Compartido
              </span>
              <span
                v-for="tag in d.tags"
                :key="tag.id"
                class="shrink-0 rounded-md px-1.5 py-0.5 text-[11px] font-medium ring-1"
                :class="[
                  color(tag.color).bg,
                  color(tag.color).text,
                  color(tag.color).ring,
                ]"
              >
                {{ tag.name }}
              </span>
            </span>
            <span class="shrink-0 tabular-nums">{{ formatMoney(d.amount) }}</span>
          </li>
        </ul>
      </div>
    </div>
  </li>
</template>
