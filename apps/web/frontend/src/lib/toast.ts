import { ref } from "vue";

export type ToastKind = "success" | "error";

export interface Toast {
  id: number;
  message: string;
  kind: ToastKind;
}

export const toasts = ref<Toast[]>([]);

let nextId = 0;

export function pushToast(message: string, kind: ToastKind = "success") {
  const id = nextId++;
  toasts.value.push({ id, message, kind });
  setTimeout(() => dismissToast(id), 3000);
}

export function dismissToast(id: number) {
  toasts.value = toasts.value.filter((t) => t.id !== id);
}
