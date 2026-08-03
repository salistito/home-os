<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { ApiRequestError } from "../../api/client";
import { financesApi } from "../../api/finances";
import Button from "../../components/Button.vue";
import Modal from "../../components/Modal.vue";
import SelectMenu, { type SelectOption } from "../../components/SelectMenu.vue";
import { auth } from "../../lib/auth";
import { colorsByUser } from "../../lib/colors";
import { formatAmountInput, formatMoney } from "../../lib/money";
import type {
  FinanceDetailMode,
  FinanceEntry,
  FinanceEntryDetailInput,
  FinanceEntryKind,
  FinanceEntryScope,
  UserRef,
} from "../../types";
import SubDetail from "./SubDetail.vue";
import TagInput from "./TagInput.vue";

const props = defineProps<{
  periodId: number;
  users: UserRef[];
  entry?: FinanceEntry | null;
  defaultScope?: FinanceEntryScope;
  defaultOwnerId?: number;
}>();
const emit = defineEmits<{ close: []; saved: [] }>();

const isEdit = computed(() => props.entry != null);

const sortedUsers = computed<UserRef[]>(() => {
  const me = auth.userId.value;
  return [...props.users]
    .filter((u) => u.deleted_at === null)
    .sort((a, b) =>
      a.id === me ? -1 : b.id === me ? 1 : 0,
    );
});

const colors = colorsByUser(props.users.map((user) => ({id: user.id})));

const kindOptions: SelectOption[] = [
  { value: "expense", label: "Gasto" },
  { value: "income", label: "Ingreso" },
];
const scopeOptions: SelectOption[] = [
  { value: "personal", label: "Personal" },
  { value: "shared", label: "Compartido" },
];
const ownerOptions = computed<SelectOption[]>(() => {
  const opts = sortedUsers.value.map((u) => ({
    value: String(u.id),
    label: u.name,
    dot: colors[u.id]?.solid,
  }));
  if (props.entry) {
    const current = props.users.find((u) => u.id === props.entry!.owner_id);
    if (
      current &&
      current.deleted_at !== null &&
      !opts.some((o) => o.value === String(current.id))
    ) {
      opts.push({
        value: String(current.id),
        label: `${current.name} (borrado)`,
        dot: colors[current.id]?.solid,
      });
    }
  }
  return opts;
});

const kind = ref<FinanceEntryKind>(props.entry?.kind ?? "expense");
const scope = ref<FinanceEntryScope>(
  props.entry?.scope ?? props.defaultScope ?? "personal",
);
const ownerId = ref<string>(
  String(props.entry?.owner_id ?? props.defaultOwnerId ?? sortedUsers.value[0]?.id ?? ""),
);
const label = ref(props.entry?.label ?? "");
const amount = ref<number | null>(props.entry?.amount ?? null);
const detailMode = ref<FinanceDetailMode>(props.entry?.detail_mode ?? "none");
const details = ref<FinanceEntryDetailInput[]>(
  (props.entry?.details ?? []).map((d) => ({
    label: d.label,
    amount: d.amount,
    tags: d.tags.map((t) => t.name),
  })),
);
const tags = ref<string[]>((props.entry?.tags ?? []).map((t) => t.name));
const tagSuggestions = ref<string[]>([]);

onMounted(async () => {
  try {
    tagSuggestions.value = (await financesApi.listTags()).map((t) => t.name);
  } catch {
    tagSuggestions.value = [];
  }
});

const isBottomUp = computed(() => detailMode.value === "bottom_up");
const detailsTotal = computed(() =>
  details.value.reduce((sum, d) => sum + (d.amount || 0), 0),
);
const effectiveAmount = computed(() =>
  isBottomUp.value ? detailsTotal.value : (amount.value ?? 0),
);

const amountDisplay = computed<string>({
  get: () => formatAmountInput(amount.value ?? 0),
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

function validate(): string | null {
  if (!Number(ownerId.value)) {
    return "Elige un responsable.";
  }
  if (!label.value.trim()) {
    return "El nombre del movimiento es obligatorio.";
  }
  if (
    !isBottomUp.value &&
    amount.value !== null &&
    (!Number.isInteger(amount.value) || amount.value < 0)
  ) {
    return "El monto debe ser un entero mayor o igual a cero.";
  }
  if (tags.value.some((t) => t.length > 30)) {
    return "La categoría debe tener a lo más 30 caracteres.";
  }
  const needsLines =
    detailMode.value === "bottom_up" || detailMode.value === "top_down";
  if (needsLines && details.value.length === 0) {
    return "Agrega al menos una línea al desglose.";
  }
  if (detailMode.value !== "none") {
    for (const d of details.value) {
      if (!d.label.trim()) {
        return "Cada línea del desglose necesita tener un concepto.";
      }
      if (d.amount < 0) {
        return "Los montos del desglose no pueden ser negativos.";
      }
      if (!Number.isInteger(d.amount)) {
        return "Los montos del desglose deben ser números enteros.";
      }
      if ((d.tags ?? []).some((t) => t.length > 30)) {
        return "Las categorías del desglose deben tener a lo más 30 caracteres.";
      }
    }
  }
  if (
    detailMode.value === "top_down" &&
    amount.value !== null &&
    detailsTotal.value !== amount.value
  ) {
    return "La suma del desglose no cuadra con el monto.";
  }
  return null;
}

async function submit() {
  error.value = validate();
  if (error.value) return;

  const ownerNumber = Number(ownerId.value);
  saving.value = true;
  try {
    if (isEdit.value && props.entry) {
      await financesApi.updateEntry(props.entry.id, {
        label: label.value.trim(),
        owner_id:
          Number(ownerId.value) !== props.entry.owner_id
            ? ownerNumber
            : undefined,
        amount: amount.value ?? undefined,
        kind: kind.value,
        scope: kind.value === "income" ? "personal" : scope.value,
        detail_mode: detailMode.value,
        details: detailMode.value === "none" ? [] : details.value,
        tags: tags.value,
      });
    } else {
      await financesApi.createEntry({
        period_id: props.periodId,
        kind: kind.value,
        scope: kind.value === "income" ? "personal" : scope.value,
        owner_id: ownerNumber,
        label: label.value.trim(),
        amount: amount.value,
        detail_mode: detailMode.value,
        details: detailMode.value === "none" ? [] : details.value,
        tags: tags.value,
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
            @update:model-value="kind = $event as FinanceEntryKind"
          />
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-slate-500">Ámbito</label>
          <SelectMenu
            :model-value="scope"
            :options="scopeOptions"
            :disabled="kind === 'income'"
            @update:model-value="scope = $event as FinanceEntryScope"
          />
        </div>
      </div>

      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">
          {{ kind === "expense" ? "Pagado por" : "Recibido por" }}
        </label>
        <SelectMenu v-model="ownerId" :options="ownerOptions" />
      </div>

      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">Nombre del movimiento</label>
        <input
          v-model="label"
          type="text"
          :placeholder="kind === 'income' ? 'Sueldo' : 'Arriendo'"
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

      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">Categoría (Opcional)</label>
        <TagInput
          v-model="tags"
          :suggestions="tagSuggestions"
          :placeholder="
            kind === 'expense'
              ? 'Vivienda, Entretención, etc.'
              : 'Sueldo, Ingresos extra, etc.'
          "
        />
      </div>

      <SubDetail
        v-model="details"
        v-model:detail-mode="detailMode"
        :entry-amount="amount ?? 0"
        :tag-suggestions="tagSuggestions"
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
