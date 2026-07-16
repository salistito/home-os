<script setup lang="ts">
import { computed, reactive, watch } from "vue";
import Icon from "../../components/Icon.vue";
import Button from "../../components/Button.vue";
import SelectMenu from "../../components/SelectMenu.vue";
import type { SelectOption } from "../../components/SelectMenu.vue";
import { icons } from "../../lib/icons";
import { formatMoney } from "../../lib/format";
import type { FinanceDetailMode, FinanceEntryDetailInput } from "../../types";

const props = defineProps<{
  modelValue: FinanceEntryDetailInput[];
  detailMode: FinanceDetailMode;
  entryAmount: number;
}>();
const emit = defineEmits<{
  "update:modelValue": [value: FinanceEntryDetailInput[]];
  "update:detailMode": [value: FinanceDetailMode];
}>();

const rows = reactive<FinanceEntryDetailInput[]>(
  props.modelValue.map((d) => ({ label: d.label, amount: d.amount })),
);

watch(
  rows,
  () =>
    emit(
      "update:modelValue",
      rows.map((r) => ({ label: r.label, amount: r.amount })),
    ),
  { deep: true },
);

const modeOptions: SelectOption[] = [
  { value: "none", label: "Sin desglose" },
  { value: "top_down", label: "Objetivo (arriba → abajo)" },
  { value: "bottom_up", label: "Suma (abajo → arriba)" },
];

const total = computed(() => rows.reduce((sum, r) => sum + (r.amount || 0), 0));
const diff = computed(() => props.entryAmount - total.value);

function addRow() {
  rows.push({ label: "", amount: 0 });
}
function removeRow(index: number) {
  rows.splice(index, 1);
}

function displayAmount(value: number): string {
  return value ? value.toLocaleString("es-CL") : "";
}
function setAmount(index: number, raw: string) {
  const digits = raw.replace(/\D/g, "");
  rows[index].amount = digits ? Number(digits) : 0;
}
</script>

<template>
  <div class="space-y-3">
    <div>
      <label class="mb-1 block text-xs font-medium text-slate-500">Desglose</label>
      <SelectMenu
        :model-value="detailMode"
        :options="modeOptions"
        @update:model-value="emit('update:detailMode', $event as FinanceDetailMode)"
      />
    </div>

    <template v-if="detailMode !== 'none'">
      <ul class="space-y-2">
        <li
          v-for="(row, index) in rows"
          :key="index"
          class="flex items-center gap-2"
        >
          <input
            v-model="row.label"
            type="text"
            placeholder="Concepto"
            class="min-w-0 flex-1 rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
          />
          <div class="relative w-32">
            <span
              class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-sm text-slate-400"
            >
              $
            </span>
            <input
              :value="displayAmount(row.amount)"
              type="text"
              inputmode="numeric"
              placeholder="0"
              class="w-full rounded-lg border border-slate-200 py-1.5 pl-6 pr-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
              @input="setAmount(index, ($event.target as HTMLInputElement).value)"
            />
          </div>
          <Button variant="ghost" size="sm" icon-only @click="removeRow(index)">
            <Icon :path="icons.close" :size="14" />
          </Button>
        </li>
      </ul>

      <Button variant="ghost" size="sm" @click="addRow">
        <Icon :path="icons.plus" :size="12" />
        Agregar línea
      </Button>

      <div
        class="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 text-sm"
      >
        <span class="text-slate-500">Suma del desglose</span>
        <span class="font-medium text-slate-900">{{ formatMoney(total) }}</span>
      </div>

      <p
        v-if="detailMode === 'top_down'"
        class="text-xs font-medium"
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
      <p v-else class="text-xs text-slate-500">
        El monto del movimiento será la suma del desglose.
      </p>
    </template>
  </div>
</template>
