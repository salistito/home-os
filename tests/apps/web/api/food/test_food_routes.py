import json
from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.requests import Request

from apps.web.api.food.routes import (
    cook_recipe_handler,
    create_ingredient_handler,
    create_meal_entry_handler,
    create_purchase_handler,
    create_recipe_handler,
    delete_ingredient_handler,
    delete_meal_entry_handler,
    delete_purchase_handler,
    delete_recipe_handler,
    get_goals_handler,
    get_ingredient_handler,
    get_meal_entry_handler,
    get_recipe_handler,
    import_ingredient_handler,
    list_cook_events_handler,
    list_expiring_handler,
    list_ingredients_handler,
    list_low_stock_handler,
    list_meal_entries_handler,
    list_purchases_handler,
    list_recipes_handler,
    list_stock_handler,
    search_ingredient_handler,
    set_stock_handler,
    suggest_recipes_handler,
    update_goals_handler,
    update_ingredient_handler,
    update_meal_entry_handler,
    update_recipe_handler,
)
from modules.food.types import (
    CookEvent,
    CookResult,
    FoodNutritionGoals,
    FoodOperationResult,
    FoodOperationStatus,
    FoodUnit,
    Ingredient,
    IngredientMacros,
    IngredientPurchase,
    IngredientStock,
    MealEntry,
    MealEntryItem,
    MealItemSource,
    MealType,
    Recipe,
    RecipeIngredient,
    RecipeMacros,
    RecipeSummary,
    SuggestResult,
)


@pytest.fixture
def mock_request():
    req = MagicMock(spec=Request)
    req.path_params = {}
    req.query_params = {}
    req.json = AsyncMock()
    req.state = MagicMock()
    req.state.user_id = 1
    return req


_INGREDIENT = Ingredient(
    1,
    "Arroz",
    "granos",
    FoodUnit.G,
    IngredientMacros.from_dict(
        {
            "serving_amount": 100,
            "serving_unit": "g",
            "kcal": 350,
            "protein_g": 7,
            "carbs_g": 77,
            "fat_g": 1,
            "fiber_g": 1,
        }
    ),
    None,
    None,
    None,
    None,
    "2026-03-15",
    "2026-03-15",
    None,
)

_STOCK = IngredientStock(1, 1, 500.0, 100.0, None, "2026-03-15")

_PURCHASE = IngredientPurchase(1, 1, 1000.0, 5990, "2026-03-15", None, "2026-03-15")

_RECIPE_INGREDIENT = RecipeIngredient(1, 1, 1, 500.0, FoodUnit.G, _INGREDIENT)

_RECIPE = Recipe(
    1,
    "Pollo a la plancha",
    None,
    None,
    4,
    None,
    "2026-03-15",
    "2026-03-15",
    None,
    [_RECIPE_INGREDIENT],
)

_COOK_EVENT = CookEvent(1, 1, 1, "Admin", 2, None, "2026-03-15", "2026-03-15")
_COOK_EVENT_NO_INGREDIENTS = CookEvent(
    1,
    1,
    1,
    "Admin",
    2,
    RecipeMacros(total={"kcal": 875}, per_portion={"kcal": 437.5}),
    "2026-03-15",
    "2026-03-15",
)

_RECIPE_SUMMARY = RecipeSummary(
    recipe=_RECIPE,
    macros=RecipeMacros(total={"kcal": 1750}, per_portion={"kcal": 437.5}),
    feasible=True,
)


def _set_json(body):
    return body


