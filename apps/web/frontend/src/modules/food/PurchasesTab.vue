<script setup lang="ts">
import { computed, ref } from "vue";
import { ApiRequestError } from "../../api/client";
import { foodApi } from "../../api/food";
import Icon from "../../components/Icon.vue";
import IconButton from "../../components/IconButton.vue";
import Modal from "../../components/Modal.vue";
import WidgetCard from "../../components/WidgetCard.vue";
import { formatDate } from "../../lib/format";
import { icons } from "../../lib/icons";
import { formatMoney } from "../../lib/money";
import { pushToast } from "../../lib/toast";
import type { Ingredient, IngredientPurchase } from "../../types";
import PurchaseFormModal from "./PurchaseFormModal.vue";

const props = defineProps<{
  ingredients: Ingredient[];
  purchases: IngredientPurchase[];
}>();
const emit = defineEmits<{ reload: [] }>();

const formOpen = ref(false);
const deleting = ref<IngredientPurchase | null>(null);
const deleteBusy = ref(false);

const sortBy = ref<"ingredient" | "quantity" | "price" | "date">("ingredient");
const sortDesc = ref(false);

const sortedRows = computed(() => {
  const dir = sortDesc.value ? -1 : 1;
  return [...props.purchases].sort((a, b) => {
    let cmp = 0;
    switch (sortBy.value) {
      case "ingredient":
        cmp = ingredientName(a.ingredient_id).localeCompare(ingredientName(b.ingredient_id), undefined, { sensitivity: "base" });
        break;
      case "quantity":
        cmp = a.quantity - b.quantity;
        break;
      case "price":
        cmp = a.price - b.price;
        break;
      case "date":
        cmp = a.purchased_at.localeCompare(b.purchased_at);
        break;
    }
    return cmp * dir;
  });
});

function setSort(col: "ingredient" | "quantity" | "price" | "date") {
  if (sortBy.value === col) {
    sortDesc.value = !sortDesc.value;
  } else {
    sortBy.value = col;
    sortDesc.value = col === "date";
  }
}

function ingredientName(id: number): string {
  return props.ingredients.find((i) => i.id === id)?.name ?? `#${id}`;
}

function ingredientByPurchase(purchase: IngredientPurchase): Ingredient | undefined {
  return props.ingredients.find((i) => i.id === purchase.ingredient_id);
}

function formatQuantity(val: number): string {
  return Number.isInteger(val) ? String(val) : val.toFixed(2);
}

function quantityDisplay(purchase: IngredientPurchase): { purchase: string | null; base: string } {
  const ing = ingredientByPurchase(purchase);
  const qty = purchase.quantity;
  if (ing?.purchase_unit && ing.purchase_conversion_factor) {
    return {
      purchase: `${formatQuantity(qty / ing.purchase_conversion_factor)} ${ing.purchase_unit}`,
      base: `${qty} ${ing.unit}`,
    };
  }
  return { purchase: null, base: `${qty} ${ing?.unit ?? ""}` };
}

async function onSaved() {
  formOpen.value = false;
  emit("reload");
  pushToast("Compra registrada");
}

function askDelete(purchase: IngredientPurchase) {
  deleting.value = purchase;
}

async function confirmDelete() {
  if (!deleting.value) return;
  deleteBusy.value = true;
  try {
    await foodApi.deletePurchase(deleting.value.id);
    deleting.value = null;
    emit("reload");
    pushToast("Compra eliminada");
  } catch (e) {
    pushToast(
      e instanceof ApiRequestError ? e.message : "No se pudo eliminar la compra.",
      "error",
    );
  } finally {
    deleteBusy.value = false;
  }
}
function openCreate() {
  formOpen.value = true;
}

defineExpose({ openCreate });
</script>

