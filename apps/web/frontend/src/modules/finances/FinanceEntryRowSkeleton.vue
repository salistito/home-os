<script setup lang="ts">
import IconButton from "../../components/IconButton.vue";
import Skeleton from "../../components/Skeleton.vue";
import { icons } from "../../lib/icons";
</script>

<template>
  <li class="group py-2.5">
    <div class="flex items-start justify-between gap-3">
      <div class="flex min-w-0 items-center gap-1">
        <Skeleton width="8rem" />
      </div>
      <div class="flex shrink-0 items-center gap-2">
        <Skeleton width="4rem" />
        <span
          class="flex shrink-0 items-center justify-end gap-0.5 transition-opacity sm:opacity-0 sm:group-hover:opacity-100"
        >
          <IconButton :icon="icons.pencil" label="Editar" />
          <IconButton :icon="icons.trash" label="Eliminar" variant="danger" />
        </span>
      </div>
    </div>
    <div class="mt-1.5 flex flex-wrap items-center gap-1.5">
      <span class="block h-2.5 w-2.5 shrink-0 animate-pulse rounded-full bg-slate-200" />
      <Skeleton width="4rem" height="0.75rem" />
      <Skeleton width="4rem" height="1.25rem" rounded />
    </div>
  </li>
</template>