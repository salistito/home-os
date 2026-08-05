<script setup lang="ts">
import { computed, reactive, watch } from "vue";
import Button from "../../components/Button.vue";
import Icon from "../../components/Icon.vue";
import SelectMenu, { type SelectOption } from "../../components/SelectMenu.vue";
import { icons } from "../../lib/icons";
import { formatAmountInput, formatMoney } from "../../lib/money";
import type {
  FinanceDetailMode,
  FinanceEntryDetailInput,
  FinanceEntryScope,
} from "../../types";
import TagInput from "./TagInput.vue";

type DetailRow = FinanceEntryDetailInput & { uid: number };

const props = defineProps<{
  modelValue: FinanceEntryDetailInput[];
  detailMode: FinanceDetailMode;
  entryScope: FinanceEntryScope;
  entryAmount: number;
  tagSuggestions?: string[];
}>();
const emit = defineEmits<{
  "update:modelValue": [value: FinanceEntryDetailInput[]];
  "update:detailMode": [value: FinanceDetailMode];
}>();

let uid = 0;
const nextUid = () => ++uid;

const rows = reactive<DetailRow[]>(
  props.modelValue.map((d) => ({
    uid: nextUid(),
    scope: d.scope ?? null,
    label: d.label,
    amount: d.amount,
    tags: d.tags ? [...d.tags] : [],
  })),
);

watch(
  rows,
  () =>
    emit(
      "update:modelValue",
      rows.map((r) => ({
        scope: r.scope ?? null,
        label: r.label,
        amount: r.amount,
        tags: [...(r.tags ?? [])],
      })),
    ),
  { deep: true },
);

watch(
  () => props.detailMode,
  (mode) => {
    if (mode !== "none" && rows.length === 0) {
      addRow();
    }
  },
  { immediate: true },
);

watch(
  () => props.entryScope,
  (scope) => {
    if (scope === "mixed") {
      for (const row of rows) {
        if (row.scope === null) {
          row.scope = "personal";
        }
      }
    }
  },
);

const modeOptions: SelectOption[] = [
  { value: "none", label: "Sin desglose" },
  { value: "top_down", label: "Monto fijo con desglose" },
  { value: "bottom_up", label: "Desglose que determina el monto" },
];

const total = computed(() => rows.reduce((sum, r) => sum + (r.amount || 0), 0));
const diff = computed(() => props.entryAmount - total.value);

function addRow() {
  rows.push({ uid: nextUid(), scope: props.entryScope === "mixed" ? "personal" : null, label: "", amount: 0, tags: [] });
}
function removeRow(row: DetailRow) {
  rows.splice(rows.indexOf(row), 1);
}

function effectiveScope(row: DetailRow): FinanceEntryScope {
  return row.scope ?? props.entryScope;
}

function toggleShared(row: DetailRow) {
  row.scope = effectiveScope(row) === "shared" ? "personal" : "shared";
}

function setAmount(row: DetailRow, raw: string) {
  const digits = raw.replace(/\D/g, "");
  row.amount = digits ? Number(digits) : 0;
}

function setRowTags(row: DetailRow, tags: string[]) {
  row.tags = tags;
}
</script>

<template>
  <div class="rounded-lg border border-slate-100 bg-slate-50/50 p-3">
    <label class="mb-1 block text-xs font-medium text-slate-500">Desglose (Opcional)</label>
    <SelectMenu
      :model-value="detailMode"
      :options="modeOptions"
      @update:model-value="emit('update:detailMode', $event as FinanceDetailMode)"
    />

    <template v-if="detailMode !== 'none'">
      <ul class="mt-3 space-y-2">
        <li
          v-for="row in rows"
          :key="row.uid"
          class="space-y-2 rounded-lg border border-slate-200 bg-white p-2.5"
        >
          <div class="flex items-center justify-between">
            <span
              class="flex items-center rounded-md bg-slate-100 px-1.5 py-0.5 text-[11px] font-semibold text-slate-500"
            >
              Detalle {{ rows.indexOf(row) + 1 }}
            </span>
            <div class="flex items-center gap-3">
              <label
                v-if="entryScope === 'mixed'"
                class="flex cursor-pointer items-center gap-1.5 text-[11px] font-medium text-slate-500 select-none"
              >
                <input
                  type="checkbox"
                  class="h-3.5 w-3.5 rounded border-slate-300 accent-slate-900"
                  :checked="effectiveScope(row) === 'shared'"
                  @change="toggleShared(row)"
                />
                Compartido
              </label>
              <Button variant="ghost" size="sm" icon-only @click="removeRow(row)">
                <Icon :path="icons.close" :size="14" />
              </Button>
            </div>
          </div>
          <div class="flex items-start gap-2">
            <div class="min-w-0 flex-1">
              <label class="mb-1 block text-xs font-medium text-slate-500">Concepto</label>
              <input
                v-model="row.label"
                type="text"
                placeholder="Supermercado"
                class="w-full rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
              />
            </div>
            <div class="w-28 shrink-0">
              <label class="mb-1 block text-xs font-medium text-slate-500">Monto</label>
              <div class="relative">
                <span
                  class="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-sm text-slate-400"
                >
                  $
                </span>
                <input
                  :value="formatAmountInput(row.amount)"
                  type="text"
                  inputmode="numeric"
                  placeholder="0"
                  class="w-full rounded-lg border border-slate-200 py-1.5 pl-5 pr-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
                  @input="setAmount(row, ($event.target as HTMLInputElement).value)"
                />
              </div>
            </div>
          </div>

          <div>
            <label class="mb-1 block text-xs font-medium text-slate-500">
              Categoría (Opcional)
            </label>
            <TagInput
              :model-value="row.tags ?? []"
              :suggestions="tagSuggestions ?? []"
              :placeholder="`Servicios, Alimentación, etc.`"
              :datalist-id="`finances-detail-tag-suggestions-${row.uid}`"
              @update:model-value="setRowTags(row, $event)"
            />
          </div>
        </li>
      </ul>

      <Button variant="ghost" size="sm" class="mt-3" @click="addRow">
        <Icon :path="icons.plus" :size="12" />
        Agregar detalle
      </Button>

      <div
        class="mt-3 flex items-center justify-between rounded-lg bg-slate-100 px-3 py-2 text-sm"
      >
        <span class="text-slate-500">Suma del desglose</span>
        <span class="font-medium text-slate-900">{{ formatMoney(total) }}</span>
      </div>

      <p
        v-if="detailMode === 'top_down'"
        class="mt-2 text-xs font-medium"
        :class="
          diff === 0
            ? 'text-emerald-600'
            : diff > 0
              ? 'text-amber-600'
              : 'text-rose-600'
        "
      >
        <template v-if="diff === 0">Cuadra con el objetivo.</template>
        <template v-else-if="diff > 0">
          Falta {{ formatMoney(diff) }} para llegar al objetivo.
        </template>
        <template v-else>
          Te pasaste por {{ formatMoney(-diff) }} del objetivo.
        </template>
      </p>
      <p v-else class="mt-2 text-xs text-slate-500">
        El monto del movimiento será la suma del desglose.
      </p>
    </template>
  </div>
</template>
