<script setup lang="ts">
import { ref, watch } from "vue";
import { ApiRequestError } from "../../api/client";
import { foodApi } from "../../api/food";
import DateInput from "../../components/DateInput.vue";
import Modal from "../../components/Modal.vue";
import type { Ingredient, IngredientStock } from "../../types";

const props = defineProps<{
  ingredient: Ingredient;
  stock: IngredientStock | null;
}>();
const emit = defineEmits<{ close: []; saved: [] }>();

const hasPurchaseUnit = !!(
  props.ingredient.purchase_unit && props.ingredient.purchase_conversion_factor
);

const baseQuantity = ref(props.stock?.quantity ?? 0);
const purchaseQuantity = ref(
  hasPurchaseUnit ? (props.stock?.quantity ?? 0) / props.ingredient.purchase_conversion_factor! : 0,
);

let syncing = false;

watch(baseQuantity, (val) => {
  if (syncing || !hasPurchaseUnit) return;
  syncing = true;
  purchaseQuantity.value = val / props.ingredient.purchase_conversion_factor!;
  syncing = false;
});

watch(purchaseQuantity, (val) => {
  if (syncing || !hasPurchaseUnit) return;
  syncing = true;
  baseQuantity.value = val * props.ingredient.purchase_conversion_factor!;
  syncing = false;
});

const minAlert = ref(props.stock?.min_alert_quantity ?? 0);
const expirationDate = ref(props.stock?.expiration_date ?? "");

const error = ref<string | null>(null);
const saving = ref(false);

async function submit() {
  error.value = null;

  if (baseQuantity.value < 0) {
    error.value = "La cantidad no puede ser negativa.";
    return;
  }

  saving.value = true;
  try {
    await foodApi.setStock(props.ingredient.id, {
      quantity: baseQuantity.value,
      min_alert_quantity: minAlert.value,
      expiration_date: expirationDate.value || null,
    });
    emit("saved");
  } catch (e) {
    error.value =
      e instanceof ApiRequestError ? e.message : "Error inesperado al guardar.";
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <Modal title="Editar stock" @close="emit('close')">
    <form class="space-y-4" @submit.prevent="submit">
      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">Ingrediente</label>
        <p class="text-sm font-medium text-slate-800">{{ ingredient.name }}</p>
      </div>

      <div class="rounded-lg border border-slate-100 bg-slate-50/50 p-3">
        <p class="mb-2 text-xs font-semibold tracking-wider text-slate-400">
          Cantidad
        </p>
        <p v-if="hasPurchaseUnit" class="mb-2 text-xs text-slate-500">
          Puedes ingresar la cantidad en la unidad de compra o en la unidad basal. Ambas se sincronizarán automáticamente.
        </p>
        <div v-if="hasPurchaseUnit" class="flex items-start gap-1.5">
          <div class="min-w-0 flex-1">
            <label class="mb-1 block text-xs font-medium text-slate-500">
              Cantidad en {{ ingredient.purchase_unit }}
            </label>
            <div class="flex items-center gap-1.5">
              <input
                v-model.number="purchaseQuantity"
                type="number"
                min="0"
                class="min-w-0 flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
              />
              <span class="shrink-0 rounded-md bg-slate-100 px-2 py-1.5 text-xs font-medium text-slate-500">
                {{ ingredient.purchase_unit }}
              </span>
            </div>
          </div>
          <span class="mt-7 shrink-0 text-sm font-medium text-slate-400">=</span>
          <div class="min-w-0 flex-1">
            <label class="mb-1 block text-xs font-medium text-slate-500">
              Cantidad en {{ ingredient.unit }}
            </label>
            <div class="flex items-center gap-1.5">
              <input
                v-model.number="baseQuantity"
                type="number"
                min="0"
                class="min-w-0 flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
              />
              <span class="shrink-0 rounded-md bg-slate-100 px-2 py-1.5 text-xs font-medium text-slate-500">
                {{ ingredient.unit }}
              </span>
            </div>
          </div>
        </div>
        <div v-else>
          <label class="mb-1 block text-xs font-medium text-slate-500">
            Cantidad en {{ ingredient.unit }}
          </label>
          <div class="flex items-center gap-1.5">
            <input
              v-model.number="baseQuantity"
              type="number"
              min="0"
              class="min-w-0 flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
            />
            <span class="shrink-0 rounded-md bg-slate-100 px-2 py-1.5 text-xs font-medium text-slate-500">
              {{ ingredient.unit }}
            </span>
          </div>
        </div>
      </div>

      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">
          Cantidad mínima alertada <span class="text-slate-400">({{ ingredient.unit }})</span>
        </label>
        <input
          v-model.number="minAlert"
          type="number"
          min="0"
          class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
        />
      </div>

      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">Fecha de expiración</label>
        <DateInput v-model="expirationDate" />
      </div>

      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

      <div class="flex justify-end gap-2 pt-1">
        <button
          type="button"
          class="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100"
          @click="emit('close')"
        >
          Cancelar
        </button>
        <button
          type="submit"
          :disabled="saving"
          class="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-700 disabled:opacity-50"
        >
          {{ saving ? "Guardando…" : "Guardar" }}
        </button>
      </div>
    </form>
  </Modal>
</template>
