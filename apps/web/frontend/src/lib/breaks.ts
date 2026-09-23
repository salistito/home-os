import { breakModuleOptions } from "../modules";
import { type BreakPeriodInfo } from "../types";
import { formatDate } from "./format";

export function breakModuleLabel(module: string): string {
  return breakModuleOptions.find((m) => m.value === module)?.label ?? module;
}

export function breakModuleIcon(module: string): string {
  return breakModuleOptions.find((m) => m.value === module)?.icon ?? "";
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