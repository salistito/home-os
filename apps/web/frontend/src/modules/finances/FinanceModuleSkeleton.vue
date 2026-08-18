<script setup lang="ts">
import Skeleton from "../../components/Skeleton.vue";
import FinanceEntryRowSkeleton from "./FinanceEntryRowSkeleton.vue";

withDefaults(defineProps<{ variant?: "full" | "content" }>(), {
  variant: "full",
});
</script>

<template>
  <div class="space-y-4">
    <template v-if="variant === 'full'">
      <div class="flex items-center justify-between gap-2">
        <div class="inline-flex items-center overflow-hidden rounded-lg border border-slate-200">
          <Skeleton width="12rem" height="1.5rem" rounded />
        </div>
        <Skeleton width="8rem" height="1.5rem" rounded />
      </div>

      <div class="rounded-xl border border-slate-200 bg-white px-4 py-4">
        <header class="flex items-center gap-2 border-b border-slate-100 pb-4">
          <Skeleton width="5rem" />
          <Skeleton width="4rem" height="1.25rem" rounded />
          <span class="block h-2.5 w-2.5 shrink-0 animate-pulse rounded-full bg-slate-200" />
          <Skeleton width="6rem" class="ml-auto hidden shrink-0 sm:block" />
        </header>

        <nav class="flex min-w-0 items-center gap-4 border-b border-slate-200 pt-3 pb-2">
          <div
            v-for="n in 3"
            :key="n"
            class="flex shrink-0 items-center gap-1.5"
          >
            <span class="block h-2.5 w-2.5 shrink-0 animate-pulse rounded-full bg-slate-200" />
            <Skeleton width="4rem" />
          </div>
        </nav>

        <div class="space-y-4 pt-4">
          <div class="flex flex-wrap gap-2">
            <div
              v-for="n in 3"
              :key="n"
              class="flex flex-1 flex-col gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2"
            >
              <div class="flex items-center gap-1.5">
                <span class="block h-2.5 w-2.5 shrink-0 animate-pulse rounded-full bg-slate-200" />
                <Skeleton width="4rem" height="0.75rem" />
              </div>
              <Skeleton width="6rem" />
            </div>
          </div>

          <div class="flex flex-wrap items-center justify-between gap-2">
            <Skeleton width="6rem" />
            <Skeleton width="5rem" height="1.5rem" rounded />
          </div>

          <ul class="divide-y divide-slate-100 pt-1">
            <FinanceEntryRowSkeleton v-for="n in 3" :key="n" />
          </ul>

          <div class="grid grid-cols-[minmax(0,1fr)_auto_auto] items-center gap-x-3 border-t border-slate-200 pt-2">
            <Skeleton width="3rem" height="0.75rem" />
            <Skeleton width="6rem" />
            <span class="w-[40px]" />
          </div>
        </div>
      </div>
    </template>

    <div v-else class="space-y-4 pt-4">
      <div class="flex flex-wrap gap-2">
        <div
          v-for="n in 3"
          :key="n"
          class="flex flex-1 flex-col gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2"
        >
          <div class="flex items-center gap-1.5">
            <span class="block h-2.5 w-2.5 shrink-0 animate-pulse rounded-full bg-slate-200" />
            <Skeleton width="4rem" height="0.75rem" />
          </div>
          <Skeleton width="6rem" />
        </div>
      </div>

      <div class="flex flex-wrap items-center justify-between gap-2">
        <Skeleton width="6rem" />
        <Skeleton width="5rem" height="1.5rem" rounded />
      </div>

      <ul class="divide-y divide-slate-100 pt-1">
        <FinanceEntryRowSkeleton v-for="n in 3" :key="n" />
      </ul>

      <div class="grid grid-cols-[minmax(0,1fr)_auto_auto] items-center gap-x-3 border-t border-slate-200 pt-2">
        <Skeleton width="3rem" height="0.75rem" />
        <Skeleton width="6rem" />
        <span class="w-[40px]" />
      </div>
    </div>
  </div>
</template>
