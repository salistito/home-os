from datetime import timedelta

from core.utils.date import get_today, to_db_date
from modules.food import repository
from modules.food.errors import IngredientAlreadyExistsError, InsufficientStockError
from modules.food.types import (
    MACROS_KEYS,
    CookResult,
    FoodOperationResult,
    FoodOperationStatus,
    FoodUnit,
    IngredientMacros,
    RecipeMacros,
    RecipeSummary,
    SuggestResult,
)


def _parse_unit(unit: str) -> FoodUnit | None:
    try:
        return FoodUnit(unit)
    except ValueError:
        return None


def parse_macros(macros: object) -> IngredientMacros | None:
    if not isinstance(macros, dict):
        return None
    try:
        return IngredientMacros.from_dict(macros)
    except ValueError:
        return None


# Ingredients
def create_ingredient(
    name: str,
    category: str | None,
    unit: str,
    macros: dict,
    external_source: str | None = None,
    external_id: str | None = None,
) -> FoodOperationResult:
    name = name.strip()
    if not name:
        return FoodOperationResult(status=FoodOperationStatus.INVALID_NAME)
    if repository.get_active_ingredient_by_name(name):
        return FoodOperationResult(status=FoodOperationStatus.DUPLICATE_NAME)

    parsed_unit = _parse_unit(unit)
    if parsed_unit is None:
        return FoodOperationResult(status=FoodOperationStatus.INVALID_UNIT)

    ingredient_macros = parse_macros(macros)
    if ingredient_macros is None:
        return FoodOperationResult(status=FoodOperationStatus.INVALID_MACROS)

    if parsed_unit != ingredient_macros.serving_unit:
        return FoodOperationResult(status=FoodOperationStatus.INVALID_UNIT)

    now = to_db_date(get_today())
    try:
        ingredient = repository.create_ingredient(
            name, category, parsed_unit, ingredient_macros, now, now, external_source, external_id
        )
    except IngredientAlreadyExistsError as e:
        return FoodOperationResult(
            ingredient=e.ingredient, status=FoodOperationStatus.DUPLICATE_NAME
        )

    return FoodOperationResult(ingredient=ingredient, status=FoodOperationStatus.OK)


def get_ingredient(ingredient_id: int) -> FoodOperationResult:
    ingredient = repository.get_active_ingredient_by_id(ingredient_id)
    if ingredient is None:
        return FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)
    return FoodOperationResult(ingredient=ingredient, status=FoodOperationStatus.OK)


def list_ingredients(category: str | None = None) -> list:
    return repository.get_active_ingredients(category)


def update_ingredient(
    ingredient_id: int,
    name: str | None = None,
    category: str | None = None,
    unit: str | None = None,
    macros: dict | None = None,
) -> FoodOperationResult:
    ingredient = repository.get_active_ingredient_by_id(ingredient_id)
    if ingredient is None:
        return FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)

    if name is not None:
        name = name.strip()
        if not name:
            return FoodOperationResult(status=FoodOperationStatus.INVALID_NAME)
        existing = repository.get_active_ingredient_by_name(name)
        if existing and existing.id != ingredient_id:
            return FoodOperationResult(status=FoodOperationStatus.DUPLICATE_NAME)

    parsed_unit = None
    if unit is not None:
        parsed_unit = _parse_unit(unit)
        if parsed_unit is None:
            return FoodOperationResult(status=FoodOperationStatus.INVALID_UNIT)
    effective_unit = parsed_unit if parsed_unit is not None else ingredient.unit

    if macros is not None:
        ingredient_macros = parse_macros(macros)
        if ingredient_macros is None:
            return FoodOperationResult(status=FoodOperationStatus.INVALID_MACROS)
        if effective_unit != ingredient_macros.serving_unit:
            return FoodOperationResult(status=FoodOperationStatus.INVALID_UNIT)

    kwargs: dict = {"updated_at": to_db_date(get_today())}
    if name is not None:
        kwargs["name"] = name
    if category is not None:
        kwargs["category"] = category if category.strip() else None
    if unit is not None:
        kwargs["unit"] = parsed_unit
    if macros is not None:
        kwargs["macros"] = ingredient_macros

    repository.update_active_ingredient(ingredient_id, **kwargs)
    ingredient = repository.get_active_ingredient_by_id(ingredient_id)
    return FoodOperationResult(ingredient=ingredient, status=FoodOperationStatus.OK)


def delete_ingredient(ingredient_id: int) -> FoodOperationResult:
    ingredient = repository.get_active_ingredient_by_id(ingredient_id)
    if ingredient is None:
        return FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)

    repository.soft_delete_active_ingredient(ingredient_id)
    return FoodOperationResult(ingredient=ingredient, status=FoodOperationStatus.OK)


