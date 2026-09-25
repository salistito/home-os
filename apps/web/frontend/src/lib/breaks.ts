import { breakModules, type ModuleId } from "../modules";
import { type BreakPeriodInfo } from "../types";
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

export function formatBreakPeriodsTooltip(breakPeriods: BreakPeriodInfo[]): string {
  return breakPeriods
    .map((breakPeriod) => {
      const days =
        breakPeriod.days != null ? ` (${breakPeriod.days} ${breakPeriod.days === 1 ? "día" : "días"})` : "";
      const range = breakPeriod.end_date
        ? `${formatDate(breakPeriod.start_date)} - ${formatDate(breakPeriod.end_date)}${days}`
        : `desde ${formatDate(breakPeriod.start_date)}`;
      return breakPeriod.label ? `${breakPeriod.label}: ${range}` : range;
    })
    .join(" · ");
}