# -- Ingredients --


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_ingredient_success(mock_request):
    mock_request.json.return_value = {
        "name": "Arroz",
        "category": "granos",
        "unit": "g",
        "macros": {"serving_amount": 100, "serving_unit": "g", "kcal": 350},
    }
    result = FoodOperationResult(ingredient=_INGREDIENT, status=FoodOperationStatus.OK)

    with patch("apps.web.api.food.routes.create_ingredient", return_value=result):
        resp = await create_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.CREATED
    body = json.loads(resp.body)
    assert body["name"] == "Arroz"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_ingredient_invalid_json(mock_request):
    mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

    resp = await create_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_ingredient_body_not_dict(mock_request):
    mock_request.json.return_value = ["not dict"]

    resp = await create_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_ingredient_missing_name(mock_request):
    mock_request.json.return_value = {
        "unit": "g",
        "macros": {"serving_amount": 100, "serving_unit": "g"},
    }

    resp = await create_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_ingredient_missing_unit(mock_request):
    mock_request.json.return_value = {
        "name": "Arroz",
        "macros": {"serving_amount": 100, "serving_unit": "g"},
    }

    resp = await create_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_ingredient_missing_macros(mock_request):
    mock_request.json.return_value = {"name": "Arroz", "unit": "g"}

    resp = await create_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_ingredient_duplicate(mock_request):
    mock_request.json.return_value = {
        "name": "Arroz",
        "unit": "g",
        "macros": {"serving_amount": 100, "serving_unit": "g"},
    }
    result = FoodOperationResult(status=FoodOperationStatus.DUPLICATE_NAME)

    with patch("apps.web.api.food.routes.create_ingredient", return_value=result):
        resp = await create_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_ingredients(mock_request):
    with patch("apps.web.api.food.routes.list_ingredients", return_value=[_INGREDIENT]):
        resp = await list_ingredients_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    body = json.loads(resp.body)
    assert len(body) == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_ingredients_with_category(mock_request):
    mock_request.query_params = {"category": "granos"}

    with patch("apps.web.api.food.routes.list_ingredients", return_value=[_INGREDIENT]) as mock_fn:
        resp = await list_ingredients_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    mock_fn.assert_called_once_with("granos")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_ingredient_success(mock_request):
    mock_request.path_params = {"id": 1}
    result = FoodOperationResult(ingredient=_INGREDIENT, status=FoodOperationStatus.OK)

    with patch("apps.web.api.food.routes.get_ingredient", return_value=result) as mock_fn:
        resp = await get_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    mock_fn.assert_called_once_with(1)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_ingredient_not_found(mock_request):
    mock_request.path_params = {"id": 999}
    result = FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)

    with patch("apps.web.api.food.routes.get_ingredient", return_value=result):
        resp = await get_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_ingredient_success(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {"name": "Updated"}
    result = FoodOperationResult(ingredient=_INGREDIENT, status=FoodOperationStatus.OK)

    with patch("apps.web.api.food.routes.update_ingredient", return_value=result):
        resp = await update_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_ingredient_invalid_json(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

    resp = await update_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_ingredient_body_not_dict(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = ["not dict"]

    resp = await update_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_ingredient_not_found(mock_request):
    mock_request.path_params = {"id": 999}
    mock_request.json.return_value = {"name": "X"}
    result = FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)

    with patch("apps.web.api.food.routes.update_ingredient", return_value=result):
        resp = await update_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_ingredient_success(mock_request):
    mock_request.path_params = {"id": 1}
    result = FoodOperationResult(ingredient=_INGREDIENT, status=FoodOperationStatus.OK)

    with patch("apps.web.api.food.routes.delete_ingredient", return_value=result):
        resp = await delete_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_ingredient_not_found(mock_request):
    mock_request.path_params = {"id": 999}
    result = FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)

    with patch("apps.web.api.food.routes.delete_ingredient", return_value=result):
        resp = await delete_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.NOT_FOUND


# -- IngredientStock --


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_stock(mock_request):
    with patch("apps.web.api.food.routes.get_stock", return_value=[_STOCK]):
        resp = await list_stock_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    body = json.loads(resp.body)
    assert len(body) == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_low_stock(mock_request):
    with patch("apps.web.api.food.routes.get_low_stock", return_value=[_STOCK]):
        resp = await list_low_stock_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_expiring(mock_request):
    mock_request.query_params = {"days": "14"}

    with patch("apps.web.api.food.routes.get_expiring_soon", return_value=[_STOCK]) as mock_fn:
        resp = await list_expiring_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    mock_fn.assert_called_once_with(14)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_expiring_default_days(mock_request):
    with patch("apps.web.api.food.routes.get_expiring_soon", return_value=[]) as mock_fn:
        resp = await list_expiring_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    mock_fn.assert_called_once_with(7)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_expiring_invalid_days(mock_request):
    mock_request.query_params = {"days": "abc"}

    resp = await list_expiring_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_set_stock_success(mock_request):
    mock_request.path_params = {"ingredient_id": 1}
    mock_request.json.return_value = {"quantity": 500, "min_alert_quantity": 100}
    result = FoodOperationResult(stock=_STOCK, status=FoodOperationStatus.OK)

    with patch("apps.web.api.food.routes.set_stock", return_value=result) as mock_fn:
        resp = await set_stock_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    mock_fn.assert_called_once_with(1, 500, None, 100, None)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_set_stock_invalid_json(mock_request):
    mock_request.path_params = {"ingredient_id": 1}
    mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

    resp = await set_stock_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_set_stock_missing_quantity(mock_request):
    mock_request.path_params = {"ingredient_id": 1}
    mock_request.json.return_value = {}

    resp = await set_stock_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_set_stock_invalid_min_alert(mock_request):
    mock_request.path_params = {"ingredient_id": 1}
    mock_request.json.return_value = {"quantity": 500, "min_alert_quantity": "abc"}

    resp = await set_stock_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_set_stock_not_found(mock_request):
    mock_request.path_params = {"ingredient_id": 999}
    mock_request.json.return_value = {"quantity": 500}
    result = FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)

    with patch("apps.web.api.food.routes.set_stock", return_value=result):
        resp = await set_stock_handler(mock_request)

    assert resp.status_code == HTTPStatus.NOT_FOUND


