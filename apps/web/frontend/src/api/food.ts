import { api } from "./client";
import type {
  CookEvent,
  CookRecipePayload,
  CreateIngredientPayload,
  CreateMealPayload,
  CreatePurchasePayload,
  CreateRecipePayload,
  ExternalSearchResult,
  ImportIngredientPayload,
  Ingredient,
  IngredientPurchase,
  IngredientStock,
  MealEntry,
  NutritionGoals,
  Recipe,
  RecipeSummary,
  SetStockPayload,
  UpdateIngredientPayload,
  UpdateMealPayload,
  UpdateRecipePayload,
} from "../types";

export const foodApi = {
  createIngredient: (p: CreateIngredientPayload) =>
    api.post<Ingredient>("/food/ingredients", p),
  listIngredients: (category?: string) =>
    api.get<Ingredient[]>("/food/ingredients" + (category ? `?category=${category}` : ""),),
  searchExternal: (name: string) =>
    api.post<ExternalSearchResult[]>("/food/ingredients/search", { name }),
  importIngredient: (p: ImportIngredientPayload) =>
    api.post<Ingredient>("/food/ingredients/import", p),
  getIngredient: (id: number) =>
    api.get<Ingredient>(`/food/ingredients/${id}`),
  updateIngredient: (id: number, p: UpdateIngredientPayload) =>
    api.patch<Ingredient>(`/food/ingredients/${id}`, p),
  deleteIngredient: (id: number) =>
    api.delete<Ingredient>(`/food/ingredients/${id}`),

  listStock: () =>
    api.get<IngredientStock[]>("/food/stock"),
  listLowStock: () =>
    api.get<IngredientStock[]>("/food/stock/low"),
  listExpiring: (days = 7) =>
    api.get<IngredientStock[]>(`/food/stock/expiring?days=${days}`),
  setStock: (ingredientId: number, p: SetStockPayload) =>
    api.patch<IngredientStock>(`/food/stock/${ingredientId}`, p),

  createPurchase: (p: CreatePurchasePayload) =>
    api.post<IngredientPurchase>("/food/purchases", p),
  listPurchases: () =>
    api.get<IngredientPurchase[]>("/food/purchases"),
  deletePurchase: (id: number) =>
    api.delete<IngredientPurchase>(`/food/purchases/${id}`),

  createRecipe: (p: CreateRecipePayload) =>
    api.post<Recipe>("/food/recipes", p),
  listRecipes: () =>
    api.get<Recipe[]>("/food/recipes"),
  suggestRecipes: (params?: {
    category?: string;
    limit?: number;
    only_with_stock?: boolean;
    variety_days?: number;
  }) => {
    const q = new URLSearchParams();
    if (params?.category) q.set("category", params.category);
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.only_with_stock != null)
      q.set("only_with_stock", String(params.only_with_stock));
    if (params?.variety_days != null)
      q.set("variety_days", String(params.variety_days));
    const qs = q.toString();
    return api.get<RecipeSummary[]>(
      `/food/recipes/suggested${qs ? `?${qs}` : ""}`,
    );
  },
  getRecipe: (id: number) =>
    api.get<Recipe>(`/food/recipes/${id}`),
  updateRecipe: (id: number, p: UpdateRecipePayload) =>
    api.patch<Recipe>(`/food/recipes/${id}`, p),
  deleteRecipe: (id: number) =>
    api.delete<Recipe>(`/food/recipes/${id}`),

  cookRecipe: (
    id: number,
    p: CookRecipePayload,
  ) =>
    api.post<{
      cook_event: CookEvent;
      macros: { total: Record<string, number>; per_portion: Record<string, number> };
    }>(`/food/recipes/${id}/cook`, p),
  listCookEvents: (params?: { from_date?: string; to_date?: string }) => {
    const q = new URLSearchParams();
    if (params?.from_date) q.set("from_date", params.from_date);
    if (params?.to_date) q.set("to_date", params.to_date);
    const qs = q.toString();
    return api.get<CookEvent[]>(`/food/cook-events${qs ? `?${qs}` : ""}`);
  },

  getNutritionGoals: () =>
    api.get<NutritionGoals>("/food/nutrition-goals"),
  updateNutritionGoals: (p: Partial<NutritionGoals>) =>
    api.patch<NutritionGoals>("/food/nutrition-goals", p),


  createMeal: (p: CreateMealPayload) =>
    api.post<MealEntry>("/food/meals", p),
  listMeals: (params?: { from_date?: string; to_date?: string }) => {
    const q = new URLSearchParams();
    if (params?.from_date) q.set("from_date", params.from_date);
    if (params?.to_date) q.set("to_date", params.to_date);
    const qs = q.toString();
    return api.get<MealEntry[]>(`/food/meals${qs ? `?${qs}` : ""}`);
  },
  getMeal: (id: number) =>
    api.get<MealEntry>(`/food/meals/${id}`),
  updateMeal: (id: number, p: UpdateMealPayload) =>
    api.patch<MealEntry>(`/food/meals/${id}`, p),
  deleteMeal: (id: number) =>
    api.delete<MealEntry>(`/food/meals/${id}`),
};
