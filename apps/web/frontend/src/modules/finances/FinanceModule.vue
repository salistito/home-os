<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import Icon from "../../components/Icon.vue";
import Button from "../../components/Button.vue";
import Skeleton from "../../components/Skeleton.vue";
import PeriodSelector from "./PeriodSelector.vue";
import EntryFormModal from "./EntryFormModal.vue";
import { icons } from "../../lib/icons";
import { financesApi } from "../../api/finances";
import { usersApi } from "../../api/users";
import { ApiRequestError } from "../../api/client";
import { pushToast } from "../../lib/toast";
import { formatDate, formatMoney } from "../../lib/format";
import { colorsByUser } from "../../lib/colors";
import type { FinanceEntry, FinancePeriod, UserRef } from "../../types";

const periods = ref<FinancePeriod[]>([]);
const users = ref<UserRef[]>([]);
const entries = ref<FinanceEntry[]>([]);
const selectedId = ref<number | null>(null);
const loading = ref(true);
const entriesLoading = ref(false);
const error = ref<string | null>(null);
const opening = ref(false);
const showEntryForm = ref(false);

const selected = computed(
  () => periods.value.find((p) => p.id === selectedId.value) ?? null,
);

const userName = (id: string) =>
  users.value.find((u) => u.id === id)?.name ?? id;

const colors = computed(() => colorsByUser(users.value.map((u) => u.id)));

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

async function loadEntries(periodId: number) {
  entriesLoading.value = true;
  try {
    entries.value = await financesApi.listEntries(periodId);
  } catch (e) {
    pushToast(
      e instanceof ApiRequestError ? e.message : "No se pudieron cargar los movimientos",
      "error",
    );
  } finally {
    entriesLoading.value = false;
  }
}

function onEntrySaved() {
  showEntryForm.value = false;
  if (selectedId.value != null) loadEntries(selectedId.value);
}

watch(selectedId, (id) => {
  entries.value = [];
  if (id != null) loadEntries(id);
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

        <div class="flex items-center justify-between pt-3">
          <h3 class="text-xs font-medium uppercase tracking-wide text-slate-400">
            Movimientos
          </h3>
          <Button size="sm" @click="showEntryForm = true">
            <Icon :path="icons.plus" :size="12" />
            Agregar
          </Button>
        </div>

        <div v-if="entriesLoading" class="space-y-2 pt-3">
          <Skeleton width="100%" height="2.5rem" />
          <Skeleton width="100%" height="2.5rem" />
        </div>

        <p
          v-else-if="entries.length === 0"
          class="py-10 text-center text-sm text-slate-400"
        >
          Todavía no hay movimientos en este mes.
        </p>

        <ul v-else class="divide-y divide-slate-100 pt-1">
          <li
            v-for="entry in entries"
            :key="entry.id"
            class="flex items-center gap-3 py-2.5"
          >
            <span
              class="rounded-md px-1.5 py-0.5 text-xs font-medium"
              :class="
                entry.kind === 'income'
                  ? 'bg-emerald-50 text-emerald-700'
                  : 'bg-rose-50 text-rose-700'
              "
            >
              {{ entry.kind === "income" ? "ingreso" : "gasto" }}
            </span>
            <span class="text-sm text-slate-800">{{ entry.label }}</span>
            <span
              v-if="entry.scope === 'shared'"
              class="rounded-md bg-slate-100 px-1.5 py-0.5 text-xs text-slate-500"
            >
              compartido
            </span>
            <span class="flex items-center gap-1.5 text-xs text-slate-400">
              <span
                v-if="colors[entry.owner_id]"
                class="h-2.5 w-2.5 shrink-0 rounded-full"
                :style="{ backgroundColor: colors[entry.owner_id].solid }"
              />
              {{ userName(entry.owner_id) }}
            </span>
            <span class="ml-auto text-sm font-medium text-slate-900">
              {{ formatMoney(entry.amount) }}
            </span>
          </li>
        </ul>
      </section>
    </template>

    <EntryFormModal
      v-if="showEntryForm && selectedId != null"
      :period-id="selectedId"
      :users="users"
      @close="showEntryForm = false"
      @saved="onEntrySaved"
    />
  </div>
</template>
