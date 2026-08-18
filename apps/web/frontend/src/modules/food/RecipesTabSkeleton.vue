<script setup lang="ts">
import IconButton from "../../components/IconButton.vue";
import Skeleton from "../../components/Skeleton.vue";
import { icons } from "../../lib/icons";
</script>

<template>
  <div class="overflow-hidden rounded-xl border border-slate-200 bg-white">
    <div class="flex items-center gap-2 border-b border-slate-100 px-4 py-3">
      <Skeleton width="6rem" height="1rem" />
      <Skeleton width="1.5rem" height="0.875rem" />
      <span class="ml-auto hidden h-8 w-32 animate-pulse rounded-lg bg-slate-200 lg:block" />
    </div>
    <div class="flex items-center gap-2 border-b border-slate-100 px-4 py-2">
      <Skeleton width="100%" height="2.25rem" rounded class="flex-1" />
      <span class="block h-9 w-9 shrink-0 animate-pulse rounded-lg bg-slate-200" />
    </div>
    <div
      class="hidden grid-cols-[1fr_8rem_6rem_12rem_6rem_7rem] items-center gap-2 border-b border-slate-100 bg-slate-50/60 px-4 py-2 sm:grid"
    >
      <Skeleton v-for="n in 5" :key="n" width="5rem" height="0.75rem" />
      <span />
    </div>
    <ul class="divide-y divide-slate-100">
      <li
        v-for="n in 4"
        :key="n"
        class="flex items-start gap-3 px-4 py-3 sm:grid sm:grid-cols-[1fr_8rem_6rem_12rem_6rem_7rem] sm:items-center sm:gap-2 sm:py-2.5"
      >
        <div class="min-w-0 flex-1 sm:contents">
          <Skeleton width="9rem" />
          <div class="mt-1.5 flex flex-wrap items-center gap-2 sm:contents">
            <Skeleton width="4rem" height="1.25rem" rounded />
            <Skeleton width="4rem" height="1.25rem" rounded />
          </div>
          <div class="mt-1 flex flex-wrap items-center gap-2 sm:contents">
            <Skeleton width="10rem" />
          </div>
          <div class="mt-1 flex flex-wrap items-center gap-2 sm:contents">
            <Skeleton width="5rem" height="1.25rem" rounded />
          </div>
        </div>
        <span class="flex items-center gap-1">
            <span
              class="ml-auto flex shrink-0 items-center gap-0.5 transition-opacity sm:opacity-0 sm:group-hover:opacity-100"
              @click.stop
            >
              <IconButton :icon="icons.pot" label="Cocinar" />
              <IconButton :icon="icons.pencil" label="Editar" />
              <IconButton :icon="icons.trash" label="Eliminar" variant="danger" />
            </span>
          </span>
      </li>
    </ul>
  </div>
</template>
