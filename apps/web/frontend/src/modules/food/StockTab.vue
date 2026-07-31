<script setup lang="ts">
import { computed, ref } from "vue";
import Icon from "../../components/Icon.vue";
import IconButton from "../../components/IconButton.vue";
import WidgetCard from "../../components/WidgetCard.vue";
import { tagColorByString } from "../../lib/colors";
import { getToday } from "../../lib/date";
import { formatDate } from "../../lib/format";
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

const sortBy = ref<"name" | "category" | "quantity" | "min_alert" | "expiration" | "status">("name");
const sortDesc = ref(false);
function statusRank(row: StockRow): number {
  if (isExpired(row)) return 0;
  if (isExpiringSoon(row)) return 1;
  if (isLow(row)) return 2;
  return 3;
}

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

const sortedRows = computed(() => {
  const dir = sortDesc.value ? -1 : 1;
  return [...rows.value].sort((a, b) => {
    let cmp = 0;
    switch (sortBy.value) {
      case "name":
        cmp = a.ingredient.name.localeCompare(b.ingredient.name, undefined, { sensitivity: "base" });
        break;
      case "category":
        cmp = (a.ingredient.category ?? "").localeCompare(b.ingredient.category ?? "", undefined, { sensitivity: "base" });
        break;
      case "quantity":
        cmp = (a.stock?.quantity ?? 0) - (b.stock?.quantity ?? 0);
        break;
      case "min_alert":
        cmp = (a.stock?.min_alert_quantity ?? 0) - (b.stock?.min_alert_quantity ?? 0);
        break;
      case "expiration":
        cmp = (a.stock?.expiration_date ?? "").localeCompare(b.stock?.expiration_date ?? "");
        break;
      case "status":
        cmp = statusRank(a) - statusRank(b);
        break;
    }
    if (cmp === 0) {
      cmp = a.ingredient.name.localeCompare(b.ingredient.name, undefined, { sensitivity: "base" });
    }
    return cmp * dir;
  });
});

function setSort(col: "name" | "category" | "quantity" | "min_alert" | "expiration" | "status") {
  if (sortBy.value === col) {
    sortDesc.value = !sortDesc.value;
  } else {
    sortBy.value = col;
    sortDesc.value = false;
  }
}

function isExpired(row: StockRow): boolean {
  if (!row.stock?.expiration_date) return false;
  return row.stock.expiration_date < getToday();
}

function isExpiringSoon(row: StockRow): boolean {
  if (!row.stock?.expiration_date) return false;
  const [ey, em, ed] = row.stock.expiration_date.split("-").map(Number);
  const [ty, tm, td] = getToday().split("-").map(Number);
  const expiration = new Date(ey, em - 1, ed);
  const today = new Date(ty, tm - 1, td);
  const diff = (expiration.getTime() - today.getTime()) / (1000 * 60 * 60 * 24);
  return diff >= 0 && diff <= 7;
}

function isLow(row: StockRow): boolean {
  if (!row.stock) return true;
  return row.stock.quantity <= row.stock.min_alert_quantity;
}

function formatQuantity(val: number): string {
  return Number.isInteger(val) ? String(val) : val.toFixed(2);
}