# Ingredients Stock
def set_stock(
    ingredient_id: int,
    quantity: float,
    min_alert_quantity: float = 0.0,
    expiration_date: str | None = None,
) -> FoodOperationResult:
    if quantity < 0:
        return FoodOperationResult(status=FoodOperationStatus.INVALID_QUANTITY)

    ingredient = repository.get_active_ingredient_by_id(ingredient_id)
    if ingredient is None:
        return FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)

    updated_at = to_db_date(get_today())
    stock = repository.upsert_stock(
        ingredient_id, quantity, min_alert_quantity, expiration_date, updated_at
    )
    return FoodOperationResult(stock=stock, status=FoodOperationStatus.OK)


def get_stock() -> list:
    return repository.get_stock()


def get_low_stock() -> list:
    return repository.get_low_stock()


def get_expiring_soon(days: int = 7) -> list:
    cutoff = to_db_date(get_today() + timedelta(days=days))
    return repository.get_expiring_soon(cutoff)


def _stock_covers(ingredient_id: int, needed: float) -> bool:
    stock = repository.get_stock_by_ingredient_id(ingredient_id)
    return stock is not None and stock.quantity >= needed


# Ingredients Purchase
def register_purchase(
    ingredient_id: int,
    quantity: float,
    price: int,
    purchased_at: str,
    notes: str | None = None,
) -> FoodOperationResult:
    if quantity <= 0:
        return FoodOperationResult(status=FoodOperationStatus.INVALID_QUANTITY)
    if price < 0:
        return FoodOperationResult(status=FoodOperationStatus.INVALID_PRICE)

    ingredient = repository.get_active_ingredient_by_id(ingredient_id)
    if ingredient is None:
        return FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)

    created_at = to_db_date(get_today())
    purchase = repository.create_purchase(
        ingredient_id, quantity, price, purchased_at, notes, created_at
    )
    repository.adjust_stock(ingredient_id, quantity)
    return FoodOperationResult(purchase=purchase, status=FoodOperationStatus.OK)


def list_purchases(
    ingredient_id: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
) -> list:
    return repository.get_purchases(ingredient_id, from_date, to_date)


# Recipes
def create_recipe(
    name: str,
    portions: int,
    ingredients: list[dict],
    description: str | None = None,
    steps: list[str] | None = None,
) -> FoodOperationResult:
    name = name.strip()
    if not name:
        return FoodOperationResult(status=FoodOperationStatus.INVALID_NAME)
    if repository.get_active_recipe_by_name(name):
        return FoodOperationResult(status=FoodOperationStatus.DUPLICATE_NAME)
    if portions <= 0:
        return FoodOperationResult(status=FoodOperationStatus.INVALID_PORTIONS)

    clean_ingredients: list[tuple[int, float, FoodUnit]] = []
    for ingredient in ingredients:
        ingredient_id = ingredient.get("ingredient_id")
        quantity = ingredient.get("quantity")
        unit = ingredient.get("unit")

        if not isinstance(ingredient_id, int):
            return FoodOperationResult(status=FoodOperationStatus.INVALID_ID)

        if not isinstance(quantity, (int, float)):
            return FoodOperationResult(status=FoodOperationStatus.INVALID_QUANTITY)
        if quantity <= 0:
            return FoodOperationResult(status=FoodOperationStatus.INVALID_QUANTITY)

        if not isinstance(unit, str):
            return FoodOperationResult(status=FoodOperationStatus.INVALID_UNIT)
        parsed_unit = _parse_unit(unit)
        if parsed_unit is None:
            return FoodOperationResult(status=FoodOperationStatus.INVALID_UNIT)

        db_ingredient = repository.get_active_ingredient_by_id(ingredient_id)
        if db_ingredient is None:
            return FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)
        if parsed_unit != db_ingredient.unit:
            return FoodOperationResult(status=FoodOperationStatus.INVALID_UNIT)
        clean_ingredients.append((ingredient_id, quantity, parsed_unit))

    now = to_db_date(get_today())
    recipe = repository.create_recipe(name, portions, description, steps, now, now)
    repository.set_recipe_ingredients(recipe.id, clean_ingredients)
    recipe = repository.get_active_recipe_by_id(recipe.id)
    return FoodOperationResult(recipe=recipe, status=FoodOperationStatus.OK)


def get_recipe(recipe_id: int) -> FoodOperationResult:
    recipe = repository.get_active_recipe_by_id(recipe_id)
    if recipe is None:
        return FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)
    return FoodOperationResult(recipe=recipe, status=FoodOperationStatus.OK)


def list_recipes(ingredient_ids: list[int] | None = None) -> list:
    return repository.get_active_recipes(ingredient_ids)


def compute_recipe_macros(recipe) -> RecipeMacros:
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


