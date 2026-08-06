from modules.food.types import (
    MACROS_KEYS,
    IngredientMacros,
    RecipeMacros,
)


def _aggregate_macros(ingredients, portions, get_quantity, get_unit, get_macros):
    total: dict = {key: 0.0 for key in MACROS_KEYS}
    for ingredient in ingredients:
        macros = get_macros(ingredient)
        if macros is None:
            continue
        if get_unit(ingredient) != macros.serving_unit:
            continue
        factor = get_quantity(ingredient) / macros.serving_amount
        for macro in MACROS_KEYS:
            value = getattr(macros, macro)
            if value is not None:
                total[macro] += value * factor
    per_portion = {k: round(v / portions, 2) for k, v in total.items()}
    return RecipeMacros(total=total, per_portion=per_portion)


def compute_recipe_macros(recipe) -> RecipeMacros:
    return _aggregate_macros(
        recipe.ingredients,
        recipe.portions,
        lambda ri: ri.quantity,
        lambda ri: ri.unit,
        lambda ri: ri.ingredient.macros if ri.ingredient else None,
    )


def compute_cook_event_macros(cook_event_ingredients, portions) -> RecipeMacros:
    return _aggregate_macros(
        cook_event_ingredients,
        portions,
        lambda cei: cei.quantity,
        lambda cei: cei.unit,
        lambda cei: cei.macros,
    )


def compute_meal_macros(items) -> dict:
    total: dict = {key: 0.0 for key in MACROS_KEYS}
    for item in items:
        macros = getattr(item, "macros", None)
        if not isinstance(macros, dict):
            continue
        for key in MACROS_KEYS:
            value = macros.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                total[key] += value
    return {key: round(value, 2) for key, value in total.items()}


def scale_macros(macros: IngredientMacros, quantity: float, unit: str) -> IngredientMacros:
    factor = quantity / macros.serving_amount
    return IngredientMacros(
        serving_amount=quantity,
        serving_unit=unit,
        kcal=(macros.kcal * factor) if macros.kcal is not None else None,
        protein_g=(macros.protein_g * factor) if macros.protein_g is not None else None,
        carbs_g=(macros.carbs_g * factor) if macros.carbs_g is not None else None,
        fat_g=(macros.fat_g * factor) if macros.fat_g is not None else None,
        fiber_g=(macros.fiber_g * factor) if macros.fiber_g is not None else None,
    )
