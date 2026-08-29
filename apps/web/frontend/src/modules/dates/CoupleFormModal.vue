<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ApiRequestError } from "../../api/client";
import { datesApi } from "../../api/dates";
import { usersApi } from "../../api/users";
import IconButton from "../../components/IconButton.vue";
import Modal from "../../components/Modal.vue";
import { icons } from "../../lib/icons";
import type {
  DateCouple,
  DateMilestone,
  DateMilestoneType,
  DateRelationStatus,
} from "../../types";
const props = defineProps<{ couple?: DateCouple | null }>();
const emit = defineEmits<{ close: []; saved: [] }>();

const isEdit = props.couple != null;

const members = ref<number[]>(props.couple?.member_ids ?? []);
const startedAt = ref(props.couple?.started_at ?? "");
const relationshipStatus = ref<DateRelationStatus>(
  props.couple?.relationship_status ?? "couple",
);
const archived = ref(props.couple?.status === "archived");
const userOptions = ref<{ id: number; name: string }[]>([]);

const error = ref<string | null>(null);
const saving = ref(false);

const milestones = ref<DateMilestone[]>([]);
const milestoneType = ref<DateMilestoneType>("monthly");
const milestoneDate = ref("");
const milestoneLabel = ref("");
const milestoneNotes = ref("");
const milestoneError = ref<string | null>(null);

const milestoneTypeLabels: Record<DateMilestoneType, string> = {
  monthly: "Cumple-mes",
  anniversary: "Aniversario",
  wedding: "Boda",
  custom: "Personalizado",
};

function toggleMember(id: number) {
  if (members.value.includes(id)) {
    members.value = members.value.filter((m) => m !== id);
  } else {
    members.value = [...members.value, id];
  }
}

async function loadMilestones() {
  if (!props.couple) return;
  try {
    milestones.value = await datesApi.listMilestones(props.couple.id);
  } catch {
    milestones.value = [];
  }
}

async function submit() {
  error.value = null;

  if (members.value.length === 0) {
    error.value = "Selecciona al menos un miembro.";
    return;
  }

  saving.value = true;
  try {
    const payload = {
      member_ids: members.value,
      started_at: startedAt.value || null,
      relationship_status: relationshipStatus.value,
      ...(isEdit ? { status: archived.value ? ("archived" as const) : ("active" as const) } : {}),
    };
    if (props.couple) {
      await datesApi.updateCouple(props.couple.id, payload);
    } else {
      await datesApi.createCouple(payload);
    }
    emit("saved");
  } catch (e) {
    error.value = e instanceof ApiRequestError ? e.message : "Error inesperado al guardar.";
  } finally {
    saving.value = false;
  }
}

async function addMilestone() {
  milestoneError.value = null;
  if (!props.couple) return;
  if (!milestoneDate.value) {
    milestoneError.value = "Indica la fecha del hito.";
    return;
  }
  if (!milestoneLabel.value.trim()) {
    milestoneError.value = "Indica una etiqueta para el hito.";
    return;
  }
  try {
    await datesApi.createMilestone(props.couple.id, {
      type: milestoneType.value,
      date: milestoneDate.value,
      label: milestoneLabel.value.trim(),
      notes: milestoneNotes.value || null,
    });
    milestoneType.value = "monthly";
    milestoneDate.value = "";
    milestoneLabel.value = "";
    milestoneNotes.value = "";
    await loadMilestones();
  } catch (e) {
    milestoneError.value =
      e instanceof ApiRequestError ? e.message : "No se pudo añadir el hito.";
  }
}

async function deleteMilestone(id: number) {
  try {
    await datesApi.deleteMilestone(id);
    await loadMilestones();
  } catch {
    milestoneError.value = "No se pudo eliminar el hito.";
  }
}

onMounted(async () => {
  try {
    const users = await usersApi.list();
    userOptions.value = users.map((u) => ({ id: u.id, name: u.name }));
  } catch {
    userOptions.value = [];
  }
  await loadMilestones();
});
</script>

