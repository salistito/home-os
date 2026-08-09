import { computed, onBeforeUnmount, ref, type Ref } from "vue";

const THRESHOLD = 55;
const MAX_PULL = 90;
const RESISTANCE = 0.65;
const MIN_SPIN_MS = 500;

export function isTouchDevice() {
  if (typeof window === "undefined") return false;
  if (new URLSearchParams(window.location.search).has("ptr")) return true;
  return window.matchMedia("(pointer: coarse)").matches;
}

export function usePullToRefresh(
  target: Ref<HTMLElement | null>,
  onRefresh: () => unknown,
) {
  const distance = ref(0);
  const refreshing = ref(false);
  const dragging = ref(false);
  const enabled = isTouchDevice();

  const progress = computed(() => Math.min(1, distance.value / THRESHOLD));
  const active = computed(() => distance.value > 0 || refreshing.value);

  let startY = 0;
  let tracking = false;

  function onTouchStart(event: TouchEvent) {
    const el = target.value;
    if (!el || refreshing.value || event.touches.length !== 1) return;
    if (el.scrollTop > 0) return;
    startY = event.touches[0].clientY;
    tracking = true;
  }

  function onTouchMove(event: TouchEvent) {
    if (!tracking) return;
    const delta = event.touches[0].clientY - startY;
    if (delta <= 0) {
      distance.value = 0;
      return;
    }
    if (event.cancelable) event.preventDefault();
    dragging.value = true;
    distance.value = Math.min(MAX_PULL, delta * RESISTANCE);
  }

  async function onTouchEnd() {
    if (!tracking) return;
    tracking = false;
    dragging.value = false;
    if (distance.value < THRESHOLD) {
      distance.value = 0;
      return;
    }
    refreshing.value = true;
    distance.value = THRESHOLD;
    try {
      await Promise.all([
        onRefresh(),
        new Promise((resolve) => setTimeout(resolve, MIN_SPIN_MS)),
      ]);
    } finally {
      refreshing.value = false;
      distance.value = 0;
    }
  }

  function detach() {
    window.removeEventListener("touchstart", onTouchStart);
    window.removeEventListener("touchmove", onTouchMove);
    window.removeEventListener("touchend", onTouchEnd);
    window.removeEventListener("touchcancel", onTouchEnd);
  }

  if (enabled) {
    window.addEventListener("touchstart", onTouchStart, { passive: true });
    window.addEventListener("touchmove", onTouchMove, { passive: false });
    window.addEventListener("touchend", onTouchEnd);
    window.addEventListener("touchcancel", onTouchEnd);
    onBeforeUnmount(detach);
  }

  return { distance, refreshing, dragging, progress, active, enabled };
}
