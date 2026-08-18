<script setup lang="ts">
import IconButton from "../../components/IconButton.vue";
import Skeleton from "../../components/Skeleton.vue";
import { icons } from "../../lib/icons";
</script>

<template>
  <div class="space-y-4">
    <div class="rounded-xl border border-slate-200 bg-white p-3">
      <div class="mb-3 flex items-center justify-between gap-2">
        <div class="flex min-w-0 items-center gap-1">
          <IconButton dense :icon="icons.chevronLeft" label="Semana anterior"  />
          <Skeleton width="12rem" height="1rem" />
          <IconButton dense :icon="icons.chevronRight" label="Semana siguiente" />
        </div>
        <span class="block h-5 w-5 shrink-0 animate-pulse rounded-lg bg-slate-200" />
      </div>
      <div class="grid grid-cols-7 gap-1.5">
        <div
          v-for="n in 7"
          :key="n"
          class="flex flex-col items-center gap-1 px-1 py-2"
        >
          <Skeleton width="1.75rem" height="0.6875rem" />
          <span class="block h-8 w-8 animate-pulse rounded-full bg-slate-200" />
        </div>
      </div>
    </div>

    <div class="overflow-hidden rounded-xl border border-slate-200 bg-white">
      <div class="flex items-center gap-2 border-b border-slate-100 px-4 py-3">
        <Skeleton width="12rem" height="1rem" />
        <Skeleton width="1.5rem" height="0.875rem" />
        <span class="ml-auto hidden h-8 w-32 animate-pulse rounded-lg bg-slate-200 lg:block" />
      </div>
      <div class="flex items-center gap-2 border-b border-slate-100 px-4 py-2">
        <Skeleton width="100%" height="2.25rem" rounded class="flex-1" />
        <span class="block h-9 w-9 shrink-0 animate-pulse rounded-lg bg-slate-200" />
      </div>
      <ul class="divide-y divide-slate-100">
        <li
          v-for="n in 4"
          :key="n"
          class="flex items-start gap-3 px-4 py-3"
        >
          <div class="min-w-0 flex-1">
            <Skeleton width="9rem" />
            <Skeleton width="10rem" class="mt-2" />
            <div class="mt-2 flex flex-wrap items-center gap-2">
              <Skeleton width="4rem" height="1.25rem" rounded />
              <Skeleton width="5rem" height="1.25rem" rounded />
            </div>
          </div>
          <Skeleton width="5rem" height="1.25rem" rounded />
        </li>
      </ul>
    </div>
  </div>
</template>
