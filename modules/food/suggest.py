from modules.food import repository
from modules.food.types import (
    MACROS_KEYS,
    GoalTarget,
    RecipeMacros,
)

# Scoring helpers for suggest_recipes().
# compute_recipe_macros: aggregates ingredient macros into per-portion totals.
# nutrition_closeness: 0-1 score measuring how close a recipe matches a GoalTarget.
# variety_score: 0-1 score penalizing recently cooked recipes.
# stock_covers: checks if current stock is sufficient for a recipe ingredient.


def compute_recipe_macros(recipe) -> RecipeMacros:
    """
    Compute total and per-portion macros for a recipe.

    Iterates over recipe.ingredients, scales each ingredient's macros by
    (quantity / serving_amount), sums across all ingredients, then divides
    by recipe.portions. Returns a RecipeMacros with total and per_portion dicts.
    """
    total: dict = {key: 0.0 for key in MACROS_KEYS}
    for recipe_ingredient in recipe.ingredients:
        if recipe_ingredient.ingredient is None:
            continue
        macros_ref = recipe_ingredient.ingredient.macros
        factor = recipe_ingredient.quantity / macros_ref.serving_amount
        for macro in MACROS_KEYS:
            value = getattr(macros_ref, macro)
            if value is not None:
                total[macro] += value * factor
    per_portion = {k: round(v / recipe.portions, 2) for k, v in total.items()}
    return RecipeMacros(total=total, per_portion=per_portion)


def nutrition_closeness(per_portion: dict, target: GoalTarget) -> float:
    """
    Score how close per-portion macros are to the user's nutrition targets.

    Returns a value between 0 and 1 (1 = perfect match). Only targets that
    are non-None and > 0 are scored. For each scored macro, the absolute
    relative distance is clamped to 1.0, then averaged across scored metrics.
    Returns 1.0 if no targets are set.
    """
    scored_metrics = 0
    total_distance = 0.0
    targets = {
        "kcal": target.kcal_target,
        "protein_g": target.protein_g_target,
        "carbs_g": target.carbs_g_target,
        "fat_g": target.fat_g_target,
    }
    for macro, target_val in targets.items():
        if target_val is None or target_val == 0:
            continue
        actual = per_portion.get(macro, 0.0)
        distance = abs(actual - target_val) / target_val
        total_distance += min(distance, 1.0)
        scored_metrics += 1
    if scored_metrics == 0:
        return 1.0
    return 1.0 - (total_distance / scored_metrics)


def variety_score(recipe_id: int, recent_recipe_ids: list[int]) -> float:
    """
    Score recipe variety based on recent cook history.

    Returns 1.0 if the recipe was never cooked recently (max variety),
    down to 0.5 for the most recently cooked recipe. Recipes not in the
    list get 1.0. recent_recipe_ids should be ordered newest-first.
    """
    if not recent_recipe_ids:
        return 1.0
    try:
        position = recent_recipe_ids.index(recipe_id)
    except ValueError:
        return 1.0
    recency = 1.0 - (position / len(recent_recipe_ids))
    return 1.0 - (0.5 * recency)


def stock_covers(ingredient_id: int, needed: float) -> bool:
    """
    Check if the current stock of an ingredient covers the needed quantity.

    Returns True if stock exists and stock.quantity >= needed.
    """
    stock = repository.get_stock_by_ingredient_id(ingredient_id)
    return stock is not None and stock.quantity >= needed
