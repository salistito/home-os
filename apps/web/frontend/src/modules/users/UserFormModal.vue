<script setup lang="ts">
import { computed, ref } from "vue";
import Modal from "../../components/Modal.vue";
import { usersApi } from "../../api/users";
import { ApiRequestError } from "../../api/client";
import type { UserRef, UserRole } from "../../types";

const props = defineProps<{ user?: UserRef | null }>();
const emit = defineEmits<{ close: []; saved: [] }>();

const isEdit = computed(() => props.user != null);

const name = ref(props.user?.name ?? "");
const role = ref<UserRole>(props.user?.role ?? "member");
const telegramChatId = ref(props.user?.telegram_chat_id ?? "");

const error = ref<string | null>(null);
const saving = ref(false);

async function submit() {
  error.value = null;

  if (!name.value.trim()) {
    error.value = "El nombre es obligatorio.";
    return;
  }

  const trimmedName = name.value.trim();

  saving.value = true;
  try {
    if (props.user) {
      const body: Record<string, string> = {};
      if (trimmedName !== props.user.name) body.name = trimmedName;
      if (role.value !== props.user.role) body.role = role.value;
      if (telegramChatId.value !== (props.user.telegram_chat_id ?? "")) {
        body.telegram_chat_id = telegramChatId.value;
      }
      if (Object.keys(body).length === 0) {
        error.value = "No hay cambios para guardar.";
        saving.value = false;
        return;
      }
      await usersApi.update(props.user.id, body);
    } else {
      await usersApi.create({
        name: trimmedName,
        role: role.value,
        ...(telegramChatId.value ? { telegram_chat_id: telegramChatId.value } : {}),
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
  <Modal :title="isEdit ? 'Editar usuario' : 'Nuevo usuario'" @close="emit('close')">
    <form class="space-y-4" @submit.prevent="submit">
      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">Nombre</label>
        <input
          v-model="name"
          type="text"
          placeholder="Nombre del usuario"
          class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
        />
      </div>

      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">Rol</label>
        <select
          v-model="role"
          class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
        >
          <option value="member">Miembro</option>
          <option value="admin">Admin</option>
        </select>
      </div>

      <div>
        <label class="mb-1 block text-xs font-medium text-slate-500">Telegram Chat ID</label>
        <input
          v-model="telegramChatId"
          type="text"
          placeholder="123456789"
          class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
        />
      </div>

      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

      <div class="flex justify-end gap-2 pt-1">
        <button
          type="button"
          class="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100"
          @click="emit('close')"
        >
          Cancelar
        </button>
        <button
          type="submit"
          :disabled="saving"
          class="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-700 disabled:opacity-50"
        >
          {{ saving ? "Guardando…" : isEdit ? "Guardar" : "Crear" }}
        </button>
      </div>
    </form>
  </Modal>
</template>
