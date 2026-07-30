import { ref } from "vue";

export const taskToggled = ref(0);

export function notifyTaskToggled() {
  taskToggled.value++;
}
