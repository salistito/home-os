import { computed, onBeforeUnmount, ref, watch, type Ref } from "vue";

const THRESHOLD = 70;
const MAX_PULL = 110;
const RESISTANCE = 0.5;
const MIN_SPIN_MS = 500;

export function isTouchDevice() {
  return (
    typeof window !== "undefined" &&
    window.matchMedia("(pointer: coarse)").matches
  );
}

export function usePullToRefresh(
  target: Ref<HTMLElement | null>,
  onRefresh: () => unknown,
) {
  const distance = ref(0);
  const refreshing = ref(false);
  const enabled = isTouchDevice();

  const progress = computed(() => Math.min(1, distance.value / THRESHOLD));
  const active = computed(() => distance.value > 0 || refreshing.value);

  let startY = 0;
  let tracking = false;
  let attached: HTMLElement | null = null;

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
    distance.value = Math.min(MAX_PULL, delta * RESISTANCE);
  }

  async function onTouchEnd() {
    if (!tracking) return;
    tracking = false;
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
    if (!attached) return;
    attached.removeEventListener("touchstart", onTouchStart);
    attached.removeEventListener("touchmove", onTouchMove);
    attached.removeEventListener("touchend", onTouchEnd);
    attached.removeEventListener("touchcancel", onTouchEnd);
    attached = null;
  }

  function attach(el: HTMLElement) {
    el.addEventListener("touchstart", onTouchStart, { passive: true });
    el.addEventListener("touchmove", onTouchMove, { passive: false });
    el.addEventListener("touchend", onTouchEnd);
    el.addEventListener("touchcancel", onTouchEnd);
    attached = el;
  }

  if (enabled) {
    watch(
      target,
      (el) => {
        detach();
        if (el) attach(el);
      },
      { immediate: true },
    );
    onBeforeUnmount(detach);
  }

  return { distance, refreshing, progress, active, enabled };
}
