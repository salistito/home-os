<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { ApiRequestError } from "../../api/client";
import { financesApi } from "../../api/finances";
import { usersApi } from "../../api/users";
import Button from "../../components/Button.vue";
import Icon from "../../components/Icon.vue";
import Modal from "../../components/Modal.vue";
import MoneyVisibilityToggle from "../../components/MoneyVisibilityToggle.vue";
import Skeleton from "../../components/Skeleton.vue";
import { auth } from "../../lib/auth";
import { color, colorsByUser } from "../../lib/colors";
import { formatDateShort } from "../../lib/format";
import { icons } from "../../lib/icons";
import { pushToast } from "../../lib/toast";
import type {
  FinanceEntry,
  FinanceEntryDeletePayload,
  FinancePeriod,
  FinancePeriodDetail,
  UserRef,
} from "../../types";
import EntryFormModal from "./EntryFormModal.vue";
import PeriodSelector from "./PeriodSelector.vue";
import PersonTab from "./PersonTab.vue";
import SharedTab from "./SharedTab.vue";

const periods = ref<FinancePeriod[]>([]);
const users = ref<UserRef[]>([]);
const detail = ref<FinancePeriodDetail | null>(null);
const selectedId = ref<number | null>(null);
const activeTab = ref<string | number>("shared");
const loading = ref(true);
const detailLoading = ref(false);
const error = ref<string | null>(null);
const showOpenConfirm = ref(false);
const opening = ref(false);
const showEntryForm = ref(false);
const editingEntry = ref<FinanceEntry | null>(null);
const deletingEntry = ref<FinanceEntry | null>(null);
const deletingItemLabel = ref<string | null>(null);
const deleteBusy = ref(false);
const busyEntryId = ref<number | null>(null);
const expandEntryId = ref<number | null>(null);

const selected = computed(
  () => periods.value.find((p) => p.id === selectedId.value) ?? null,
);

const closed = computed(() => selected.value?.status !== "open");

const colors = computed(() => colorsByUser(users.value.map((user) => ({id: user.id}))));

const tabColor = (tabId: string | number): string | null =>
  typeof tabId === "number" ? colors.value[tabId]?.solid ?? null : null;

const entries = computed(() => detail.value?.entries ?? []);

const tabs = computed(() => {
  const me = auth.userId.value;
  const people = [...users.value].sort((a, b) =>
    a.id === me ? -1 : b.id === me ? 1 : 0,
  );
  return [
    { id: "shared", label: "Compartido" },
    ...people.map((u) => ({ id: u.id, label: u.name })),
  ];
});

function onOpenNewPeriod() {
  if (periods.value.length === 0) {
    doOpenNewPeriod();
    return;
  }
  showOpenConfirm.value = true;
}

async function confirmOpenNewPeriod() {
  showOpenConfirm.value = false;
  await doOpenNewPeriod();
}

async function doOpenNewPeriod() {
  opening.value = true;
  try {
    const period = await financesApi.openPeriod();
    await load();
    selectedId.value = period.id;
    pushToast(`Mes abierto: ${period.label}`);
  } catch (e) {
    pushToast(
      e instanceof ApiRequestError ? e.message : "No se pudo abrir el mes",
      "error",
    );
  } finally {
    opening.value = false;
  }
}

const personSummary = (ownerId: number) =>
  detail.value?.summary.people.find((p) => p.owner_id === ownerId) ?? null;

