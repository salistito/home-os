<script setup lang="ts">
import { computed, ref } from "vue";
import { ApiRequestError } from "../../api/client";
import { foodApi } from "../../api/food";
import Icon from "../../components/Icon.vue";
import IconButton from "../../components/IconButton.vue";
import Modal from "../../components/Modal.vue";
import WidgetCard from "../../components/WidgetCard.vue";
import { tagColorByString } from "../../lib/colors";
import { icons } from "../../lib/icons";
import { pushToast } from "../../lib/toast";
import type { Ingredient } from "../../types";
import IngredientFormModal from "./IngredientFormModal.vue";

const props = defineProps<{ ingredients: Ingredient[] }>();
const emit = defineEmits<{ reload: [] }>();

const formOpen = ref(false);
const editing = ref<Ingredient | null>(null);
const importMode = ref(false);

const deleting = ref<Ingredient | null>(null);
const deleteBusy = ref(false);

const sortBy = ref<"name" | "category" | "unit" | "macros">("name");
const sortDesc = ref(false);

const sorted = computed(() => {
  const dir = sortDesc.value ? -1 : 1;
  return [...props.ingredients].sort((a, b) => {
    let cmp = 0;
    switch (sortBy.value) {
      case "name":
        cmp = a.name.localeCompare(b.name, undefined, { sensitivity: "base" });
        break;
      case "category": {
        const ca = a.category ?? "";
        const cb = b.category ?? "";
        if (ca && cb) {
          cmp = ca.localeCompare(cb, undefined, { sensitivity: "base" });
        } else if (ca) {
          cmp = -dir;
        } else if (cb) {
          cmp = dir;
        } else {
          cmp = 0;
        }
        break;
      }
      case "unit":
        cmp = a.unit.localeCompare(b.unit);
        break;
      case "macros":
        cmp = a.macros.kcal - b.macros.kcal;
        break;
    }
    return cmp * dir;
  });
});

function setSort(col: "name" | "category" | "unit" | "macros") {
  if (sortBy.value === col) {
    sortDesc.value = !sortDesc.value;
  } else {
    sortBy.value = col;
    sortDesc.value = false;
  }
}

function openCreate() {
  editing.value = null;
  importMode.value = false;
  formOpen.value = true;
}

function openImport() {
  editing.value = null;
  importMode.value = true;
  formOpen.value = true;
}

function openEdit(ing: Ingredient) {
  editing.value = ing;
  importMode.value = false;
  formOpen.value = true;
}

async function onSaved() {
  const wasEdit = editing.value != null;
  formOpen.value = false;
  editing.value = null;
  emit("reload");
  pushToast(wasEdit ? "Ingrediente actualizado" : "Ingrediente creado");
}

function askDelete(ing: Ingredient) {
  deleting.value = ing;
}

async function confirmDelete() {
  if (!deleting.value) return;
  deleteBusy.value = true;
  try {
    await foodApi.deleteIngredient(deleting.value.id);
    deleting.value = null;
    emit("reload");
    pushToast("Ingrediente eliminado");
  } catch (e) {
    pushToast(
      e instanceof ApiRequestError ? e.message : "No se pudo eliminar el ingrediente.",
      "error",
    );
  } finally {
    deleteBusy.value = false;
  }
}

function macrosSummary(macros: { serving_amount: number; serving_unit: string, kcal: number; protein_g: number; carbs_g: number; fat_g: number; fiber_g: number; }): string {
  return `${macros.serving_amount}${macros.serving_unit} | ${macros.kcal}kcal · ${macros.protein_g}P · ${macros.carbs_g}C · ${macros.fat_g}G · ${macros.fiber_g}F`;
}
</script>

