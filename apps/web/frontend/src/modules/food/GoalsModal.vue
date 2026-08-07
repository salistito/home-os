<script setup lang="ts">
import { computed, ref } from "vue";
import { ApiRequestError } from "../../api/client";
import { foodApi } from "../../api/food";
import Modal from "../../components/Modal.vue";
import type { NutritionGoals } from "../../types";

const props = defineProps<{ goals: NutritionGoals | null }>();
const emit = defineEmits<{ close: []; saved: [] }>();

const showRecommendations = ref(false);
const selectedPreset = ref(0);

const presets = [
  { name: "Alta en proteína", label: "35/40/25", protein: 0.35, carbs: 0.4, fat: 0.25 },
  { name: "Equilibrada", label: "30/40/30", protein: 0.3, carbs: 0.4, fat: 0.3 },
  { name: "Alta en carbos", label: "20/50/30", protein: 0.2, carbs: 0.5, fat: 0.3 },
] as const;

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

const suggestion = computed(() => {
  const kcal = Number(normalizedValue("kcal_target"));
  if (!Number.isFinite(kcal) || kcal <= 0) return null;
  const preset = presets[selectedPreset.value];
  return {
    protein_g_target: Math.round((kcal * preset.protein) / 4),
    carbs_g_target: Math.round((kcal * preset.carbs) / 4),
    fat_g_target: Math.round((kcal * preset.fat) / 9),
  };
});

const macros = computed(() => {
  if (!suggestion.value) return null;
  return [
    { name: "Proteínas", grams: suggestion.value.protein_g_target, kcalPerGram: 4 },
    { name: "Carbohidratos", grams: suggestion.value.carbs_g_target, kcalPerGram: 4 },
    { name: "Grasas", grams: suggestion.value.fat_g_target, kcalPerGram: 9 },
  ];
});

function applySuggestion() {
  if (!suggestion.value) return;
  for (const [key, gram] of Object.entries(suggestion.value)) {
    values.value[key] = String(gram);
  }
}

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
      <p class="text-xs font-medium text-slate-700">
        Ingresa tus objetivos nutricionales de calorías y macronutrientes.
      </p>

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
        Si no quieres medir el progreso de algún objetivo, puedes dejar su campo vacío.
      </p>

      <div
        class="rounded-lg border border-amber-100 bg-amber-50 px-3 py-2 text-xs text-slate-600"
      >
        <p class="font-medium text-slate-700">Aporte calórico de macronutrientes</p>
        <div class="mt-1 space-y-1">
          <div class="flex items-center justify-between border-b border-amber-100 pb-1 last:border-0">
            <span>Proteínas</span>
            <span class="font-medium text-slate-700">4 kcal/g</span>
          </div>
          <div class="flex items-center justify-between border-b border-amber-100 pb-1 last:border-0">
            <span>Carbohidratos</span>
            <span class="font-medium text-slate-700">4 kcal/g</span>
          </div>
          <div class="flex items-center justify-between border-b border-amber-100 pb-1 last:border-0">
            <span>Grasas</span>
            <span class="font-medium text-slate-700">9 kcal/g</span>
          </div>
        </div>

        <hr class="my-2 border-amber-200" />
        
        <p v-if="!showRecommendations" class="mt-2 text-slate-500">
          ¿No sabes cuánto poner en cada macronutriente?
        </p>
        <button
          v-if="!showRecommendations"
          type="button"
          class="mt-1 w-full rounded-md border border-amber-300 bg-white px-2 py-1.5 text-xs font-medium text-amber-700 transition-colors hover:bg-amber-100"
          @click="showRecommendations = true"
        >
          Ver recomendaciones
        </button>

        <template v-if="showRecommendations">
          <p v-if="!suggestion" class="text-slate-500">
            Ingresar tu objetivo de calorías para ver las recomendaciones.
          </p>
          <template v-else>
            <p class="mb-1 font-medium text-slate-700">Tipo de dieta</p>
            <div class="grid gap-1 sm:grid-cols-3">
              <button
                v-for="(p, i) in presets"
                :key="p.name"
                type="button"
                :class="[
                  'flex flex-col items-center gap-0.5 rounded-md px-2 py-1.5 transition-colors',
                  i === selectedPreset
                    ? 'bg-slate-900 text-white'
                    : 'bg-white text-slate-600 hover:bg-slate-100',
                ]"
                @click="selectedPreset = i"
              >
                <span class="text-xs font-medium">{{ p.name }}</span>
                <span
                  :class="i === selectedPreset ? 'text-[11px] text-slate-300' : 'text-[11px] text-slate-500'"
                >
                  {{ p.label }}
                </span>
              </button>
            </div>
            <p class="mb-1 mt-3 font-medium text-slate-700">
              Desglose para {{ normalizedValue("kcal_target") }} kcal
            </p>
            <div class="space-y-1">
              <div
                v-for="m in macros"
                :key="m.name"
                class="flex items-center justify-between border-b border-amber-100 pb-1 last:border-0"
              >
                <span>{{ m.name }}</span>
                <span class="font-medium text-slate-700">
                  {{ m.grams }} g <span class="text-slate-500">({{ m.grams * m.kcalPerGram }} kcal)</span>
                </span>
              </div>
            </div>
          </template>
          <div class="mt-2 flex gap-2">
            <button
              type="button"
              class="flex-1 rounded-md border border-amber-300 bg-white px-3 py-1.5 text-xs font-medium text-amber-700 transition-colors hover:bg-amber-100"
              @click="showRecommendations = false"
            >
              Ocultar
            </button>
            <button
              v-if="suggestion"
              type="button"
              class="flex-1 rounded-md bg-amber-500 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-amber-600"
              @click="applySuggestion"
            >
              Aplicar
            </button>
          </div>
        </template>
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
