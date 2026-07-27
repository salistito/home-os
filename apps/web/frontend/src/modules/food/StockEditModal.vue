<script setup lang="ts">
import { computed, ref } from "vue";
import { ApiRequestError } from "../../api/client";
import { foodApi } from "../../api/food";
import Modal from "../../components/Modal.vue";
import type { Ingredient, IngredientStock } from "../../types";

const props = defineProps<{
  ingredient: Ingredient;
  stock: IngredientStock | null;
}>();
const emit = defineEmits<{ close: []; saved: [] }>();

const displayUnit = computed(() => props.ingredient.purchase_unit || props.ingredient.unit);
const quantity = ref(props.stock?.quantity ?? 0);
const minAlert = ref(props.stock?.min_alert_quantity ?? 0);
const expirationDate = ref(props.stock?.expiration_date ?? "");
const expirationInput = ref(
  expirationDate.value ? expirationDate.value.split("-").reverse().join("/") : "",
);

function syncExpirationInput() {
  const parts = expirationInput.value.split("/");
  if (parts.length === 3) {
    const [dd, mm, yyyy] = parts;
    if (dd.length === 2 && mm.length === 2 && yyyy.length === 4) {
      expirationDate.value = `${yyyy}-${mm}-${dd}`;
    }
  } else {
    expirationDate.value = "";
  }
}

const error = ref<string | null>(null);
const saving = ref(false);

async function submit() {
  syncExpirationInput();
  error.value = null;

  if (quantity.value < 0) {
    error.value = "La cantidad no puede ser negativa.";
    return;
  }

  saving.value = true;
  try {
    await foodApi.setStock(props.ingredient.id, {
      quantity: quantity.value,
      unit: props.ingredient.purchase_unit || undefined,
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

      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">
          Cantidad <span class="text-slate-400">({{ displayUnit }})</span>
        </label>
        <input
          v-model.number="quantity"
          type="number"
          min="0"
          class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
        />
      </div>

      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">
          Cantidad mín. de alerta <span class="text-slate-400">({{ displayUnit }})</span>
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
        <input
          v-model="expirationInput"
          type="text"
          placeholder="dd/mm/yyyy"
          maxlength="10"
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
          {{ saving ? "Guardando…" : "Guardar" }}
        </button>
      </div>
    </form>
  </Modal>
</template>