<template>
  <Modal :title="isEdit ? 'Editar pareja' : 'Nueva pareja'" @close="emit('close')">
    <form class="space-y-4" @submit.prevent="submit">
      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">Miembros</label>
        <p v-if="userOptions.length === 0" class="text-xs text-slate-400">
          No hay usuarios activos disponibles.
        </p>
        <ul v-else class="space-y-1">
          <li v-for="u in userOptions" :key="u.id">
            <label
              class="flex cursor-pointer items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 transition-colors hover:bg-slate-50"
              :class="members.includes(u.id) ? 'border-slate-400 bg-slate-50' : ''"
            >
              <input
                type="checkbox"
                class="h-4 w-4 rounded border-slate-300 accent-slate-900"
                :checked="members.includes(u.id)"
                @change="toggleMember(u.id)"
              />
              {{ u.name }}
            </label>
          </li>
        </ul>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">Inicio (opcional)</label>
          <input
            v-model="startedAt"
            type="date"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
          />
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">Estado</label>
          <select
            v-model="relationshipStatus"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
          >
            <option value="couple">Pareja</option>
            <option value="married">Casados</option>
          </select>
        </div>
      </div>

      <label
        v-if="isEdit"
        class="flex cursor-pointer items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700"
      >
        <input
          v-model="archived"
          type="checkbox"
          class="h-4 w-4 rounded border-slate-300 accent-slate-900"
        />
        Archivar pareja (se oculta del flujo normal)
      </label>

      <div v-if="isEdit" class="border-t border-slate-100 pt-3">
        <p class="mb-2 text-xs font-medium text-slate-500">Hitos</p>
        <ul v-if="milestones.length" class="space-y-1">
          <li
            v-for="m in milestones"
            :key="m.id"
            class="flex items-center justify-between gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm"
          >
            <span class="min-w-0">
              <span class="block truncate font-medium text-slate-800">
                {{ m.label }}
              </span>
              <span class="block text-xs text-slate-500">
                {{ milestoneTypeLabels[m.type] }} · {{ m.date }}
              </span>
            </span>
            <IconButton
              :icon="icons.trash"
              label="Eliminar hito"
              variant="danger"
              @click="deleteMilestone(m.id)"
            />
          </li>
        </ul>
        <p v-else class="mb-2 text-xs text-slate-400">Sin hitos aún.</p>

        <div class="mt-2 space-y-2 rounded-lg bg-slate-50 p-3">
          <div class="grid grid-cols-2 gap-2">
            <select
              v-model="milestoneType"
              class="rounded-lg border border-slate-200 px-2.5 py-1.5 text-sm outline-none"
            >
              <option v-for="(label, value) in milestoneTypeLabels" :key="value" :value="value">
                {{ label }}
              </option>
            </select>
            <input
              v-model="milestoneDate"
              type="date"
              class="rounded-lg border border-slate-200 px-2.5 py-1.5 text-sm outline-none"
            />
          </div>
          <input
            v-model="milestoneLabel"
            type="text"
            placeholder="Etiqueta del hito"
            class="w-full rounded-lg border border-slate-200 px-2.5 py-1.5 text-sm outline-none"
          />
          <input
            v-model="milestoneNotes"
            type="text"
            placeholder="Notas (opcional)"
            class="w-full rounded-lg border border-slate-200 px-2.5 py-1.5 text-sm outline-none"
          />
          <p v-if="milestoneError" class="text-xs text-red-600">{{ milestoneError }}</p>
          <button
            type="button"
            class="inline-flex items-center gap-1 rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-slate-700"
            @click="addMilestone"
          >
            Añadir hito
          </button>
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
          {{ saving ? "Guardando\u2026" : isEdit ? "Guardar" : "Crear" }}
        </button>
      </div>
    </form>
  </Modal>
</template>
