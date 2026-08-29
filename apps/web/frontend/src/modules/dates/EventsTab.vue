<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ApiRequestError } from "../../api/client";
import { datesApi } from "../../api/dates";
import { usersApi } from "../../api/users";
import Icon from "../../components/Icon.vue";
import IconButton from "../../components/IconButton.vue";
import Modal from "../../components/Modal.vue";
import SearchBar from "../../components/SearchBar.vue";
import SelectMenu from "../../components/SelectMenu.vue";
import Skeleton from "../../components/Skeleton.vue";
import WidgetCard from "../../components/WidgetCard.vue";
import { formatDate, formatWeekdayAndDayShort } from "../../lib/format";
import { icons } from "../../lib/icons";
import { pushToast } from "../../lib/toast";
import type { DateCouple, DateEvent } from "../../types";
import EventDetailModal from "./EventDetailModal.vue";
import EventFormModal from "./EventFormModal.vue";

defineProps<{ loading: boolean }>();

defineExpose({ openCreate });

const couples = ref<DateCouple[]>([]);
const events = ref<DateEvent[]>([]);
const memberNames = ref<Record<number, string>>({});
const error = ref<string | null>(null);
const loadingData = ref(true);

const searchQuery = ref("");
const coupleFilter = ref<string>("all");

const formOpen = ref(false);
const editing = ref<DateEvent | null>(null);
const detailEvent = ref<DateEvent | null>(null);

const deleting = ref<DateEvent | null>(null);
const deleteError = ref<string | null>(null);
const deleteBusy = ref(false);

const coupleOptions = computed(() => {
  const base = [{ value: "all", label: "Todas las parejas" }];
  return [
    ...base,
    ...couples.value.map((c) => ({ value: String(c.id), label: coupleDisplayName(c) })),
  ];
});

function coupleDisplayName(couple: DateCouple): string {
  const names = couple.member_ids
    .map((id) => memberNames.value[id] ?? `#${id}`)
    .filter(Boolean);
  return names.length ? names.join(" & ") : `Pareja #${couple.id}`;
}

function coupleName(id: number): string {
  const couple = couples.value.find((c) => c.id === id);
  return couple ? coupleDisplayName(couple) : `#${id}`;
}

async function load() {
  try {
    const [c, e, u] = await Promise.all([
      datesApi.listCouples(),
      datesApi.listEvents(),
      usersApi.list(),
    ]);
    couples.value = c;
    events.value = e;
    memberNames.value = Object.fromEntries(u.map((x) => [x.id, x.name]));
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Error inesperado";
  } finally {
    loadingData.value = false;
  }
}

function memberName(id: number): string {
  return memberNames.value[id] ?? `#${id}`;
}

function statusLabel(status: string): string {
  switch (status) {
    case "done":
      return "Hecha";
    case "scheduled":
      return "Programada";
    default:
      return "Por planear";
  }
}

function statusBadge(status: string): string {
  switch (status) {
    case "done":
      return "bg-green-50 text-green-700 border-green-200";
    case "scheduled":
      return "bg-blue-50 text-blue-700 border-blue-200";
    default:
      return "bg-amber-50 text-amber-700 border-amber-200";
  }
}

const filteredEvents = computed(() => {
  const term = searchQuery.value.trim().toLowerCase();
  return events.value.filter((e) => {
    if (coupleFilter.value !== "all" && String(e.couple_id) !== coupleFilter.value) {
      return false;
    }
    if (!term) return true;
    return (
      (e.title ?? "").toLowerCase().includes(term) ||
      (e.scheduled_date ?? e.week_start).toLowerCase().includes(term)
    );
  });
});

function openCreate() {
  editing.value = null;
  formOpen.value = true;
}

function openEdit(event: DateEvent) {
  editing.value = event;
  formOpen.value = true;
}

function openDetail(event: DateEvent) {
  detailEvent.value = event;
}

async function onSaved() {
  const wasEdit = editing.value != null;
  formOpen.value = false;
  await load();
  pushToast(wasEdit ? "Cita actualizada" : "Cita creada");
}

async function onCompleted() {
  detailEvent.value = null;
  await load();
  pushToast("Cita marcada como hecha");
}

function askDelete(event: DateEvent) {
  deleting.value = event;
  deleteError.value = null;
}

async function confirmDelete() {
  if (!deleting.value) return;
  deleteBusy.value = true;
  try {
    await datesApi.deleteEvent(deleting.value.id);
    deleting.value = null;
    await load();
    pushToast("Cita eliminada");
  } catch (e) {
    deleteError.value =
      e instanceof ApiRequestError ? e.message : "No se pudo eliminar la cita.";
  } finally {
    deleteBusy.value = false;
  }
}

