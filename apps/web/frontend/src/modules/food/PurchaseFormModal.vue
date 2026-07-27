<script setup lang="ts">
import { computed, ref } from "vue";
import { ApiRequestError } from "../../api/client";
import { foodApi } from "../../api/food";
import Modal from "../../components/Modal.vue";
import type { Ingredient } from "../../types";

const props = defineProps<{ ingredients: Ingredient[] }>();
const emit = defineEmits<{ close: []; saved: [] }>();

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

const ingredientId = ref<number | null>(null);
const quantity = ref(0);
const price = ref(0);
const purchasedAt = ref(today());
const notes = ref("");

const error = ref<string | null>(null);
const saving = ref(false);

const selectedIngredient = computed(() => {
  if (!ingredientId.value) return null;
  return props.ingredients.find((i) => i.id === ingredientId.value) ?? null;
});

const selectedUnit = computed(() => {
  const ing = selectedIngredient.value;
  if (!ing) return "";
  return ing.purchase_unit || ing.unit;
});

const unit = computed(() => {
  const ing = selectedIngredient.value;
  if (!ing) return undefined;
  return ing.purchase_unit || undefined;
});

async function submit() {
  error.value = null;

  if (!ingredientId.value) {
    error.value = "Selecciona un ingrediente.";
    return;
  }
  if (quantity.value <= 0) {
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
      quantity: quantity.value,
      unit: unit.value,
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
          <option :value="null" disabled>Seleccionar ingrediente</option>
          <option v-for="ing in ingredients" :key="ing.id" :value="ing.id">
            {{ ing.name }}
          </option>
        </select>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">Cantidad</label>
          <div class="flex items-center gap-2">
            <input
              v-model.number="quantity"
              type="number"
              min="0.1"
              step="0.1"
              class="min-w-0 flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
            />
            <span v-if="selectedUnit" class="shrink-0 text-xs text-slate-400">
              {{ selectedUnit }}
            </span>
          </div>
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">Precio</label>
          <input
            v-model.number="price"
            type="number"
            min="0"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
          />
        </div>
      </div>

      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">Fecha</label>
        <input
          v-model="purchasedAt"
          type="date"
          class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
        />
      </div>

      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">Notas</label>
        <textarea
          v-model="notes"
          rows="2"
          placeholder="Opcional"
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
