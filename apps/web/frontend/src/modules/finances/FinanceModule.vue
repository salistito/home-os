<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import Icon from "../../components/Icon.vue";
import Button from "../../components/Button.vue";
import Modal from "../../components/Modal.vue";
import Skeleton from "../../components/Skeleton.vue";
import PeriodSelector from "./PeriodSelector.vue";
import EntryFormModal from "./EntryFormModal.vue";
import SharedTab from "./SharedTab.vue";
import PersonTab from "./PersonTab.vue";
import { icons } from "../../lib/icons";
import { financesApi } from "../../api/finances";
import { usersApi } from "../../api/users";
import { auth } from "../../lib/auth";
import { ApiRequestError } from "../../api/client";
import { pushToast } from "../../lib/toast";
import { formatDate } from "../../lib/format";
import { colorsByUser } from "../../lib/colors";
import type {
  FinanceEntry,
  FinancePeriod,
  FinancePeriodDetail,
  UserRef,
} from "../../types";

const periods = ref<FinancePeriod[]>([]);
const users = ref<UserRef[]>([]);
const detail = ref<FinancePeriodDetail | null>(null);
const selectedId = ref<number | null>(null);
const activeTab = ref<string | number>("shared");
const loading = ref(true);
const detailLoading = ref(false);
const error = ref<string | null>(null);
const opening = ref(false);
const showEntryForm = ref(false);
const editingEntry = ref<FinanceEntry | null>(null);
const deletingEntry = ref<FinanceEntry | null>(null);
const deleteBusy = ref(false);
const busyEntryId = ref<number | null>(null);

const selected = computed(
  () => periods.value.find((p) => p.id === selectedId.value) ?? null,
);

const colors = computed(() => colorsByUser(users.value.map((u) => u.id)));

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

function onEntrySaved() {
  showEntryForm.value = false;
  editingEntry.value = null;
  if (selectedId.value != null) loadDetail(selectedId.value);
}

function closeEntryForm() {
  showEntryForm.value = false;
  editingEntry.value = null;
}

function editEntry(id: number) {
  const entry = entries.value.find((e) => e.id === id);
  if (!entry) return;
  editingEntry.value = entry;
  showEntryForm.value = true;
}

function askDelete(id: number) {
  deletingEntry.value = entries.value.find((e) => e.id === id) ?? null;
}

async function confirmDelete() {
  if (!deletingEntry.value) return;
  deleteBusy.value = true;
  try {
    await financesApi.deleteEntry(deletingEntry.value.id);
    deletingEntry.value = null;
    if (selectedId.value != null) await loadDetail(selectedId.value);
    pushToast("Movimiento borrado");
  } catch (e) {
    pushToast(
      e instanceof ApiRequestError ? e.message : "No se pudo borrar el movimiento",
      "error",
    );
  } finally {
    deleteBusy.value = false;
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

watch(selectedId, (id) => {
  detail.value = null;
  activeTab.value = "shared";
  if (id != null) loadDetail(id);
});

async function openNew() {
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

onMounted(load);
</script>

<template>
  <div class="mx-auto max-w-5xl space-y-4">
    <p v-if="error" class="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-600">
      {{ error }}
    </p>

    <div v-else-if="loading" class="space-y-4">
      <Skeleton width="18rem" height="2.25rem" />
      <Skeleton width="100%" height="10rem" />
    </div>

    <div
      v-else-if="periods.length === 0"
      class="rounded-xl border border-slate-200 bg-white px-6 py-12 text-center"
    >
      <p class="text-sm text-slate-500">
        Todavía no hay ningún mes abierto.
      </p>
      <Button :loading="opening" class="mt-4" @click="openNew">
        <Icon v-if="!opening" :path="icons.plus" :size="14" />
        {{ opening ? "Abriendo…" : "Abrir primer mes" }}
      </Button>
    </div>

    <template v-else>
      <PeriodSelector
        v-model="selectedId"
        :periods="periods"
        :busy="opening"
        @open-new="openNew"
      />

      <section
        class="rounded-xl border border-slate-200 bg-white px-4 py-3"
        v-if="selected"
      >
        <header class="flex items-baseline gap-2 border-b border-slate-100 pb-3">
          <h2 class="text-sm font-semibold text-slate-900">
            {{ selected.label }}
          </h2>
          <span
            class="rounded-md px-1.5 py-0.5 text-xs font-medium"
            :class="
              selected.status === 'open'
                ? 'bg-emerald-50 text-emerald-700'
                : 'bg-slate-100 text-slate-500'
            "
          >
            {{ selected.status === "open" ? "abierto" : "cerrado" }}
          </span>
          <span class="ml-auto flex items-center gap-1 text-xs text-slate-400">
            <Icon :path="icons.calendar" :size="12" />
            abierto el {{ formatDate(selected.opened_at) }}
          </span>
        </header>

        <div class="flex items-end justify-between border-b border-slate-200 pt-3">
          <nav class="flex gap-6">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              class="-mb-px flex items-center gap-1.5 border-b-2 pb-2 text-sm transition-colors"
              :class="
                activeTab === tab.id
                  ? 'border-slate-900 font-medium text-slate-900'
                  : 'border-transparent text-slate-400 hover:text-slate-600'
              "
              @click="activeTab = tab.id"
            >
              <Icon v-if="tab.id === 'shared'" :path="icons.users" :size="14" />
              <span
                v-else
                class="h-2.5 w-2.5 shrink-0 rounded-full"
                :style="{ backgroundColor: colors[tab.id]?.solid ?? '#cbd5e1' }"
              />
              {{ tab.label }}
            </button>
          </nav>
          <Button size="sm" class="mb-2" @click="showEntryForm = true">
            <Icon :path="icons.plus" :size="12" />
            Agregar
          </Button>
        </div>

        <div v-if="detailLoading || !detail" class="space-y-2 pt-4">
          <Skeleton width="100%" height="2.5rem" />
          <Skeleton width="100%" height="2.5rem" />
        </div>

        <div v-else class="pt-4">
          <SharedTab
            v-if="activeTab === 'shared'"
            :entries="entries"
            :summary="detail.summary"
            :users="users"
            :colors="colors"
            :busy-entry-id="busyEntryId"
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
      v-if="deletingEntry"
      title="Borrar movimiento"
      @close="deletingEntry = null"
    >
      <p class="text-sm text-slate-600">
        ¿Seguro que quieres borrar
        <span class="font-medium text-slate-900">{{ deletingEntry.label }}</span>?
      </p>
      <div class="mt-5 flex justify-end gap-2">
        <button
          type="button"
          class="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100"
          @click="deletingEntry = null"
        >
          Cancelar
        </button>
        <button
          type="button"
          :disabled="deleteBusy"
          class="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-500 disabled:opacity-50"
          @click="confirmDelete"
        >
          {{ deleteBusy ? "Borrando…" : "Borrar" }}
        </button>
      </div>
    </Modal>
  </div>
</template>