onMounted(load);
</script>

<template>
  <WidgetCard title="Citas" :count="!loadingData && !error ? events.length : undefined">
    <template #filter>
      <SearchBar v-model="searchQuery" placeholder="Buscar cita…" />
      <SelectMenu
        v-model="coupleFilter"
        :options="coupleOptions"
        class="w-44 shrink-0"
      />
    </template>

    <p v-if="error" class="px-4 py-6 text-sm text-red-600">{{ error }}</p>

    <p
      v-else-if="!loadingData && events.length === 0"
      class="px-4 py-10 text-center text-sm text-slate-500"
    >
      No hay citas. Crea la primera para empezar.
    </p>

    <div v-else>
      <ul class="divide-y divide-slate-100">
        <template v-if="loadingData">
          <li
            v-for="n in 4"
            :key="n"
            class="flex items-start gap-3 px-4 py-3"
          >
            <div class="min-w-0 flex-1 space-y-1.5">
              <Skeleton width="12rem" />
              <Skeleton width="8rem" />
            </div>
            <span class="flex shrink-0 items-center gap-0.5">
              <IconButton :icon="icons.eye" label="Ver detalle" />
              <IconButton :icon="icons.pencil" label="Editar" />
              <IconButton :icon="icons.trash" label="Eliminar" variant="danger" />
            </span>
          </li>
        </template>

        <template v-else>
          <li
            v-for="event in filteredEvents"
            :key="event.id"
            class="group flex items-start gap-3 px-4 py-3 transition-colors hover:bg-slate-50"
          >
            <div class="min-w-0 flex-1">
              <div class="flex flex-wrap items-center gap-2">
                <span
                  class="block truncate text-[13px] font-medium text-slate-800"
                >
                  {{ event.title ?? `Cita del ${formatWeekdayAndDayShort(event.week_start)}` }}
                </span>
                <span
                  class="inline-flex items-center rounded-md border px-2 py-0.5 text-xs"
                  :class="statusBadge(event.status)"
                >
                  {{ statusLabel(event.status) }}
                </span>
              </div>

              <div class="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500">
                <span class="inline-flex items-center gap-1">
                  <Icon :path="icons.users" :size="12" class="shrink-0 text-slate-400" />
                  {{ coupleName(event.couple_id) }}
                </span>
                <span class="inline-flex items-center gap-1">
                  <Icon :path="icons.calendar" :size="12" class="shrink-0 text-slate-400" />
                  {{ formatDate(event.scheduled_date ?? event.week_start) }}
                  <template v-if="event.scheduled_time">· {{ event.scheduled_time }}</template>
                </span>
                <span class="inline-flex items-center gap-1">
                  <Icon :path="icons.star" :size="12" class="shrink-0 text-slate-400" />
                  Planea: {{ memberName(event.planned_by) }}
                </span>
              </div>
            </div>

            <span
              class="flex shrink-0 items-center gap-0.5 transition-opacity sm:opacity-0 sm:group-hover:opacity-100"
            >
              <IconButton :icon="icons.eye" label="Ver detalle" @click="openDetail(event)" />
              <IconButton :icon="icons.pencil" label="Editar" @click="openEdit(event)" />
              <IconButton
                :icon="icons.trash"
                label="Eliminar"
                variant="danger"
                @click="askDelete(event)"
              />
            </span>
          </li>
        </template>
      </ul>
    </div>
  </WidgetCard>

  <EventFormModal
    v-if="formOpen"
    :event="editing"
    :couples="couples"
    :member-names="memberNames"
    @close="formOpen = false"
    @saved="onSaved"
  />

  <EventDetailModal
    v-if="detailEvent"
    :event="detailEvent"
    :member-names="memberNames"
    @close="detailEvent = null"
    @updated="detailEvent = $event"
    @completed="onCompleted"
  />

  <Modal v-if="deleting" title="Eliminar cita" @close="deleting = null">
    <p class="text-sm text-slate-600">
      ¿Seguro que quieres eliminar la cita del
      <span class="font-medium text-slate-900">
        {{ formatDate(deleting.scheduled_date ?? deleting.week_start) }}
      </span>
      de {{ coupleName(deleting.couple_id) }}?
    </p>
    <p v-if="deleteError" class="mt-3 text-sm text-red-600">{{ deleteError }}</p>
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
        {{ deleteBusy ? "Eliminando\u2026" : "Eliminar" }}
      </button>
    </div>
  </Modal>
</template>