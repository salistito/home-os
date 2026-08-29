<script setup lang="ts">
import { computed, ref } from "vue";
import { ApiRequestError } from "../../api/client";
import { datesApi } from "../../api/dates";
import DateInput from "../../components/DateInput.vue";
import Icon from "../../components/Icon.vue";
import Modal from "../../components/Modal.vue";
import SelectMenu from "../../components/SelectMenu.vue";
import { getToday } from "../../lib/date";
import { icons } from "../../lib/icons";
import type { DateCouple, DateEvent } from "../../types";

const props = defineProps<{
  event?: DateEvent | null;
  couples: DateCouple[];
  memberNames: Record<number, string>;
}>();
const emit = defineEmits<{ close: []; saved: [] }>();

const isEdit = props.event != null;

const coupleId = ref<string>(props.event ? String(props.event.couple_id) : "");
const weekStart = ref(props.event?.week_start ?? getToday());
const title = ref(props.event?.title ?? "");
const scheduledDate = ref(props.event?.scheduled_date ?? "");
const scheduledTime = ref(props.event?.scheduled_time ?? "");
const plannedBy = ref<string>(props.event ? String(props.event.planned_by) : "auto");

interface AttributeRow {
  key: string;
  value: string;
  is_secret: boolean;
  reveal_on: string;
}
const attributes = ref<AttributeRow[]>(
  props.event?.attributes.map((a) => ({
    key: a.key,
    value: a.value,
    is_secret: a.is_secret,
    reveal_on: a.reveal_on ? (a.reveal_on.length === 10 ? `${a.reveal_on}T00:00` : a.reveal_on) : "",
  })) ?? [],
);

const error = ref<string | null>(null);
const saving = ref(false);

function coupleDisplayName(couple: DateCouple): string {
  const names = couple.member_ids
    .map((id) => props.memberNames[id] ?? `#${id}`)
    .filter(Boolean);
  return names.length ? names.join(" & ") : `Pareja #${couple.id}`;
}

const coupleOptions = computed(() =>
  props.couples.map((c) => ({ value: String(c.id), label: coupleDisplayName(c) })),
);

const plannerOptions = computed(() => {
  const couple = props.couples.find((c) => String(c.id) === coupleId.value);
  const members =
    couple?.member_ids.map((id) => ({ value: String(id), label: `Miembro #${id}` })) ?? [];
  return [{ value: "auto", label: "Automático (turno)" }, ...members];
});

function addAttribute() {
  attributes.value = [...attributes.value, { key: "", value: "", is_secret: false, reveal_on: "" }];
}

function removeAttribute(index: number) {
  attributes.value = attributes.value.filter((_, i) => i !== index);
}

function updateAttribute(index: number, field: keyof AttributeRow, value: string | boolean) {
  attributes.value = attributes.value.map((a, i) =>
    i === index ? { ...a, [field]: value } : a,
  );
}

function buildPayload() {
  const attrs = attributes.value
    .filter((a) => a.key.trim() !== "")
    .map((a) => ({
      key: a.key.trim(),
      value: a.value,
      is_secret: a.is_secret,
      reveal_on: a.is_secret ? a.reveal_on || null : null,
    }));

  return {
    couple_id: Number(coupleId.value),
    week_start: weekStart.value,
    planned_by: plannedBy.value === "auto" ? null : Number(plannedBy.value),
    title: title.value.trim() || null,
    scheduled_date: scheduledDate.value || null,
    scheduled_time: scheduledTime.value || null,
    attributes: attrs,
  };
}

