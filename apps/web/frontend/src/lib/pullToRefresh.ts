import { computed, onBeforeUnmount, ref, type Ref } from "vue";

const THRESHOLD = 55;
const MAX_PULL = 90;
const RESISTANCE = 0.5;
const MIN_SPIN_MS = 500;
const ARM_DELTA = 10;
const LOCK_DELTA = 10;
const COOLDOWN_MS = 400;

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
  let startX = 0;
  let phase: "idle" | "pending" | "pull" | "scroll" = "idle";
  let lastRefreshAt = 0;

  function onTouchStart(event: TouchEvent) {
    const el = target.value;
    if (!el || refreshing.value || event.touches.length !== 1) return;
    if (el.scrollTop > 0) return;
    if (!el.contains(event.target as Node)) return;
    if (Date.now() - lastRefreshAt < COOLDOWN_MS) return;
    startY = event.touches[0].clientY;
    startX = event.touches[0].clientX;
    phase = "pending";
  }

  function onTouchMove(event: TouchEvent) {
    if (phase === "idle" || phase === "scroll") return;
    const touch = event.touches[0];
    const dy = touch.clientY - startY;
    const dx = touch.clientX - startX;

    if (phase === "pending") {
      if (dy <= -ARM_DELTA || Math.abs(dx) > LOCK_DELTA) {
        phase = "scroll";
        distance.value = 0;
        return;
      }
      if (dy < ARM_DELTA) return;
      phase = "pull";
    }

    if (event.cancelable) event.preventDefault();
    dragging.value = true;
    distance.value = Math.min(
      MAX_PULL,
      Math.max(0, dy - ARM_DELTA) * RESISTANCE,
    );
  }

  async function onTouchEnd() {
    if (phase === "idle") return;
    const shouldRefresh = phase === "pull" && distance.value >= THRESHOLD;
    phase = "idle";
    dragging.value = false;
    if (!shouldRefresh) {
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
      lastRefreshAt = Date.now();
      refreshing.value = false;
      distance.value = 0;
    }
  }

  function onTouchCancel() {
    if (phase === "idle") return;
    phase = "idle";
    dragging.value = false;
    distance.value = 0;
  }

  function detach() {
    window.removeEventListener("touchstart", onTouchStart);
    window.removeEventListener("touchmove", onTouchMove);
    window.removeEventListener("touchend", onTouchEnd);
    window.removeEventListener("touchcancel", onTouchCancel);
  }

  if (enabled) {
    window.addEventListener("touchstart", onTouchStart, { passive: true });
    window.addEventListener("touchmove", onTouchMove, { passive: false });
    window.addEventListener("touchend", onTouchEnd);
    window.addEventListener("touchcancel", onTouchCancel);
    onBeforeUnmount(detach);
  }

  return { distance, refreshing, dragging, progress, active, enabled };
}
