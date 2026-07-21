<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ApiRequestError } from "../../api/client";
import { usersApi } from "../../api/users";
import { auth } from "../../lib/auth";
import Icon from "../../components/Icon.vue";
import IconButton from "../../components/IconButton.vue";
import Modal from "../../components/Modal.vue";
import Skeleton from "../../components/Skeleton.vue";
import WidgetCard from "../../components/WidgetCard.vue";
import { icons } from "../../lib/icons";
import { pushToast } from "../../lib/toast";
import type { UserRef } from "../../types";
import UserFormModal from "./UserFormModal.vue";

const users = ref<UserRef[]>([]);
const error = ref<string | null>(null);
const loading = ref(true);

const formOpen = ref(false);
const editing = ref<UserRef | null>(null);

const deleting = ref<UserRef | null>(null);
const deleteError = ref<string | null>(null);
const deleteBusy = ref(false);

async function load() {
  try {
    users.value = await usersApi.list();
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Error inesperado";
  } finally {
    loading.value = false;
  }
}

function openCreate() {
  editing.value = null;
  formOpen.value = true;
}

function openEdit(user: UserRef) {
  editing.value = user;
  formOpen.value = true;
}

async function onSaved() {
  const wasEdit = editing.value != null;
  formOpen.value = false;
  await load();
  pushToast(wasEdit ? "Usuario actualizado" : "Usuario creado");
}

function askDelete(user: UserRef) {
  if (user.id === auth.userId.value) {
    pushToast("No puedes eliminarte a ti mismo.", "error");
    return;
  }
  const activeAdmins = users.value.filter(
    (u) => u.role === "admin" && u.deleted_at === null,
  );
  if (user.role === "admin" && activeAdmins.length <= 1) {
    pushToast("No se puede eliminar al último administrador.", "error");
    return;
  }
  deleting.value = user;
  deleteError.value = null;
}

async function confirmDelete() {
  if (!deleting.value) return;
  deleteBusy.value = true;
  try {
    await usersApi.delete(deleting.value.id);
    deleting.value = null;
    await load();
    pushToast("Usuario eliminado");
  } catch (e) {
    deleteError.value =
      e instanceof ApiRequestError ? e.message : "No se pudo eliminar el usuario.";
  } finally {
    deleteBusy.value = false;
  }
}

async function restoreUser(user: UserRef) {
  try {
    await usersApi.update(user.id, { restore: true });
    await load();
    pushToast("Usuario restaurado");
  } catch (e) {
    pushToast(
      e instanceof ApiRequestError ? e.message : "No se pudo restaurar el usuario.",
      "error",
    );
  }
}

const activeCount = computed(
  () => users.value.filter((u) => u.deleted_at === null).length,
);

onMounted(load);
</script>

<template>
  <WidgetCard title="Usuarios" :count="!loading && !error ? activeCount : undefined">
    <template #actions>
      <button
        type="button"
        class="inline-flex items-center gap-1 rounded-lg bg-slate-900 px-2.5 py-1.5 text-xs font-medium text-white transition-colors hover:bg-slate-700"
        @click="openCreate"
      >
        <Icon :path="icons.plus" :size="14" />
        Nuevo usuario
      </button>
    </template>

    <p v-if="error" class="px-4 py-6 text-sm text-red-600">{{ error }}</p>

    <p
      v-else-if="!loading && users.length === 0"
      class="px-4 py-10 text-center text-sm text-slate-500"
    >
      No hay usuarios registrados.
    </p>

    <div v-else>
      <div
        class="hidden grid-cols-[1fr_6rem_9rem_5rem_5.25rem] items-center gap-3 border-b border-slate-100 bg-slate-50/60 px-4 py-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400 sm:grid"
      >
        <span>Nombre</span>
        <span>Rol</span>
        <span>Telegram Chat ID</span>
        <span>Estado</span>
        <span></span>
      </div>

      <ul class="divide-y divide-slate-100">
        <template v-if="loading">
          <li
            v-for="n in 4"
            :key="n"
            class="flex items-center gap-3 px-4 py-3 sm:grid sm:grid-cols-[1fr_6rem_9rem_5rem_5.25rem] sm:items-center sm:py-2.5"
          >
            <Skeleton width="8rem" />
            <Skeleton width="3rem" />
            <Skeleton width="5rem" />
            <Skeleton width="3rem" />
            <span></span>
          </li>
        </template>

        <template v-else>
          <li
            v-for="user in users"
            :key="user.id"
            class="group flex items-start gap-3 px-4 py-3 transition-colors hover:bg-slate-50 sm:grid sm:grid-cols-[1fr_6rem_9rem_5rem_5.25rem] sm:items-center sm:py-2.5"
          >
            <div class="min-w-0 flex-1 sm:contents">
              <span
                class="block truncate text-[13px] font-medium text-slate-800"
              >
                {{ user.name }}
              </span>

              <span
                class="inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ring-1 sm:justify-self-start"
                :class="
                  user.role === 'admin'
                    ? 'bg-purple-50 text-purple-700 ring-purple-100'
                    : 'bg-slate-50 text-slate-600 ring-slate-200'
                "
              >
                {{ user.role === "admin" ? "Admin" : "Miembro" }}
              </span>

              <span
                class="inline-flex items-center gap-1 text-xs text-slate-400 sm:justify-self-start"
              >
                {{ user.telegram_chat_id ?? "—" }}
              </span>

              <span
                class="inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ring-1 sm:justify-self-start"
                :class="
                  user.deleted_at === null
                    ? 'bg-emerald-50 text-emerald-700 ring-emerald-100'
                    : 'bg-slate-100 text-slate-400 ring-slate-200'
                "
              >
                {{ user.deleted_at === null ? "Activo" : "Eliminado" }}
              </span>

              <span
                class="flex shrink-0 items-center justify-end gap-0.5 transition-opacity sm:opacity-0 sm:group-hover:opacity-100"
              >
                <IconButton
                  :icon="icons.pencil"
                  label="Editar"
                  @click="openEdit(user)"
                />
                <IconButton
                  v-if="user.deleted_at === null"
                  :icon="icons.trash"
                  label="Eliminar"
                  variant="danger"
                  @click="askDelete(user)"
                />
                <IconButton
                  v-if="user.deleted_at !== null"
                  :icon="icons.repeat"
                  label="Restaurar"
                  @click="restoreUser(user)"
                />
              </span>
            </div>
          </li>
        </template>
      </ul>
    </div>
  </WidgetCard>

  <UserFormModal
    v-if="formOpen"
    :user="editing"
    @close="formOpen = false"
    @saved="onSaved"
  />

  <Modal v-if="deleting" title="Eliminar usuario" @close="deleting = null">
    <p class="text-sm text-slate-600">
      ¿Seguro que quieres eliminar
      <span class="font-medium text-slate-900">{{ deleting.name }}</span>?
    </p>
    <p class="mt-3 text-xs text-slate-400">
      El usuario se marcará como eliminado. Sus datos seguirán visibles en el historial.
    </p>
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
        {{ deleteBusy ? "Eliminando…" : "Eliminar" }}
      </button>
    </div>
  </Modal>
</template>
