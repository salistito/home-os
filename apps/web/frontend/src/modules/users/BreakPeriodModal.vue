<script setup lang="ts">
import { computed, ref } from "vue";
import { breakPeriodsApi } from "../../api/breaks";
import { ApiRequestError } from "../../api/client";
import DateInput from "../../components/DateInput.vue";
import Icon from "../../components/Icon.vue";
import Modal from "../../components/Modal.vue";
import { auth } from "../../lib/auth";
import { breakModuleHint } from "../../lib/breaks";
import { getToday } from "../../lib/date";
import { breakModules, modules, type ModuleId } from "../../modules";
import type { BreakPeriod, UpdateBreakPeriodPayload, UserRef } from "../../types";

const props = defineProps<{ users: UserRef[]; breakPeriod?: BreakPeriod | null }>();
const emit = defineEmits<{ close: []; saved: [] }>();

const isEdit = computed(() => props.breakPeriod != null);

const label = ref(props.breakPeriod?.label ?? "");
const startDate = ref(props.breakPeriod?.start_date ?? getToday());
const endDate = ref(props.breakPeriod?.end_date ?? "");
const selectedUsers = ref<Set<number>>(
  new Set(props.breakPeriod?.user_ids ?? (auth.userId.value == null ? [] : [auth.userId.value])),
);
const selectedModules = ref<Set<ModuleId>>(
  new Set(props.breakPeriod?.modules ?? breakModules.map((m) => m.id)),
);

const error = ref<string | null>(null);
const saving = ref(false);

const activeUsers = computed(() =>
  props.users.filter((u) => u.deleted_at === null),
);

const selectableModules = computed(() =>
  modules.filter((m) => m.canBeInBreak === true || selectedModules.value.has(m.id)),
);

function toggleUser(id: number) {
  const next = new Set(selectedUsers.value);
  if (next.has(id)) {
    next.delete(id);
  } else {
    next.add(id);
  }
  selectedUsers.value = next;
}

function toggleModule(module: ModuleId) {
  const next = new Set(selectedModules.value);
  if (next.has(module)) {
    next.delete(module);
  } else {
    next.add(module);
  }
  selectedModules.value = next;
}

async function submit() {
  error.value = null;

  const trimmedLabel = label.value.trim();
  const trimmedStart = startDate.value.trim();
  const trimmedEnd = endDate.value.trim();

  if (!trimmedStart) {
    error.value = "La fecha de inicio es obligatoria.";
    return;
  }
  if (trimmedEnd && trimmedEnd < trimmedStart) {
    error.value = "La fecha de término debe ser igual o posterior a la de inicio.";
    return;
  }
  if (selectedUsers.value.size === 0) {
    error.value = "Selecciona al menos un usuario para el receso.";
    return;
  }
  if (selectedModules.value.size === 0) {
    error.value = "Selecciona al menos un módulo para el receso.";
    return;
  }

  saving.value = true;
  try {
    if (props.breakPeriod) {
      const body: Partial<UpdateBreakPeriodPayload> = {};
      if (trimmedLabel !== (props.breakPeriod.label ?? "")) {
        body.label = trimmedLabel || null;
      }
      if (trimmedStart !== props.breakPeriod.start_date) {
        body.start_date = trimmedStart;
      }
      const nextEnd = trimmedEnd || null;
      if (nextEnd !== props.breakPeriod.end_date) {
        body.end_date = nextEnd;
      }
      const nextUsers = [...selectedUsers.value].sort();
      const prevUsers = [...props.breakPeriod.user_ids].sort();
      if (nextUsers.join() !== prevUsers.join()) {
        body.user_ids = nextUsers;
      }
      const nextModules = [...selectedModules.value].sort();
      const prevModules = [...(props.breakPeriod.modules ?? [])].sort();
      if (nextModules.join() !== prevModules.join()) {
        body.modules = nextModules;
      }
      if (Object.keys(body).length === 0) {
        error.value = "No hay cambios para guardar.";
        saving.value = false;
        return;
      }
      await breakPeriodsApi.update(props.breakPeriod.id, body);
    } else {
      await breakPeriodsApi.create({
        label: trimmedLabel || undefined,
        start_date: trimmedStart,
        ...(trimmedEnd ? { end_date: trimmedEnd } : { end_date: null }),
        user_ids: [...selectedUsers.value],
        modules: [...selectedModules.value],
      });
    }
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
  <Modal
    :title="isEdit ? 'Editar periodo de receso' : 'Nuevo periodo de receso'"
    @close="emit('close')"
  >
    <form class="space-y-4" @submit.prevent="submit">
      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">Etiqueta (Opcional)</label>
        <input
          v-model="label"
          type="text"
          placeholder="Vacaciones de verano"
          class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
        />
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">Fecha de inicio</label>
          <DateInput v-model="startDate" />
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">Fecha de término (Opcional)</label>
          <DateInput v-model="endDate" :min="startDate" />
          <p class="mt-1 text-xs text-slate-400">
            Si se deja vacío, el receso se aplicará de forma indefinida.
          </p>
        </div>
      </div>

      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">
          Usuarios en receso
        </label>
        <div class="max-h-48 space-y-1 overflow-y-auto rounded-lg border border-slate-200 p-2">
          <label
            v-for="user in activeUsers"
            :key="user.id"
            class="flex cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 text-sm text-slate-700 transition-colors hover:bg-slate-50"
          >
            <input
              type="checkbox"
              class="h-4 w-4 rounded border-slate-300 text-amber-500 focus:ring-amber-200"
              :checked="selectedUsers.has(user.id)"
              @change="toggleUser(user.id)"
            />
            {{ user.name }}
          </label>
          <p v-if="activeUsers.length === 0" class="px-2 py-1 text-xs text-slate-400">
            No hay usuarios activos.
          </p>
        </div>
      </div>

      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">Módulos en receso</label>
        <div class="grid grid-cols-1 gap-1.5">
          <label
            v-for="module in selectableModules"
            :key="module.id"
            class="flex cursor-pointer gap-2 rounded-md border border-slate-200 px-3 py-2 transition-colors hover:bg-slate-50"
          >
            <input
              type="checkbox"
              class="mt-0.5 h-4 w-4 shrink-0 rounded border-slate-300 text-amber-500 focus:ring-amber-200"
              :checked="selectedModules.has(module.id)"
              @change="toggleModule(module.id)"
            />
            <span class="min-w-0">
              <span class="flex items-center gap-2 text-sm text-slate-700">
                <Icon :path="module.icon" :size="14" class="shrink-0 text-slate-500" />
                {{ module.label }}
              </span>
              <span class="mt-0.5 block text-xs text-slate-400">
                {{ module.canBeInBreak ? breakModuleHint(module.id) : "Este módulo no es elegible para receso." }}
              </span>
            </span>
          </label>
        </div>
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
          {{ saving ? "Guardando…" : isEdit ? "Guardar" : "Crear" }}
        </button>
      </div>
    </form>
  </Modal>
</template>