<script setup lang="ts">
import IconButton from "../../components/IconButton.vue";
import Skeleton from "../../components/Skeleton.vue";
import { icons } from "../../lib/icons";
</script>

<template>
  <div class="space-y-4">
    <div class="hidden rounded-xl border border-slate-200 bg-white p-3 lg:block">
      <div class="mb-3 flex items-center justify-between gap-2">
        <div class="flex min-w-0 items-center gap-1">
          <IconButton dense :icon="icons.chevronLeft" label="Semana anterior" />
          <Skeleton width="12rem" height="1rem" />
          <IconButton dense :icon="icons.chevronRight" label="Semana siguiente" />
        </div>
        <div class="flex shrink-0 items-center gap-1">
          <IconButton :icon="icons.calendar" label="Cambiar fecha" />
        </div>
      </div>
      <div class="grid grid-cols-7 gap-1.5">
        <div
          v-for="n in 7"
          :key="n"
          class="flex flex-col items-center gap-1 px-1 py-2"
        >
          <Skeleton width="1.75rem" height="0.6875rem" />
          <span
            class="block h-8 w-8 animate-pulse rounded-full"
            :class="n === 1 ? 'bg-slate-300' : 'bg-slate-200'"
          />
        </div>
      </div>
    </div>

    <section class="rounded-xl border border-slate-200 bg-white p-4">
      <header
        class="-mx-1 flex items-center justify-between gap-1 border-b border-slate-100 pb-3 lg:hidden"
      >
        <div class="flex min-w-0 items-center gap-1">
          <IconButton dense :icon="icons.chevronLeft" label="Anterior" />
          <Skeleton width="12rem" height="1rem" />
          <IconButton dense :icon="icons.chevronRight" label="Siguiente" />
        </div>
        <div class="flex shrink-0 items-center gap-1">
          <IconButton :icon="icons.calendar" label="Cambiar fecha" />
        </div>
      </header>

      <div class="mt-3 flex items-start justify-between gap-2 lg:hidden">
        <div class="flex min-w-0 items-center gap-2 max-[420px]:flex-wrap">
          <Skeleton width="11rem" height="1rem" />
          <div class="flex shrink-0 rounded-lg bg-slate-100 p-0.5">
            <Skeleton width="2.75rem" height="1.25rem" rounded />
            <Skeleton width="3.5rem" height="1.25rem" rounded class="ml-0.5" />
          </div>
        </div>
      </div>

      <div class="hidden items-center justify-between lg:flex">
        <div class="flex items-center gap-2">
          <Skeleton width="12rem" height="1rem" />
          <div class="flex rounded-lg bg-slate-100 p-0.5">
            <Skeleton width="2.75rem" height="1.25rem" rounded />
            <Skeleton width="3.5rem" height="1.25rem" rounded class="ml-0.5" />
          </div>
        </div>
      </div>

      <div class="mt-4 flex flex-wrap items-center gap-2">
        <span
          v-for="n in 3"
          :key="n"
          class="inline-flex items-center gap-2 rounded-xl bg-slate-50 px-3.5 py-2.5 ring-1 ring-slate-200"
        >
          <span class="block h-[18px] w-[18px] shrink-0 animate-pulse rounded-md bg-slate-200" />
          <Skeleton :width="n === 1 ? '7rem' : '5rem'" height="1rem" />
        </span>
      </div>

      <div class="mt-4 border-t border-slate-100 pt-4">
        <div class="flex items-center justify-between">
          <Skeleton width="10rem" height="0.75rem" />
          <span class="flex items-center gap-2">
            <Skeleton width="6rem" height="0.75rem" />
            <IconButton :icon="icons.chevronDown" label="Expandir" />
          </span>
        </div>
      </div>

      <div class="mt-4 border-t border-slate-100 pt-4">
        <div class="flex items-center justify-between">
          <Skeleton width="8rem" height="0.75rem" />
          <IconButton :icon="icons.chevronDown" label="Expandir" />
        </div>
      </div>
    </section>

    <section class="rounded-xl border border-slate-200 bg-white">
      <header class="flex items-center gap-2 border-b border-slate-100 px-4 py-3">
        <Skeleton width="8rem" text rounded />
        <Skeleton width="1.5rem" height="0.875rem" />
        <span class="ml-auto hidden h-8 w-40 animate-pulse rounded-lg bg-slate-200 lg:block" />
      </header>
      <div class="divide-y divide-slate-100">
        <div v-for="n in 1" :key="`h${n}`" class="bg-slate-100/50 px-4 py-2">
          <div class="flex items-center justify-between">
            <Skeleton width="3rem" height="0.75rem" />
            <div class="flex items-center gap-2">
              <Skeleton width="2.5rem" height="0.6875rem" />
              <Skeleton width="2.5rem" height="0.6875rem" />
              <Skeleton width="2.5rem" height="0.6875rem" />
            </div>
          </div>
        </div>
        <div v-for="n in 3" :key="n" class="flex items-center gap-3 pl-4 pr-1 py-3">
          <span class="hidden h-9 w-9 shrink-0 animate-pulse rounded-full bg-slate-200 sm:block" />
          <div class="min-w-0 flex-1">
            <Skeleton width="10rem" />
            <div class="mt-2 flex flex-wrap items-center gap-2">
              <Skeleton width="4rem" height="1.25rem" rounded />
              <Skeleton width="4rem" height="1.25rem" rounded />
              <Skeleton width="4rem" height="1.25rem" rounded />
            </div>
          </div>
          <span class="flex shrink-0 items-center gap-1 sm:opacity-0">
            <IconButton :icon="icons.pencil" label="Editar" />
            <IconButton :icon="icons.trash" label="Eliminar" variant="danger" />
          </span>
        </div>
      </div>
    </section>
  </div>
</template>
