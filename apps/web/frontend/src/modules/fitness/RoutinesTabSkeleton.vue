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
        <Skeleton width="8rem" height="1.75rem" rounded class="hidden lg:block" />
      </div>
    </header>
    <div class="flex items-center gap-2 border-b border-slate-100 px-4 py-2">
      <Skeleton width="60%" height="2.25rem" rounded class="flex-1" />
    </div>
    <div class="divide-y divide-slate-100">
      <div
        v-for="n in 4"
        :key="n"
        class="flex items-start gap-3 px-4 py-3"
      >
        <div class="min-w-0 flex-1 space-y-1.5">
          <div class="flex items-center gap-2">
            <Skeleton width="8rem" text rounded />
            <Skeleton width="4rem" height="1.125rem" rounded />
          </div>
          <Skeleton width="15rem" height="0.75rem" rounded />
          <Skeleton width="5rem" height="1.125rem" rounded />
        </div>
        <div class="flex shrink-0 items-center gap-1">
          <IconButton :icon="icons.pencil" label="Editar" />
          <IconButton :icon="icons.trash" label="Eliminar" variant="danger" />
          <IconButton :icon="icons.chevronDown" label="Expandir" />
        </div>
      </div>
    </div>
  </section>
</template>