<template>
  <WidgetCard title="Ingredientes" :count="ingredients.length">
    <template #actions>
      <button
        type="button"
        class="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-50"
        @click="openImport"
      >
        Importar
      </button>
      <button
        type="button"
        class="inline-flex items-center gap-1 rounded-lg bg-slate-900 px-2.5 py-1.5 text-xs font-medium text-white transition-colors hover:bg-slate-700"
        @click="openCreate"
      >
        <Icon :path="icons.plus" :size="14" />
        Nuevo
      </button>
    </template>

    <p
      v-if="!ingredients.length"
      class="px-4 py-10 text-center text-sm text-slate-500"
    >
      Todavía no hay ingredientes registrados.
    </p>

    <div v-else>
      <div class="flex items-center gap-2 px-4 py-3 sm:hidden">
        <select
          v-model="sortBy"
          class="rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs text-slate-700 outline-none focus:border-slate-400"
        >
          <option value="name">Ingrediente</option>
          <option value="category">Categoría</option>
          <option value="unit">Unidad</option>
          <option value="macros">Macros</option>
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
        class="hidden grid-cols-[1fr_8rem_6rem_1fr_2.25rem] items-center gap-3 border-b border-slate-100 bg-slate-50/60 px-4 py-2 text-xs font-semibold tracking-wider text-slate-400 sm:grid"
      >
        <button type="button" class="flex items-center gap-1 text-left" @click="setSort('name')">
          Ingrediente
          <span v-if="sortBy === 'name'">{{ sortDesc ? "↓" : "↑" }}</span>
        </button>
        <button type="button" class="flex items-center gap-1" @click="setSort('category')">
          Categoría
          <span v-if="sortBy === 'category'">{{ sortDesc ? "↓" : "↑" }}</span>
        </button>
        <button type="button" class="flex items-center gap-1" @click="setSort('unit')">
          Unidad
          <span v-if="sortBy === 'unit'">{{ sortDesc ? "↓" : "↑" }}</span>
        </button>
        <button type="button" class="flex items-center gap-1" @click="setSort('macros')">
          Macros
          <span v-if="sortBy === 'macros'">{{ sortDesc ? "↓" : "↑" }}</span>
        </button>
      </div>

      <ul class="divide-y divide-slate-100">
        <li
          v-for="ing in sorted"
          :key="ing.id"
          class="group flex items-start gap-3 px-4 py-3 transition-colors hover:bg-slate-50 sm:grid sm:grid-cols-[1fr_8rem_6rem_1fr_2.25rem] sm:items-center sm:py-2.5"
        >
          <div class="min-w-0 flex-1 sm:contents">
            <span class="block truncate text-[13px] font-medium text-slate-800">
              {{ ing.name }}
            </span>

            <div class="mt-1.5 flex flex-wrap items-center gap-1.5 sm:contents">
              <span
                v-if="ing.category"
                class="inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium sm:justify-self-start"
                :class="[tagColorByString(ing.category).bg, tagColorByString(ing.category).text]"
              >
                {{ ing.category }}
              </span>
              <span v-else class="hidden text-xs text-slate-400 sm:inline sm:ml-6.5">—</span>

              <span class="inline-flex items-center gap-1 rounded-md border border-slate-200 px-2 py-0.5 text-xs text-slate-600 sm:justify-self-start">
                <Icon :path="icons.measuringCup" :size="12" class="shrink-0 text-slate-400" />
                {{ ing.unit }}
              </span>

              <span class="text-xs text-slate-600 sm:justify-self-start">
                {{ macrosSummary(ing.macros) }}
              </span>
            </div>
          </div>
          <span
            class="flex shrink-0 items-center justify-end gap-0.5 transition-opacity sm:opacity-0 sm:group-hover:opacity-100"
          >
            <IconButton :icon="icons.pencil" label="Editar" @click="openEdit(ing)" />
            <IconButton :icon="icons.trash" label="Eliminar" variant="danger" @click="askDelete(ing)" />
          </span>
        </li>
      </ul>
    </div>
  </WidgetCard>

  <IngredientFormModal
    v-if="formOpen"
    :ingredient="editing"
    :import-mode="importMode"
    @close="formOpen = false"
    @saved="onSaved"
  />

  <Modal v-if="deleting" title="Eliminar ingrediente" @close="deleting = null">
    <p class="text-sm text-slate-600">
      ¿Seguro que quieres eliminar
      <span class="font-medium text-slate-900">{{ deleting.name }}</span>?
    </p>
    <p class="mt-2 text-xs text-slate-400">
      El stock del ingrediente se pondrá en 0 pero las recetas que lo utilicen seguirán existiendo.
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
