<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ApiRequestError } from "../../api/client";
import { datesApi } from "../../api/dates";
import Icon from "../../components/Icon.vue";
import IconButton from "../../components/IconButton.vue";
import Modal from "../../components/Modal.vue";
import { formatDate } from "../../lib/format";
import { icons } from "../../lib/icons";
import { pushToast } from "../../lib/toast";
import type { DateEvent, DateMemory } from "../../types";

const props = defineProps<{
  event: DateEvent;
  memberNames: Record<number, string>;
}>();

const emit = defineEmits<{ close: []; updated: [event: DateEvent]; completed: [] }>();

const event = ref<DateEvent>(props.event);
const memories = ref<DateMemory[]>([]);
const memoriesError = ref<string | null>(null);
const loadingMemories = ref(true);

const addOpen = ref(false);
const memoryKind = ref<"photo" | "note">("photo");
const memoryUrl = ref("");
const memoryCaption = ref("");
const memoryTakenBy = ref<string>("");
const addError = ref<string | null>(null);
const addBusy = ref(false);

const deleting = ref<DateMemory | null>(null);
const deleteBusy = ref(false);
const deleteError = ref<string | null>(null);

const completeBusy = ref(false);
const completeError = ref<string | null>(null);

const memberOptions = computed(() => {
  const options: { value: string; label: string }[] = [];
  for (const [id, name] of Object.entries(props.memberNames)) {
    options.push({ value: id, label: name });
  }
  return options;
});

function attributeEmoji(key: string): string {
  switch (key) {
    case "place":
      return "📍";
    case "dresscode":
      return "👗";
    case "vibes":
      return "✨";
    default:
      return "•";
  }
}

async function loadMemories() {
  loadingMemories.value = true;
  memoriesError.value = null;
  try {
    memories.value = await datesApi.listMemories(event.value.id);
  } catch (e) {
    memoriesError.value = e instanceof Error ? e.message : "Error inesperado";
  } finally {
    loadingMemories.value = false;
  }
}

async function submitMemory() {
  addError.value = null;

  if (memoryKind.value === "photo" && !memoryUrl.value.trim()) {
    addError.value = "El recuerdo de tipo foto requiere una URL.";
    return;
  }
  if (memoryKind.value === "note" && !memoryCaption.value.trim()) {
    addError.value = "Escribe una nota para el recuerdo.";
    return;
  }

  addBusy.value = true;
  try {
    await datesApi.addMemory(event.value.id, {
      kind: memoryKind.value,
      media_url: memoryUrl.value.trim() || null,
      caption: memoryCaption.value.trim() || null,
      taken_by: memoryTakenBy.value ? Number(memoryTakenBy.value) : null,
    });
    addOpen.value = false;
    memoryKind.value = "photo";
    memoryUrl.value = "";
    memoryCaption.value = "";
    memoryTakenBy.value = "";
    await loadMemories();
    pushToast("Recuerdo añadido");
  } catch (e) {
    addError.value = e instanceof ApiRequestError ? e.message : "No se pudo añadir el recuerdo.";
  } finally {
    addBusy.value = false;
  }
}

function askDelete(memory: DateMemory) {
  deleting.value = memory;
  deleteError.value = null;
}

async function confirmDelete() {
  if (!deleting.value) return;
  deleteBusy.value = true;
  try {
    await datesApi.deleteMemory(deleting.value.id);
    deleting.value = null;
    await loadMemories();
    pushToast("Recuerdo eliminado");
  } catch (e) {
    deleteError.value =
      e instanceof ApiRequestError ? e.message : "No se pudo eliminar el recuerdo.";
  } finally {
    deleteBusy.value = false;
  }
}

async function complete() {
  completeBusy.value = true;
  completeError.value = null;
  try {
    const updated = await datesApi.completeEvent(event.value.id);
    event.value = updated;
    emit("completed");
  } catch (e) {
    completeError.value =
      e instanceof ApiRequestError ? e.message : "No se pudo marcar la cita como hecha.";
  } finally {
    completeBusy.value = false;
  }
}

