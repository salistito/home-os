from http import HTTPStatus

from starlette.responses import JSONResponse

from modules.food.types import (
    CookEvent,
    FoodNutritionGoals,
    FoodOperationStatus,
    Ingredient,
    IngredientPurchase,
    IngredientStock,
    MealEntry,
    MealEntryItem,
    Recipe,
    RecipeSummary,
)

_STATUS_HTTP = {
    FoodOperationStatus.INVALID_ID: HTTPStatus.BAD_REQUEST,
    FoodOperationStatus.INVALID_NAME: HTTPStatus.BAD_REQUEST,
    FoodOperationStatus.DUPLICATE_NAME: HTTPStatus.BAD_REQUEST,
    FoodOperationStatus.INVALID_UNIT: HTTPStatus.BAD_REQUEST,
    FoodOperationStatus.INVALID_MACROS: HTTPStatus.BAD_REQUEST,
    FoodOperationStatus.INVALID_PURCHASE_UNIT: HTTPStatus.BAD_REQUEST,
    FoodOperationStatus.INVALID_PURCHASE_CONVERSION_FACTOR: HTTPStatus.BAD_REQUEST,
    FoodOperationStatus.INVALID_QUANTITY: HTTPStatus.BAD_REQUEST,
    FoodOperationStatus.INVALID_PRICE: HTTPStatus.BAD_REQUEST,
    FoodOperationStatus.INVALID_PORTIONS: HTTPStatus.BAD_REQUEST,
    FoodOperationStatus.INSUFFICIENT_STOCK: HTTPStatus.CONFLICT,
    FoodOperationStatus.CANNOT_REVERT_PURCHASE: HTTPStatus.CONFLICT,
    FoodOperationStatus.INVALID_COOK_INGREDIENTS: HTTPStatus.BAD_REQUEST,
    FoodOperationStatus.INVALID_MEAL_TYPE: HTTPStatus.BAD_REQUEST,
    FoodOperationStatus.INVALID_MEAL_ITEM: HTTPStatus.BAD_REQUEST,
    FoodOperationStatus.INVALID_MEAL_ITEM_SOURCE: HTTPStatus.BAD_REQUEST,
    FoodOperationStatus.INVALID_EATEN_AT: HTTPStatus.BAD_REQUEST,
    FoodOperationStatus.NOT_FOUND: HTTPStatus.NOT_FOUND,
    FoodOperationStatus.EXTERNAL_NOT_FOUND: HTTPStatus.NOT_FOUND,
}

_STATUS_MESSAGE = {
    FoodOperationStatus.INVALID_ID: "Invalid ingredient ID.",
    FoodOperationStatus.INVALID_NAME: "Name cannot be empty.",
    FoodOperationStatus.DUPLICATE_NAME: "An item with that name already exists.",
    FoodOperationStatus.INVALID_MACROS: "Invalid macros format.",
    FoodOperationStatus.INVALID_PURCHASE_UNIT: "Purchase unit must be a non-empty string.",
    FoodOperationStatus.INVALID_PURCHASE_CONVERSION_FACTOR: "Conversion factor must be > 0.",
    FoodOperationStatus.INVALID_QUANTITY: "Quantity must be greater than 0.",
    FoodOperationStatus.INVALID_PRICE: "Price cannot be negative.",
    FoodOperationStatus.INVALID_UNIT: "Unit does not match the ingredient's default unit.",
    FoodOperationStatus.INVALID_PORTIONS: "Portions must be greater than 0.",
    FoodOperationStatus.INSUFFICIENT_STOCK: "Insufficient stock for one or more ingredients.",
    FoodOperationStatus.CANNOT_REVERT_PURCHASE: "Cannot revert purchase: stock already consumed.",
    FoodOperationStatus.INVALID_COOK_INGREDIENTS: (
        "Invalid cook ingredients: ingredient_id (int) and quantity > 0 required."
    ),
    FoodOperationStatus.INVALID_MEAL_TYPE: "Invalid meal type.",
    FoodOperationStatus.INVALID_MEAL_ITEM: "A meal must contain at least one item.",
    FoodOperationStatus.INVALID_MEAL_ITEM_SOURCE: "Invalid meal item source.",
    FoodOperationStatus.INVALID_EATEN_AT: "eaten_at is required and must be a non-empty string.",
    FoodOperationStatus.NOT_FOUND: "Not found.",
    FoodOperationStatus.EXTERNAL_NOT_FOUND: "Ingredient not found in external source.",
}


def serialize_ingredient(ingredient: Ingredient) -> dict:
    return {
        "id": ingredient.id,
        "name": ingredient.name,
        "category": ingredient.category,
        "unit": ingredient.unit,
        "macros": ingredient.macros.to_dict(),
        "purchase_unit": ingredient.purchase_unit,
        "purchase_conversion_factor": ingredient.purchase_conversion_factor,
        "external_source": ingredient.external_source,
        "external_id": ingredient.external_id,
        "created_at": ingredient.created_at,
        "updated_at": ingredient.updated_at,
    }


