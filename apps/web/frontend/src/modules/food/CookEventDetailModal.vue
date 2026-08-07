<script setup lang="ts">
import Icon from "../../components/Icon.vue";
import Modal from "../../components/Modal.vue";
import { cookEventPortions } from "../../lib/food";
import { formatDate } from "../../lib/format";
import { icons } from "../../lib/icons";
import type { CookEvent } from "../../types";
import IngredientListRow from "./IngredientListRow.vue";
import MacroGrid from "./MacroGrid.vue";

const props = defineProps<{
  event: CookEvent;
  name: string;
  chefColor: { bg: string; text: string; ring: string };
  cutoffDate: string;
}>();
const emit = defineEmits<{ close: [] }>();

const portions = cookEventPortions(props.event, props.cutoffDate);
</script>

<template>
  <Modal :title="name" @close="emit('close')">
    <div class="space-y-4">
      <div class="space-y-2">
        <div class="flex items-center gap-3">
          <span class="w-16 shrink-0 text-xs text-slate-500">Chef:</span>
          <span
            class="inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium ring-1"
            :class="[chefColor.bg, chefColor.text, chefColor.ring]"
          >
            <Icon :path="icons.users" :size="12" />
            {{ event.user_name }}
          </span>
        </div>
        <div class="flex items-center gap-3">
          <span class="w-16 shrink-0 text-xs text-slate-500">Porciones:</span>
          <span
            class="inline-flex items-center gap-1 rounded-md bg-slate-50 px-2 py-0.5 text-xs tabular-nums text-slate-700 ring-1 ring-slate-200"
          >
            <Icon :path="icons.pot" :size="12" class="shrink-0 text-slate-400" />
            {{ event.portions }} porc. {{ event.portions === 1 ? "cocinada" : "cocinadas" }}
          </span>
        </div>
        <div class="flex items-center gap-3">
          <span class="w-16 shrink-0 text-xs text-slate-500">Estado:</span>
          <span
            class="inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium"
            :class="portions.classes"
          >
            <Icon v-if="portions.icon" :path="portions.icon" :size="12" class="shrink-0" />
            {{ portions.label }}<template v-if="portions.label.includes('porc.')">
              {{ portions.label === "1 porc." ? "disponible" : "disponibles" }}
            </template>
          </span>
        </div>
        <div class="flex items-center gap-3">
          <span class="w-16 shrink-0 text-xs text-slate-500">Fecha:</span>
          <span
            class="inline-flex items-center gap-1 rounded-md bg-slate-50 px-2 py-0.5 text-xs tabular-nums text-slate-700 ring-1 ring-slate-200"
          >
            <Icon :path="icons.calendar" :size="12" class="shrink-0 text-slate-400" />
            {{ formatDate(event.cooked_at) }}
          </span>
        </div>
      </div>

      <div v-if="event.macros">
        <h4 class="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
          Macros por porción
        </h4>
        <MacroGrid :macros="event.macros" />
      </div>

      <div v-if="event.ingredients.length">
        <h4 class="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
          Ingredientes utilizados
        </h4>
        <ul class="divide-y divide-slate-100 rounded-lg border border-slate-100">
          <IngredientListRow
            v-for="ing in event.ingredients"
            :key="ing.id"
            :name="ing.ingredient_name"
            :quantity="ing.quantity"
            :unit="ing.unit"
            :macros="ing.macros"
          />
        </ul>
      </div>

      <div class="flex justify-end pt-2">
        <button
          type="button"
          class="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100"
          @click="emit('close')"
        >
          Cerrar
        </button>
      </div>
    </div>
  </Modal>
</template>
