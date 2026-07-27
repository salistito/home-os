<script setup lang="ts">
import { computed, ref } from "vue";
import Icon from "../../components/Icon.vue";
import IconButton from "../../components/IconButton.vue";
import WidgetCard from "../../components/WidgetCard.vue";
import { icons } from "../../lib/icons";
import type { Ingredient, IngredientStock } from "../../types";
import StockEditModal from "./StockEditModal.vue";

const props = defineProps<{
  ingredients: Ingredient[];
  stock: IngredientStock[];
}>();
const emit = defineEmits<{ reload: [] }>();

const editingIng = ref<Ingredient | null>(null);
const editingStock = ref<IngredientStock | null>(null);

interface StockRow {
  ingredient: Ingredient;
  stock: IngredientStock | null;
}

const rows = computed<StockRow[]>(() => {
  const stockMap = new Map(props.stock.map((s) => [s.ingredient_id, s]));
  return props.ingredients.map((ing) => ({
    ingredient: ing,
    stock: stockMap.get(ing.id) ?? null,
  }));
});

const sortedRows = computed(() =>
  [...rows.value].sort((a, b) => {
    const aLow = a.stock ? a.stock.quantity <= a.stock.min_alert_quantity : true;
    const bLow = b.stock ? b.stock.quantity <= b.stock.min_alert_quantity : true;
    if (aLow !== bLow) return aLow ? -1 : 1;
    return a.ingredient.name.localeCompare(b.ingredient.name, undefined, {
      sensitivity: "base",
    });
  }),
);

function isLow(row: StockRow): boolean {
  if (!row.stock) return true;
  return row.stock.quantity <= row.stock.min_alert_quantity;
}

function isExpiringSoon(row: StockRow): boolean {
  if (!row.stock?.expiration_date) return false;
  const exp = new Date(row.stock.expiration_date);
  const now = new Date();
  const diff = (exp.getTime() - now.getTime()) / (1000 * 60 * 60 * 24);
  return diff >= 0 && diff <= 7;
}

function isExpired(row: StockRow): boolean {
  if (!row.stock?.expiration_date) return false;
  return new Date(row.stock.expiration_date) < new Date();
}

function openEdit(row: StockRow) {
  editingIng.value = row.ingredient;
  editingStock.value = row.stock;
}

async function onSaved() {
  editingIng.value = null;
  editingStock.value = null;
  emit("reload");
}
</script>

<template>
  <WidgetCard title="Stock" :count="rows.length">
    <p
      v-if="!rows.length"
      class="px-4 py-10 text-center text-sm text-slate-500"
    >
      No hay ingredientes para mostrar stock.
    </p>

    <div v-else>
      <div
        class="hidden grid-cols-[1fr_6rem_6rem_7rem_6rem_2.25rem] items-center gap-3 border-b border-slate-100 bg-slate-50/60 px-4 py-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400 sm:grid"
      >
        <span>Ingrediente</span>
        <span class="text-right">Cantidad</span>
        <span class="text-right">Mín. alerta</span>
        <span>Vence</span>
        <span>Estado</span>
        <span></span>
      </div>

      <ul class="divide-y divide-slate-100">
        <li
          v-for="row in sortedRows"
          :key="row.ingredient.id"
          class="group flex items-start gap-3 px-4 py-3 transition-colors sm:grid sm:grid-cols-[1fr_6rem_6rem_7rem_6rem_2.25rem] sm:items-center sm:py-2.5"
          :class="
            isExpired(row)
              ? 'bg-red-50/50'
              : isLow(row)
                ? 'bg-amber-50/50'
                : 'hover:bg-slate-50'
          "
        >
          <div class="min-w-0 flex-1 sm:contents">
            <span class="block truncate text-[13px] font-medium text-slate-800">
              {{ row.ingredient.name }}
            </span>
            <span class="mt-1 text-right text-sm tabular-nums text-slate-700 sm:mt-0">
              {{ row.stock?.quantity ?? 0 }} <span class="text-xs text-slate-400">{{ row.ingredient.unit }}</span>
            </span>
            <span class="mt-1 text-right text-xs text-slate-400 sm:mt-0">
              {{ row.stock?.min_alert_quantity ?? 0 }} <span class="text-[10px]">{{ row.ingredient.unit }}</span>
            </span>
            <span class="mt-1 text-xs text-slate-500 sm:mt-0">
              {{ row.stock?.expiration_date ? row.stock.expiration_date.split("-").reverse().join("/") : "—" }}
            </span>
            <span class="mt-1 sm:mt-0">
              <span
                v-if="isExpired(row)"
                class="inline-flex items-center gap-1 rounded-md bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700"
              >
                <Icon :path="icons.alertTriangle" :size="12" />
                Vencido
              </span>
              <span
                v-else-if="isExpiringSoon(row)"
                class="inline-flex items-center gap-1 rounded-md bg-orange-100 px-2 py-0.5 text-xs font-medium text-orange-700"
              >
                <Icon :path="icons.clock" :size="12" />
                Por vencer
              </span>
              <span
                v-else-if="isLow(row)"
                class="inline-flex items-center gap-1 rounded-md bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700"
              >
                Stock bajo
              </span>
              <span
                v-else
                class="inline-flex rounded-md bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700"
              >
                OK
              </span>
            </span>
          </div>
          <span
            class="flex shrink-0 items-center justify-end transition-opacity sm:opacity-0 sm:group-hover:opacity-100"
          >
            <IconButton :icon="icons.pencil" label="Editar stock" @click="openEdit(row)" />
          </span>
        </li>
      </ul>
    </div>
  </WidgetCard>

  <StockEditModal
    v-if="editingIng"
    :ingredient="editingIng"
    :stock="editingStock"
    @close="editingIng = null"
    @saved="onSaved"
  />
</template>