async function load() {
  try {
    [periods.value, users.value] = await Promise.all([
      financesApi.listPeriods(),
      usersApi.list(),
    ]);
    if (
      selectedId.value == null ||
      !periods.value.some((p) => p.id === selectedId.value)
    ) {
      const open = periods.value.find((p) => p.status === "open");
      selectedId.value = open?.id ?? periods.value[0]?.id ?? null;
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Error inesperado";
  } finally {
    loading.value = false;
  }
}

async function loadDetail(periodId: number) {
  detailLoading.value = true;
  try {
    detail.value = await financesApi.getPeriod(periodId);
  } catch (e) {
    pushToast(
      e instanceof ApiRequestError ? e.message : "No se pudo cargar el mes",
      "error",
    );
  } finally {
    detailLoading.value = false;
  }
}

async function confirmEntry(id: number) {
  busyEntryId.value = id;
  try {
    await financesApi.confirmEntry(id);
    if (selectedId.value != null) await loadDetail(selectedId.value);
  } catch (e) {
    pushToast(
      e instanceof ApiRequestError ? e.message : "No se pudo confirmar el movimiento",
      "error",
    );
  } finally {
    busyEntryId.value = null;
  }
}

function editEntry(id: number) {
  const entry = entries.value.find((e) => e.id === id);
  if (!entry) return;
  editingEntry.value = entry;
  showEntryForm.value = true;
}

function onEntrySaved() {
  showEntryForm.value = false;
  editingEntry.value = null;
  if (selectedId.value != null) loadDetail(selectedId.value);
}

function closeEntryForm() {
  showEntryForm.value = false;
  editingEntry.value = null;
}

const deletingOwnerName = computed(
  () =>
    users.value.find((u) => u.id === deletingEntry.value?.owner_id)?.name ??
    (deletingEntry.value ? `User_${deletingEntry.value.owner_id}` : ""),
);

function askDelete(payload: FinanceEntryDeletePayload) {
  deletingEntry.value = entries.value.find((e) => e.id === payload.id) ?? null;
  deletingItemLabel.value = payload.itemLabel ?? null;
}

async function confirmDelete() {
  if (!deletingEntry.value) return;
  deleteBusy.value = true;
  try {
    await financesApi.deleteEntry(deletingEntry.value.id);
    deletingEntry.value = null;
    deletingItemLabel.value = null;
    if (selectedId.value != null) await loadDetail(selectedId.value);
    pushToast("Movimiento eliminado");
  } catch (e) {
    pushToast(
      e instanceof ApiRequestError ? e.message : "No se pudo eliminar el movimiento",
      "error",
    );
  } finally {
    deleteBusy.value = false;
  }
}

function goToParentMovement() {
  const entry = deletingEntry.value;
  const ownerId = entry?.owner_id;
  if (entry == null || ownerId == null) return;
  closeDeleteModal();
  activeTab.value = ownerId;
  expandEntryId.value = entry.id;
  nextTick(() => {
    expandEntryId.value = null;
  });
}

function closeDeleteModal() {
  deletingEntry.value = null;
  deletingItemLabel.value = null;
}

watch(selectedId, (id) => {
  detail.value = null;
  if (id != null) loadDetail(id);
});

onMounted(load);
</script>

<template>
  <div class="mx-auto max-w-5xl space-y-4">
    <p v-if="error" class="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-600">
      {{ error }}
    </p>

    <div v-else-if="loading" class="space-y-4">
      <div class="flex items-center justify-between gap-2">
        <div class="inline-flex items-center overflow-hidden rounded-lg border border-slate-200">
          <span class="block h-8 w-9 animate-pulse bg-slate-200" />
          <span class="block h-8 w-36 animate-pulse border-x border-slate-200 bg-slate-200" />
          <span class="block h-8 w-9 animate-pulse bg-slate-200" />
        </div>
        <Skeleton width="7rem" height="2rem" />
      </div>
      <div class="rounded-xl border border-slate-200 bg-white">
        <div class="flex items-center gap-2 border-b border-slate-100 px-4 pb-4">
          <Skeleton width="6rem" height="1.25rem" />
          <Skeleton width="3.5rem" height="1.5rem" />
          <Skeleton width="1.75rem" height="1.75rem" />
          <Skeleton width="5rem" height="1rem" class="ml-auto hidden sm:block" />
        </div>
        <div class="flex items-center gap-6 border-b border-slate-200 px-4 pt-3 pb-2">
          <Skeleton v-for="n in 3" :key="n" width="4rem" height="1.25rem" />
        </div>
        <div class="space-y-4 px-4 pt-4 pb-4">
          <div class="flex gap-2">
            <div
              v-for="n in 3"
              :key="n"
              class="flex flex-1 flex-col gap-2 rounded-lg border border-slate-200 px-3 py-2"
            >
              <Skeleton width="3.5rem" height="0.75rem" />
              <Skeleton width="4.5rem" height="1.25rem" />
            </div>
          </div>
          <div class="flex items-center justify-between gap-2">
            <Skeleton width="6rem" height="1rem" />
            <Skeleton width="5rem" height="2rem" />
          </div>
          <div class="divide-y divide-slate-100">
            <div v-for="n in 3" :key="n" class="space-y-2 py-2.5 sm:py-2">
              <div class="flex items-center gap-3">
                <Skeleton width="9rem" class="flex-1" />
                <Skeleton width="3rem" />
                <Skeleton width="2rem" />
              </div>
              <div class="flex gap-2">
                <Skeleton width="3.5rem" height="1rem" />
                <Skeleton width="3.5rem" height="1rem" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div
      v-else-if="periods.length === 0"
      class="rounded-xl border border-slate-200 bg-white px-6 py-12 text-center"
    >
      <p class="text-sm text-slate-500">
        Todavía no hay ningún mes abierto.
      </p>
      <Button :loading="opening" class="mt-4" @click="onOpenNewPeriod">
        <Icon v-if="!opening" :path="icons.plus" :size="14" />
        {{ opening ? "Abriendo…" : "Abrir primer mes" }}
      </Button>
    </div>

    <template v-else>
      <PeriodSelector
        v-model="selectedId"
        :periods="periods"
        :busy="opening"
        @open-new="onOpenNewPeriod"
      />

      <section
        class="relative rounded-xl border border-slate-200 bg-white px-4 py-4"
        v-if="selected"
      >
        <header class="relative z-2 flex items-center gap-2 border-b border-slate-100 pb-4">
          <h2 class="min-w-0 truncate text-sm font-semibold text-slate-900">
            {{ selected.label }}
          </h2>
          <span
            class="shrink-0 rounded-md px-1.5 py-0.5 text-xs font-medium ring-1"
            :class="
              selected.status === 'open'
                ? 'bg-emerald-50 text-emerald-700 ring-emerald-100'
                : 'bg-rose-50 text-rose-700 ring-rose-100'
            "
          >
            <Icon
              :path="selected.status === 'open' ? icons.lockOpen : icons.lock"
              :size="12"
              class="mr-1 -mt-px inline"
            />
            {{ selected.status === "open" ? "abierto" : "cerrado" }}
          </span>
          <MoneyVisibilityToggle />
          <span class="ml-auto hidden shrink-0 items-center gap-1 text-xs text-slate-400 sm:flex">
            <Icon :path="icons.calendar" :size="12" />
            abierto el {{ formatDateShort(selected.opened_at) }}
          </span>
        </header>

        <nav class="flex min-w-0 gap-6 overflow-x-auto overflow-y-hidden border-b border-slate-200 pt-3">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            class="relative flex shrink-0 items-center gap-1.5 pb-2 text-sm transition-colors after:absolute after:inset-x-0 after:bottom-0 after:h-0.5 after:content-['']"
            :class="
              activeTab === tab.id
                ? 'font-medium text-slate-900 after:bg-slate-900'
                : 'text-slate-400 after:bg-transparent hover:text-slate-600'
            "
            @click="activeTab = tab.id"
          >
            <Icon v-if="tab.id === 'shared'" :path="icons.users" :size="14" />
            <span
              v-else
              class="h-2.5 w-2.5 shrink-0 rounded-full"
              :style="{ backgroundColor: tabColor(tab.id) ?? color('neutral').solid }"
            />
            {{ tab.label }}
          </button>
        </nav>

        <div v-if="detailLoading || !detail" class="space-y-4 pt-4">
          <div class="flex gap-2">
            <div
              v-for="n in 3"
              :key="n"
              class="flex flex-1 flex-col gap-2 rounded-lg border border-slate-200 px-3 py-2"
            >
              <Skeleton width="3.5rem" height="0.75rem" />
              <Skeleton width="4.5rem" height="1.25rem" />
            </div>
          </div>
          <div class="flex items-center justify-between gap-2">
            <Skeleton width="6rem" height="1rem" />
            <Skeleton width="5rem" height="2rem" />
          </div>
          <div class="divide-y divide-slate-100">
            <div v-for="n in 3" :key="n" class="space-y-2 py-2.5 sm:py-2">
              <div class="flex items-center gap-3">
                <Skeleton width="9rem" class="flex-1" />
                <Skeleton width="3rem" />
                <Skeleton width="2rem" />
              </div>
              <div class="flex gap-2">
                <Skeleton width="3.5rem" height="1rem" />
                <Skeleton width="3.5rem" height="1rem" />
              </div>
            </div>
          </div>
        </div>

        <div v-else class="pt-4">
          <SharedTab
            v-if="activeTab === 'shared'"
            :entries="entries"
            :summary="detail.summary"
            :users="users"
            :colors="colors"
            :busy-entry-id="busyEntryId"
            :expand-entry-id="expandEntryId"
            :closed="closed"
            @add="showEntryForm = true"
            @confirm="confirmEntry"
            @edit="editEntry"
            @delete="askDelete"
          />
          <PersonTab
            v-else
            :owner-id="Number(activeTab)"
            :entries="entries"
            :summary="personSummary(Number(activeTab))"
            :users="users"
            :colors="colors"
            :busy-entry-id="busyEntryId"
            :expand-entry-id="expandEntryId"
            :closed="closed"
            @add="showEntryForm = true"
            @confirm="confirmEntry"
            @edit="editEntry"
            @delete="askDelete"
          />
        </div>
      </section>
    </template>

    <EntryFormModal
      v-if="showEntryForm && selectedId != null"
      :period-id="selectedId"
      :users="users"
      :entry="editingEntry"
      :default-scope="activeTab === 'shared' ? 'shared' : 'personal'"
      :default-owner-id="activeTab === 'shared' ? (auth.userId.value ?? undefined) : Number(activeTab)"
      @close="closeEntryForm"
      @saved="onEntrySaved"
    />

    <Modal
      v-if="showOpenConfirm"
      title="Abrir nuevo mes"
      @close="showOpenConfirm = false"
    >
      <div class="space-y-2 text-sm text-slate-600">
        <p>Esta acción <strong>cerrará</strong> el período actual e iniciará uno nuevo.</p>
        <p>Las entradas confirmadas se copiarán al nuevo período con estado
        <strong>pendiente</strong>, para que puedas revisarlas antes de confirmarlas nuevamente.</p>
      </div>
      <div class="mt-5 flex justify-end gap-2">
        <button
          type="button"
          class="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100"
          @click="showOpenConfirm = false"
        >
          Cancelar
        </button>
        <button
          type="button"
          class="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-700 disabled:opacity-50"
          :disabled="opening"
          @click="confirmOpenNewPeriod"
        >
          {{ opening ? "Abriendo…" : "Confirmar" }}
        </button>
      </div>
    </Modal>

    <Modal
      v-if="deletingEntry"
      title="Eliminar movimiento"
      @close="closeDeleteModal"
    >
      <div v-if="deletingItemLabel" class="space-y-3 text-sm">
        <p class="text-slate-600">
          <span class="font-medium text-slate-900">{{ deletingItemLabel }}</span>
          pertenece al movimiento
          <span class="font-medium text-slate-900">{{ deletingEntry.label }}</span>
          de
          <span class="font-medium text-slate-900">{{ deletingOwnerName }}</span>.
        </p>
        <div class="rounded-lg bg-amber-50 px-3 py-2 text-amber-700 ring-1 ring-amber-100">
          <p class="font-medium">
            Al eliminar, se borrará ese movimiento completo, junto con todas sus líneas personales y compartidas.
          </p>
        </div>
        <p class="text-slate-600">
          Si solo quieres eliminar
          <span class="font-medium text-slate-900">{{ deletingItemLabel }}</span>,
          ve al movimiento para que puedas editarlo y eliminar esa línea desde ahí.
        </p>
      </div>
      <p v-else class="text-sm text-slate-600">
        ¿Seguro que quieres eliminar el movimiento
        <span class="font-medium text-slate-900">{{ deletingEntry.label }}</span>?
      </p>
      <div
        class="mt-5 flex gap-2"
        :class="deletingItemLabel ? 'flex-col sm:flex-row sm:justify-end' : 'justify-end'"
      >
        <button
          type="button"
          class="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100"
          @click="closeDeleteModal"
        >
          Cancelar
        </button>
        <button
          v-if="deletingItemLabel"
          type="button"
          class="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100"
          @click="goToParentMovement"
        >
          Ir al movimiento
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
  </div>
</template>
