import type { CookEvent, CookingSourceDetails, FoodUnit, MacroKey, MealType, Recipe } from "../types";
import { icons } from "./icons";

export const MACRO_SHORT_LABELS: Record<MacroKey, string> = {
  kcal: "kcal",
  protein_g: "P (g)",
  carbs_g: "C (g)",
  fat_g: "G (g)",
  fiber_g: "F (g)",
};

export const FOOD_UNIT_OPTIONS: { value: FoodUnit; label: string }[] = [
  { value: "g", label: "Gramos (g)" },
  { value: "ml", label: "Mililitros (ml)" },
  { value: "unit", label: "Unidad" },
  { value: "tablespoon", label: "Cucharada" },
];

export const FOOD_UNIT_LABELS: Record<FoodUnit, { singular: string; plural: string }> = {
  g: { singular: "g", plural: "g" },
  ml: { singular: "ml", plural: "ml" },
  unit: { singular: "unidad", plural: "unidades" },
  tablespoon: { singular: "cucharada", plural: "cucharadas" },
};

export const MEAL_TYPE_LABELS: Record<MealType, string> = {
  breakfast: "Desayuno",
  lunch: "Almuerzo",
  dinner: "Cena",
  snack: "Snack",
};

export function formatFoodUnit(unit: string, quantity?: number): string {
  const unitLabels = FOOD_UNIT_LABELS[unit as FoodUnit];
  if (!unitLabels) return unit;
  return quantity != null && quantity !== 1 ? unitLabels.plural : unitLabels.singular;
}

export function formatFoodUnitPlural(unit: string): string {
  const unitLabels = FOOD_UNIT_LABELS[unit as FoodUnit];
  return unitLabels?.plural ?? unit;
}

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

export function formatCookingAssignmentName(details: CookingSourceDetails): string {
  const { recipe_category, recipe_name } = details;
  if (recipe_category) {
    return `Cocinar ${recipe_category} (${recipe_name})`;
  }
  return `Cocinar (${recipe_name})`;
}
