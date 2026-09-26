import { ref, toValue, watch, type Ref } from "vue";
import { breakPeriodsApi } from "../api/breaks";
import { breakModules, type ModuleId } from "../modules";
import { type BreakPeriodInfo } from "../types";
import { daysOfWeek, getToday, startOfWeek } from "./date";
import { formatDate } from "./format";

const BREAK_MODULE_HINTS: Partial<Record<ModuleId, string>> = {
  tasks: "No se asignarán tareas nuevas y las pendientes se descartarán.",
  food: "Solo informativo: no bloquea ninguna funcionalidad.",
  fitness: "Solo informativo: no bloquea ninguna funcionalidad.",
};

export function breakModuleHint(module: ModuleId): string {
  return BREAK_MODULE_HINTS[module] ?? "";
}

function breakModuleRank(id: ModuleId): number {
  const index = breakModules.findIndex((m) => m.id === id);
  return index === -1 ? Number.MAX_SAFE_INTEGER : index;
}

export function sortedBreakModules(moduleIds: ModuleId[] | undefined): ModuleId[] {
  return [...(moduleIds ?? [])].sort((a, b) => breakModuleRank(a) - breakModuleRank(b));
}

export function formatBreakPeriodsChip(breakPeriods: BreakPeriodInfo[]): string {
  if (breakPeriods.length === 1 && breakPeriods[0]?.label) {
    return `🌴 ${breakPeriods[0].label}`;
  }
  return "🌴 En receso";
}

export function breakPeriodRangeLabel(breakPeriod: BreakPeriodInfo): string {
  if (!breakPeriod.end_date) {
    return `Desde el ${formatDate(breakPeriod.start_date)}`;
  }
  const days = breakPeriod.days;
  const daysSuffix = days != null ? ` (${days} ${days === 1 ? "día" : "días"})` : "";
  return `${formatDate(breakPeriod.start_date)} - ${formatDate(breakPeriod.end_date)}${daysSuffix}`;
}

export function formatBreakPeriodsTooltip(breakPeriods: BreakPeriodInfo[]): string {
  return breakPeriods
    .map((breakPeriod) => {
      const range = breakPeriodRangeLabel(breakPeriod);
      return breakPeriods.length > 1 && breakPeriod.label ? `${breakPeriod.label}: ${range}` : range;
    })
    .join(" · ");
}

function isDayOnBreakPeriod(breakPeriod: BreakPeriodInfo, day: string): boolean {
  if (day < breakPeriod.start_date) return false;
  if (breakPeriod.end_date && day > breakPeriod.end_date) return false;
  return true;
}

export function breakPeriodsOnDay(
  breakPeriods: BreakPeriodInfo[],
  day: string,
): BreakPeriodInfo[] {
  return breakPeriods.filter((breakPeriod) => isDayOnBreakPeriod(breakPeriod, day));
}

export function breakPeriodDaysIn(breakPeriods: BreakPeriodInfo[], days: string[]): Set<string> {
  return new Set(days.filter((day) => breakPeriodsOnDay(breakPeriods, day).length > 0));
}

export function useBreakPeriods(module: ModuleId, day?: Ref<string> | string) {
  let latestRequestId = 0;
  const breakPeriods = ref<BreakPeriodInfo[]>([]);
  watch(
    () => (day === undefined ? getToday() : startOfWeek(toValue(day))),
    async (value) => {
      const days = daysOfWeek(value);
      const requestId = ++latestRequestId;
      try {
        const response = await breakPeriodsApi.inRange({
          module,
          from_date: days[0],
          to_date: days[days.length - 1],
        });
        if (requestId === latestRequestId) breakPeriods.value = response.periods;
      } catch {
        if (requestId === latestRequestId) breakPeriods.value = [];
      }
    },
    { immediate: true },
  );
  return { breakPeriods };
}
