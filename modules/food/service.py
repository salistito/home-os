from datetime import timedelta

from core.utils.date import get_today, to_db_date
from modules.food import external, repository
from modules.food.errors import IngredientAlreadyExistsError, InsufficientStockError
from modules.food.macros import (
    compute_cook_event_macros,
    compute_recipe_macros,
    scale_macros,
)
from modules.food.suggest import (
    nutrition_closeness,
    stock_covers,
    variety_score,
)
from modules.food.types import (
    CookEventIngredient,
    CookResult,
    FoodOperationResult,
    FoodOperationStatus,
    FoodUnit,
    GoalTarget,
    Ingredient,
    IngredientMacros,
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


def _to_ingredient_quantity_unit(
    ingredient: Ingredient,
    quantity_to_convert: float,
    unit_to_convert: str | None,
) -> tuple[float, FoodOperationStatus]:
    if unit_to_convert is None or unit_to_convert == ingredient.unit.value:
        return quantity_to_convert, FoodOperationStatus.OK
    if (
        ingredient.purchase_unit
        and ingredient.purchase_conversion_factor
        and unit_to_convert == ingredient.purchase_unit
    ):
        return quantity_to_convert * ingredient.purchase_conversion_factor, FoodOperationStatus.OK
    return 0.0, FoodOperationStatus.INVALID_UNIT


# Ingredients
def create_ingredient(
    name: str,
    category: str | None,
    unit: str,
    macros: dict,
    purchase_unit: str | None = None,
    purchase_conversion_factor: float | None = None,
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

    if purchase_unit is not None:
        purchase_unit = purchase_unit.strip() or None
        if purchase_unit is not None and (
            purchase_conversion_factor is None or purchase_conversion_factor <= 0
        ):
            return FoodOperationResult(
                status=FoodOperationStatus.INVALID_PURCHASE_CONVERSION_FACTOR
            )

    now = to_db_date(get_today())
    try:
        ingredient = repository.create_ingredient(
            name,
            category,
            parsed_unit,
            ingredient_macros,
            now,
            now,
            purchase_unit,
            purchase_conversion_factor,
            external_source,
            external_id,
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
    purchase_unit: str | None = None,
    purchase_conversion_factor: float | None = None,
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
    elif effective_unit != ingredient.macros.serving_unit:
        return FoodOperationResult(status=FoodOperationStatus.INVALID_UNIT)

    if purchase_unit is not None:
        purchase_unit = purchase_unit.strip()
    if purchase_conversion_factor is not None and purchase_conversion_factor <= 0:
        return FoodOperationResult(status=FoodOperationStatus.INVALID_PURCHASE_CONVERSION_FACTOR)

    kwargs: dict = {"updated_at": to_db_date(get_today())}
    if name is not None:
        kwargs["name"] = name
    if category is not None:
        kwargs["category"] = category if category.strip() else None
    if unit is not None:
        kwargs["unit"] = parsed_unit
    if macros is not None:
        kwargs["macros"] = ingredient_macros
    if purchase_unit is not None:
        if not purchase_unit:
            kwargs["purchase_unit"] = None
            kwargs["purchase_conversion_factor"] = None
        else:
            kwargs["purchase_unit"] = purchase_unit
    if purchase_conversion_factor is not None:
        kwargs["purchase_conversion_factor"] = purchase_conversion_factor

    repository.update_active_ingredient(ingredient_id, **kwargs)
    ingredient = repository.get_active_ingredient_by_id(ingredient_id)
    return FoodOperationResult(ingredient=ingredient, status=FoodOperationStatus.OK)


def delete_ingredient(ingredient_id: int) -> FoodOperationResult:
    ingredient = repository.get_active_ingredient_by_id(ingredient_id)
    if ingredient is None:
        return FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)

    repository.soft_delete_active_ingredient(ingredient_id)
    return FoodOperationResult(ingredient=ingredient, status=FoodOperationStatus.OK)


def search_ingredient_from_external(name: str, source: str = "openfoodfacts") -> list[dict]:
    name = name.strip()
    if not name:
        return []

    try:
        products = external.search_open_food_facts(name)
    except Exception:
        return []

    results = []
    for product in products:
        parsed = external.parse_off_product(product)
        if parsed is None:
            continue
        product_name, external_id, macros_dict = parsed
        macros = parse_macros(macros_dict)
        if macros is None:
            continue
        results.append(
            {
                "name": product_name,
                "external_id": external_id,
                "source": source,
                "macros": macros.to_dict(),
            }
        )
    return results


def import_ingredient_from_external(
    name: str, source: str = "openfoodfacts"
) -> FoodOperationResult:
    name = name.strip()
    if not name:
        return FoodOperationResult(status=FoodOperationStatus.INVALID_NAME)

    if repository.get_active_ingredient_by_name(name):
        return FoodOperationResult(status=FoodOperationStatus.DUPLICATE_NAME)

    try:
        products = external.search_open_food_facts(name)
    except Exception:
        return FoodOperationResult(status=FoodOperationStatus.EXTERNAL_NOT_FOUND)

    if not products:
        return FoodOperationResult(status=FoodOperationStatus.EXTERNAL_NOT_FOUND)

    parsed = external.parse_off_product(products[0])
    if parsed is None:
        return FoodOperationResult(status=FoodOperationStatus.EXTERNAL_NOT_FOUND)

    product_name, external_id, macros_dict = parsed
    ingredient_macros = parse_macros(macros_dict)
    if ingredient_macros is None:
        return FoodOperationResult(status=FoodOperationStatus.EXTERNAL_NOT_FOUND)

    parsed_unit = _parse_unit(macros_dict["serving_unit"])
    if parsed_unit is None:
        return FoodOperationResult(status=FoodOperationStatus.EXTERNAL_NOT_FOUND)

    now = to_db_date(get_today())
    try:
        ingredient = repository.create_ingredient(
            name=product_name,
            category=None,
            unit=parsed_unit,
            macros=ingredient_macros,
            created_at=now,
            updated_at=now,
            external_source=source,
            external_id=external_id,
        )
    except IngredientAlreadyExistsError as e:
        return FoodOperationResult(
            ingredient=e.ingredient, status=FoodOperationStatus.DUPLICATE_NAME
        )

    return FoodOperationResult(ingredient=ingredient, status=FoodOperationStatus.OK)


# Ingredients Stock
def set_stock(
    ingredient_id: int,
    quantity: float,
    unit: str | None = None,
    min_alert_quantity: float = 0.0,
    expiration_date: str | None = None,
) -> FoodOperationResult:
    ingredient = repository.get_active_ingredient_by_id(ingredient_id)
    if ingredient is None:
        return FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)

    if quantity < 0:
        return FoodOperationResult(status=FoodOperationStatus.INVALID_QUANTITY)

    converted_quantity, status = _to_ingredient_quantity_unit(ingredient, quantity, unit)
    if status != FoodOperationStatus.OK:
        return FoodOperationResult(status=status)

    updated_at = to_db_date(get_today())
    stock = repository.upsert_stock(
        ingredient_id, converted_quantity, min_alert_quantity, expiration_date, updated_at
    )
    return FoodOperationResult(stock=stock, status=FoodOperationStatus.OK)


def get_stock() -> list:
    return repository.get_stock()


def get_low_stock() -> list:
    return repository.get_low_stock()


def get_expiring_soon(days: int = 7) -> list:
    cutoff = to_db_date(get_today() + timedelta(days=days))
    return repository.get_expiring_soon(cutoff)


# Ingredients Purchase
def register_purchase(
    ingredient_id: int,
    quantity: float,
    price: int,
    purchased_at: str,
    unit: str | None = None,
    notes: str | None = None,
) -> FoodOperationResult:
    if quantity <= 0:
        return FoodOperationResult(status=FoodOperationStatus.INVALID_QUANTITY)
    if price < 0:
        return FoodOperationResult(status=FoodOperationStatus.INVALID_PRICE)

    ingredient = repository.get_active_ingredient_by_id(ingredient_id)
    if ingredient is None:
        return FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)

    converted_quantity, status = _to_ingredient_quantity_unit(ingredient, quantity, unit)
    if status != FoodOperationStatus.OK:
        return FoodOperationResult(status=status)

    created_at = to_db_date(get_today())
    purchase = repository.create_purchase(
        ingredient_id, converted_quantity, price, purchased_at, notes, created_at
    )
    repository.adjust_stock(ingredient_id, converted_quantity)
    return FoodOperationResult(purchase=purchase, status=FoodOperationStatus.OK)


