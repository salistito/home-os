<script setup lang="ts">
import { computed, ref } from "vue";
import { ApiRequestError } from "../../api/client";
import { foodApi } from "../../api/food";
import Icon from "../../components/Icon.vue";
import IconButton from "../../components/IconButton.vue";
import Modal from "../../components/Modal.vue";
import WidgetCard from "../../components/WidgetCard.vue";
import { formatMoney } from "../../lib/format";
import { icons } from "../../lib/icons";
import { pushToast } from "../../lib/toast";
import type { Ingredient, IngredientPurchase } from "../../types";
import PurchaseFormModal from "./PurchaseFormModal.vue";

const props = defineProps<{
  purchases: IngredientPurchase[];
  ingredients: Ingredient[];
}>();
const emit = defineEmits<{ reload: [] }>();

const formOpen = ref(false);
const deleting = ref<IngredientPurchase | null>(null);
const deleteBusy = ref(false);

const sorted = computed(() =>
  [...props.purchases].sort(
    (a, b) => b.purchased_at.localeCompare(a.purchased_at),
  ),
);

function ingredientName(id: number): string {
  return props.ingredients.find((i) => i.id === id)?.name ?? `#${id}`;
}

function ingredientUnit(id: number): string {
  const ing = props.ingredients.find((i) => i.id === id);
  if (!ing) return "";
  return ing.purchase_unit || ing.unit;
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
</script>

<template>
  <WidgetCard title="Compras" :count="purchases.length">
    <template #actions>
      <button
        type="button"
        class="inline-flex items-center gap-1 rounded-lg bg-slate-900 px-2.5 py-1.5 text-xs font-medium text-white transition-colors hover:bg-slate-700"
        @click="formOpen = true"
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
      <div
        class="hidden grid-cols-[1fr_6rem_6rem_7rem_1fr_2.25rem] items-center gap-3 border-b border-slate-100 bg-slate-50/60 px-4 py-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400 sm:grid"
      >
        <span>Ingrediente</span>
        <span class="text-right">Cantidad</span>
        <span class="text-right">Precio</span>
        <span>Fecha</span>
        <span>Notas</span>
        <span></span>
      </div>

      <ul class="divide-y divide-slate-100">
        <li
          v-for="purchase in sorted"
          :key="purchase.id"
          class="group flex items-start gap-3 px-4 py-3 transition-colors hover:bg-slate-50 sm:grid sm:grid-cols-[1fr_6rem_6rem_7rem_1fr_2.25rem] sm:items-center sm:py-2.5"
        >
          <div class="min-w-0 flex-1 sm:contents">
            <span class="block truncate text-[13px] font-medium text-slate-800">
              {{ ingredientName(purchase.ingredient_id) }}
            </span>
            <span class="mt-1 text-right text-sm tabular-nums text-slate-700 sm:mt-0">
              {{ purchase.quantity }} {{ ingredientUnit(purchase.ingredient_id) }}
            </span>
            <span class="mt-1 text-right text-sm tabular-nums text-slate-700 sm:mt-0">
              {{ formatMoney(purchase.price) }}
            </span>
            <span class="mt-1 text-xs text-slate-500 sm:mt-0">
              {{ purchase.purchased_at.split("-").reverse().join("/") }}
            </span>
            <span class="mt-1 truncate text-xs text-slate-400 sm:mt-0">
              {{ purchase.notes || "—" }}
            </span>
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
