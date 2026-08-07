export const MACRO_KEYS = ["kcal", "protein_g", "carbs_g", "fat_g", "fiber_g"] as const;

export type MacroKey = (typeof MACRO_KEYS)[number];

export type FoodUnit = "g" | "ml" | "unit" | "tablespoon";

export type ExternalSource = "openfoodfacts" | "usda"

export type MealType = "breakfast" | "lunch" | "dinner" | "snack";

export const MEAL_TYPE_LABELS: Record<MealType, string> = {
  breakfast: "Desayuno",
  lunch: "Almuerzo",
  dinner: "Cena",
  snack: "Snack",
};

export type MealItemSource = "cook_event" | "manual";

export interface IngredientMacros {
  serving_amount: number;
  serving_unit: string;
  kcal: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g: number;
}

export interface Ingredient {
  id: number;
  name: string;
  category: string | null;
  unit: FoodUnit;
  macros: IngredientMacros;
  purchase_unit: string | null;
  purchase_conversion_factor: number | null;
  external_source: string | null;
  external_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface IngredientStock {
  id: number;
  ingredient_id: number;
  quantity: number;
  min_alert_quantity: number;
  expiration_date: string | null;
  updated_at: string;
}

export interface IngredientPurchase {
  id: number;
  ingredient_id: number;
  quantity: number;
  price: number;
  purchased_at: string;
  notes: string | null;
  created_at: string;
}

export interface RecipeIngredient {
  id: number;
  recipe_id: number;
  ingredient_id: number;
  quantity: number;
  unit: string;
  ingredient?: {
    id: number;
    name: string;
    unit: string;
    macros: IngredientMacros;
    purchase_unit: string | null;
    purchase_conversion_factor: number | null;
  };
}

export interface Recipe {
  id: number;
  name: string;
  category: string | null;
  description: string | null;
  portions: number;
  steps: string[] | null;
  ingredients: RecipeIngredient[];
  created_at: string;
  updated_at: string;
}

export interface RecipeMacros {
  total: Record<string, number>;
  per_portion: Record<string, number>;
}

export interface RecipeSummary {
  recipe: Recipe;
  macros: RecipeMacros;
  feasible: boolean;
  score: number;
}

export interface CookEventIngredientRow {
  id: number;
  ingredient_id: number | null;
  quantity: number;
  unit: string;
  isOriginal: boolean;
  originalQuantity: number;
  originalIngredientId: number | null;
  edited: boolean;
}

export interface CookEventIngredient {
  id: number;
  ingredient_id: number;
  ingredient_name: string;
  quantity: number;
  unit: string;
  macros?: IngredientMacros;
}

export interface CookEvent {
  id: number;
  recipe_id: number;
  user_id: number;
  user_name: string;
  portions: number;
  macros: RecipeMacros | null;
  cooked_at: string;
  created_at: string;
  ingredients: CookEventIngredient[];
  remaining_portions: number;
}

export interface NutritionGoals {
  kcal_target: number | null;
  protein_g_target: number | null;
  carbs_g_target: number | null;
  fat_g_target: number | null;
  updated_at: string | null;
}

export interface MealEntryItem {
  id: number;
  source: MealItemSource;
  name: string;
  macros: Record<string, number>;
  cook_event_id: number | null;
  portions: number | null;

}

export interface MealEntry {
  id: number;
  user_id: number;
  user_name: string;
  meal_type: MealType;
  macros: Record<string, number>;
  notes: string | null;
  eaten_at: string;
  created_at: string;
  items: MealEntryItem[];
}

export type CreateIngredientPayload = {
  name: string;
  category: string | null;
  unit: FoodUnit;
  macros: IngredientMacros;
  purchase_unit: string | null;
  purchase_conversion_factor: number | null;
};

export type UpdateIngredientPayload = Partial<{
  name: string;
  category: string | null;
  unit: FoodUnit;
  macros: IngredientMacros;
  purchase_unit: string | null;
  purchase_conversion_factor: number | null;
}>;

export type SetStockPayload = {
  quantity: number;
  unit?: string;
  min_alert_quantity?: number;
  expiration_date?: string | null;
};

export type CreatePurchasePayload = {
  ingredient_id: number;
  quantity: number;
  unit?: string;
  price: number;
  purchased_at: string;
  notes?: string | null;
};

export type RecipeIngredientInput = {
  ingredient_id: number;
  quantity: number;
  unit: string;
};

export type CreateRecipePayload = {
  name: string;
  category?: string | null;
  description?: string | null;
  portions: number;
  steps?: string[] | null;
  ingredients: RecipeIngredientInput[];
};

export type UpdateRecipePayload = Partial<{
  name: string;
  category: string | null;
  description: string | null;
  portions: number;
  steps: string[] | null;
  ingredients: RecipeIngredientInput[];
}>;

export type CookRecipeIngredientOverride = {
  ingredient_id: number;
  quantity: number;
  unit: string;
};

export type CookRecipePayload = {
  portions: number;
  ingredients?: CookRecipeIngredientOverride[] | null;
  cooked_at?: string | null;
};

export type MealEntryItemInput = {
  source: MealItemSource;
  name?: string;
  macros?: Record<string, number>;
  cook_event_id?: number | null;
  portions?: number | null;
};

export type CreateMealPayload = {
  meal_type: MealType;
  notes?: string | null;
  eaten_at: string;
  items: MealEntryItemInput[];
};

export type UpdateMealPayload = Partial<{
  meal_type: MealType;
  notes: string | null;
  eaten_at: string;
  items: MealEntryItemInput[];
}>;

export interface ExternalSearchResult {
  name: string;
  external_id: string;
  source: string;
  macros: IngredientMacros;
}

export type ImportIngredientPayload = {
  name: string;
  source?: string;
};
