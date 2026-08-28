<script setup lang="ts">
import IconButton from "../../components/IconButton.vue";
import Skeleton from "../../components/Skeleton.vue";
import { icons } from "../../lib/icons";
</script>

<template>
  <section class="rounded-xl border border-slate-200 bg-white">
    <header class="flex items-center gap-2 border-b border-slate-100 px-4 py-3">
      <Skeleton width="20%" text rounded />
      <Skeleton width="6rem" height="0.875rem" />
      <div class="ml-auto">
        <Skeleton width="7rem" height="1.75rem" rounded class="hidden lg:block" />
      </div>
    </header>
    <div class="flex items-center gap-2 border-b border-slate-100 px-4 py-2">
      <Skeleton width="60%" height="2.25rem" rounded class="flex-1" />
      <IconButton :icon="icons.filter" label="Filtros" />
    </div>
    <div
      class="hidden grid-cols-[minmax(0,1fr)_6rem_9rem_10rem_4.75rem] items-center gap-3 border-b border-slate-100 bg-slate-50/60 px-4 py-2 sm:grid"
    >
      <Skeleton width="5rem" text rounded />
      <Skeleton width="3rem" text rounded class="justify-self-center" />
      <div class="flex flex-col items-center space-y-1">
        <Skeleton width="7rem" text rounded />
        <Skeleton width="7rem" text rounded />
      </div>
      <div class="flex flex-col items-center space-y-1">
        <Skeleton width="8rem" text rounded />
        <Skeleton width="7rem" text rounded />
      </div>
      <span></span>
    </div>
    <div class="divide-y divide-slate-100">
      <div
        v-for="n in 6"
        :key="n"
        class="flex items-start gap-3 px-4 py-3 sm:grid sm:grid-cols-[minmax(0,1fr)_6rem_9rem_10rem_4.75rem] sm:items-center sm:py-2.5"
      >
        <div class="min-w-0 flex-1 space-y-1.5 sm:contents">
          <Skeleton width="8rem" text rounded />
          <Skeleton width="3.5rem" height="1.125rem" rounded class="sm:justify-self-center" />
          <div class="flex w-full flex-col gap-1.5 sm:hidden">
            <Skeleton width="5rem" height="0.75rem" rounded />
            <div class="flex flex-wrap items-center gap-1.5">
              <Skeleton width="8rem" height="1.125rem" rounded />
              <Skeleton width="10rem" height="1.125rem" rounded />
            </div>
          </div>
          <div class="hidden items-center gap-1 sm:flex sm:justify-self-center">
            <Skeleton width="8rem" height="1.125rem" rounded />
          </div>
          <div class="hidden sm:block">
            <Skeleton width="10rem" height="1.125rem" rounded />
          </div>
        </div>
        <span class="flex shrink-0 items-center justify-end gap-1 sm:opacity-0">
          <IconButton :icon="icons.pencil" label="Editar" />
          <IconButton :icon="icons.trash" label="Eliminar" variant="danger" />
        </span>
      </div>
    </div>
  </section>
</template>