<template>
  <WidgetCard title="Compras" :count="purchases.length">
    <template #actions>
      <button
        type="button"
        class="hidden items-center gap-1 rounded-lg bg-slate-900 px-2.5 py-1.5 text-xs font-medium text-white transition-colors hover:bg-slate-700 lg:inline-flex"
        @click="openCreate"
      >
        <Icon :path="icons.plus" :size="14" />
        Registrar
      </button>
    </template>

    <p
      v-if="!purchases.length"
      class="px-4 py-10 text-center text-sm text-slate-500"
    >
      Todavía no hay compras registradas.
    </p>

    <div v-else>
      <div class="flex items-center gap-2 px-4 py-3 sm:hidden">
        <select
          v-model="sortBy"
          class="rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs text-slate-700 outline-none focus:border-slate-400"
        >
          <option value="ingredient">Ingrediente</option>
          <option value="quantity">Cantidad</option>
          <option value="price">Precio</option>
          <option value="date">Fecha de compra</option>
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
        class="hidden grid-cols-[1fr_8rem_6rem_10rem_1fr_2.25rem] items-center gap-2 border-b border-slate-100 bg-slate-50/60 px-4 py-2 text-xs font-semibold tracking-wider text-slate-400 sm:grid"
      >
        <button type="button" class="flex items-center gap-1 text-left" @click="setSort('ingredient')">
          Ingrediente
          <span v-if="sortBy === 'ingredient'">{{ sortDesc ? "↓" : "↑" }}</span>
        </button>
        <button type="button" class="flex items-center gap-1" @click="setSort('quantity')">
          Cantidad
          <span v-if="sortBy === 'quantity'">{{ sortDesc ? "↓" : "↑" }}</span>
        </button>
        <button type="button" class="flex items-center gap-1" @click="setSort('price')">
          Precio
          <span v-if="sortBy === 'price'">{{ sortDesc ? "↓" : "↑" }}</span>
        </button>
        <button type="button" class="flex items-center gap-1" @click="setSort('date')">
          Fecha de compra
          <span v-if="sortBy === 'date'">{{ sortDesc ? "↓" : "↑" }}</span>
        </button>
        <span>Notas</span>
        <span></span>
      </div>

      <ul class="divide-y divide-slate-100">
        <li
          v-for="purchase in sortedRows"
          :key="purchase.id"
          class="group flex items-start gap-3 px-4 py-3 transition-colors hover:bg-slate-50 sm:grid sm:grid-cols-[1fr_8rem_6rem_10rem_1fr_2.25rem] sm:items-center sm:gap-2 sm:py-2.5"
        >
          <div class="min-w-0 flex-1 sm:contents">
            <span class="block truncate text-[13px] font-medium text-slate-800">
              {{ ingredientName(purchase.ingredient_id) }}
            </span>

            <div class="sm:contents">
              <div class="mt-1.5 flex flex-wrap items-center gap-2 sm:contents">
                <span class="sm:justify-self-start">
                  <template v-if="quantityDisplay(purchase).purchase">
                    <span class="sm:hidden inline-flex items-center gap-1 rounded-md border border-slate-200 px-2 py-0.5 text-xs tabular-nums text-slate-600">
                      <Icon :path="icons.shoppingBag" :size="12" class="shrink-0 text-slate-400" />
                      {{ quantityDisplay(purchase).purchase }} ({{ quantityDisplay(purchase).base }})
                    </span>
                    <span class="hidden sm:block">
                      <span class="block text-xs tabular-nums font-medium text-slate-600">
                        <Icon :path="icons.shoppingBag" :size="12" class="mr-0.5 inline shrink-0 text-slate-400" />
                        {{ quantityDisplay(purchase).purchase }}
                      </span>
                      <span class="block text-[11px] tabular-nums leading-tight text-slate-400">
                        {{ quantityDisplay(purchase).base }}
                      </span>
                    </span>
                  </template>
                  <template v-else>
                    <span class="sm:hidden inline-flex items-center gap-1 rounded-md border border-slate-200 px-2 py-0.5 text-xs tabular-nums text-slate-600">
                      <Icon :path="icons.shoppingBag" :size="12" class="shrink-0 text-slate-400" />
                      {{ quantityDisplay(purchase).base }}
                    </span>
                    <span class="hidden sm:block text-xs tabular-nums font-medium text-slate-600">
                      <Icon :path="icons.shoppingBag" :size="12" class="mr-0.5 inline shrink-0 text-slate-400" />
                      {{ quantityDisplay(purchase).base }}
                    </span>
                  </template>
                </span>

                <span class="inline-flex items-center gap-1 rounded-md border border-slate-200 px-2 py-0.5 text-xs tabular-nums text-slate-600 sm:justify-self-start">
                  <Icon :path="icons.wallet" :size="12" class="shrink-0 text-slate-400" />
                  {{ formatMoney(purchase.price) }}
                </span>

              </div>

              <div class="mt-1 flex flex-wrap items-center gap-2 sm:contents">
                <span class="inline-flex items-center gap-1 text-xs text-slate-600 sm:justify-self-start">
                  <Icon :path="icons.calendar" :size="12" class="shrink-0 text-slate-400" />
                  {{ formatDate(purchase.purchased_at) }}
                </span>

                <template v-if="purchase.notes">
                  <span
                    class="truncate text-xs text-slate-500 sm:justify-self-start"
                    :title="purchase.notes"
                  >
                    {{ purchase.notes }}
                  </span>
                </template>
                <span
                  v-else
                  class="hidden text-xs text-slate-400 sm:inline sm:ml-6.5"
                >
                  —
                </span>
              </div>
            </div>
          </div>
          <span
            class="flex shrink-0 items-center justify-end transition-opacity sm:opacity-0 sm:group-hover:opacity-100"
          >
            <IconButton
              :icon="icons.trash"
              label="Eliminar"
              variant="danger"
              @click="askDelete(purchase)"
            />
          </span>
        </li>
      </ul>
    </div>
  </WidgetCard>

  <PurchaseFormModal
    v-if="formOpen"
    :ingredients="ingredients"
    @close="formOpen = false"
    @saved="onSaved"
  />

  <Modal v-if="deleting" title="Eliminar compra" @close="deleting = null">
    <p class="text-sm text-slate-600">
      ¿Seguro que quieres eliminar la compra de
      <span class="font-medium text-slate-900">
        {{ ingredientName(deleting.ingredient_id) }}
      </span>
      ?
    </p>
    <p class="mt-2 text-xs text-slate-400">
      El stock del ingrediente se ajustará automáticamente restando la cantidad ingresada en esta compra.
    </p>
    <div class="mt-5 flex justify-end gap-2">
      <button
        type="button"
        class="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100"
        @click="deleting = null"
      >
        Cancelar
      </button>
      <button
        type="button"
        :disabled="deleteBusy"
        class="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-500 disabled:opacity-50"
        @click="confirmDelete"
      >
        {{ deleteBusy ? "Eliminando…" : "Eliminar" }}
      </button>
    </div>
  </Modal>
</template>