function quantityDisplay(row: StockRow): { purchase: string | null; base: string } {
  const ing = row.ingredient;
  const qty = row.stock?.quantity ?? 0;
  if (ing.purchase_unit && ing.purchase_conversion_factor) {
    return {
      purchase: `${formatQuantity(qty / ing.purchase_conversion_factor)} ${ing.purchase_unit}`,
      base: `${qty} ${ing.unit}`,
    };
  }
  return { purchase: null, base: `${qty} ${ing.unit}` };
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
      <div class="flex items-center gap-2 px-4 py-3 sm:hidden">
        <select
          v-model="sortBy"
          class="rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs text-slate-700 outline-none focus:border-slate-400"
        >
          <option value="name">Nombre</option>
          <option value="category">Categoría</option>
          <option value="quantity">Cantidad</option>
          <option value="min_alert">Mín. alerta</option>
          <option value="expiration">Vencimiento</option>
          <option value="status">Estado</option>
        </select>
        <button
          type="button"
          class="inline-flex items-center rounded-lg border border-slate-200 px-2 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-50"
          @click="sortDesc = !sortDesc"
        >
          {{ sortDesc ? "↓ DESC" : "↑ ASC" }}
        </button>
      </div>

      <div
        class="hidden grid-cols-[1fr_8rem_8rem_7rem_6rem_6rem_2.25rem] items-center gap-2 border-b border-slate-100 bg-slate-50/60 px-4 py-2 text-xs font-semibold tracking-wider text-slate-400 sm:grid"
      >
        <button type="button" class="flex items-center gap-1 text-left" @click="setSort('name')">
          Ingrediente
          <span v-if="sortBy === 'name'">{{ sortDesc ? "↓" : "↑" }}</span>
        </button>
        <button type="button" class="flex items-center gap-1" @click="setSort('category')">
          Categoría
          <span v-if="sortBy === 'category'">{{ sortDesc ? "↓" : "↑" }}</span>
        </button>
        <button type="button" class="flex items-center gap-1" @click="setSort('quantity')">
          Cantidad
          <span v-if="sortBy === 'quantity'">{{ sortDesc ? "↓" : "↑" }}</span>
        </button>
        <button type="button" class="flex items-center gap-1" @click="setSort('min_alert')">
          Mín. alerta
          <span v-if="sortBy === 'min_alert'">{{ sortDesc ? "↓" : "↑" }}</span>
        </button>
        <button type="button" class="flex items-center gap-1" @click="setSort('expiration')">
          Expiración
          <span v-if="sortBy === 'expiration'">{{ sortDesc ? "↓" : "↑" }}</span>
        </button>
        <button type="button" class="flex items-center gap-1" @click="setSort('status')">
          Estado
          <span v-if="sortBy === 'status'">{{ sortDesc ? "↓" : "↑" }}</span>
        </button>
        <span></span>
      </div>

      <ul class="divide-y divide-slate-100">
        <li
          v-for="row in sortedRows"
          :key="row.ingredient.id"
           class="group flex items-start gap-3 px-4 py-3 transition-colors sm:grid sm:grid-cols-[1fr_8rem_8rem_7rem_6rem_6rem_2.25rem] sm:items-center sm:gap-2 sm:py-2.5"
          :class="
            isExpired(row)
              ? 'bg-red-50/50'
              : isExpiringSoon(row)
                ? 'bg-orange-50/50'
                : isLow(row)
                  ? 'bg-amber-50/50'
                  : 'hover:bg-slate-50'
          "
        >
          <div class="min-w-0 flex-1 sm:contents">
            <span class="block truncate text-[13px] font-medium text-slate-800">
              {{ row.ingredient.name }}
            </span>

            <div class="sm:contents">
              <div class="mt-1.5 flex flex-wrap items-center gap-2 sm:contents">
                <span
                  v-if="row.ingredient.category"
                  class="inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium sm:justify-self-start"
                  :class="[tagColorByString(row.ingredient.category).bg, tagColorByString(row.ingredient.category).text]"
                >
                  {{ row.ingredient.category }}
                </span>
                <span v-else class="hidden text-xs text-slate-400 sm:inline sm:ml-6.5">—</span>

                <span class="sm:justify-self-start">
                  <template v-if="quantityDisplay(row).purchase">
                    <span class="sm:hidden inline-flex items-center gap-1 rounded-md border border-slate-200 px-2 py-0.5 text-xs tabular-nums text-slate-600">
                      <Icon :path="icons.shoppingBag" :size="12" class="shrink-0 text-slate-400" />
                      {{ quantityDisplay(row).purchase }} ({{ quantityDisplay(row).base }})
                    </span>
                    <span class="hidden sm:block">
                      <span class="block text-xs tabular-nums font-medium text-slate-600">
                        <Icon :path="icons.shoppingBag" :size="12" class="mr-0.5 inline shrink-0 text-slate-400" />
                        {{ quantityDisplay(row).purchase }}
                      </span>
                      <span class="block text-[11px] tabular-nums leading-tight text-slate-400">
                        {{ quantityDisplay(row).base }}
                      </span>
                    </span>
                  </template>
                  <template v-else>
                    <span class="sm:hidden inline-flex items-center gap-1 rounded-md border border-slate-200 px-2 py-0.5 text-xs tabular-nums text-slate-600">
                      <Icon :path="icons.shoppingBag" :size="12" class="shrink-0 text-slate-400" />
                      {{ quantityDisplay(row).base }}
                    </span>
                    <span class="hidden sm:block text-xs tabular-nums font-medium text-slate-600">
                      <Icon :path="icons.shoppingBag" :size="12" class="mr-0.5 inline shrink-0 text-slate-400" />
                      {{ quantityDisplay(row).base }}
                    </span>
                  </template>
                </span>
              </div>

              <div class="mt-1 flex flex-wrap items-center gap-2 sm:contents">
                <span class="inline-flex items-center gap-1 rounded-md border border-slate-200 px-2 py-0.5 text-xs text-slate-600 sm:justify-self-start">
                  <Icon :path="icons.bell" :size="12" class="shrink-0 text-slate-400" />
                  {{ row.stock?.min_alert_quantity ?? 0 }} {{ row.ingredient.unit }}
                </span>

                <span v-if="row.stock?.expiration_date" class="inline-flex items-center gap-1 text-xs text-slate-600 sm:justify-self-start">
                  <Icon :path="icons.calendar" :size="12" class="shrink-0 text-slate-400" />
                  {{ formatDate(row.stock.expiration_date) }}
                </span>
                <span v-else class="hidden sm:inline-flex items-center gap-1 text-xs text-slate-400 sm:justify-self-start">
                  <Icon :path="icons.calendar" :size="12" class="shrink-0 text-slate-400" />
                  —
                </span>

                <span class="sm:justify-self-start">
                  <span
                    v-if="isExpired(row)"
                    class="inline-flex items-center gap-1 rounded-md bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700"
                  >
                    <Icon :path="icons.close" :size="12" />
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
                    <Icon :path="icons.alertTriangle" :size="12" />
                    Stock bajo
                  </span>
                  <span
                    v-else
                    class="inline-flex items-center gap-1 rounded-md bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700"
                  >
                    <Icon :path="icons.check" :size="12" />
                    OK
                  </span>
                </span>
              </div>
            </div>
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