def list_purchases(
    ingredient_id: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
) -> list:
    return repository.get_purchases(ingredient_id, from_date, to_date)


def delete_purchase(purchase_id: int) -> FoodOperationResult:
    purchase = repository.get_purchase_by_id(purchase_id)
    if purchase is None:
        return FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)

    stock = repository.get_stock_by_ingredient_id(purchase.ingredient_id)
    if stock is not None and stock.quantity < purchase.quantity:
        return FoodOperationResult(status=FoodOperationStatus.CANNOT_REVERT_PURCHASE)

    repository.adjust_stock(purchase.ingredient_id, -purchase.quantity)
    repository.delete_purchase(purchase_id)
    return FoodOperationResult(purchase=purchase, status=FoodOperationStatus.OK)


# Recipes
def create_recipe(
    name: str,
    portions: int,
    ingredients: list[dict],
    category: str | None = None,
    description: str | None = None,
    steps: list[str] | None = None,
) -> FoodOperationResult:
    name = name.strip()
    if not name:
        return FoodOperationResult(status=FoodOperationStatus.INVALID_NAME)
    if repository.get_active_recipe_by_name(name):
        return FoodOperationResult(status=FoodOperationStatus.DUPLICATE_NAME)
    if category is not None:
        category = category.strip() or None
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
    recipe = repository.create_recipe(name, category, description, portions, steps, now, now)
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


