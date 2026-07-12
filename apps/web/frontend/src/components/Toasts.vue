<script setup lang="ts">
import { toasts, dismissToast } from "../lib/toast";
</script>

<template>
  <Teleport to="body">
    <div class="fixed bottom-4 right-4 z-[60] flex flex-col gap-2">
      <TransitionGroup name="toast">
        <button
          v-for="toast in toasts"
          :key="toast.id"
          type="button"
          class="flex items-center gap-2 rounded-lg border px-3.5 py-2.5 text-sm font-medium shadow-lg"
          :class="
            toast.kind === 'success'
              ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
              : 'border-red-200 bg-red-50 text-red-800'
          "
          @click="dismissToast(toast.id)"
        >
          <span
            class="h-1.5 w-1.5 rounded-full"
            :class="toast.kind === 'success' ? 'bg-emerald-500' : 'bg-red-500'"
          />
          {{ toast.message }}
        </button>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.2s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
