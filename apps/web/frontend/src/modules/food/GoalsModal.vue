<script setup lang="ts">
import { ref } from "vue";
import { ApiRequestError } from "../../api/client";
import { foodApi } from "../../api/food";
import Modal from "../../components/Modal.vue";
import type { NutritionGoals } from "../../types";

const props = defineProps<{ goals: NutritionGoals | null }>();
const emit = defineEmits<{ close: []; saved: [] }>();

const fields = [
  { key: "kcal_target", label: "Calorías", unit: "kcal", integer: true },
  { key: "protein_g_target", label: "Proteínas", unit: "g", integer: false },
  { key: "carbs_g_target", label: "Carbohidratos", unit: "g", integer: false },
  { key: "fat_g_target", label: "Grasas", unit: "g", integer: false },
] as const;

const values = ref<Record<string, string | number>>(
  Object.fromEntries(
    fields.map((f) => [f.key, props.goals?.[f.key] != null ? String(props.goals[f.key]) : ""]),
  ),
);

const error = ref<string | null>(null);
const saving = ref(false);

function normalizedValue(key: string): string {
  return String(values.value[key] ?? "").trim();
}

async function submit() {
  error.value = null;
  const payload: Partial<NutritionGoals> = {};
  for (const f of fields) {
    const raw = normalizedValue(f.key);
    if (raw === "") {
      payload[f.key] = null;
      continue;
    }
    const num = f.integer ? Math.round(Number(raw)) : Number(raw);
    if (!Number.isFinite(num) || num < 0) {
      error.value = `"${f.label}" debe ser un número válido.`;
      return;
    }
    payload[f.key] = num;
  }
  saving.value = true;
  try {
    await foodApi.updateNutritionGoals(payload);
    emit("saved");
  } catch (e) {
    error.value =
      e instanceof ApiRequestError ? e.message : "No se pudieron guardar los objetivos.";
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <Modal title="Objetivos nutricionales" @close="emit('close')">
    <form class="space-y-4" @submit.prevent="submit">
      <div class="grid grid-cols-2 gap-3">
        <div v-for="f in fields" :key="f.key">
          <label class="mb-1 block text-xs font-medium text-slate-500">
            {{ f.label }} ({{ f.unit }})
          </label>
          <input
            v-model="values[f.key]"
            type="number"
            min="0"
            :step="f.integer ? '1' : 'any'"
            placeholder="—"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
          />
        </div>
      </div>
      <p class="text-xs text-slate-500">
        Si quieres quitar un objetivo, deja su campo vacío.
      </p>

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