def _resolve_goal_target(user_id: int | None, goal_target: GoalTarget | None) -> GoalTarget | None:
    if user_id is None or goal_target is not None:
        return goal_target
    nutrition_goals = repository.get_nutrition_goals(user_id)
    if nutrition_goals is None:
        return None
    if not any(
        [
            nutrition_goals.kcal_target,
            nutrition_goals.protein_g_target,
            nutrition_goals.carbs_g_target,
            nutrition_goals.fat_g_target,
        ]
    ):
        return None
    return GoalTarget(
        kcal_target=nutrition_goals.kcal_target,
        protein_g_target=nutrition_goals.protein_g_target,
        carbs_g_target=nutrition_goals.carbs_g_target,
        fat_g_target=nutrition_goals.fat_g_target,
    )


def suggest_recipes(
    user_id: int | None = None,
    category: str | None = None,
    limit: int = 3,
    only_with_stock: bool = True,
    goal_target: GoalTarget | None = None,
    variety_days: int = 0,
) -> SuggestResult:
    goal_target = _resolve_goal_target(user_id, goal_target)

    use_variety = variety_days > 0
    recent_ids: list[int] = []
    if use_variety:
        from_date = to_db_date(get_today() - timedelta(days=variety_days))
        recent_ids = repository.get_cook_event_recipe_ids_since(from_date, category)

    if goal_target is not None:
        recipes = repository.get_suggested_recipes(category, limit * 10, only_with_stock)
    elif use_variety:
        recipes = repository.get_suggested_recipes(
            category, limit, only_with_stock, order_random=True, exclude_recipe_ids=recent_ids
        )
    else:
        recipes = repository.get_suggested_recipes(
            category, limit, only_with_stock, order_random=True
        )

    suggestions: list[RecipeSummary] = []
    for recipe in recipes:
        macros = compute_recipe_macros(recipe)
        feasible = True
        if not only_with_stock:
            feasible = all(stock_covers(ri.ingredient_id, ri.quantity) for ri in recipe.ingredients)
        score = 0.0
        if goal_target is not None:
            closeness = nutrition_closeness(macros.per_portion, goal_target)
            if use_variety:
                variety = variety_score(recipe.id, recent_ids)
                score = closeness * variety
            else:
                score = closeness
        suggestions.append(
            RecipeSummary(recipe=recipe, macros=macros, feasible=feasible, score=score)
        )

    if goal_target is not None:
        suggestions.sort(key=lambda s: s.score, reverse=True)
        suggestions = suggestions[:limit]

    return SuggestResult(recipes=suggestions, status=FoodOperationStatus.OK)


