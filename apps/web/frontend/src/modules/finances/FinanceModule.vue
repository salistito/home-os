<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import Icon from "../../components/Icon.vue";
import Skeleton from "../../components/Skeleton.vue";
import PeriodSelector from "./PeriodSelector.vue";
import { icons } from "../../lib/icons";
import { financesApi } from "../../api/finances";
import { ApiRequestError } from "../../api/client";
import { pushToast } from "../../lib/toast";
import { formatDate } from "../../lib/format";
import type { FinancePeriod } from "../../types";

const periods = ref<FinancePeriod[]>([]);
const selectedId = ref<number | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);
const opening = ref(false);

const selected = computed(
  () => periods.value.find((p) => p.id === selectedId.value) ?? null,
);

async function load() {
  try {
    periods.value = await financesApi.listPeriods();
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
      <button
        type="button"
        :disabled="opening"
        class="mt-4 inline-flex items-center gap-1 rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-700 disabled:opacity-50"
        @click="openNew"
      >
        <Icon :path="icons.plus" :size="14" />
        {{ opening ? "Abriendo…" : "Abrir primer mes" }}
      </button>
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

        <p class="py-10 text-center text-sm text-slate-400">
          Las cuentas compartidas y por persona llegan en el próximo paso.
        </p>
      </section>
    </template>
  </div>
</template>
