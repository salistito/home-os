import type { CookEvent, MacroKey, Recipe } from "../types";
import { icons } from "./icons";

export const MACRO_SHORT_LABELS: Record<MacroKey, string> = {
  kcal: "kcal",
  protein_g: "P (g)",
  carbs_g: "C (g)",
  fat_g: "G (g)",
  fiber_g: "F (g)",
};

export function recipeName(id: number, recipes: Recipe[]): string {
  return recipes.find((r) => r.id === id)?.name ?? `#${id}`;
}

export function cookEventPortions(
  event: CookEvent,
  cutoffDate: string,
): { label: string; classes: string; icon: string | null } {
  const remaining = Math.round(event.remaining_portions ?? 0);
  if (remaining <= 0) {
    return { label: "Consumida", classes: "bg-slate-50 text-slate-700 ring-1 ring-slate-200", icon: icons.utensils };
  }
  if (event.cooked_at.slice(0, 10) < cutoffDate) {
    return { label: "Expirada", classes: "bg-slate-50 text-slate-700 ring-1 ring-slate-200", icon: icons.clock };
  }
  const classes = remaining > event.portions / 2
    ? "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-100"
    : "bg-amber-50 text-amber-700 ring-1 ring-amber-100";
  return { label: `${remaining} porc.`, classes, icon: icons.utensils };
}
