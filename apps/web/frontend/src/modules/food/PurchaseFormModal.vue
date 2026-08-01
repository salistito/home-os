<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { ApiRequestError } from "../../api/client";
import { foodApi } from "../../api/food";
import DateInput from "../../components/DateInput.vue";
import Modal from "../../components/Modal.vue";
import { getToday } from "../../lib/date";
import type { Ingredient } from "../../types";

const props = defineProps<{ ingredients: Ingredient[] }>();
const emit = defineEmits<{ close: []; saved: [] }>();

const ingredientId = ref<number | null>(null);
const price = ref(0);
const purchasedAt = ref(getToday());
const notes = ref("");

const error = ref<string | null>(null);
const saving = ref(false);

const selectedIngredient = computed(() => {
  if (!ingredientId.value) return null;
  return props.ingredients.find((i) => i.id === ingredientId.value) ?? null;
});

const hasPurchaseUnit = computed(
  () => !!(selectedIngredient.value?.purchase_unit && selectedIngredient.value?.purchase_conversion_factor),
);

const factor = computed(() => selectedIngredient.value?.purchase_conversion_factor ?? 1);

const baseQuantity = ref(0);
const purchaseQuantity = ref(0);

let syncing = false;

watch(selectedIngredient, () => {
  baseQuantity.value = 0;
  purchaseQuantity.value = 0;
});

watch(baseQuantity, (val) => {
  if (syncing || !hasPurchaseUnit.value) return;
  syncing = true;
  purchaseQuantity.value = val / factor.value;
  syncing = false;
});

watch(purchaseQuantity, (val) => {
  if (syncing || !hasPurchaseUnit.value) return;
  syncing = true;
  baseQuantity.value = val * factor.value;
  syncing = false;
});

async function submit() {
  error.value = null;

  if (!ingredientId.value) {
    error.value = "Selecciona un ingrediente.";
    return;
  }
  if (baseQuantity.value <= 0) {
    error.value = "La cantidad debe ser mayor a 0.";
    return;
  }
  if (!Number.isInteger(price.value) || price.value < 0) {
    error.value = "El precio debe ser un entero mayor o igual a 0.";
    return;
  }

  saving.value = true;
  try {
    await foodApi.createPurchase({
      ingredient_id: ingredientId.value,
      quantity: baseQuantity.value,
      price: price.value,
      purchased_at: purchasedAt.value,
      notes: notes.value.trim() || null,
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
  <Modal title="Registrar compra" @close="emit('close')">
    <form class="space-y-4" @submit.prevent="submit">
      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">Ingrediente</label>
        <select
          v-model.number="ingredientId"
          class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
        >
          <option :value="null" disabled>Selecciona un ingrediente</option>
          <option v-for="ing in ingredients" :key="ing.id" :value="ing.id">
            {{ ing.name }}
          </option>
        </select>
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
              Cantidad en {{ selectedIngredient!.purchase_unit }}
            </label>
            <div class="flex items-center gap-1.5">
              <input
                v-model.number="purchaseQuantity"
                type="number"
                min="0"
                step="any"
                class="min-w-0 flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
              />
              <span class="shrink-0 rounded-md bg-slate-100 px-2 py-1.5 text-xs font-medium text-slate-500">
                {{ selectedIngredient!.purchase_unit }}
              </span>
            </div>
          </div>
          <span class="mt-7 shrink-0 text-sm font-medium text-slate-400">=</span>
          <div class="min-w-0 flex-1">
            <label class="mb-1 block text-xs font-medium text-slate-500">
              Cantidad en {{ selectedIngredient!.unit }}
            </label>
            <div class="flex items-center gap-1.5">
              <input
                v-model.number="baseQuantity"
                type="number"
                min="0"
                step="any"
                class="min-w-0 flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
              />
              <span class="shrink-0 rounded-md bg-slate-100 px-2 py-1.5 text-xs font-medium text-slate-500">
                {{ selectedIngredient!.unit }}
              </span>
            </div>
          </div>
        </div>
        <div v-else>
          <label class="mb-1 block text-xs font-medium text-slate-500">
            Cantidad en {{ selectedIngredient?.unit ?? "—" }}
          </label>
          <div class="flex items-center gap-1.5">
            <input
              v-model.number="baseQuantity"
              type="number"
              min="0"
              step="any"
              class="min-w-0 flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
            />
            <span class="shrink-0 rounded-md bg-slate-100 px-2 py-1.5 text-xs font-medium text-slate-500">
              {{ selectedIngredient?.unit ?? "—" }}
            </span>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">Precio</label>
          <input
            v-model.number="price"
            type="number"
            min="0"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
          />
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">Fecha de compra</label>
          <DateInput v-model="purchasedAt" />
        </div>
      </div>

      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">Notas (Opcional)</label>
        <textarea
          v-model="notes"
          rows="2"
          placeholder="Para los gains"
          class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
        />
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
          {{ saving ? "Guardando…" : "Registrar" }}
        </button>
      </div>
    </form>
  </Modal>
</template>
