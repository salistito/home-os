<script setup lang="ts">
import { ref } from "vue";
import { auth } from "../lib/auth";
import { ApiRequestError } from "../api/client";

const username = ref("");
const password = ref("");
const error = ref<string | null>(null);
const loading = ref(false);

async function submit() {
  if (loading.value) return;
  error.value = null;
  loading.value = true;
  try {
    await auth.login(username.value.trim(), password.value);
  } catch (e) {
    error.value =
      e instanceof ApiRequestError
        ? e.message
        : "No se pudo conectar. Intenta de nuevo.";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div
    class="flex min-h-screen items-center justify-center bg-slate-50/50 px-4 font-sans text-slate-900 antialiased"
  >
    <form
      class="w-full max-w-sm rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
      @submit.prevent="submit"
    >
      <div class="mb-6 flex items-center gap-2.5">
        <div
          class="flex h-7 w-7 items-center justify-center rounded-md bg-slate-900 text-xs font-bold text-white"
        >
          H
        </div>
        <span class="text-base font-semibold text-slate-800">HomeOS</span>
      </div>

      <label class="mb-1 block text-[13px] font-medium text-slate-600">
        Usuario
      </label>
      <input
        v-model="username"
        type="text"
        autocomplete="username"
        autocapitalize="none"
        autofocus
        class="mb-4 w-full rounded-md border border-slate-200 px-3 py-2 text-sm outline-none focus:border-slate-400 focus:ring-1 focus:ring-slate-300"
      />

      <label class="mb-1 block text-[13px] font-medium text-slate-600">
        Contraseña
      </label>
      <input
        v-model="password"
        type="password"
        autocomplete="current-password"
        class="mb-4 w-full rounded-md border border-slate-200 px-3 py-2 text-sm outline-none focus:border-slate-400 focus:ring-1 focus:ring-slate-300"
      />

      <p v-if="error" class="mb-3 text-[13px] text-red-600">{{ error }}</p>

      <button
        type="submit"
        :disabled="loading"
        class="w-full rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-800 disabled:opacity-60"
      >
        {{ loading ? "Entrando..." : "Entrar" }}
      </button>
    </form>
  </div>
</template>
