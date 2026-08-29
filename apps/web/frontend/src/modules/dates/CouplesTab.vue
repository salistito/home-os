<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ApiRequestError } from "../../api/client";
import { datesApi } from "../../api/dates";
import { usersApi } from "../../api/users";
import Icon from "../../components/Icon.vue";
import IconButton from "../../components/IconButton.vue";
import Modal from "../../components/Modal.vue";
import Skeleton from "../../components/Skeleton.vue";
import WidgetCard from "../../components/WidgetCard.vue";
import { icons } from "../../lib/icons";
import { pushToast } from "../../lib/toast";
import type { DateCouple } from "../../types";
import CoupleFormModal from "./CoupleFormModal.vue";

defineProps<{ loading: boolean }>();

defineExpose({ openCreate });

const couples = ref<DateCouple[]>([]);
const error = ref<string | null>(null);
const loadingData = ref(true);
const memberNames = ref<Record<number, string>>({});

const formOpen = ref(false);
const editing = ref<DateCouple | null>(null);
const includeArchived = ref(false);

const deleting = ref<DateCouple | null>(null);
const deleteError = ref<string | null>(null);
const deleteBusy = ref(false);

async function load() {
  try {
    const [c, u] = await Promise.all([
      datesApi.listCouples(includeArchived.value),
      usersApi.list(),
    ]);
    couples.value = c;
    memberNames.value = Object.fromEntries(u.map((x) => [x.id, x.name]));
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Error inesperado";
  } finally {
    loadingData.value = false;
  }
}

function memberLabel(couple: DateCouple): string {
  return couple.member_ids.map((id) => memberNames.value[id] ?? `#${id}`).join(", ");
}

function displayName(couple: DateCouple): string {
  const names = couple.member_ids.map((id) => memberNames.value[id] ?? `#${id}`).filter(Boolean);
  return names.length ? names.join(" & ") : "Pareja sin miembros";
}

function toggleArchived() {
  includeArchived.value = !includeArchived.value;
  load();
}

function openCreate() {
  editing.value = null;
  formOpen.value = true;
}

function openEdit(couple: DateCouple) {
  editing.value = couple;
  formOpen.value = true;
}

async function onSaved() {
  const wasEdit = editing.value != null;
  formOpen.value = false;
  await load();
  pushToast(wasEdit ? "Pareja actualizada" : "Pareja creada");
}

function askDelete(couple: DateCouple) {
  deleting.value = couple;
  deleteError.value = null;
}

async function confirmDelete() {
  if (!deleting.value) return;
  deleteBusy.value = true;
  try {
    await datesApi.deleteCouple(deleting.value.id);
    deleting.value = null;
    await load();
    pushToast("Pareja eliminada");
  } catch (e) {
    deleteError.value =
      e instanceof ApiRequestError ? e.message : "No se pudo eliminar la pareja.";
  } finally {
    deleteBusy.value = false;
  }
}

onMounted(load);
</script>

<template>
  <WidgetCard title="Parejas" :count="!loadingData && !error ? couples.length : undefined">
    <template #actions>
      <button
        type="button"
        class="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-50"
        @click="toggleArchived"
      >
        <Icon :path="includeArchived ? icons.eyeOff : icons.eye" :size="14" />
        {{ includeArchived ? "Ocultar archivadas" : "Ver archivadas" }}
      </button>
      <button
        type="button"
        class="inline-flex items-center gap-1 rounded-lg bg-slate-900 px-2.5 py-1.5 text-xs font-medium text-white transition-colors hover:bg-slate-700"
        @click="openCreate"
      >
        <Icon :path="icons.plus" :size="14" />
        Nueva pareja
      </button>
    </template>

    <p v-if="error" class="px-4 py-6 text-sm text-red-600">{{ error }}</p>

    <p
      v-else-if="!loadingData && couples.length === 0"
      class="px-4 py-10 text-center text-sm text-slate-500"
    >
      No hay parejas. Crea la primera para empezar.
    </p>

    <div v-else>
      <ul class="divide-y divide-slate-100">
        <template v-if="loadingData">
          <li
            v-for="n in 3"
            :key="n"
            class="flex items-center justify-between gap-3 px-4 py-3"
          >
            <div class="min-w-0 flex-1 space-y-1.5">
              <Skeleton width="10rem" />
              <Skeleton width="14rem" />
            </div>
            <span class="flex shrink-0 items-center gap-0.5">
              <IconButton :icon="icons.pencil" label="Editar" />
              <IconButton :icon="icons.trash" label="Eliminar" variant="danger" />
            </span>
          </li>
        </template>

        <template v-else>
          <li
            v-for="couple in couples"
            :key="couple.id"
            class="group flex items-center justify-between gap-3 px-4 py-3 transition-colors hover:bg-slate-50"
          >
            <div class="min-w-0 flex-1">
              <span class="flex items-center gap-2">
                <span class="block truncate text-[13px] font-medium text-slate-800">
                  {{ displayName(couple) }}
                </span>
                <span
                  v-if="couple.status === 'archived'"
                  class="shrink-0 rounded-full bg-slate-200 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-slate-600"
                >
                  Archivada
                </span>
              </span>
              <span class="mt-0.5 block truncate text-xs text-slate-500">
                {{ memberLabel(couple) }}
              </span>
            </div>
            <span
              class="flex shrink-0 items-center gap-0.5 transition-opacity sm:opacity-0 sm:group-hover:opacity-100"
            >
              <IconButton :icon="icons.pencil" label="Editar" @click="openEdit(couple)" />
              <IconButton
                :icon="icons.trash"
                label="Eliminar"
                variant="danger"
                @click="askDelete(couple)"
              />
            </span>
          </li>
        </template>
      </ul>
    </div>
  </WidgetCard>

  <CoupleFormModal
    v-if="formOpen"
    :couple="editing"
    @close="formOpen = false"
    @saved="onSaved"
  />

  <Modal v-if="deleting" title="Eliminar pareja" @close="deleting = null">
    <p class="text-sm text-slate-600">
      ¿Seguro que quieres eliminar la pareja
      <span class="font-medium text-slate-900">{{ deleting ? displayName(deleting) : "" }}</span>?
      También se eliminarán sus citas, hitos y recuerdos.
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