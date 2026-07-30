<script setup lang="ts">
import { nextTick, ref, watch } from "vue";

const props = defineProps<{
  modelValue: string;
  min?: string;
  max?: string;
  disabled?: boolean;
}>();

const emit = defineEmits<{ "update:modelValue": [value: string] }>();

const display = ref(toDisplay(props.modelValue));
const invalid = ref(false);

function toDisplay(iso: string): string {
  if (!iso) return "";
  const parts = iso.split("-");
  if (parts.length !== 3) return iso;
  return `${parts[2]}/${parts[1]}/${parts[0]}`;
}

function toIso(ddmmYyyy: string): string {
  const parts = ddmmYyyy.split("/");
  if (parts.length !== 3) return "";
  const [dd, mm, yyyy] = parts;
  if (dd.length !== 2 || mm.length !== 2 || yyyy.length !== 4) return "";
  return `${yyyy}-${mm}-${dd}`;
}

function isValidDate(d: number, m: number, y: number): boolean {
  const date = new Date(y, m - 1, d);
  return date.getFullYear() === y && date.getMonth() === m - 1 && date.getDate() === d;
}

watch(
  () => props.modelValue,
  (val) => {
    display.value = toDisplay(val);
  },
);

function onFocus(e: Event) {
  nextTick(() => (e.target as HTMLInputElement).select());
}

function onInput(e: Event) {
  invalid.value = false;
  const raw = (e.target as HTMLInputElement).value;
  const digits = raw.replace(/\D/g, "").slice(0, 8);
  let formatted = "";
  if (digits.length > 0) formatted = digits.slice(0, 2);
  if (digits.length > 2) formatted += "/" + digits.slice(2, 4);
  if (digits.length > 4) formatted += "/" + digits.slice(4, 8);
  display.value = formatted;

  if (digits.length === 8) {
    const dd = digits.slice(0, 2);
    const mm = digits.slice(2, 4);
    const yyyy = digits.slice(4, 8);
    const d = parseInt(dd, 10);
    const m = parseInt(mm, 10);
    const y = parseInt(yyyy, 10);
    if (isValidDate(d, m, y)) {
      const iso = `${yyyy}-${mm}-${dd}`;
      emit("update:modelValue", iso);
      if (props.min && iso < props.min) {
        invalid.value = true;
      } else if (props.max && iso > props.max) {
        invalid.value = true;
      } else {
        invalid.value = false;
      }
      return;
    }
    invalid.value = true;
  } else if (digits.length === 0) {
    emit("update:modelValue", "");
  }
}

function onBlur() {
  if (!display.value) {
    emit("update:modelValue", "");
    invalid.value = false;
    return;
  }

  const parts = display.value.split("/");
  if (parts.length !== 3) {
    invalid.value = true;
    return;
  }

  const [dd, mm, yyyy] = parts;
  const d = parseInt(dd, 10);
  const m = parseInt(mm, 10);
  const y = parseInt(yyyy, 10);

  if (d < 1 || d > 31 || m < 1 || m > 12 || y < 1000 || y > 9999) {
    invalid.value = true;
    return;
  }

  if (!isValidDate(d, m, y)) {
    invalid.value = true;
    return;
  }

  const iso = toIso(display.value);
  if (props.min && iso < props.min) {
    invalid.value = true;
    return;
  }
  if (props.max && iso > props.max) {
    invalid.value = true;
    return;
  }

  invalid.value = false;
  emit("update:modelValue", iso);
}
</script>

<template>
  <input
    type="text"
    :value="display"
    placeholder="dd/mm/yyyy"
    maxlength="10"
    :disabled="disabled"
    class="w-full rounded-lg border px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:ring-2"
    :class="invalid
      ? 'border-red-400 focus:border-red-400 focus:ring-red-100'
      : 'border-slate-200 focus:border-amber-400 focus:ring-amber-100'"
    @focus="onFocus"
    @input="onInput"
    @blur="onBlur"
  />
</template>