# -- Purchases --


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_purchase_success(mock_request):
    mock_request.json.return_value = {
        "ingredient_id": 1,
        "quantity": 1000,
        "price": 5990,
        "purchased_at": "2026-03-15",
    }
    result = FoodOperationResult(purchase=_PURCHASE, status=FoodOperationStatus.OK)

    with patch("apps.web.api.food.routes.register_purchase", return_value=result):
        resp = await create_purchase_handler(mock_request)

    assert resp.status_code == HTTPStatus.CREATED


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_purchase_invalid_json(mock_request):
    mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

    resp = await create_purchase_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_purchase_missing_ingredient_id(mock_request):
    mock_request.json.return_value = {"quantity": 1000, "price": 5990, "purchased_at": "2026-03-15"}

    resp = await create_purchase_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_purchase_not_found(mock_request):
    mock_request.json.return_value = {
        "ingredient_id": 999,
        "quantity": 1000,
        "price": 5990,
        "purchased_at": "2026-03-15",
    }
    result = FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)

    with patch("apps.web.api.food.routes.register_purchase", return_value=result):
        resp = await create_purchase_handler(mock_request)

    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_purchases(mock_request):
    with patch("apps.web.api.food.routes.list_purchases", return_value=[_PURCHASE]):
        resp = await list_purchases_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_purchases_with_filters(mock_request):
    mock_request.query_params = {
        "ingredient_id": "1",
        "from_date": "2026-01-01",
        "to_date": "2026-12-31",
    }

    with patch("apps.web.api.food.routes.list_purchases", return_value=[_PURCHASE]) as mock_fn:
        resp = await list_purchases_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    mock_fn.assert_called_once_with(1, "2026-01-01", "2026-12-31")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_purchases_invalid_ingredient_id(mock_request):
    mock_request.query_params = {"ingredient_id": "abc"}

    resp = await list_purchases_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


