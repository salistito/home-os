<script setup lang="ts">
import IconButton from "../../components/IconButton.vue";
import Skeleton from "../../components/Skeleton.vue";
import { icons } from "../../lib/icons";
</script>

<template>
  <div class="space-y-4">
    <div class="grid grid-cols-3 gap-3">
      <div
        v-for="n in 3"
        :key="n"
        class="flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-4 text-center"
      >
        <Skeleton width="50%" height="0.75rem" rounded class="mx-auto" />
        <div class="mt-2">
          <Skeleton width="80%" height="1.5rem" rounded class="mx-auto" />
        </div>
      </div>
    </div>

    <section class="rounded-xl border border-slate-200 bg-white">
      <header class="flex items-center gap-2 border-b border-slate-100 px-4 py-3">
        <Skeleton width="6rem" height="0.875rem" rounded />
        <span class="ml-auto">
          <div class="flex rounded-lg bg-slate-100 p-0.5">
            <Skeleton width="2.5rem" height="1.25rem" rounded />
            <Skeleton width="2.5rem" height="1.25rem" rounded class="ml-0.5" />
            <Skeleton width="2.75rem" height="1.25rem" rounded class="ml-0.5" />
          </div>
        </span>
      </header>
      <div class="px-4 py-4">
        <div class="mb-3 flex items-center justify-between">
          <Skeleton width="10rem" text rounded />
          <Skeleton width="7rem" text rounded />
        </div>
        <Skeleton width="100%" height="12rem" rounded />
      </div>
    </section>

    <section class="rounded-xl border border-slate-200 bg-white">
      <header class="flex items-center gap-2 border-b border-slate-100 px-4 py-3">
        <Skeleton width="6rem" height="0.875rem" rounded />
        <Skeleton width="1.5rem" height="0.875rem" />
        <span class="ml-auto hidden h-8 w-32 animate-pulse rounded-lg bg-slate-200 lg:block" />
      </header>
      <div class="divide-y divide-slate-100">
        <div v-for="n in 1" :key="`h${n}`" class="bg-slate-100/50 px-4 py-2">
          <div class="flex items-center justify-between">
            <Skeleton width="6rem" height="0.75rem" />
            <Skeleton width="3rem" height="0.75rem" />
          </div>
        </div>
        <div v-for="n in 3" :key="n" class="flex items-center gap-3 px-4 py-3">
          <Skeleton width="3.5rem" text rounded />
          <div class="flex items-baseline gap-1">
            <Skeleton width="3.5rem" text rounded />
            <Skeleton width="3rem" text rounded />
          </div>
          <span class="ml-auto flex shrink-0 items-center gap-1 sm:ml-0 sm:opacity-0">
            <IconButton :icon="icons.pencil" label="Editar registro" />
            <IconButton :icon="icons.trash" label="Eliminar registro" variant="danger" />
          </span>
        </div>
      </div>
    </section>
  </div>
</template>
