<script setup lang="ts">
import { computed, ref } from "vue";
import Icon from "../../components/Icon.vue";
import { icons } from "../../lib/icons";

const props = defineProps<{
  modelValue: string[];
  suggestions: string[];
}>();
const emit = defineEmits<{ "update:modelValue": [value: string[]] }>();

const draft = ref("");

const available = computed(() => {
  const chosen = new Set(props.modelValue.map((t) => t.toLowerCase()));
  return props.suggestions.filter((s) => !chosen.has(s.toLowerCase()));
});

function add(name: string) {
  const value = name.trim();
  if (!value) return;
  const exists = props.modelValue.some(
    (t) => t.toLowerCase() === value.toLowerCase(),
  );
  if (!exists) emit("update:modelValue", [...props.modelValue, value]);
  draft.value = "";
}

function removeAt(index: number) {
  emit(
    "update:modelValue",
    props.modelValue.filter((_, i) => i !== index),
  );
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === "Enter" || event.key === ",") {
    event.preventDefault();
    add(draft.value);
  } else if (event.key === "Backspace" && !draft.value) {
    removeAt(props.modelValue.length - 1);
  }
}
</script>

<template>
  <div>
    <div
      class="flex flex-wrap items-center gap-1.5 rounded-lg border border-slate-200 px-2 py-1.5 focus-within:border-amber-400 focus-within:ring-2 focus-within:ring-amber-100"
    >
      <span
        v-for="(tag, index) in modelValue"
        :key="tag"
        class="flex items-center gap-1 rounded-md bg-slate-100 py-0.5 pl-2 pr-1 text-xs text-slate-600"
      >
        {{ tag }}
        <button
          type="button"
          class="rounded text-slate-400 transition-colors hover:text-slate-700"
          aria-label="Quitar tag"
          @click="removeAt(index)"
        >
          <Icon :path="icons.close" :size="12" />
        </button>
      </span>
      <input
        v-model="draft"
        type="text"
        list="finances-tag-suggestions"
        placeholder="Agregar tag…"
        class="min-w-24 flex-1 border-0 bg-transparent px-1 py-0.5 text-sm text-slate-800 outline-none"
        @keydown="onKeydown"
        @change="add(draft)"
      />
      <datalist id="finances-tag-suggestions">
        <option v-for="s in available" :key="s" :value="s" />
      </datalist>
    </div>
  </div>
</template>
