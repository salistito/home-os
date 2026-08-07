import type { MacroKey, Recipe } from "../types";

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