def suggest_recipes(limit: int = 3, only_with_stock: bool = True) -> SuggestResult:
    recipes = repository.get_suggested_recipes(limit, only_with_stock)
    suggestions: list[RecipeSummary] = []
    for recipe in recipes:
        macros = compute_recipe_macros(recipe)
        feasible = True
        if not only_with_stock:
            feasible = all(
                _stock_covers(ri.ingredient_id, ri.quantity) for ri in recipe.ingredients
            )
        suggestions.append(RecipeSummary(recipe=recipe, macros=macros, feasible=feasible))
    return SuggestResult(recipes=suggestions, status=FoodOperationStatus.OK)


def update_recipe(
    recipe_id: int,
    name: str | None = None,
    portions: int | None = None,
    description: str | None = None,
    steps: list[str] | None = None,
    ingredients: list[dict] | None = None,
) -> FoodOperationResult:
    recipe = repository.get_active_recipe_by_id(recipe_id)
    if recipe is None:
        return FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)

    if name is not None:
        name = name.strip()
        if not name:
            return FoodOperationResult(status=FoodOperationStatus.INVALID_NAME)
        existing = repository.get_active_recipe_by_name(name)
        if existing and existing.id != recipe_id:
            return FoodOperationResult(status=FoodOperationStatus.DUPLICATE_NAME)

    if portions is not None and portions <= 0:
        return FoodOperationResult(status=FoodOperationStatus.INVALID_PORTIONS)

    if ingredients is not None:
        clean_ingredients: list[tuple[int, float, FoodUnit]] = []
        for ingredient in ingredients:
            ingredient_id = ingredient.get("ingredient_id")
            quantity = ingredient.get("quantity")
            unit = ingredient.get("unit")

            if not isinstance(ingredient_id, int):
                return FoodOperationResult(status=FoodOperationStatus.INVALID_ID)

            if not isinstance(quantity, (int, float)):
                return FoodOperationResult(status=FoodOperationStatus.INVALID_QUANTITY)
            if quantity <= 0:
                return FoodOperationResult(status=FoodOperationStatus.INVALID_QUANTITY)

            if not isinstance(unit, str):
                return FoodOperationResult(status=FoodOperationStatus.INVALID_UNIT)
            parsed_unit = _parse_unit(unit)
            if parsed_unit is None:
                return FoodOperationResult(status=FoodOperationStatus.INVALID_UNIT)

            db_ingredient = repository.get_active_ingredient_by_id(ingredient_id)
            if db_ingredient is None:
                return FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)
            if parsed_unit != db_ingredient.unit:
                return FoodOperationResult(status=FoodOperationStatus.INVALID_UNIT)
            clean_ingredients.append((ingredient_id, quantity, parsed_unit))
        repository.set_recipe_ingredients(recipe_id, clean_ingredients)

    kwargs: dict = {"updated_at": to_db_date(get_today())}
    if name is not None:
        kwargs["name"] = name
    if portions is not None:
        kwargs["portions"] = portions
    if description is not None:
        kwargs["description"] = description if description else None
    if steps is not None:
        kwargs["steps"] = steps

    repository.update_active_recipe(recipe_id, **kwargs)
    recipe = repository.get_active_recipe_by_id(recipe_id)
    return FoodOperationResult(recipe=recipe, status=FoodOperationStatus.OK)


def delete_recipe(recipe_id: int) -> FoodOperationResult:
    recipe = repository.get_active_recipe_by_id(recipe_id)
    if recipe is None:
        return FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)

    repository.soft_delete_active_recipe(recipe_id)
    return FoodOperationResult(recipe=recipe, status=FoodOperationStatus.OK)


# Cook Event
def cook_recipe(
    recipe_id: int,
    portions_cooked: int,
    cooked_at: str | None = None,
) -> CookResult:
    recipe = repository.get_active_recipe_by_id(recipe_id)
    if recipe is None:
        return CookResult(cook_event=None, macros=None, status=FoodOperationStatus.NOT_FOUND)

    if portions_cooked <= 0:
        return CookResult(cook_event=None, macros=None, status=FoodOperationStatus.INVALID_PORTIONS)

    now = to_db_date(get_today())
    cooked_at = cooked_at or now

    deltas = [
        (ri.ingredient_id, ri.quantity * (portions_cooked / recipe.portions))
        for ri in recipe.ingredients
    ]

    try:
        cook_event = repository.cook_recipe_transactional(
            recipe_id, portions_cooked, deltas, cooked_at, now
        )
    except InsufficientStockError as e:
        return CookResult(
            cook_event=None,
            macros=None,
            status=FoodOperationStatus.INSUFFICIENT_STOCK,
            missing_ingredient_ids=[ing.id for ing in e.ingredients],
        )

    macros = compute_recipe_macros(recipe)
    return CookResult(cook_event=cook_event, macros=macros, status=FoodOperationStatus.OK)


def list_cook_events(
    recipe_id: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
) -> list:
    return repository.get_cook_events(recipe_id, from_date, to_date)