def update_recipe(
    recipe_id: int,
    name: str | None = None,
    category: str | None = None,
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
    if category is not None:
        kwargs["category"] = category.strip() or None
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
    user_id: int,
    portions_cooked: int,
    ingredients: list[dict] | None = None,
    cooked_at: str | None = None,
) -> CookResult:
    recipe = repository.get_active_recipe_by_id(recipe_id)
    if recipe is None:
        return CookResult(cook_event=None, macros=None, status=FoodOperationStatus.NOT_FOUND)

    if portions_cooked <= 0:
        return CookResult(cook_event=None, macros=None, status=FoodOperationStatus.INVALID_PORTIONS)

    now = to_db_date(get_today())
    cooked_at = cooked_at or now

    if ingredients is not None:
        if not ingredients:
            return CookResult(
                cook_event=None,
                macros=None,
                status=FoodOperationStatus.INVALID_COOK_INGREDIENTS,
            )

        cook_event_ingredients: list[CookEventIngredient] = []
        for raw in ingredients:
            if not isinstance(raw, dict):
                return CookResult(
                    cook_event=None,
                    macros=None,
                    status=FoodOperationStatus.INVALID_COOK_INGREDIENTS,
                )
            ingredient_id = raw.get("ingredient_id")
            quantity = raw.get("quantity")
            unit = raw.get("unit")

            if not isinstance(ingredient_id, int) or isinstance(ingredient_id, bool):
                return CookResult(
                    cook_event=None,
                    macros=None,
                    status=FoodOperationStatus.INVALID_COOK_INGREDIENTS,
                )
            if (
                not isinstance(quantity, (int, float))
                or isinstance(quantity, bool)
                or quantity <= 0
            ):
                return CookResult(
                    cook_event=None,
                    macros=None,
                    status=FoodOperationStatus.INVALID_QUANTITY,
                )

            db_ingredient = repository.get_active_ingredient_by_id(ingredient_id)
            if db_ingredient is None:
                return CookResult(
                    cook_event=None,
                    macros=None,
                    status=FoodOperationStatus.NOT_FOUND,
                )

            parsed_unit = FoodUnit(unit) if unit else db_ingredient.unit
            if parsed_unit != db_ingredient.unit:
                return CookResult(
                    cook_event=None,
                    macros=None,
                    status=FoodOperationStatus.INVALID_UNIT,
                )

            cook_event_ingredients.append(
                CookEventIngredient(
                    id=0,
                    cook_event_id=None,
                    ingredient_id=ingredient_id,
                    ingredient_name=db_ingredient.name,
                    quantity=float(quantity),
                    unit=parsed_unit,
                    macros=scale_macros(db_ingredient.macros, float(quantity), parsed_unit),
                )
            )
    else:
        if not recipe.ingredients:
            return CookResult(
                cook_event=None,
                macros=None,
                status=FoodOperationStatus.INVALID_COOK_INGREDIENTS,
            )

        scale = portions_cooked / recipe.portions
        cook_event_ingredients = []
        for ri in recipe.ingredients:
            if ri.ingredient is None:
                continue
            cook_event_ingredients.append(
                CookEventIngredient(
                    id=0,
                    cook_event_id=None,
                    ingredient_id=ri.ingredient_id,
                    ingredient_name=ri.ingredient.name,
                    quantity=ri.quantity * scale,
                    unit=ri.unit,
                    macros=scale_macros(ri.ingredient.macros, ri.quantity * scale, ri.unit),
                )
            )

        if not cook_event_ingredients:
            return CookResult(
                cook_event=None,
                macros=None,
                status=FoodOperationStatus.INVALID_COOK_INGREDIENTS,
            )

    macros = compute_cook_event_macros(cook_event_ingredients, portions_cooked)

    try:
        cook_event = repository.cook_recipe_transactional(
            recipe_id, user_id, portions_cooked, macros, cook_event_ingredients, cooked_at, now
        )
    except InsufficientStockError as e:
        return CookResult(
            cook_event=None,
            macros=None,
            status=FoodOperationStatus.INSUFFICIENT_STOCK,
            missing_ingredient_ids=[ing.id for ing in e.ingredients],
        )

    return CookResult(cook_event=cook_event, macros=macros, status=FoodOperationStatus.OK)


def list_cook_events(
    recipe_id: int | None = None,
    user_id: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
) -> list:
    return repository.get_cook_events(recipe_id, user_id, from_date, to_date)


# Nutrition Goals
def get_nutrition_goals(user_id: int) -> FoodOperationResult:
    goals = repository.get_nutrition_goals(user_id)
    if goals is None:
        return FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)
    return FoodOperationResult(goals=goals, status=FoodOperationStatus.OK)


def update_nutrition_goals(
    user_id: int,
    kcal_target: int | None = None,
    protein_g_target: float | None = None,
    carbs_g_target: float | None = None,
    fat_g_target: float | None = None,
) -> FoodOperationResult:
    if kcal_target is not None and not isinstance(kcal_target, int):
        return FoodOperationResult(status=FoodOperationStatus.INVALID_MACROS)
    for value in [protein_g_target, carbs_g_target, fat_g_target]:
        if value is not None and not isinstance(value, (int, float)):
            return FoodOperationResult(status=FoodOperationStatus.INVALID_MACROS)
    now = to_db_date(get_today())
    goals = repository.upsert_nutrition_goals(
        user_id=user_id,
        kcal_target=kcal_target,
        protein_g_target=protein_g_target,
        carbs_g_target=carbs_g_target,
        fat_g_target=fat_g_target,
        updated_at=now,
    )
    return FoodOperationResult(goals=goals, status=FoodOperationStatus.OK)