def serialize_stock(stock: IngredientStock) -> dict:
    return {
        "id": stock.id,
        "ingredient_id": stock.ingredient_id,
        "quantity": stock.quantity,
        "min_alert_quantity": stock.min_alert_quantity,
        "expiration_date": stock.expiration_date,
        "updated_at": stock.updated_at,
    }


def serialize_purchase(purchase: IngredientPurchase) -> dict:
    return {
        "id": purchase.id,
        "ingredient_id": purchase.ingredient_id,
        "quantity": purchase.quantity,
        "price": purchase.price,
        "purchased_at": purchase.purchased_at,
        "notes": purchase.notes,
        "created_at": purchase.created_at,
    }


def serialize_recipe_ingredient(ri) -> dict:
    result = {
        "id": ri.id,
        "recipe_id": ri.recipe_id,
        "ingredient_id": ri.ingredient_id,
        "quantity": ri.quantity,
        "unit": ri.unit,
    }
    if ri.ingredient:
        result["ingredient"] = {
            "id": ri.ingredient.id,
            "name": ri.ingredient.name,
            "unit": ri.ingredient.unit,
            "macros": ri.ingredient.macros.to_dict(),
            "purchase_unit": ri.ingredient.purchase_unit,
            "purchase_conversion_factor": ri.ingredient.purchase_conversion_factor,
        }
    return result


def serialize_recipe(recipe: Recipe) -> dict:
    return {
        "id": recipe.id,
        "name": recipe.name,
        "category": recipe.category,
        "description": recipe.description,
        "portions": recipe.portions,
        "steps": recipe.steps,
        "ingredients": [serialize_recipe_ingredient(ri) for ri in recipe.ingredients],
        "created_at": recipe.created_at,
        "updated_at": recipe.updated_at,
    }


def serialize_recipe_summary(rs: RecipeSummary) -> dict:
    return {
        "recipe": serialize_recipe(rs.recipe),
        "macros": {
            "total": rs.macros.total,
            "per_portion": rs.macros.per_portion,
        },
        "feasible": rs.feasible,
        "score": rs.score,
    }


def serialize_cook_event_ingredient(cei) -> dict:
    return {
        "id": cei.id,
        "ingredient_id": cei.ingredient_id,
        "ingredient_name": cei.ingredient_name,
        "quantity": cei.quantity,
        "unit": cei.unit,
        "macros": cei.macros.to_dict() if cei.macros is not None else None,
    }


def serialize_cook_event(ce: CookEvent) -> dict:
    return {
        "id": ce.id,
        "recipe_id": ce.recipe_id,
        "user_id": ce.user_id,
        "user_name": ce.user_name,
        "portions": ce.portions,
        "macros": {
            "total": ce.macros.total,
            "per_portion": ce.macros.per_portion,
        }
        if ce.macros is not None
        else None,
        "cooked_at": ce.cooked_at,
        "created_at": ce.created_at,
        "ingredients": [serialize_cook_event_ingredient(i) for i in ce.ingredients],
    }


def serialize_nutrition_goals(goals: FoodNutritionGoals) -> dict:
    return {
        "kcal_target": goals.kcal_target,
        "protein_g_target": goals.protein_g_target,
        "carbs_g_target": goals.carbs_g_target,
        "fat_g_target": goals.fat_g_target,
        "updated_at": goals.updated_at,
    }


def serialize_meal_entry(entry: MealEntry) -> dict:
    return {
        "id": entry.id,
        "user_id": entry.user_id,
        "user_name": entry.user_name,
        "meal_type": entry.meal_type,
        "macros": entry.macros,
        "notes": entry.notes,
        "eaten_at": entry.eaten_at,
        "created_at": entry.created_at,
        "items": [serialize_meal_entry_item(i) for i in entry.items],
    }


def serialize_meal_entry_item(item: MealEntryItem) -> dict:
    return {
        "id": item.id,
        "source": item.source,
        "name": item.name,
        "macros": item.macros,
        "cook_event_id": item.cook_event_id,
        "portions": item.portions,
    }


def insufficient_stock_response(missing_ingredient_ids: list[int]) -> JSONResponse:
    return JSONResponse(
        {
            "error": FoodOperationStatus.INSUFFICIENT_STOCK.value,
            "missing_ingredient_ids": missing_ingredient_ids,
        },
        status_code=HTTPStatus.CONFLICT,
    )


def error_response(status: FoodOperationStatus) -> JSONResponse:
    return JSONResponse(
        {"error": status.value, "message": _STATUS_MESSAGE[status]},
        status_code=_STATUS_HTTP[status],
    )
