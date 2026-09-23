import { modules, type ModuleOption } from "../modules";
import { type BreakPeriodInfo } from "../types";
import { formatDate } from "./format";

export const BREAK_MODULE_OPTIONS: ModuleOption[] = modules
  .filter((m) => m.canBeInBreak === true)
  .map((m) => ({ value: m.id, label: m.label, icon: m.icon }));

export function breakModuleLabel(module: string): string {
  return BREAK_MODULE_OPTIONS.find((m) => m.value === module)?.label ?? module;
}

export function breakModuleIcon(module: string): string {
  return BREAK_MODULE_OPTIONS.find((m) => m.value === module)?.icon ?? "";
}

export function formatBreakPeriodsTooltip(periods: BreakPeriodInfo[]): string {
  return periods
    .map((period) => {
      const days =
        period.days != null ? ` (${period.days} ${period.days === 1 ? "día" : "días"})` : "";
      const range = period.end_date
        ? `${formatDate(period.start_date)} - ${formatDate(period.end_date)}${days}`
        : `desde ${formatDate(period.start_date)}`;
      return period.label ? `${period.label}: ${range}` : range;
    })
    .join(" · ");
}