# -- Recipes --


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_recipe_success(mock_request):
    mock_request.json.return_value = {
        "name": "Pollo a la plancha",
        "portions": 4,
        "ingredients": [{"ingredient_id": 1, "quantity": 500, "unit": "g"}],
    }
    result = FoodOperationResult(recipe=_RECIPE, status=FoodOperationStatus.OK)

    with patch("apps.web.api.food.routes.create_recipe", return_value=result):
        resp = await create_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.CREATED


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_recipe_invalid_json(mock_request):
    mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

    resp = await create_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_recipe_body_not_dict(mock_request):
    mock_request.json.return_value = ["not dict"]

    resp = await create_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_recipe_missing_name(mock_request):
    mock_request.json.return_value = {"portions": 4, "ingredients": []}

    resp = await create_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_recipe_missing_portions(mock_request):
    mock_request.json.return_value = {"name": "X", "ingredients": []}

    resp = await create_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_recipe_boolean_portions(mock_request):
    mock_request.json.return_value = {"name": "X", "portions": True, "ingredients": []}

    resp = await create_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_recipe_missing_ingredients(mock_request):
    mock_request.json.return_value = {"name": "X", "portions": 4}

    resp = await create_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_recipe_duplicate(mock_request):
    mock_request.json.return_value = {
        "name": "X",
        "portions": 4,
        "ingredients": [{"ingredient_id": 1, "quantity": 500, "unit": "g"}],
    }
    result = FoodOperationResult(status=FoodOperationStatus.DUPLICATE_NAME)

    with patch("apps.web.api.food.routes.create_recipe", return_value=result):
        resp = await create_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_recipes(mock_request):
    with patch("apps.web.api.food.routes.list_recipes", return_value=[_RECIPE]):
        resp = await list_recipes_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_recipes_with_ingredient_ids(mock_request):
    mock_request.query_params = {"ingredient_ids": "1,2,3"}

    with patch("apps.web.api.food.routes.list_recipes", return_value=[_RECIPE]) as mock_fn:
        resp = await list_recipes_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    mock_fn.assert_called_once_with([1, 2, 3])


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_recipes_invalid_ingredient_ids(mock_request):
    mock_request.query_params = {"ingredient_ids": "1,abc,3"}

    resp = await list_recipes_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_recipe_success(mock_request):
    mock_request.path_params = {"id": 1}
    result = FoodOperationResult(recipe=_RECIPE, status=FoodOperationStatus.OK)

    with patch("apps.web.api.food.routes.get_recipe", return_value=result):
        resp = await get_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_recipe_not_found(mock_request):
    mock_request.path_params = {"id": 999}
    result = FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)

    with patch("apps.web.api.food.routes.get_recipe", return_value=result):
        resp = await get_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_recipe_success(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {"name": "Updated"}
    result = FoodOperationResult(recipe=_RECIPE, status=FoodOperationStatus.OK)

    with patch("apps.web.api.food.routes.update_recipe", return_value=result):
        resp = await update_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_recipe_invalid_json(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

    resp = await update_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_recipe_body_not_dict(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = ["not dict"]

    resp = await update_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_recipe_not_found(mock_request):
    mock_request.path_params = {"id": 999}
    mock_request.json.return_value = {"name": "X"}
    result = FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)

    with patch("apps.web.api.food.routes.update_recipe", return_value=result):
        resp = await update_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_recipe_invalid_name_type(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {"name": 123}

    resp = await update_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_recipe_invalid_ingredients_type(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {"ingredients": "not a list"}

    resp = await update_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_recipe_success(mock_request):
    mock_request.path_params = {"id": 1}
    result = FoodOperationResult(recipe=_RECIPE, status=FoodOperationStatus.OK)

    with patch("apps.web.api.food.routes.delete_recipe", return_value=result):
        resp = await delete_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_recipe_not_found(mock_request):
    mock_request.path_params = {"id": 999}
    result = FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)

    with patch("apps.web.api.food.routes.delete_recipe", return_value=result):
        resp = await delete_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.NOT_FOUND


# -- Suggest --


@pytest.mark.unit
@pytest.mark.asyncio
async def test_suggest_recipes(mock_request):
    suggest_result = SuggestResult(recipes=[_RECIPE_SUMMARY])
    mock_request.query_params = {"limit": "5"}

    with patch("apps.web.api.food.routes.suggest_recipes", return_value=suggest_result) as mock_fn:
        resp = await suggest_recipes_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    mock_fn.assert_called_once_with(
        user_id=1,
        limit=5,
        only_with_stock=True,
        goal_target=None,
        variety_days=0,
        category=None,
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_suggest_recipes_only_with_stock_false(mock_request):
    suggest_result = SuggestResult(recipes=[_RECIPE_SUMMARY])
    mock_request.query_params = {"only_with_stock": "false"}

    with patch("apps.web.api.food.routes.suggest_recipes", return_value=suggest_result) as mock_fn:
        resp = await suggest_recipes_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    mock_fn.assert_called_once_with(
        user_id=1,
        limit=3,
        only_with_stock=False,
        goal_target=None,
        variety_days=0,
        category=None,
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_suggest_recipes_invalid_limit(mock_request):
    mock_request.query_params = {"limit": "abc"}

    resp = await suggest_recipes_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


# -- Cook --


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cook_recipe_success(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {"portions": 2, "user_id": 5}
    cook_result = CookResult(
        cook_event=_COOK_EVENT_NO_INGREDIENTS,
        macros=RecipeMacros(total={"kcal": 875}, per_portion={"kcal": 437.5}),
        status=FoodOperationStatus.OK,
    )

    with patch("apps.web.api.food.routes.get_active_user_by_id", return_value=object()):
        with patch("apps.web.api.food.routes.cook_recipe", return_value=cook_result) as mock_fn:
            resp = await cook_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.CREATED
    mock_fn.assert_called_once_with(1, 5, 2, None, None)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cook_recipe_with_cooked_at(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {
        "portions": 2,
        "cooked_at": "2026-03-20",
        "user_id": 5,
    }
    cook_result = CookResult(
        cook_event=_COOK_EVENT_NO_INGREDIENTS,
        macros=RecipeMacros(total={}, per_portion={}),
        status=FoodOperationStatus.OK,
    )

    with patch("apps.web.api.food.routes.get_active_user_by_id", return_value=object()):
        with patch("apps.web.api.food.routes.cook_recipe", return_value=cook_result) as mock_fn:
            await cook_recipe_handler(mock_request)

    mock_fn.assert_called_once_with(1, 5, 2, None, "2026-03-20")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cook_recipe_with_user_id(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {"user_id": 5, "portions": 2}
    cook_result = CookResult(
        cook_event=_COOK_EVENT_NO_INGREDIENTS,
        macros=RecipeMacros(total={}, per_portion={}),
        status=FoodOperationStatus.OK,
    )

    with patch(
        "apps.web.api.food.routes.get_active_user_by_id", return_value=object()
    ) as mock_user:
        with patch("apps.web.api.food.routes.cook_recipe", return_value=cook_result) as mock_fn:
            resp = await cook_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.CREATED
    mock_user.assert_called_once_with(5)
    mock_fn.assert_called_once_with(1, 5, 2, None, None)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cook_recipe_user_id_not_int(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {"user_id": "5", "portions": 2}

    resp = await cook_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cook_recipe_user_id_inactive(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {"user_id": 5, "portions": 2}

    with patch("apps.web.api.food.routes.get_active_user_by_id", return_value=None):
        resp = await cook_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cook_recipe_missing_user_id(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {"portions": 2}

    resp = await cook_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cook_recipe_invalid_json(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

    resp = await cook_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cook_recipe_body_not_dict(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = ["not dict"]

    resp = await cook_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cook_recipe_missing_portions(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {}

    resp = await cook_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cook_recipe_boolean_portions(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {"portions": True}

    resp = await cook_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cook_recipe_insufficient_stock(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {"portions": 2, "user_id": 5}
    cook_result = CookResult(
        cook_event=None,
        macros=None,
        status=FoodOperationStatus.INSUFFICIENT_STOCK,
        missing_ingredient_ids=[1, 2],
    )

    with patch("apps.web.api.food.routes.get_active_user_by_id", return_value=object()):
        with patch("apps.web.api.food.routes.cook_recipe", return_value=cook_result):
            resp = await cook_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.CONFLICT
    body = json.loads(resp.body)
    assert body["missing_ingredient_ids"] == [1, 2]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cook_recipe_with_ingredients(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {
        "portions": 2,
        "ingredients": [{"ingredient_id": 1, "quantity": 200, "unit": "g"}],
        "user_id": 5,
    }
    cook_result = CookResult(
        cook_event=_COOK_EVENT_NO_INGREDIENTS,
        macros=RecipeMacros(total={"kcal": 875}, per_portion={"kcal": 437.5}),
        status=FoodOperationStatus.OK,
    )

    with patch("apps.web.api.food.routes.get_active_user_by_id", return_value=object()):
        with patch("apps.web.api.food.routes.cook_recipe", return_value=cook_result) as mock_fn:
            resp = await cook_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.CREATED
    mock_fn.assert_called_once()
    call = mock_fn.call_args
    assert call[0][3] == [{"ingredient_id": 1, "quantity": 200, "unit": "g"}]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cook_recipe_ingredients_not_list(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {
        "portions": 2,
        "ingredients": "not a list",
        "user_id": 5,
    }

    with patch("apps.web.api.food.routes.get_active_user_by_id", return_value=object()):
        resp = await cook_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cook_recipe_ingredients_item_not_dict(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {
        "portions": 2,
        "ingredients": ["bad"],
        "user_id": 5,
    }

    with patch("apps.web.api.food.routes.get_active_user_by_id", return_value=object()):
        resp = await cook_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cook_recipe_ingredients_missing_fields(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {"portions": 2, "ingredients": [{"name": "x"}]}

    resp = await cook_recipe_handler(mock_request)
    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cook_recipe_ingredients_bad_type(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {
        "portions": 2,
        "ingredients": [{"ingredient_id": "abc", "quantity": 100}],
    }

    resp = await cook_recipe_handler(mock_request)
    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cook_recipe_ingredients_bad_quantity(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {
        "portions": 2,
        "ingredients": [{"ingredient_id": 1, "quantity": "x"}],
    }

    resp = await cook_recipe_handler(mock_request)
    assert resp.status_code == HTTPStatus.BAD_REQUEST


# -- Cook Events --


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_cook_events(mock_request):
    with patch("apps.web.api.food.routes.list_cook_events", return_value=[_COOK_EVENT]):
        resp = await list_cook_events_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_cook_events_with_filters(mock_request):
    mock_request.query_params = {
        "recipe_id": "1",
        "from_date": "2026-01-01",
        "to_date": "2026-12-31",
    }

    with patch("apps.web.api.food.routes.list_cook_events", return_value=[_COOK_EVENT]) as mock_fn:
        resp = await list_cook_events_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    mock_fn.assert_called_once_with(
        recipe_id=1, user_id=None, from_date="2026-01-01", to_date="2026-12-31"
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_cook_events_invalid_recipe_id(mock_request):
    mock_request.query_params = {"recipe_id": "abc"}

    resp = await list_cook_events_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_recipe_boolean_portions(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {"portions": True}

    resp = await update_recipe_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_ingredient_with_category_listing(mock_request):
    mock_request.query_params = {"category": "granos"}

    with patch("apps.web.api.food.routes.list_ingredients", return_value=[_INGREDIENT]) as mock_fn:
        resp = await list_ingredients_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    mock_fn.assert_called_once_with("granos")


# -- Import ingredient --


@pytest.mark.unit
@pytest.mark.asyncio
async def test_import_ingredient_success(mock_request):
    mock_request.json.return_value = {"name": "arroz"}
    result = FoodOperationResult(ingredient=_INGREDIENT, status=FoodOperationStatus.OK)

    with patch("apps.web.api.food.routes.import_ingredient_from_external", return_value=result):
        resp = await import_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.CREATED


@pytest.mark.unit
@pytest.mark.asyncio
async def test_import_ingredient_not_found(mock_request):
    mock_request.json.return_value = {"name": "xyz"}
    result = FoodOperationResult(status=FoodOperationStatus.EXTERNAL_NOT_FOUND)

    with patch("apps.web.api.food.routes.import_ingredient_from_external", return_value=result):
        resp = await import_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.unit
@pytest.mark.asyncio
async def test_import_ingredient_empty_name(mock_request):
    mock_request.json.return_value = {"name": ""}

    resp = await import_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_import_ingredient_invalid_json(mock_request):
    mock_request.json.side_effect = json.JSONDecodeError("err", "", 0)

    resp = await import_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_ingredient_success(mock_request):
    mock_request.json.return_value = {"name": "arroz"}
    search_results = [
        {
            "name": "Arroz integral",
            "external_id": "123456",
            "source": "openfoodfacts",
            "macros": {
                "serving_amount": 100,
                "serving_unit": "g",
                "kcal": 350,
                "protein_g": 7.0,
                "carbs_g": 78.0,
                "fat_g": 2.5,
                "fiber_g": 3.5,
            },
        }
    ]

    with patch(
        "apps.web.api.food.routes.search_ingredient_from_external", return_value=search_results
    ):
        resp = await search_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_ingredient_empty_name(mock_request):
    mock_request.json.return_value = {"name": ""}

    resp = await search_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_ingredient_invalid_json(mock_request):
    mock_request.json.side_effect = json.JSONDecodeError("err", "", 0)

    resp = await search_ingredient_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


# -- Delete purchase --


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_purchase_success(mock_request):
    mock_request.path_params = {"id": 1}
    result = FoodOperationResult(purchase=_PURCHASE, status=FoodOperationStatus.OK)

    with patch("apps.web.api.food.routes.delete_purchase", return_value=result):
        resp = await delete_purchase_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_purchase_not_found(mock_request):
    mock_request.path_params = {"id": 999}
    result = FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)

    with patch("apps.web.api.food.routes.delete_purchase", return_value=result):
        resp = await delete_purchase_handler(mock_request)

    assert resp.status_code == HTTPStatus.NOT_FOUND


# -- Nutrition goals --


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_goals(mock_request):
    goals = FoodNutritionGoals(1, 1, 2000, 100, 250, 70, "2026-03-15")
    result = FoodOperationResult(goals=goals, status=FoodOperationStatus.OK)

    with patch("apps.web.api.food.routes.get_nutrition_goals", return_value=result) as mock_fn:
        resp = await get_goals_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    mock_fn.assert_called_once_with(1)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_goals_not_set(mock_request):
    result = FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)
    with patch("apps.web.api.food.routes.get_nutrition_goals", return_value=result):
        resp = await get_goals_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    data = json.loads(resp.body)
    assert data["kcal_target"] is None
    assert data["updated_at"] is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_goals(mock_request):
    mock_request.json.return_value = {"kcal_target": 2000, "protein_g_target": 100}
    goals = FoodNutritionGoals(1, 1, 2000, 100, None, None, "2026-03-15")
    result = FoodOperationResult(goals=goals, status=FoodOperationStatus.OK)

    with patch("apps.web.api.food.routes.update_nutrition_goals", return_value=result) as mock_fn:
        resp = await update_goals_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    mock_fn.assert_called_once_with(user_id=1, kcal_target=2000, protein_g_target=100)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_goals_empty_body(mock_request):
    mock_request.json.return_value = {}

    resp = await update_goals_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_goals_invalid_kcal_type(mock_request):
    mock_request.json.return_value = {"kcal_target": 2000.5}
    result = FoodOperationResult(status=FoodOperationStatus.INVALID_QUANTITY)

    with patch("apps.web.api.food.routes.update_nutrition_goals", return_value=result):
        resp = await update_goals_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_suggest_recipes_with_target(mock_request):
    suggest_result = SuggestResult(recipes=[_RECIPE_SUMMARY])
    mock_request.query_params = {
        "limit": "3",
        "kcal_target": "2000",
        "protein_g_target": "100",
    }

    with patch("apps.web.api.food.routes.suggest_recipes", return_value=suggest_result) as mock_fn:
        resp = await suggest_recipes_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    call_kwargs = mock_fn.call_args
    assert call_kwargs[1]["goal_target"] is not None
    assert call_kwargs[1]["goal_target"].kcal_target == 2000
    assert call_kwargs[1]["user_id"] == 1


# -- Meal entries --


_MEAL_ENTRY_ITEM = MealEntryItem(
    1,
    1,
    MealItemSource.MANUAL,
    "Hamburguesa",
    {"kcal": 1000.0, "protein_g": 40.0, "carbs_g": 60.0, "fat_g": 60.0, "fiber_g": 5.0},
    None,
    None,
)

_MEAL_ENTRY = MealEntry(
    1,
    1,
    "Admin",
    MealType.LUNCH,
    {"kcal": 1000.0, "protein_g": 40.0, "carbs_g": 60.0, "fat_g": 60.0, "fiber_g": 5.0},
    "restaurant",
    "2026-03-15T13:00",
    "2026-03-15",
    [_MEAL_ENTRY_ITEM],
)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_meal_entry_success(mock_request):
    mock_request.json.return_value = {
        "eaten_at": "2026-03-15T13:00",
        "meal_type": "lunch",
        "notes": "restaurant",
        "items": [{"source": "manual", "name": "Hamburguesa", "macros": {"kcal": 1000}}],
    }
    result = FoodOperationResult(meal_entry=_MEAL_ENTRY, status=FoodOperationStatus.OK)

    with patch("apps.web.api.food.routes.create_meal_entry", return_value=result) as mock_fn:
        resp = await create_meal_entry_handler(mock_request)

    assert resp.status_code == HTTPStatus.CREATED
    body = json.loads(resp.body)
    assert body["id"] == 1
    assert body["meal_type"] == "lunch"
    assert body["items"][0]["name"] == "Hamburguesa"
    call = mock_fn.call_args
    assert call[0][0] == 1
    assert call[0][1] == "lunch"
    assert call[0][2] == "2026-03-15T13:00"
    assert call[0][3] == [{"source": "manual", "name": "Hamburguesa", "macros": {"kcal": 1000}}]
    assert call[0][4] == "restaurant"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_meal_entry_invalid_json(mock_request):
    mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

    resp = await create_meal_entry_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_meal_entry_body_not_dict(mock_request):
    mock_request.json.return_value = ["not dict"]

    resp = await create_meal_entry_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_meal_entry_missing_eaten_at(mock_request):
    mock_request.json.return_value = {"meal_type": "lunch", "items": []}

    resp = await create_meal_entry_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_meal_entry_missing_meal_type(mock_request):
    mock_request.json.return_value = {"eaten_at": "2026-03-15T13:00", "items": []}

    resp = await create_meal_entry_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_meal_entry_items_not_list(mock_request):
    mock_request.json.return_value = {
        "eaten_at": "2026-03-15T13:00",
        "meal_type": "lunch",
        "items": "nope",
    }

    resp = await create_meal_entry_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_meal_entry_service_error(mock_request):
    mock_request.json.return_value = {
        "eaten_at": "2026-03-15T13:00",
        "meal_type": "brunch",
        "items": [],
    }
    result = FoodOperationResult(status=FoodOperationStatus.INVALID_MEAL_TYPE)

    with patch("apps.web.api.food.routes.create_meal_entry", return_value=result):
        resp = await create_meal_entry_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST
    body = json.loads(resp.body)
    assert body["error"] == "invalid_meal_type"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_meal_entry_insufficient_portions(mock_request):
    mock_request.json.return_value = {
        "eaten_at": "2026-03-15T13:00",
        "meal_type": "lunch",
        "items": [{"source": "cook_event", "cook_event_id": 7, "portions": 2}],
    }
    result = FoodOperationResult(status=FoodOperationStatus.INSUFFICIENT_PORTIONS)

    with patch("apps.web.api.food.routes.create_meal_entry", return_value=result):
        resp = await create_meal_entry_handler(mock_request)

    assert resp.status_code == HTTPStatus.CONFLICT
    body = json.loads(resp.body)
    assert body["error"] == "insufficient_portions"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_meal_entry_expired_cook_event(mock_request):
    mock_request.json.return_value = {
        "eaten_at": "2026-03-15T13:00",
        "meal_type": "lunch",
        "items": [{"source": "cook_event", "cook_event_id": 7, "portions": 2}],
    }
    result = FoodOperationResult(status=FoodOperationStatus.EXPIRED_COOK_EVENT)

    with patch("apps.web.api.food.routes.create_meal_entry", return_value=result):
        resp = await create_meal_entry_handler(mock_request)

    assert resp.status_code == HTTPStatus.CONFLICT
    body = json.loads(resp.body)
    assert body["error"] == "expired_cook_event"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_meal_entries(mock_request):
    mock_request.query_params = {"from_date": "2026-03-15", "to_date": "2026-03-15"}

    with patch("apps.web.api.food.routes.list_meal_entries", return_value=[_MEAL_ENTRY]) as mock_fn:
        resp = await list_meal_entries_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    body = json.loads(resp.body)
    assert len(body) == 1
    mock_fn.assert_called_once_with(1, "2026-03-15", "2026-03-15")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_meal_entry(mock_request):
    mock_request.path_params = {"id": 1}
    result = FoodOperationResult(meal_entry=_MEAL_ENTRY, status=FoodOperationStatus.OK)

    with patch("apps.web.api.food.routes.get_meal_entry", return_value=result) as mock_fn:
        resp = await get_meal_entry_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    body = json.loads(resp.body)
    assert body["id"] == 1
    mock_fn.assert_called_once_with(1, 1)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_meal_entry_not_found(mock_request):
    mock_request.path_params = {"id": 99}
    result = FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)

    with patch("apps.web.api.food.routes.get_meal_entry", return_value=result):
        resp = await get_meal_entry_handler(mock_request)

    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_meal_entry_success(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {"meal_type": "dinner"}
    result = FoodOperationResult(meal_entry=_MEAL_ENTRY, status=FoodOperationStatus.OK)

    with patch("apps.web.api.food.routes.update_meal_entry", return_value=result) as mock_fn:
        resp = await update_meal_entry_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    mock_fn.assert_called_once_with(1, 1, eaten_at=None, meal_type="dinner", items=None, notes=None)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_meal_entry_invalid_eaten_at(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {"eaten_at": 123}

    resp = await update_meal_entry_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_meal_entry_items_not_list(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {"items": "nope"}

    resp = await update_meal_entry_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_meal_entry_not_found(mock_request):
    mock_request.path_params = {"id": 99}
    mock_request.json.return_value = {"meal_type": "dinner"}
    result = FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)

    with patch("apps.web.api.food.routes.update_meal_entry", return_value=result):
        resp = await update_meal_entry_handler(mock_request)

    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_meal_entry(mock_request):
    mock_request.path_params = {"id": 1}
    result = FoodOperationResult(meal_entry=_MEAL_ENTRY, status=FoodOperationStatus.OK)

    with patch("apps.web.api.food.routes.delete_meal_entry", return_value=result) as mock_fn:
        resp = await delete_meal_entry_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    mock_fn.assert_called_once_with(1, 1)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_meal_entry_not_found(mock_request):
    mock_request.path_params = {"id": 99}
    result = FoodOperationResult(status=FoodOperationStatus.NOT_FOUND)

    with patch("apps.web.api.food.routes.delete_meal_entry", return_value=result):
        resp = await delete_meal_entry_handler(mock_request)

    assert resp.status_code == HTTPStatus.NOT_FOUND
