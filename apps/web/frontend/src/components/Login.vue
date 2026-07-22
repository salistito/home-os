<script setup lang="ts">
import { computed, ref } from "vue";
import { api, ApiRequestError } from "../api/client";
import { auth, type LoginResponse } from "../lib/auth";

const mode = ref<"login" | "signup">("login");
const username = ref("");
const password = ref("");
const confirmPassword = ref("");
const error = ref<string | null>(null);
const loading = ref(false);

const isSignup = computed(() => mode.value === "signup");

async function submit() {
  if (loading.value) return;
  error.value = null;

  if (isSignup.value) {
    if (!password.value) {
      error.value = "La contrase\u00f1a es obligatoria.";
      return;
    }
    if (password.value.length < 6) {
      error.value = "La contrase\u00f1a debe tener al menos 6 caracteres.";
      return;
    }
    if (password.value !== confirmPassword.value) {
      error.value = "Las contrase\u00f1as no coinciden.";
      return;
    }
  }

  loading.value = true;
  try {
    if (isSignup.value) {
      const res = await api.post<LoginResponse>("/signup", {
        name: username.value.trim(),
        password: password.value,
      });
      auth.applySession(res);
    } else {
      await auth.login(username.value.trim(), password.value);
    }
  } catch (e) {
    error.value =
      e instanceof ApiRequestError
        ? e.message
        : "No se pudo conectar. Intenta de nuevo.";
  } finally {
    loading.value = false;
  }
}

function toggleMode() {
  mode.value = isSignup.value ? "login" : "signup";
  error.value = null;
  confirmPassword.value = "";
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
        <img
          src="/homeos-logo.png"
          alt="HomeOS"
          class="h-7 w-7 rounded-md object-cover"
        />
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
        :autocomplete="isSignup ? 'new-password' : 'current-password'"
        class="mb-3 w-full rounded-md border border-slate-200 px-3 py-2 text-sm outline-none focus:border-slate-400 focus:ring-1 focus:ring-slate-300"
      />

      <label
        v-if="isSignup"
        class="mb-1 block text-[13px] font-medium text-slate-600"
      >
        Confirmar contraseña
      </label>
      <input
        v-if="isSignup"
        v-model="confirmPassword"
        type="password"
        autocomplete="new-password"
        class="mb-4 w-full rounded-md border border-slate-200 px-3 py-2 text-sm outline-none focus:border-slate-400 focus:ring-1 focus:ring-slate-300"
      />

      <p v-if="error" class="mb-3 text-[13px] text-red-600">{{ error }}</p>

      <button
        type="submit"
        :disabled="loading"
        class="w-full rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-800 disabled:opacity-60"
      >
        <template v-if="isSignup">
          {{ loading ? "Creando acceso..." : "Crear acceso" }}
        </template>
        <template v-else>
          {{ loading ? "Iniciando sesión..." : "Iniciar sesión" }}
        </template>
      </button>

      <p class="mt-4 text-center text-[13px] text-slate-500">
        <template v-if="isSignup">
          ¿Ya tienes una cuenta?
          <button
            type="button"
            class="font-medium text-slate-700 underline hover:text-slate-900"
            @click="toggleMode"
          >
            Inicia sesión
          </button>
        </template>
        <template v-else>
          ¿Aún no creas tu acceso?
          <button
            type="button"
            class="font-medium text-slate-700 underline hover:text-slate-900"
            @click="toggleMode"
          >
            Registrate
          </button>
        </template>
      </p>
    </form>
  </div>
</template>
