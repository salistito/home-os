<script setup lang="ts">
import Skeleton from "../../components/Skeleton.vue";
</script>

<template>
  <div class="space-y-4">
    <div class="grid grid-cols-3 gap-3">
      <div
        v-for="n in 3"
        :key="n"
        class="rounded-xl border border-slate-200 bg-white p-4"
      >
        <Skeleton width="55%" text rounded />
        <div class="mt-2">
          <Skeleton width="70%" height="1.5rem" rounded />
        </div>
      </div>
    </div>

    <section class="rounded-xl border border-slate-200 bg-white">
      <header class="border-b border-slate-100 px-4 py-3">
        <Skeleton width="30%" text rounded />
      </header>
      <div class="px-4 py-4">
        <Skeleton width="100%" height="12rem" rounded />
      </div>
    </section>

    <section class="rounded-xl border border-slate-200 bg-white">
      <header
        class="flex items-center gap-2 border-b border-slate-100 px-4 py-3"
      >
        <Skeleton width="25%" text rounded />
      </header>
      <div class="divide-y divide-slate-100">
        <div v-for="n in 5" :key="n" class="flex items-center gap-3 px-4 py-3">
          <Skeleton width="6rem" text rounded />
          <Skeleton width="5rem" text rounded />
          <span class="ml-auto"
            ><Skeleton width="2rem" height="1.75rem" rounded
          /></span>
        </div>
      </div>
    </section>
  </div>
</template>
