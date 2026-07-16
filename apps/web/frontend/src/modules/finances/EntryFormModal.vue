<script setup lang="ts">
import { computed, ref, watch } from "vue";
import Modal from "../../components/Modal.vue";
import Button from "../../components/Button.vue";
import SelectMenu from "../../components/SelectMenu.vue";
import type { SelectOption } from "../../components/SelectMenu.vue";
import SubDetail from "./SubDetail.vue";
import { financesApi } from "../../api/finances";
import { ApiRequestError } from "../../api/client";
import { auth } from "../../lib/auth";
import { colorsByUser } from "../../lib/colors";
import { formatMoney } from "../../lib/format";
import type {
  FinanceDetailMode,
  FinanceEntry,
  FinanceEntryDetailInput,
  FinanceEntryKind,
  FinanceEntryScope,
  UserRef,
} from "../../types";

const props = defineProps<{
  periodId: number;
  users: UserRef[];
  entry?: FinanceEntry | null;
  defaultScope?: FinanceEntryScope;
  defaultOwnerId?: string;
}>();
const emit = defineEmits<{ close: []; saved: [] }>();

const isEdit = computed(() => props.entry != null);

const sortedUsers = computed<UserRef[]>(() => {
  const me = auth.userId.value;
  return [...props.users].sort((a, b) =>
    a.id === me ? -1 : b.id === me ? 1 : 0,
  );
});

const kind = ref<FinanceEntryKind>(props.entry?.kind ?? "expense");
const scope = ref<FinanceEntryScope>(
  props.entry?.scope ?? props.defaultScope ?? "personal",
);
const ownerId = ref<string>(
  props.entry?.owner_id ?? props.defaultOwnerId ?? sortedUsers.value[0]?.id ?? "",
);
const label = ref(props.entry?.label ?? "");
const amount = ref<number | null>(props.entry?.amount ?? null);
const detailMode = ref<FinanceDetailMode>(props.entry?.detail_mode ?? "none");
const details = ref<FinanceEntryDetailInput[]>(
  (props.entry?.details ?? []).map((d) => ({ label: d.label, amount: d.amount })),
);

const kindOptions: SelectOption[] = [
  { value: "expense", label: "Gasto" },
  { value: "income", label: "Ingreso" },
];
const scopeOptions: SelectOption[] = [
  { value: "personal", label: "Personal" },
  { value: "shared", label: "Compartido" },
];

const colors = colorsByUser(props.users.map((u) => u.id));
const ownerOptions = computed<SelectOption[]>(() =>
  sortedUsers.value.map((u) => ({
    value: u.id,
    label: u.name,
    dot: colors[u.id]?.solid,
  })),
);

const isBottomUp = computed(() => detailMode.value === "bottom_up");
const detailsTotal = computed(() =>
  details.value.reduce((sum, d) => sum + (d.amount || 0), 0),
);
const effectiveAmount = computed(() =>
  isBottomUp.value ? detailsTotal.value : (amount.value ?? 0),
);

const amountDisplay = computed<string>({
  get: () => (amount.value ? amount.value.toLocaleString("es-CL") : ""),
  set: (value) => {
    const digits = value.replace(/\D/g, "");
    amount.value = digits ? Number(digits) : null;
  },
});

const error = ref<string | null>(null);
const saving = ref(false);

watch(kind, (value) => {
  if (value === "income") {
    scope.value = "personal";
  }
});

async function submit() {
  error.value = null;

  if (!label.value.trim()) {
    error.value = "El nombre es obligatorio.";
    return;
  }
  if (!ownerId.value) {
    error.value = "Elige un responsable.";
    return;
  }
  if (
    !isBottomUp.value &&
    amount.value !== null &&
    (!Number.isInteger(amount.value) || amount.value < 0)
  ) {
    error.value = "El monto debe ser un entero mayor o igual a cero.";
    return;
  }
  if (detailMode.value !== "none") {
    for (const d of details.value) {
      if (!d.label.trim()) {
        error.value = "Cada línea del desglose necesita un nombre.";
        return;
      }
      if (d.amount < 0) {
        error.value = "Los montos del desglose no pueden ser negativos.";
        return;
      }
    }
  }

  saving.value = true;
  try {
    if (isEdit.value && props.entry) {
      await financesApi.updateEntry(props.entry.id, {
        label: label.value.trim(),
        owner_id: ownerId.value,
        amount: amount.value ?? undefined,
        detail_mode: detailMode.value,
        details: detailMode.value === "none" ? [] : details.value,
      });
    } else {
      await financesApi.createEntry({
        period_id: props.periodId,
        kind: kind.value,
        scope: kind.value === "income" ? "personal" : scope.value,
        owner_id: ownerId.value,
        label: label.value.trim(),
        amount: amount.value,
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
  <Modal :title="isEdit ? 'Editar movimiento' : 'Nuevo movimiento'" @close="emit('close')">
    <form class="space-y-4" @submit.prevent="submit">
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">Tipo</label>
          <SelectMenu
            :model-value="kind"
            :options="kindOptions"
            :disabled="isEdit"
            @update:model-value="kind = $event as FinanceEntryKind"
          />
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">Ámbito</label>
          <SelectMenu
            :model-value="scope"
            :options="scopeOptions"
            :disabled="isEdit || kind === 'income'"
            @update:model-value="scope = $event as FinanceEntryScope"
          />
        </div>
      </div>

      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">
          {{ scope === "shared" ? "Pagado por" : "Responsable" }}
        </label>
        <SelectMenu v-model="ownerId" :options="ownerOptions" />
      </div>

      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">Nombre</label>
        <input
          v-model="label"
          type="text"
          placeholder="Arriendo"
          class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
        />
      </div>

      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">Monto</label>
        <div v-if="isBottomUp" class="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-600">
          {{ formatMoney(effectiveAmount) }}
          <span class="text-xs text-slate-400">(suma del desglose)</span>
        </div>
        <div v-else class="relative">
          <span
            class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-sm text-slate-400"
          >
            $
          </span>
          <input
            v-model="amountDisplay"
            type="text"
            inputmode="numeric"
            placeholder="0"
            class="w-full rounded-lg border border-slate-200 py-2 pl-6 pr-3 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
          />
        </div>
      </div>

      <SubDetail
        v-if="isEdit"
        v-model="details"
        v-model:detail-mode="detailMode"
        :entry-amount="amount ?? 0"
      />

      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

      <div class="flex justify-end gap-2 pt-1">
        <Button variant="ghost" @click="emit('close')">Cancelar</Button>
        <Button type="submit" :loading="saving">
          {{ saving ? "Guardando…" : isEdit ? "Guardar" : "Crear" }}
        </Button>
      </div>
    </form>
  </Modal>
</template>