async function submit() {
  error.value = null;

  if (!coupleId.value) {
    error.value = "Selecciona una pareja.";
    return;
  }
  if (!weekStart.value) {
    error.value = "La fecha de la semana es obligatoria.";
    return;
  }

  saving.value = true;
  try {
    if (props.event) {
      const { couple_id, week_start, ...rest } = buildPayload();
      await datesApi.updateEvent(props.event.id, rest);
    } else {
      await datesApi.createEvent(buildPayload());
    }
    emit("saved");
  } catch (e) {
    error.value = e instanceof ApiRequestError ? e.message : "Error inesperado al guardar.";
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <Modal :title="isEdit ? 'Editar cita' : 'Nueva cita'" size="lg" @close="emit('close')">
    <form class="space-y-4" @submit.prevent="submit">
      <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">Pareja</label>
          <SelectMenu
            v-model="coupleId"
            :options="coupleOptions"
            placeholder="Seleccionar pareja"
          />
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">Inicio de semana</label>
          <DateInput v-model="weekStart" />
        </div>
      </div>

      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">Título (Opcional)</label>
        <input
          v-model="title"
          type="text"
          placeholder="Cena romántica"
          class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
        />
      </div>

      <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">Fecha de la cita (Opcional)</label>
          <DateInput v-model="scheduledDate" />
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">Hora (Opcional)</label>
          <input
            v-model="scheduledTime"
            type="time"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
          />
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">Quién planea</label>
          <SelectMenu v-model="plannedBy" :options="plannerOptions" />
        </div>
      </div>

      <div>
        <div class="mb-1 flex items-center justify-between">
          <label class="block text-xs font-medium text-slate-500">Detalles (Opcional)</label>
          <button
            type="button"
            class="inline-flex items-center gap-1 text-xs font-medium text-slate-600 transition-colors hover:text-slate-900"
            @click="addAttribute"
          >
            <Icon :path="icons.plus" :size="12" />
            Añadir
          </button>
        </div>

        <div v-if="attributes.length === 0" class="text-xs text-slate-400">
          Lugar, vestimenta, vibra… y opcionalmente secretos para sorprender.
        </div>

        <ul v-else class="space-y-2">
          <li
            v-for="(attr, index) in attributes"
            :key="index"
            class="rounded-lg border border-slate-200 p-2"
          >
            <div class="grid grid-cols-1 gap-2 sm:grid-cols-[8rem_1fr_auto]">
              <input
                :value="attr.key"
                type="text"
                placeholder="place / dresscode / vibes"
                class="w-full rounded-lg border border-slate-200 px-2 py-1.5 text-sm text-slate-800 outline-none focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
                @input="updateAttribute(index, 'key', ($event.target as HTMLInputElement).value)"
              />
              <input
                :value="attr.value"
                type="text"
                placeholder="Valor"
                class="w-full rounded-lg border border-slate-200 px-2 py-1.5 text-sm text-slate-800 outline-none focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
                @input="updateAttribute(index, 'value', ($event.target as HTMLInputElement).value)"
              />
              <button
                type="button"
                class="self-center rounded-md p-1.5 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-600"
                aria-label="Quitar"
                @click="removeAttribute(index)"
              >
                <Icon :path="icons.trash" :size="14" />
              </button>
            </div>
            <div class="mt-2 flex flex-wrap items-center gap-3">
              <label class="flex cursor-pointer items-center gap-1.5 text-xs text-slate-600">
                <input
                  type="checkbox"
                  class="h-3.5 w-3.5 rounded border-slate-300 accent-slate-900"
                  :checked="attr.is_secret"
                  @change="updateAttribute(index, 'is_secret', ($event.target as HTMLInputElement).checked)"
                />
                Secreto
              </label>
              <input
                v-if="attr.is_secret"
                :value="attr.reveal_on"
                type="datetime-local"
                class="rounded-lg border border-slate-200 px-2 py-1 text-xs text-slate-800 outline-none focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
                @input="updateAttribute(index, 'reveal_on', ($event.target as HTMLInputElement).value)"
              />
              <span v-if="attr.is_secret" class="text-xs text-slate-400">
                Deja vacío para revelarlo en persona.
              </span>
            </div>
          </li>
        </ul>
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