function memberName(id: number): string {
  return props.memberNames[id] ?? `#${id}`;
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

onMounted(loadMemories);
</script>

<template>
  <Modal title="Detalle de la cita" size="lg" @close="emit('close')">
    <div class="space-y-4">
      <div>
        <div class="flex flex-wrap items-center gap-2">
          <h3 class="text-base font-semibold text-slate-900">
            {{ event.title ?? `Cita del ${formatDate(event.week_start)}` }}
          </h3>
          <span
            class="rounded-md border px-2 py-0.5 text-xs font-medium"
            :class="
              event.status === 'done'
                ? 'border-green-200 bg-green-50 text-green-700'
                : event.status === 'scheduled'
                  ? 'border-blue-200 bg-blue-50 text-blue-700'
                  : 'border-amber-200 bg-amber-50 text-amber-700'
            "
          >
            {{ statusLabel(event.status) }}
          </span>
        </div>
        <dl class="mt-2 space-y-1 text-sm text-slate-600">
          <div class="flex gap-2">
            <dt class="w-28 shrink-0 text-slate-400">Semana</dt>
            <dd>{{ formatDate(event.week_start) }}</dd>
          </div>
          <div v-if="event.scheduled_date" class="flex gap-2">
            <dt class="w-28 shrink-0 text-slate-400">Cita</dt>
            <dd>
              {{ formatDate(event.scheduled_date) }}
              <template v-if="event.scheduled_time"> · {{ event.scheduled_time }}</template>
            </dd>
          </div>
          <div class="flex gap-2">
            <dt class="w-28 shrink-0 text-slate-400">Planea</dt>
            <dd>{{ memberName(event.planned_by) }}</dd>
          </div>
        </dl>
      </div>

      <div v-if="event.attributes.length > 0">
        <h4 class="mb-1.5 text-xs font-semibold tracking-wider text-slate-400">
          DETALLES
        </h4>
        <ul class="space-y-1">
          <li
            v-for="attr in event.attributes"
            :key="attr.id"
            class="flex items-center gap-2 rounded-lg bg-slate-50 px-3 py-1.5 text-sm text-slate-700"
          >
            <span>{{ attributeEmoji(attr.key) }}</span>
            <span class="font-medium">{{ attr.key }}</span>
            <span class="text-slate-500">{{ attr.value }}</span>
          </li>
        </ul>
      </div>

      <div v-if="event.status !== 'done'">
        <button
          type="button"
          :disabled="completeBusy"
          class="w-full rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-green-500 disabled:opacity-50"
          @click="complete"
        >
          {{ completeBusy ? "Completando\u2026" : "Marcar como hecha" }}
        </button>
        <p v-if="completeError" class="mt-2 text-sm text-red-600">{{ completeError }}</p>
      </div>

      <div>
        <div class="mb-1.5 flex items-center justify-between">
          <h4 class="text-xs font-semibold tracking-wider text-slate-400">RECUERDOS</h4>
          <button
            type="button"
            class="inline-flex items-center gap-1 text-xs font-medium text-slate-600 transition-colors hover:text-slate-900"
            @click="addOpen = true"
          >
            <Icon :path="icons.plus" :size="12" />
            Añadir
          </button>
        </div>

        <p v-if="memoriesError" class="text-sm text-red-600">{{ memoriesError }}</p>
        <p
          v-else-if="!loadingMemories && memories.length === 0"
          class="text-sm text-slate-400"
        >
          Aún no hay recuerdos de esta cita.
        </p>

        <ul v-else class="space-y-2">
          <li v-for="n in 2" v-if="loadingMemories" :key="n">
            <div class="h-20 animate-pulse rounded-lg bg-slate-200" />
          </li>
          <li
            v-for="memory in memories"
            :key="memory.id"
            class="group relative rounded-lg border border-slate-200 p-3"
          >
            <img
              v-if="memory.kind === 'photo' && memory.media_url"
              :src="memory.media_url"
              alt="Recuerdo"
              class="max-h-48 w-full rounded-md object-cover"
            />
            <p v-if="memory.caption" class="mt-1 text-sm text-slate-700">
              {{ memory.caption }}
            </p>
            <p class="mt-1 text-xs text-slate-400">
              {{ memory.kind === "photo" ? "Foto" : "Nota" }}
              <template v-if="memory.taken_by">
                · {{ memberName(memory.taken_by) }}
              </template>
            </p>
            <IconButton
              :icon="icons.trash"
              label="Eliminar recuerdo"
              variant="danger"
              class="absolute right-2 top-2 rounded-md bg-white/80 transition-opacity sm:opacity-0 sm:group-hover:opacity-100"
              @click="askDelete(memory)"
            />
          </li>
        </ul>
      </div>

      <Modal v-if="addOpen" title="Nuevo recuerdo" @close="addOpen = false">
        <form class="space-y-4" @submit.prevent="submitMemory">
          <div>
            <label class="mb-1 block text-xs font-medium text-slate-500">Tipo</label>
            <div class="flex gap-2">
              <button
                type="button"
                class="flex-1 rounded-lg border px-3 py-2 text-sm transition-colors"
                :class="
                  memoryKind === 'photo'
                    ? 'border-slate-900 bg-slate-900 text-white'
                    : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                "
                @click="memoryKind = 'photo'"
              >
                Foto
              </button>
              <button
                type="button"
                class="flex-1 rounded-lg border px-3 py-2 text-sm transition-colors"
                :class="
                  memoryKind === 'note'
                    ? 'border-slate-900 bg-slate-900 text-white'
                    : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                "
                @click="memoryKind = 'note'"
              >
                Nota
              </button>
            </div>
          </div>

          <div v-if="memoryKind === 'photo'">
            <label class="mb-1 block text-xs font-medium text-slate-500">URL de la foto</label>
            <input
              v-model="memoryUrl"
              type="url"
              placeholder="https://…"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
            />
          </div>

          <div>
            <label class="mb-1 block text-xs font-medium text-slate-500">
              {{ memoryKind === "photo" ? "Descripción (Opcional)" : "Nota" }}
            </label>
            <textarea
              v-model="memoryCaption"
              rows="3"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
            />
          </div>

          <div>
            <label class="mb-1 block text-xs font-medium text-slate-500">Añadido por (Opcional)</label>
            <select
              v-model="memoryTakenBy"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
            >
              <option value="">—</option>
              <option v-for="opt in memberOptions" :key="opt.value" :value="opt.value">
                {{ opt.label }}
              </option>
            </select>
          </div>

          <p v-if="addError" class="text-sm text-red-600">{{ addError }}</p>

          <div class="flex justify-end gap-2 pt-1">
            <button
              type="button"
              class="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100"
              @click="addOpen = false"
            >
              Cancelar
            </button>
            <button
              type="submit"
              :disabled="addBusy"
              class="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-700 disabled:opacity-50"
            >
              {{ addBusy ? "Guardando\u2026" : "Añadir" }}
            </button>
          </div>
        </form>
      </Modal>

      <Modal v-if="deleting" title="Eliminar recuerdo" @close="deleting = null">
        <p class="text-sm text-slate-600">¿Seguro que quieres eliminar este recuerdo?</p>
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
    </div>
  </Modal>
</template>